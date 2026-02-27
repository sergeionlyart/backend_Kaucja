from __future__ import annotations

import json
import mimetypes
import shutil
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence

from app.llm_client.base import LLMClient, LLMResult
from app.ocr_client.types import OCROptions, OCRResult
from app.pipeline.pack_documents import load_and_pack_documents
from app.pipeline.validate_output import ValidationResult, validate_output
from app.storage.artifacts import ArtifactsManager, DocumentArtifacts, RunArtifacts
from app.storage.models import OCRStatus
from app.storage.repo import StorageRepo
from app.storage.run_manifest import init_run_manifest, update_run_manifest
from app.utils.error_taxonomy import (
    ContextTooLargeError,
    build_error_details,
    classify_llm_api_error,
    classify_ocr_error,
    is_retryable_llm_exception,
    is_retryable_ocr_exception,
)
from app.utils.retry import run_with_retry


class OCRClientProtocol(Protocol):
    def process_document(
        self,
        *,
        input_path: Path,
        doc_id: str,
        options: OCROptions,
        output_dir: Path,
    ) -> OCRResult: ...


@dataclass(frozen=True, slots=True)
class OCRDocumentStageResult:
    doc_id: str
    ocr_status: OCRStatus
    pages_count: int | None
    combined_markdown_path: str
    ocr_artifacts_path: str
    ocr_error: str | None


@dataclass(frozen=True, slots=True)
class OcrStageResult:
    session_id: str
    run_id: str
    run_status: str
    documents: list[OCRDocumentStageResult]


@dataclass(frozen=True, slots=True)
class FullPipelineResult:
    session_id: str
    run_id: str
    run_status: str
    documents: list[OCRDocumentStageResult]
    critical_gaps_summary: list[str]
    next_questions_to_user: list[str]
    raw_json_text: str
    parsed_json: dict[str, Any] | None
    validation_valid: bool
    validation_errors: list[str]
    metrics: dict[str, Any]
    error_code: str | None
    error_message: str | None


_OCR_MAX_RETRIES = 1
_LLM_MAX_RETRIES = 1
_RETRY_BASE_DELAY_SECONDS = 0.2
_DEFAULT_CONTEXT_CHAR_LIMIT = 120_000


class OCRPipelineOrchestrator:
    def __init__(
        self,
        *,
        repo: StorageRepo,
        artifacts_manager: ArtifactsManager,
        ocr_client: OCRClientProtocol,
        llm_clients: dict[str, LLMClient] | None = None,
        prompt_root: Path | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.repo = repo
        self.artifacts_manager = artifacts_manager
        self.ocr_client = ocr_client
        self.llm_clients = llm_clients or {}
        self.prompt_root = prompt_root or Path("app/prompts")
        self.sleep_fn = sleep_fn

    def run_ocr_stage(
        self,
        *,
        input_files: Sequence[str | Path],
        session_id: str | None,
        provider: str,
        model: str,
        prompt_name: str,
        prompt_version: str,
        ocr_options: OCROptions,
    ) -> OcrStageResult:
        paths = _normalize_input_paths(input_files)
        if not paths:
            raise ValueError("At least one input file is required")

        session = self.repo.create_session(session_id=session_id or None)
        run = self.repo.create_run(
            session_id=session.session_id,
            provider=provider,
            model=model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            schema_version=prompt_version,
            status="running",
        )

        run_artifacts = self.artifacts_manager.ensure_run_structure(
            run.artifacts_root_path
        )
        init_run_manifest(
            artifacts_root_path=run.artifacts_root_path,
            session_id=session.session_id,
            run_id=run.run_id,
            inputs=_build_manifest_inputs(
                provider=provider,
                model=model,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                schema_version=prompt_version,
                ocr_options=ocr_options,
                llm_params={},
            ),
            artifacts={
                "root": str(run_artifacts.artifacts_root_path.resolve()),
                "run_log": str(run_artifacts.run_log_path.resolve()),
                "documents": [],
                "llm": {},
            },
            status="running",
        )
        ocr_stage = self._run_ocr_documents(
            run_id=run.run_id,
            run_artifacts=run_artifacts,
            input_paths=paths,
            ocr_options=ocr_options,
        )

        final_status = "failed" if ocr_stage.has_failures else "completed"
        error_code = ocr_stage.error_code if ocr_stage.has_failures else None
        error_message = ocr_stage.error_message if ocr_stage.has_failures else None
        timings = {
            "t_ocr_total_ms": ocr_stage.t_ocr_total_ms,
            "t_total_ms": ocr_stage.t_ocr_total_ms,
        }
        metrics_persist_error = _safe_update_run_metrics(
            repo=self.repo,
            run_id=run.run_id,
            timings_json=timings,
            usage_json={},
            usage_normalized_json={},
            cost_json={},
            run_log_path=run_artifacts.run_log_path,
        )
        status_persist_error = _safe_update_run_status(
            repo=self.repo,
            run_id=run.run_id,
            status=final_status,
            error_code=error_code,
            error_message=error_message,
            run_log_path=run_artifacts.run_log_path,
        )
        merged_error_code, merged_error_message = _merge_persistence_error(
            error_code=error_code or "UNKNOWN_ERROR",
            error_message=error_message or "Run finished with OCR issues.",
            persistence_errors=[metrics_persist_error, status_persist_error],
        )
        manifest_persist_error = _safe_update_manifest(
            artifacts_root_path=run.artifacts_root_path,
            run_log_path=run_artifacts.run_log_path,
            updates={
                "status": final_status,
                "stages": {
                    "ocr": {"status": final_status, "updated_at": _utc_now()},
                    "llm": {"status": "skipped", "updated_at": _utc_now()},
                    "finalize": {"status": final_status, "updated_at": _utc_now()},
                },
                "artifacts": {
                    "documents": _manifest_document_entries(ocr_stage.documents),
                },
                "metrics": {
                    "timings": timings,
                    "usage": {},
                    "usage_normalized": {},
                    "cost": {},
                },
                "validation": {
                    "valid": not ocr_stage.has_failures,
                    "errors": []
                    if not ocr_stage.has_failures
                    else [error_message or "One or more documents failed OCR"],
                },
                "error_code": error_code,
                "error_message": error_message,
            },
        )
        if manifest_persist_error is not None:
            merged_error_code, merged_error_message = _merge_persistence_error(
                error_code=merged_error_code,
                error_message=merged_error_message,
                persistence_errors=[manifest_persist_error],
            )
            _safe_append_run_log(
                run_artifacts.run_log_path,
                (
                    "Run finalization storage warning: "
                    f"{merged_error_code} ({merged_error_message})"
                ),
            )
        _append_run_log(
            run_artifacts.run_log_path,
            f"Run finished with status={final_status}",
        )

        return OcrStageResult(
            session_id=session.session_id,
            run_id=run.run_id,
            run_status=final_status,
            documents=ocr_stage.documents,
        )

    def run_full_pipeline(
        self,
        *,
        input_files: Sequence[str | Path],
        session_id: str | None,
        provider: str,
        model: str,
        prompt_name: str,
        prompt_version: str,
        ocr_options: OCROptions,
        llm_params: dict[str, Any] | None = None,
    ) -> FullPipelineResult:
        paths = _normalize_input_paths(input_files)
        if not paths:
            raise ValueError("At least one input file is required")

        started_at = time.perf_counter()
        llm_runtime_params = llm_params or {}
        session = self.repo.create_session(session_id=session_id or None)
        run = self.repo.create_run(
            session_id=session.session_id,
            provider=provider,
            model=model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            schema_version=prompt_version,
            status="running",
            openai_reasoning_effort=_to_optional_param(
                llm_runtime_params.get("openai_reasoning_effort")
            ),
            gemini_thinking_level=_to_optional_param(
                llm_runtime_params.get("gemini_thinking_level")
            ),
        )

        run_artifacts = self.artifacts_manager.ensure_run_structure(
            run.artifacts_root_path
        )
        llm_artifacts = self.artifacts_manager.create_llm_artifacts(
            artifacts_root_path=run.artifacts_root_path
        )
        init_run_manifest(
            artifacts_root_path=run.artifacts_root_path,
            session_id=session.session_id,
            run_id=run.run_id,
            inputs=_build_manifest_inputs(
                provider=provider,
                model=model,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                schema_version=prompt_version,
                ocr_options=ocr_options,
                llm_params=llm_runtime_params,
            ),
            artifacts={
                "root": str(run_artifacts.artifacts_root_path.resolve()),
                "run_log": str(run_artifacts.run_log_path.resolve()),
                "documents": [],
                "llm": {
                    "request_path": str(llm_artifacts.request_path.resolve()),
                    "response_raw_path": str(llm_artifacts.response_raw_path.resolve()),
                    "response_parsed_path": str(
                        llm_artifacts.response_parsed_path.resolve()
                    ),
                    "validation_path": str(llm_artifacts.validation_path.resolve()),
                },
            },
            status="running",
        )

        _append_run_log(
            run_artifacts.run_log_path, f"Run started with {len(paths)} files"
        )

        ocr_stage = self._run_ocr_documents(
            run_id=run.run_id,
            run_artifacts=run_artifacts,
            input_paths=paths,
            ocr_options=ocr_options,
        )
        update_run_manifest(
            artifacts_root_path=run.artifacts_root_path,
            updates={
                "stages": {
                    "ocr": {
                        "status": "failed" if ocr_stage.has_failures else "completed",
                        "updated_at": _utc_now(),
                    }
                },
                "artifacts": {
                    "documents": _manifest_document_entries(ocr_stage.documents),
                },
            },
        )

        if ocr_stage.has_failures:
            error_code = ocr_stage.error_code or "OCR_API_ERROR"
            error_message = (
                ocr_stage.error_message or "One or more documents failed OCR"
            )
            metrics = {
                "timings": {
                    "t_ocr_total_ms": ocr_stage.t_ocr_total_ms,
                    "t_total_ms": _elapsed_ms(started_at),
                },
                "usage": {},
                "usage_normalized": {},
                "cost": {},
            }
            metrics_persist_error = _safe_update_run_metrics(
                repo=self.repo,
                run_id=run.run_id,
                timings_json=metrics["timings"],
                usage_json=metrics["usage"],
                usage_normalized_json=metrics["usage_normalized"],
                cost_json=metrics["cost"],
                run_log_path=run_artifacts.run_log_path,
            )
            status_persist_error = _safe_update_run_status(
                repo=self.repo,
                run_id=run.run_id,
                status="failed",
                error_code=error_code,
                error_message=error_message,
                run_log_path=run_artifacts.run_log_path,
            )
            error_code, error_message = _merge_persistence_error(
                error_code=error_code,
                error_message=error_message,
                persistence_errors=[metrics_persist_error, status_persist_error],
            )
            manifest_persist_error = _safe_update_manifest(
                artifacts_root_path=run.artifacts_root_path,
                run_log_path=run_artifacts.run_log_path,
                updates={
                    "status": "failed",
                    "stages": {
                        "llm": {"status": "skipped", "updated_at": _utc_now()},
                        "finalize": {"status": "failed", "updated_at": _utc_now()},
                    },
                    "metrics": metrics,
                    "validation": {
                        "valid": False,
                        "errors": [error_message],
                    },
                    "error_code": error_code,
                    "error_message": error_message,
                },
            )
            if manifest_persist_error is not None:
                error_code, error_message = _merge_persistence_error(
                    error_code=error_code,
                    error_message=error_message,
                    persistence_errors=[manifest_persist_error],
                )
            _append_run_log(
                run_artifacts.run_log_path,
                f"Run failed after OCR stage: {error_code} ({error_message})",
            )

            return FullPipelineResult(
                session_id=session.session_id,
                run_id=run.run_id,
                run_status="failed",
                documents=ocr_stage.documents,
                critical_gaps_summary=[],
                next_questions_to_user=[],
                raw_json_text="",
                parsed_json=None,
                validation_valid=False,
                validation_errors=[error_message],
                metrics=metrics,
                error_code=error_code,
                error_message=error_message,
            )

        try:
            update_run_manifest(
                artifacts_root_path=run.artifacts_root_path,
                updates={
                    "stages": {"llm": {"status": "running", "updated_at": _utc_now()}}
                },
            )
            system_prompt, schema = self._load_prompt_assets(
                prompt_name=prompt_name,
                prompt_version=prompt_version,
            )
            packed_documents = load_and_pack_documents(ocr_stage.packed_documents)
            context_char_limit = int(
                llm_runtime_params.get("context_char_limit")
                or _DEFAULT_CONTEXT_CHAR_LIMIT
            )
            if len(packed_documents) > context_char_limit:
                raise ContextTooLargeError(
                    (
                        "Packed document payload exceeds context threshold: "
                        f"{len(packed_documents)} > {context_char_limit}"
                    )
                )
            _write_request_artifact(
                path=llm_artifacts.request_path,
                system_prompt=system_prompt,
                user_content=packed_documents,
            )

            llm_client = self._resolve_llm_client(provider)
            llm_result = run_with_retry(
                operation=lambda: llm_client.generate_json(
                    system_prompt=system_prompt,
                    user_content=packed_documents,
                    json_schema=schema,
                    model=model,
                    params=llm_runtime_params,
                    run_meta={
                        "session_id": session.session_id,
                        "run_id": run.run_id,
                        "schema_name": f"{prompt_name}_{prompt_version}",
                    },
                ),
                should_retry=is_retryable_llm_exception,
                max_retries=_LLM_MAX_RETRIES,
                base_delay_seconds=_RETRY_BASE_DELAY_SECONDS,
                sleep_fn=self.sleep_fn,
                on_retry=lambda retry_number, delay, error: _append_run_log(
                    run_artifacts.run_log_path,
                    (
                        "LLM transient error, retrying "
                        f"(retry={retry_number} delay={delay:.2f}s): {error}"
                    ),
                ),
            )
            _write_llm_success_artifacts(
                llm_result=llm_result,
                response_raw_path=llm_artifacts.response_raw_path,
                response_parsed_path=llm_artifacts.response_parsed_path,
            )

            validation = validate_output(
                parsed_json=llm_result.parsed_json, schema=schema
            )
            _write_validation_artifact(
                path=llm_artifacts.validation_path, validation=validation
            )

            self.repo.upsert_llm_output(
                run_id=run.run_id,
                response_json_path=str(llm_artifacts.response_parsed_path.resolve()),
                response_valid=validation.valid,
                schema_validation_errors_path=(
                    None
                    if validation.valid
                    else str(llm_artifacts.validation_path.resolve())
                ),
            )

            timings = {
                "t_ocr_total_ms": ocr_stage.t_ocr_total_ms,
                "t_llm_total_ms": llm_result.timings.get("t_llm_total_ms", 0.0),
                "t_total_ms": _elapsed_ms(started_at),
            }
            metrics = {
                "timings": timings,
                "usage": llm_result.usage_raw,
                "usage_normalized": llm_result.usage_normalized,
                "cost": llm_result.cost,
            }
            self.repo.update_run_metrics(
                run_id=run.run_id,
                timings_json=timings,
                usage_json=llm_result.usage_raw,
                usage_normalized_json=llm_result.usage_normalized,
                cost_json=llm_result.cost,
            )
            update_run_manifest(
                artifacts_root_path=run.artifacts_root_path,
                updates={
                    "stages": {
                        "llm": {"status": "completed", "updated_at": _utc_now()}
                    },
                    "metrics": metrics,
                    "validation": {
                        "valid": validation.valid,
                        "errors": validation.errors,
                    },
                },
            )

            if not validation.valid:
                error_message = "; ".join(validation.errors)
                self.repo.update_run_status(
                    run_id=run.run_id,
                    status="failed",
                    error_code="LLM_SCHEMA_INVALID",
                    error_message=error_message,
                )
                _append_run_log(
                    run_artifacts.run_log_path,
                    f"Validation failed: LLM_SCHEMA_INVALID ({error_message})",
                )
                update_run_manifest(
                    artifacts_root_path=run.artifacts_root_path,
                    updates={
                        "status": "failed",
                        "stages": {
                            "finalize": {
                                "status": "failed",
                                "updated_at": _utc_now(),
                            }
                        },
                        "error_code": "LLM_SCHEMA_INVALID",
                        "error_message": error_message,
                    },
                )
                return FullPipelineResult(
                    session_id=session.session_id,
                    run_id=run.run_id,
                    run_status="failed",
                    documents=ocr_stage.documents,
                    critical_gaps_summary=_extract_string_list(
                        llm_result.parsed_json.get("critical_gaps_summary")
                    ),
                    next_questions_to_user=_extract_string_list(
                        llm_result.parsed_json.get("next_questions_to_user")
                    ),
                    raw_json_text=llm_result.raw_text,
                    parsed_json=llm_result.parsed_json,
                    validation_valid=False,
                    validation_errors=validation.errors,
                    metrics=metrics,
                    error_code="LLM_SCHEMA_INVALID",
                    error_message=error_message,
                )

            self.repo.update_run_status(run_id=run.run_id, status="completed")
            _append_run_log(run_artifacts.run_log_path, "Run completed")
            update_run_manifest(
                artifacts_root_path=run.artifacts_root_path,
                updates={
                    "status": "completed",
                    "stages": {
                        "finalize": {"status": "completed", "updated_at": _utc_now()}
                    },
                    "error_code": None,
                    "error_message": None,
                },
            )

            return FullPipelineResult(
                session_id=session.session_id,
                run_id=run.run_id,
                run_status="completed",
                documents=ocr_stage.documents,
                critical_gaps_summary=_extract_string_list(
                    llm_result.parsed_json.get("critical_gaps_summary")
                ),
                next_questions_to_user=_extract_string_list(
                    llm_result.parsed_json.get("next_questions_to_user")
                ),
                raw_json_text=llm_result.raw_text,
                parsed_json=llm_result.parsed_json,
                validation_valid=True,
                validation_errors=[],
                metrics=metrics,
                error_code=None,
                error_message=None,
            )

        except ContextTooLargeError as error:
            context_error = str(error)
            error_code = "CONTEXT_TOO_LARGE"
            error_message = context_error
            llm_artifacts.response_raw_path.write_text(context_error, encoding="utf-8")
            llm_artifacts.response_parsed_path.write_text(
                json.dumps({}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            validation = ValidationResult(
                valid=False,
                schema_errors=[context_error],
                invariant_errors=[],
            )
            _write_validation_artifact(
                path=llm_artifacts.validation_path,
                validation=validation,
            )
            self.repo.upsert_llm_output(
                run_id=run.run_id,
                response_json_path=str(llm_artifacts.response_parsed_path.resolve()),
                response_valid=False,
                schema_validation_errors_path=str(
                    llm_artifacts.validation_path.resolve()
                ),
            )
            metrics = {
                "timings": {
                    "t_ocr_total_ms": ocr_stage.t_ocr_total_ms,
                    "t_total_ms": _elapsed_ms(started_at),
                },
                "usage": {},
                "usage_normalized": {},
                "cost": {},
            }
            metrics_persist_error = _safe_update_run_metrics(
                repo=self.repo,
                run_id=run.run_id,
                timings_json=metrics["timings"],
                usage_json=metrics["usage"],
                usage_normalized_json=metrics["usage_normalized"],
                cost_json=metrics["cost"],
                run_log_path=run_artifacts.run_log_path,
            )
            status_persist_error = _safe_update_run_status(
                repo=self.repo,
                run_id=run.run_id,
                status="failed",
                error_code=error_code,
                error_message=error_message,
                run_log_path=run_artifacts.run_log_path,
            )
            error_code, error_message = _merge_persistence_error(
                error_code=error_code,
                error_message=error_message,
                persistence_errors=[metrics_persist_error, status_persist_error],
            )
            manifest_persist_error = _safe_update_manifest(
                artifacts_root_path=run.artifacts_root_path,
                run_log_path=run_artifacts.run_log_path,
                updates={
                    "status": "failed",
                    "stages": {
                        "llm": {"status": "failed", "updated_at": _utc_now()},
                        "finalize": {"status": "failed", "updated_at": _utc_now()},
                    },
                    "metrics": metrics,
                    "validation": {
                        "valid": False,
                        "errors": validation.errors,
                    },
                    "error_code": error_code,
                    "error_message": error_message,
                },
            )
            if manifest_persist_error is not None:
                error_code, error_message = _merge_persistence_error(
                    error_code=error_code,
                    error_message=error_message,
                    persistence_errors=[manifest_persist_error],
                )
            _append_run_log(
                run_artifacts.run_log_path,
                f"Run failed before LLM call: {error_code} ({error_message})",
            )
            return FullPipelineResult(
                session_id=session.session_id,
                run_id=run.run_id,
                run_status="failed",
                documents=ocr_stage.documents,
                critical_gaps_summary=[],
                next_questions_to_user=[],
                raw_json_text=context_error,
                parsed_json=None,
                validation_valid=False,
                validation_errors=validation.errors,
                metrics=metrics,
                error_code=error_code,
                error_message=error_message,
            )

        except json.JSONDecodeError as error:
            llm_artifacts.response_raw_path.write_text(
                error.doc or "", encoding="utf-8"
            )
            validation = ValidationResult(
                valid=False,
                schema_errors=[f"JSON parse error: {error.msg}"],
                invariant_errors=[],
            )
            _write_validation_artifact(
                path=llm_artifacts.validation_path, validation=validation
            )
            self.repo.upsert_llm_output(
                run_id=run.run_id,
                response_json_path=str(llm_artifacts.response_parsed_path.resolve()),
                response_valid=False,
                schema_validation_errors_path=str(
                    llm_artifacts.validation_path.resolve()
                ),
            )
            metrics = {
                "timings": {
                    "t_ocr_total_ms": ocr_stage.t_ocr_total_ms,
                    "t_total_ms": _elapsed_ms(started_at),
                },
                "usage": {},
                "usage_normalized": {},
                "cost": {},
            }
            error_code = "LLM_INVALID_JSON"
            error_message = str(error)
            metrics_persist_error = _safe_update_run_metrics(
                repo=self.repo,
                run_id=run.run_id,
                timings_json=metrics["timings"],
                usage_json=metrics["usage"],
                usage_normalized_json=metrics["usage_normalized"],
                cost_json=metrics["cost"],
                run_log_path=run_artifacts.run_log_path,
            )
            status_persist_error = _safe_update_run_status(
                repo=self.repo,
                run_id=run.run_id,
                status="failed",
                error_code=error_code,
                error_message=error_message,
                run_log_path=run_artifacts.run_log_path,
            )
            error_code, error_message = _merge_persistence_error(
                error_code=error_code,
                error_message=error_message,
                persistence_errors=[metrics_persist_error, status_persist_error],
            )
            _append_run_log(
                run_artifacts.run_log_path,
                f"Run failed: {error_code} ({error_message})",
            )
            manifest_persist_error = _safe_update_manifest(
                artifacts_root_path=run.artifacts_root_path,
                run_log_path=run_artifacts.run_log_path,
                updates={
                    "status": "failed",
                    "stages": {
                        "llm": {"status": "failed", "updated_at": _utc_now()},
                        "finalize": {"status": "failed", "updated_at": _utc_now()},
                    },
                    "metrics": metrics,
                    "validation": {
                        "valid": False,
                        "errors": validation.errors,
                    },
                    "error_code": error_code,
                    "error_message": error_message,
                },
            )
            if manifest_persist_error is not None:
                error_code, error_message = _merge_persistence_error(
                    error_code=error_code,
                    error_message=error_message,
                    persistence_errors=[manifest_persist_error],
                )
            return FullPipelineResult(
                session_id=session.session_id,
                run_id=run.run_id,
                run_status="failed",
                documents=ocr_stage.documents,
                critical_gaps_summary=[],
                next_questions_to_user=[],
                raw_json_text=error.doc or "",
                parsed_json=None,
                validation_valid=False,
                validation_errors=validation.errors,
                metrics=metrics,
                error_code=error_code,
                error_message=error_message,
            )

        except Exception as error:  # noqa: BLE001
            error_code = classify_llm_api_error(error)
            error_details = build_error_details(error)
            stacktrace = traceback.format_exc()
            llm_artifacts.response_raw_path.write_text(
                f"{error_details}\n\n{stacktrace}",
                encoding="utf-8",
            )
            metrics = {
                "timings": {
                    "t_ocr_total_ms": ocr_stage.t_ocr_total_ms,
                    "t_total_ms": _elapsed_ms(started_at),
                },
                "usage": {},
                "usage_normalized": {},
                "cost": {},
            }
            metrics_persist_error = _safe_update_run_metrics(
                repo=self.repo,
                run_id=run.run_id,
                timings_json=metrics["timings"],
                usage_json=metrics["usage"],
                usage_normalized_json=metrics["usage_normalized"],
                cost_json=metrics["cost"],
                run_log_path=run_artifacts.run_log_path,
            )
            status_persist_error = _safe_update_run_status(
                repo=self.repo,
                run_id=run.run_id,
                status="failed",
                error_code=error_code,
                error_message=error_details,
                run_log_path=run_artifacts.run_log_path,
            )
            error_code, error_details = _merge_persistence_error(
                error_code=error_code,
                error_message=error_details,
                persistence_errors=[metrics_persist_error, status_persist_error],
            )
            manifest_persist_error = _safe_update_manifest(
                artifacts_root_path=run.artifacts_root_path,
                run_log_path=run_artifacts.run_log_path,
                updates={
                    "status": "failed",
                    "stages": {
                        "llm": {"status": "failed", "updated_at": _utc_now()},
                        "finalize": {"status": "failed", "updated_at": _utc_now()},
                    },
                    "metrics": metrics,
                    "validation": {
                        "valid": False,
                        "errors": [error_details],
                    },
                    "error_code": error_code,
                    "error_message": error_details,
                },
            )
            if manifest_persist_error is not None:
                error_code, error_details = _merge_persistence_error(
                    error_code=error_code,
                    error_message=error_details,
                    persistence_errors=[manifest_persist_error],
                )
            _append_run_log(
                run_artifacts.run_log_path,
                f"Run failed: {error_code} ({error_details})\n{stacktrace}",
            )
            return FullPipelineResult(
                session_id=session.session_id,
                run_id=run.run_id,
                run_status="failed",
                documents=ocr_stage.documents,
                critical_gaps_summary=[],
                next_questions_to_user=[],
                raw_json_text=error_details,
                parsed_json=None,
                validation_valid=False,
                validation_errors=[error_details],
                metrics=metrics,
                error_code=error_code,
                error_message=error_details,
            )

    def _run_ocr_documents(
        self,
        *,
        run_id: str,
        run_artifacts: RunArtifacts,
        input_paths: Sequence[Path],
        ocr_options: OCROptions,
    ) -> "_OcrStageInternals":
        started_at = time.perf_counter()
        documents: list[OCRDocumentStageResult] = []
        packed_documents: list[tuple[str, Path]] = []
        has_failures = False
        first_error_code: str | None = None
        first_error_message: str | None = None

        for index, source_path in enumerate(input_paths, start=1):
            doc_id = _build_doc_id(index)
            document_artifacts = self.artifacts_manager.create_document_artifacts(
                artifacts_root_path=run_artifacts.artifacts_root_path,
                doc_id=doc_id,
            )

            original_path = _store_original_file(
                source_path=source_path,
                document_artifacts=document_artifacts,
            )
            original_mime, _ = mimetypes.guess_type(source_path.name)

            self.repo.create_document(
                run_id=run_id,
                doc_id=doc_id,
                original_filename=source_path.name,
                original_mime=original_mime,
                original_path=str(original_path.resolve()),
                ocr_status="pending",
                ocr_artifacts_path=str(document_artifacts.ocr_dir.resolve()),
            )

            try:
                ocr_result = run_with_retry(
                    operation=lambda: self.ocr_client.process_document(
                        input_path=original_path,
                        doc_id=doc_id,
                        options=ocr_options,
                        output_dir=document_artifacts.ocr_dir,
                    ),
                    should_retry=is_retryable_ocr_exception,
                    max_retries=_OCR_MAX_RETRIES,
                    base_delay_seconds=_RETRY_BASE_DELAY_SECONDS,
                    sleep_fn=self.sleep_fn,
                    on_retry=lambda retry_number, delay, error: _append_run_log(
                        run_artifacts.run_log_path,
                        (
                            f"Doc {doc_id}: OCR transient error, retrying "
                            f"(retry={retry_number} delay={delay:.2f}s): {error}"
                        ),
                    ),
                )
                self.repo.update_document_ocr(
                    run_id=run_id,
                    doc_id=doc_id,
                    ocr_status="ok",
                    ocr_model=ocr_result.ocr_model,
                    pages_count=ocr_result.pages_count,
                    ocr_artifacts_path=str(document_artifacts.ocr_dir.resolve()),
                    ocr_error=None,
                )
                documents.append(
                    OCRDocumentStageResult(
                        doc_id=doc_id,
                        ocr_status="ok",
                        pages_count=ocr_result.pages_count,
                        combined_markdown_path=ocr_result.combined_markdown_path,
                        ocr_artifacts_path=str(document_artifacts.ocr_dir.resolve()),
                        ocr_error=None,
                    )
                )
                packed_documents.append(
                    (doc_id, Path(ocr_result.combined_markdown_path))
                )
                if ocr_result.converted_pdf_path:
                    try:
                        orig_size = original_path.stat().st_size
                        conv_size = Path(ocr_result.converted_pdf_path).stat().st_size
                        _append_run_log(
                            run_artifacts.run_log_path,
                            f"Doc {doc_id}: TXT pre-processed to PDF (size: {orig_size}B -> {conv_size}B) via {ocr_result.converted_pdf_path}",
                        )
                    except Exception as sz_err:  # noqa: BLE001
                        _append_run_log(
                            run_artifacts.run_log_path,
                            f"Doc {doc_id}: TXT converted to PDF but stats failed: {sz_err}",
                        )

                _append_run_log(run_artifacts.run_log_path, f"Doc {doc_id}: OCR ok")
            except Exception as error:  # noqa: BLE001
                has_failures = True
                error_code = classify_ocr_error(error)
                error_details = build_error_details(error)
                stacktrace = traceback.format_exc()
                if first_error_code is None:
                    first_error_code = error_code
                if first_error_message is None:
                    first_error_message = error_details
                self.repo.update_document_ocr(
                    run_id=run_id,
                    doc_id=doc_id,
                    ocr_status="failed",
                    ocr_model=ocr_options.model,
                    pages_count=None,
                    ocr_artifacts_path=str(document_artifacts.ocr_dir.resolve()),
                    ocr_error=f"{error_code}: {error_details}",
                )
                documents.append(
                    OCRDocumentStageResult(
                        doc_id=doc_id,
                        ocr_status="failed",
                        pages_count=None,
                        combined_markdown_path=str(
                            (document_artifacts.ocr_dir / "combined.md").resolve()
                        ),
                        ocr_artifacts_path=str(document_artifacts.ocr_dir.resolve()),
                        ocr_error=f"{error_code}: {error_details}",
                    )
                )
                _append_run_log(
                    run_artifacts.run_log_path,
                    f"Doc {doc_id}: OCR failed ({error_code}) {error_details}\n{stacktrace}",
                )

        return _OcrStageInternals(
            documents=documents,
            packed_documents=packed_documents,
            has_failures=has_failures,
            t_ocr_total_ms=_elapsed_ms(started_at),
            error_code=first_error_code,
            error_message=first_error_message,
        )

    def _resolve_llm_client(self, provider: str) -> LLMClient:
        llm_client = self.llm_clients.get(provider)
        if llm_client is None:
            raise ValueError(f"LLM client not configured for provider: {provider}")

        return llm_client

    def _load_prompt_assets(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
    ) -> tuple[str, dict[str, Any]]:
        prompt_dir = self.prompt_root / prompt_name / prompt_version
        requested_prompt_path = prompt_dir / "system_prompt.txt"
        requested_schema_path = prompt_dir / "schema.json"

        if not requested_prompt_path.exists():
            raise FileNotFoundError(
                f"Requested Prompt not found: {requested_prompt_path}"
            )
        if not requested_schema_path.exists():
            raise FileNotFoundError(
                f"Requested Schema not found: {requested_schema_path}"
            )

        system_prompt = requested_prompt_path.read_text(encoding="utf-8")
        schema_text = requested_schema_path.read_text(encoding="utf-8")

        # Enforce canonical TechSpec Lock: the requested files MUST match the canonical versions.
        canonical_prompt_path = Path("app/prompts/canonical_prompt.txt")
        canonical_schema_path = Path("app/schemas/canonical_schema.json")

        if canonical_prompt_path.exists():
            canonical_prompt_text = canonical_prompt_path.read_text(encoding="utf-8")
            if system_prompt != canonical_prompt_text:
                raise ValueError(
                    f"Requested prompt version '{prompt_version}' violates the byte-for-byte canonical TechSpec lock."
                )

        if canonical_schema_path.exists():
            canonical_schema_text = canonical_schema_path.read_text(encoding="utf-8")
            try:
                canonical_schema_json = json.loads(canonical_schema_text)
                requested_schema_json = json.loads(schema_text)
                if requested_schema_json != canonical_schema_json:
                    raise ValueError(
                        f"Requested schema version '{prompt_version}' violates the exact canonical TechSpec lock."
                    )
            except json.JSONDecodeError:
                pass  # Handled by the next block if requested schema is invalid

        schema = json.loads(schema_text)

        if not isinstance(schema, dict):
            raise ValueError("Schema must be a JSON object")

        return system_prompt, schema


@dataclass(frozen=True, slots=True)
class _OcrStageInternals:
    documents: list[OCRDocumentStageResult]
    packed_documents: list[tuple[str, Path]]
    has_failures: bool
    t_ocr_total_ms: float
    error_code: str | None
    error_message: str | None


def _normalize_input_paths(input_files: Sequence[str | Path]) -> list[Path]:
    paths: list[Path] = []
    for input_file in input_files:
        path = Path(input_file)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")
        paths.append(path)
    return paths


def _build_doc_id(index: int) -> str:
    return f"{index:07d}"


def _store_original_file(
    *,
    source_path: Path,
    document_artifacts: DocumentArtifacts,
) -> Path:
    destination_path = document_artifacts.original_dir / source_path.name
    shutil.copy2(source_path, destination_path)
    return destination_path


def _append_run_log(log_path: Path, message: str) -> None:
    with log_path.open("a", encoding="utf-8") as file:
        file.write(message)
        file.write("\n")


def _write_request_artifact(
    *,
    path: Path,
    system_prompt: str,
    user_content: str,
) -> None:
    payload = (
        "<SYSTEM_PROMPT>\n"
        f"{system_prompt}\n"
        "</SYSTEM_PROMPT>\n\n"
        "<USER_CONTENT>\n"
        f"{user_content}\n"
        "</USER_CONTENT>\n"
    )
    path.write_text(payload, encoding="utf-8")


def _write_llm_success_artifacts(
    *,
    llm_result: LLMResult,
    response_raw_path: Path,
    response_parsed_path: Path,
) -> None:
    response_raw_path.write_text(llm_result.raw_text, encoding="utf-8")
    response_parsed_path.write_text(
        json.dumps(llm_result.parsed_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _write_validation_artifact(*, path: Path, validation: ValidationResult) -> None:
    payload = {
        "valid": validation.valid,
        "schema_errors": validation.schema_errors,
        "invariant_errors": validation.invariant_errors,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _elapsed_ms(started_at: float) -> float:
    return (time.perf_counter() - started_at) * 1000


def _extract_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _build_manifest_inputs(
    *,
    provider: str,
    model: str,
    prompt_name: str,
    prompt_version: str,
    schema_version: str,
    ocr_options: OCROptions,
    llm_params: dict[str, Any],
) -> dict[str, Any]:
    return {
        "provider": provider,
        "model": model,
        "prompt_name": prompt_name,
        "prompt_version": prompt_version,
        "schema_version": schema_version,
        "ocr_params": {
            "model": ocr_options.model,
            "table_format": ocr_options.table_format,
            "include_image_base64": ocr_options.include_image_base64,
        },
        "llm_params": llm_params,
    }


def _manifest_document_entries(
    documents: Sequence[OCRDocumentStageResult],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for document in documents:
        entries.append(
            {
                "doc_id": document.doc_id,
                "ocr_status": document.ocr_status,
                "pages_count": document.pages_count,
                "combined_markdown_path": document.combined_markdown_path,
                "ocr_artifacts_path": document.ocr_artifacts_path,
                "ocr_error": document.ocr_error,
            }
        )
    return entries


def _to_optional_param(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _safe_update_run_metrics(
    *,
    repo: StorageRepo,
    run_id: str,
    timings_json: dict[str, Any],
    usage_json: dict[str, Any],
    usage_normalized_json: dict[str, Any],
    cost_json: dict[str, Any],
    run_log_path: Path,
) -> str | None:
    try:
        repo.update_run_metrics(
            run_id=run_id,
            timings_json=timings_json,
            usage_json=usage_json,
            usage_normalized_json=usage_normalized_json,
            cost_json=cost_json,
        )
        return None
    except Exception as error:  # noqa: BLE001
        details = build_error_details(error)
        _safe_append_run_log(
            run_log_path,
            f"Storage persistence failed in update_run_metrics: {details}",
        )
        return details


def _safe_update_run_status(
    *,
    repo: StorageRepo,
    run_id: str,
    status: str,
    error_code: str | None,
    error_message: str | None,
    run_log_path: Path,
) -> str | None:
    try:
        repo.update_run_status(
            run_id=run_id,
            status=status,
            error_code=error_code,
            error_message=error_message,
        )
        return None
    except Exception as error:  # noqa: BLE001
        details = build_error_details(error)
        _safe_append_run_log(
            run_log_path,
            f"Storage persistence failed in update_run_status: {details}",
        )
        return details


def _safe_update_manifest(
    *,
    artifacts_root_path: str,
    updates: dict[str, Any],
    run_log_path: Path,
) -> str | None:
    try:
        update_run_manifest(
            artifacts_root_path=artifacts_root_path,
            updates=updates,
        )
        return None
    except Exception as error:  # noqa: BLE001
        details = build_error_details(error)
        _safe_append_run_log(
            run_log_path,
            f"Storage persistence failed in update_run_manifest: {details}",
        )
        return details


def _safe_append_run_log(log_path: Path, message: str) -> None:
    try:
        _append_run_log(log_path, message)
    except Exception:
        # If log write fails, we keep pipeline execution alive.
        return


def _merge_persistence_error(
    *,
    error_code: str,
    error_message: str,
    persistence_errors: list[str | None],
) -> tuple[str, str]:
    details = [item for item in persistence_errors if item]
    if not details:
        return error_code, error_message

    merged = "\n".join(details)
    if error_code != "STORAGE_ERROR":
        return "STORAGE_ERROR", f"{error_message}\nStorage details:\n{merged}"
    return "STORAGE_ERROR", f"{error_message}\n{merged}"
