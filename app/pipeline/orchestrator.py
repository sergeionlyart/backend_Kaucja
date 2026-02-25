from __future__ import annotations

import json
import mimetypes
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence

from app.llm_client.base import LLMClient, LLMResult
from app.ocr_client.types import OCROptions, OCRResult
from app.pipeline.pack_documents import load_and_pack_documents
from app.pipeline.validate_output import ValidationResult, validate_output
from app.storage.artifacts import ArtifactsManager, DocumentArtifacts, RunArtifacts
from app.storage.models import OCRStatus
from app.storage.repo import StorageRepo


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


class OCRPipelineOrchestrator:
    def __init__(
        self,
        *,
        repo: StorageRepo,
        artifacts_manager: ArtifactsManager,
        ocr_client: OCRClientProtocol,
        llm_clients: dict[str, LLMClient] | None = None,
        prompt_root: Path | None = None,
    ) -> None:
        self.repo = repo
        self.artifacts_manager = artifacts_manager
        self.ocr_client = ocr_client
        self.llm_clients = llm_clients or {}
        self.prompt_root = prompt_root or Path("app/prompts")

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
        ocr_stage = self._run_ocr_documents(
            run_id=run.run_id,
            run_artifacts=run_artifacts,
            input_paths=paths,
            ocr_options=ocr_options,
        )

        final_status = "failed" if ocr_stage.has_failures else "completed"
        self.repo.update_run_status(
            run_id=run.run_id,
            status=final_status,
            error_code="OCR_STAGE_FAILED" if ocr_stage.has_failures else None,
            error_message="One or more documents failed OCR"
            if ocr_stage.has_failures
            else None,
        )
        self.repo.update_run_metrics(
            run_id=run.run_id,
            timings_json={
                "t_ocr_total_ms": ocr_stage.t_ocr_total_ms,
                "t_total_ms": ocr_stage.t_ocr_total_ms,
            },
            usage_json={},
            usage_normalized_json={},
            cost_json={},
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
        llm_artifacts = self.artifacts_manager.create_llm_artifacts(
            artifacts_root_path=run.artifacts_root_path
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

        if ocr_stage.has_failures:
            metrics = {
                "timings": {
                    "t_ocr_total_ms": ocr_stage.t_ocr_total_ms,
                    "t_total_ms": _elapsed_ms(started_at),
                },
                "usage": {},
                "usage_normalized": {},
                "cost": {},
            }
            self.repo.update_run_metrics(
                run_id=run.run_id,
                timings_json=metrics["timings"],
                usage_json=metrics["usage"],
                usage_normalized_json=metrics["usage_normalized"],
                cost_json=metrics["cost"],
            )
            self.repo.update_run_status(
                run_id=run.run_id,
                status="failed",
                error_code="OCR_STAGE_FAILED",
                error_message="One or more documents failed OCR",
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
                validation_errors=["One or more documents failed OCR"],
                metrics=metrics,
                error_code="OCR_STAGE_FAILED",
                error_message="One or more documents failed OCR",
            )

        try:
            system_prompt, schema = self._load_prompt_assets(
                prompt_name=prompt_name,
                prompt_version=prompt_version,
            )
            packed_documents = load_and_pack_documents(ocr_stage.packed_documents)
            _write_request_artifact(
                path=llm_artifacts.request_path,
                system_prompt=system_prompt,
                user_content=packed_documents,
            )

            llm_client = self._resolve_llm_client(provider)
            llm_result = llm_client.generate_json(
                system_prompt=system_prompt,
                user_content=packed_documents,
                json_schema=schema,
                model=model,
                params=llm_params or {},
                run_meta={
                    "session_id": session.session_id,
                    "run_id": run.run_id,
                    "schema_name": f"{prompt_name}_{prompt_version}",
                },
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

            if not validation.valid:
                error_message = "; ".join(validation.errors)
                self.repo.update_run_status(
                    run_id=run.run_id,
                    status="failed",
                    error_code="LLM_SCHEMA_INVALID",
                    error_message=error_message,
                )
                _append_run_log(run_artifacts.run_log_path, "Validation failed")
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
            self.repo.update_run_metrics(
                run_id=run.run_id,
                timings_json={
                    "t_ocr_total_ms": ocr_stage.t_ocr_total_ms,
                    "t_total_ms": _elapsed_ms(started_at),
                },
                usage_json={},
                usage_normalized_json={},
                cost_json={},
            )
            self.repo.update_run_status(
                run_id=run.run_id,
                status="failed",
                error_code="LLM_INVALID_JSON",
                error_message=str(error),
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
                metrics={
                    "timings": {
                        "t_ocr_total_ms": ocr_stage.t_ocr_total_ms,
                        "t_total_ms": _elapsed_ms(started_at),
                    },
                    "usage": {},
                    "usage_normalized": {},
                    "cost": {},
                },
                error_code="LLM_INVALID_JSON",
                error_message=str(error),
            )

        except Exception as error:  # noqa: BLE001
            llm_artifacts.response_raw_path.write_text(str(error), encoding="utf-8")
            self.repo.update_run_metrics(
                run_id=run.run_id,
                timings_json={
                    "t_ocr_total_ms": ocr_stage.t_ocr_total_ms,
                    "t_total_ms": _elapsed_ms(started_at),
                },
                usage_json={},
                usage_normalized_json={},
                cost_json={},
            )
            self.repo.update_run_status(
                run_id=run.run_id,
                status="failed",
                error_code="LLM_API_ERROR",
                error_message=str(error),
            )
            return FullPipelineResult(
                session_id=session.session_id,
                run_id=run.run_id,
                run_status="failed",
                documents=ocr_stage.documents,
                critical_gaps_summary=[],
                next_questions_to_user=[],
                raw_json_text=str(error),
                parsed_json=None,
                validation_valid=False,
                validation_errors=[str(error)],
                metrics={
                    "timings": {
                        "t_ocr_total_ms": ocr_stage.t_ocr_total_ms,
                        "t_total_ms": _elapsed_ms(started_at),
                    },
                    "usage": {},
                    "usage_normalized": {},
                    "cost": {},
                },
                error_code="LLM_API_ERROR",
                error_message=str(error),
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
                ocr_result = self.ocr_client.process_document(
                    input_path=original_path,
                    doc_id=doc_id,
                    options=ocr_options,
                    output_dir=document_artifacts.ocr_dir,
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
                _append_run_log(run_artifacts.run_log_path, f"Doc {doc_id}: OCR ok")
            except Exception as error:  # noqa: BLE001
                has_failures = True
                error_message = str(error)
                self.repo.update_document_ocr(
                    run_id=run_id,
                    doc_id=doc_id,
                    ocr_status="failed",
                    ocr_model=ocr_options.model,
                    pages_count=None,
                    ocr_artifacts_path=str(document_artifacts.ocr_dir.resolve()),
                    ocr_error=error_message,
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
                        ocr_error=error_message,
                    )
                )
                _append_run_log(
                    run_artifacts.run_log_path,
                    f"Doc {doc_id}: OCR failed ({error_message})",
                )

        return _OcrStageInternals(
            documents=documents,
            packed_documents=packed_documents,
            has_failures=has_failures,
            t_ocr_total_ms=_elapsed_ms(started_at),
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
        system_prompt_path = prompt_dir / "system_prompt.txt"
        schema_path = prompt_dir / "schema.json"

        if not system_prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {system_prompt_path}")
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        system_prompt = system_prompt_path.read_text(encoding="utf-8")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        if not isinstance(schema, dict):
            raise ValueError("Schema must be a JSON object")

        return system_prompt, schema


@dataclass(frozen=True, slots=True)
class _OcrStageInternals:
    documents: list[OCRDocumentStageResult]
    packed_documents: list[tuple[str, Path]]
    has_failures: bool
    t_ocr_total_ms: float


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
