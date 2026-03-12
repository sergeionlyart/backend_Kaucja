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

from app.agentic.case_workspace_store import Scenario2CaseMetadata
from app.agentic.legal_corpus_contract import LegalCorpusTool
from app.agentic.scenario2_verifier import (
    build_scenario2_review_payload,
    build_scenario2_verifier_gate_payload,
    normalize_scenario2_verifier_policy,
)
from app.llm_client.base import LLMClient, LLMResult
from app.agentic.scenario2_runner import (
    Scenario2RunConfig,
    Scenario2RunResult,
    Scenario2Runner,
    Scenario2RunnerError,
    StubScenario2Runner,
)
from app.ocr_client.types import OCROptions, OCRResult
from app.pipeline.pack_documents import load_and_pack_documents
from app.pipeline.validate_output import ValidationResult, validate_output
from app.pipeline.scenario_router import (
    SCENARIO_1_ID,
    SCENARIO_2_ID,
    SCENARIO2_CONFIG_ERROR,
    SCENARIO_2_VALIDATION_MESSAGE,
    SCENARIO_2_VALIDATION_STATUS,
    SCENARIO2_RUNTIME_ERROR,
    SCENARIO2_RUNNER_MODE_STUB,
    SCENARIO2_TRACE_PERSIST_ERROR,
    is_openai_tool_loop_mode,
    normalize_scenario2_runner_mode,
    resolve_scenario_prompt_source_path,
    resolve_scenario_config,
)
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
    scenario_id: str = SCENARIO_1_ID


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
        scenario2_runner: Scenario2Runner | None = None,
        legal_corpus_tool: LegalCorpusTool | None = None,
        scenario2_case_workspace_store: Any | None = None,
        scenario2_runner_mode: str = SCENARIO2_RUNNER_MODE_STUB,
        scenario2_verifier_policy: str = "informational",
        scenario2_bootstrap_error: str | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.repo = repo
        self.artifacts_manager = artifacts_manager
        self.ocr_client = ocr_client
        self.llm_clients = llm_clients or {}
        self.prompt_root = prompt_root or Path("app/prompts")
        self.scenario2_runner = scenario2_runner or StubScenario2Runner()
        self.legal_corpus_tool = legal_corpus_tool
        self.scenario2_case_workspace_store = scenario2_case_workspace_store
        self.scenario2_runner_mode = normalize_scenario2_runner_mode(
            runner_mode=scenario2_runner_mode
        )
        self.scenario2_verifier_policy = normalize_scenario2_verifier_policy(
            scenario2_verifier_policy
        )
        self.scenario2_bootstrap_error = scenario2_bootstrap_error
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
                scenario_id=SCENARIO_1_ID,
                prompt_source_path=None,
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
        scenario_id: str | None = None,
        llm_params: dict[str, Any] | None = None,
        scenario2_case_metadata: Scenario2CaseMetadata | None = None,
        scenario2_case_workspace_id: str | None = None,
    ) -> FullPipelineResult:
        paths = _normalize_input_paths(input_files)
        if not paths:
            raise ValueError("At least one input file is required")

        started_at = time.perf_counter()
        llm_runtime_params = llm_params or {}
        scenario = resolve_scenario_config(
            scenario_id=scenario_id or SCENARIO_1_ID,
            requested_provider=provider,
            requested_model=model,
            requested_prompt_name=prompt_name,
            requested_prompt_version=prompt_version,
        )
        effective_provider = scenario.provider
        effective_model = scenario.model
        effective_prompt_name = scenario.prompt_name
        effective_prompt_version = scenario.prompt_version
        session = self.repo.create_session(session_id=session_id or None)
        run = self.repo.create_run(
            session_id=session.session_id,
            provider=effective_provider,
            model=effective_model,
            prompt_name=effective_prompt_name,
            prompt_version=effective_prompt_version,
            schema_version=effective_prompt_version,
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
        effective_scenario2_case_workspace_id = None
        if scenario.scenario_id == SCENARIO_2_ID:
            requested_case_workspace_id = str(scenario2_case_workspace_id or "").strip()
            effective_scenario2_case_workspace_id = (
                requested_case_workspace_id or session.session_id
            )
        init_run_manifest(
            artifacts_root_path=run.artifacts_root_path,
            session_id=session.session_id,
            run_id=run.run_id,
            inputs=_build_manifest_inputs(
                provider=effective_provider,
                model=effective_model,
                prompt_name=effective_prompt_name,
                prompt_version=effective_prompt_version,
                schema_version=effective_prompt_version,
                ocr_options=ocr_options,
                llm_params=llm_runtime_params,
                scenario_id=scenario.scenario_id,
                prompt_source_path=scenario.prompt_source_path,
                scenario2_case_workspace_id=effective_scenario2_case_workspace_id,
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
        if effective_scenario2_case_workspace_id is not None:
            _safe_record_scenario2_case_workspace_start(
                store=self.scenario2_case_workspace_store,
                case_id=effective_scenario2_case_workspace_id,
                session_id=session.session_id,
                run_id=run.run_id,
                scenario_id=scenario.scenario_id,
                input_paths=paths,
                case_metadata=scenario2_case_metadata,
                artifacts_root_path=str(run.artifacts_root_path),
                run_log_path=run_artifacts.run_log_path,
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
            if effective_scenario2_case_workspace_id is not None:
                _safe_record_scenario2_analysis_run(
                    store=self.scenario2_case_workspace_store,
                    case_id=effective_scenario2_case_workspace_id,
                    session_id=session.session_id,
                    run_id=run.run_id,
                    scenario_id=scenario.scenario_id,
                    status="failed",
                    review_status="not_applicable",
                    verifier_gate_status="not_applicable",
                    diagnostics={
                        "stage": "ocr",
                        "error_code": error_code,
                        "error_message": error_message,
                    },
                    artifacts_root_path=str(run.artifacts_root_path),
                    run_log_path=run_artifacts.run_log_path,
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
                scenario_id=scenario.scenario_id,
            )

        if not scenario.llm_stage_enabled:
            scenario2_trace_path = llm_artifacts.llm_dir / "scenario2_trace.json"
            scenario2_runner_mode = self.scenario2_runner_mode
            scenario2_llm_executed = is_openai_tool_loop_mode(
                runner_mode=scenario2_runner_mode
            )
            scenario2_runner = (
                self.scenario2_runner
                if scenario2_llm_executed
                else StubScenario2Runner()
            )
            scenario2_llm_start_required = scenario2_llm_executed

            def _scenario2_artifacts_payload(
                *,
                llm_executed: bool,
                trace_path: str | None = None,
            ) -> dict[str, Any]:
                payload: dict[str, Any] = {
                    "runner_mode": scenario2_runner_mode,
                    "llm_executed": llm_executed,
                }
                if trace_path is not None:
                    payload["trace_path"] = trace_path
                return payload

            def build_failure_trace_payload(
                *,
                failure_stage: str,
                failure_error_code: str,
                failure_error_message: str,
                run_result: Scenario2RunResult | None,
                llm_executed: bool,
            ) -> dict[str, Any]:
                steps: list[str] = []
                tool_trace: list[dict[str, Any]] = []
                diagnostics: dict[str, Any] = {}
                final_text = ""
                if run_result is not None:
                    steps.extend(run_result.steps)
                    tool_trace.extend(run_result.tool_trace)
                    diagnostics.update(run_result.diagnostics)
                    final_text = run_result.final_text

                if not steps:
                    steps = [f"scenario2_{failure_stage}_failed"]
                else:
                    steps.append(f"scenario2_{failure_stage}_failed")

                diagnostics = dict(diagnostics)
                diagnostics.update(
                    {
                        "stage": failure_stage,
                        "error_code": failure_error_code,
                        "error_message": failure_error_message,
                    }
                )
                diagnostics = _scenario2_diagnostics_with_verifier_gate(
                    diagnostics=diagnostics,
                    verifier_policy=self.scenario2_verifier_policy,
                    llm_executed=llm_executed,
                )
                return {
                    "response_mode": "plain_text",
                    "final_text": final_text,
                    "steps": steps,
                    "tool_trace": tool_trace,
                    "diagnostics": diagnostics,
                    "runner_mode": scenario2_runner_mode,
                    "llm_executed": llm_executed,
                    "model": run_result.model if run_result else None,
                    "tool_round_count": run_result.tool_round_count
                    if run_result
                    else 0,
                }

            def build_success_trace_payload(
                *,
                run_result: Scenario2RunResult,
                llm_executed: bool,
            ) -> dict[str, Any]:
                diagnostics = _scenario2_diagnostics_with_verifier_gate(
                    diagnostics=run_result.diagnostics,
                    verifier_policy=self.scenario2_verifier_policy,
                    llm_executed=llm_executed,
                )
                return {
                    "response_mode": run_result.response_mode,
                    "final_text": run_result.final_text,
                    "steps": list(run_result.steps),
                    "tool_trace": list(run_result.tool_trace),
                    "diagnostics": diagnostics,
                    "runner_mode": scenario2_runner_mode,
                    "llm_executed": llm_executed,
                    "model": run_result.model,
                    "tool_round_count": run_result.tool_round_count,
                }

            def handle_scenario2_failure(
                *,
                scenario2_error_code: str,
                scenario2_error_message: str,
                runner_mode: str,
                llm_stage_status: str,
                llm_executed: bool,
                run_result: Scenario2RunResult | None = None,
                failure_stage: str = "runtime",
            ) -> FullPipelineResult:
                failure_payload = build_failure_trace_payload(
                    failure_stage=failure_stage,
                    failure_error_code=scenario2_error_code,
                    failure_error_message=scenario2_error_message,
                    run_result=run_result,
                    llm_executed=llm_executed,
                )
                trace_persisted = False
                try:
                    _write_scenario2_trace_artifact(
                        path=scenario2_trace_path,
                        trace_payload=failure_payload,
                    )
                    trace_persisted = True
                except Exception as error:  # noqa: BLE001
                    trace_error = build_error_details(error)
                    _safe_append_run_log(
                        run_artifacts.run_log_path,
                        (
                            "Scenario2 trace write failed: "
                            f"{scenario2_error_code} ({trace_error})"
                        ),
                    )
                    scenario2_error_code = SCENARIO2_TRACE_PERSIST_ERROR
                    scenario2_error_message = (
                        f"{scenario2_error_message} "
                        f"(trace persistence failed: {trace_error})"
                    )
                    failure_payload["diagnostics"]["error_code"] = scenario2_error_code
                    failure_payload["diagnostics"]["error_message"] = (
                        scenario2_error_message
                    )
                    failure_payload["steps"] = failure_payload["steps"] + [
                        "scenario2_trace_persist_failed"
                    ]

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
                    error_code=scenario2_error_code,
                    error_message=scenario2_error_message,
                    run_log_path=run_artifacts.run_log_path,
                )
                scenario2_error_code, scenario2_error_message = (
                    _merge_persistence_error(
                        error_code=scenario2_error_code,
                        error_message=scenario2_error_message,
                        persistence_errors=[
                            metrics_persist_error,
                            status_persist_error,
                        ],
                    )
                )
                manifest_updates: dict[str, Any] = {
                    "status": "failed",
                    "stages": {
                        "llm": {"status": llm_stage_status, "updated_at": _utc_now()},
                        "finalize": {
                            "status": "failed",
                            "updated_at": _utc_now(),
                        },
                    },
                    "metrics": metrics,
                    "validation": {
                        "status": "failed",
                        "errors": [scenario2_error_message],
                    },
                    "error_code": scenario2_error_code,
                    "error_message": scenario2_error_message,
                }
                manifest_updates.update(
                    _scenario2_review_manifest_updates(
                        diagnostics=failure_payload.get("diagnostics"),
                    )
                )
                manifest_updates.update(
                    _scenario2_verifier_gate_manifest_updates(
                        diagnostics=failure_payload.get("diagnostics"),
                        verifier_policy=self.scenario2_verifier_policy,
                        llm_executed=llm_executed,
                    )
                )
                artifacts_update = _scenario2_artifacts_payload(
                    llm_executed=llm_executed,
                )
                if trace_persisted:
                    artifacts_update["trace_path"] = str(scenario2_trace_path.resolve())
                manifest_updates["artifacts"] = {
                    "llm": artifacts_update,
                }
                manifest_persist_error = _safe_update_manifest(
                    artifacts_root_path=run.artifacts_root_path,
                    run_log_path=run_artifacts.run_log_path,
                    updates=manifest_updates,
                )
                if manifest_persist_error is not None:
                    scenario2_error_code, scenario2_error_message = (
                        _merge_persistence_error(
                            error_code=scenario2_error_code,
                            error_message=scenario2_error_message,
                            persistence_errors=[manifest_persist_error],
                        )
                    )
                _safe_append_run_log(
                    run_artifacts.run_log_path,
                    (
                        f"Scenario2 failed ({scenario2_error_code}): "
                        f"{scenario2_error_message}"
                    ),
                )
                failure_write_errors: list[str] = []
                if failure_payload["final_text"]:
                    write_error = _safe_write_text_file(
                        path=llm_artifacts.response_raw_path,
                        payload=failure_payload["final_text"],
                        label="scenario2_response_raw",
                        run_log_path=run_artifacts.run_log_path,
                    )
                    if write_error is not None:
                        failure_write_errors.append(write_error)
                validation_write_error = _safe_write_text_file(
                    path=llm_artifacts.validation_path,
                    payload=json.dumps(
                        {
                            "status": "failed",
                            "errors": [scenario2_error_message],
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    label="scenario2_validation",
                    run_log_path=run_artifacts.run_log_path,
                )
                if validation_write_error is not None:
                    failure_write_errors.append(validation_write_error)

                if failure_write_errors:
                    failures = "; ".join(failure_write_errors)
                    scenario2_error_message = (
                        f"{scenario2_error_message} "
                        f"(artifact persistence warning: {failures})"
                    )
                if effective_scenario2_case_workspace_id is not None:
                    diagnostics_dict = (
                        failure_payload.get("diagnostics")
                        if isinstance(failure_payload.get("diagnostics"), dict)
                        else {}
                    )
                    review_payload = build_scenario2_review_payload(
                        verifier_status=str(
                            diagnostics_dict.get("verifier_status") or ""
                        ),
                        verifier_warnings=_extract_string_list(
                            diagnostics_dict.get("verifier_warnings")
                        ),
                    )
                    verifier_gate_payload = build_scenario2_verifier_gate_payload(
                        verifier_policy=self.scenario2_verifier_policy,
                        verifier_status=str(
                            diagnostics_dict.get("verifier_status") or ""
                        ),
                        llm_executed=llm_executed,
                        verifier_warnings=_extract_string_list(
                            diagnostics_dict.get("verifier_warnings")
                        ),
                    )
                    _safe_record_scenario2_analysis_run(
                        store=self.scenario2_case_workspace_store,
                        case_id=effective_scenario2_case_workspace_id,
                        session_id=session.session_id,
                        run_id=run.run_id,
                        scenario_id=scenario.scenario_id,
                        status="failed",
                        review_status=str(review_payload["status"]),
                        verifier_gate_status=str(verifier_gate_payload["status"]),
                        diagnostics=failure_payload.get("diagnostics"),
                        artifacts_root_path=str(run.artifacts_root_path),
                        run_log_path=run_artifacts.run_log_path,
                    )

                return FullPipelineResult(
                    session_id=session.session_id,
                    run_id=run.run_id,
                    run_status="failed",
                    documents=ocr_stage.documents,
                    critical_gaps_summary=[],
                    next_questions_to_user=[],
                    raw_json_text=scenario2_error_message,
                    parsed_json=None,
                    validation_valid=False,
                    validation_errors=[scenario2_error_message],
                    metrics=metrics,
                    error_code=scenario2_error_code,
                    error_message=scenario2_error_message,
                    scenario_id=scenario.scenario_id,
                )

            try:
                packed_documents = load_and_pack_documents(
                    documents=[
                        (doc.doc_id, Path(doc.combined_markdown_path))
                        for doc in ocr_stage.documents
                    ]
                )
            except Exception as error:  # noqa: BLE001
                return handle_scenario2_failure(
                    scenario2_error_code=SCENARIO2_RUNTIME_ERROR,
                    scenario2_error_message=str(error),
                    runner_mode=scenario2_runner_mode,
                    llm_stage_status="skipped",
                    llm_executed=False,
                    failure_stage="pack_documents",
                )

            runner_result: Scenario2RunResult | None = None
            runner_started = False
            try:
                if scenario2_llm_start_required and self.scenario2_bootstrap_error:
                    return handle_scenario2_failure(
                        scenario2_error_code=SCENARIO2_CONFIG_ERROR,
                        scenario2_error_message=self.scenario2_bootstrap_error,
                        runner_mode=scenario2_runner_mode,
                        llm_stage_status="skipped",
                        llm_executed=False,
                        failure_stage="runner_bootstrap",
                    )
                if scenario2_llm_start_required and isinstance(
                    scenario2_runner, StubScenario2Runner
                ):
                    return handle_scenario2_failure(
                        scenario2_error_code=SCENARIO2_RUNTIME_ERROR,
                        scenario2_error_message=(
                            "Scenario2 openai_tool_loop mode requires a real "
                            "Scenario2 runner injection."
                        ),
                        runner_mode=scenario2_runner_mode,
                        llm_stage_status="skipped",
                        llm_executed=False,
                        failure_stage="runner_config",
                    )
                if scenario2_llm_start_required and self.legal_corpus_tool is None:
                    return handle_scenario2_failure(
                        scenario2_error_code=SCENARIO2_RUNTIME_ERROR,
                        scenario2_error_message=(
                            "Legal corpus tool adapter is not configured"
                        ),
                        runner_mode=scenario2_runner_mode,
                        llm_stage_status="skipped",
                        llm_executed=False,
                        failure_stage="runner_config",
                    )
                try:
                    resolved_prompt_path = resolve_scenario_prompt_source_path(
                        prompt_source_path=scenario.prompt_source_path,
                        prompt_root=self.prompt_root,
                    )
                except Exception as error:  # noqa: BLE001
                    return handle_scenario2_failure(
                        scenario2_error_code=SCENARIO2_CONFIG_ERROR,
                        scenario2_error_message=str(error),
                        runner_mode=scenario2_runner_mode,
                        llm_stage_status="skipped",
                        llm_executed=False,
                        failure_stage="prompt_resolution",
                    )

                runner_config = Scenario2RunConfig(
                    provider=effective_provider,
                    model=effective_model,
                    prompt_name=effective_prompt_name,
                    prompt_version=effective_prompt_version,
                    prompt_source_path=resolved_prompt_path,
                    placeholder_text=scenario.scenario_placeholder or "",
                )

                try:
                    runner_started = True
                    runner_result = scenario2_runner.run(
                        packed_documents=packed_documents,
                        config=runner_config,
                        system_prompt_path=resolved_prompt_path,
                        legal_corpus_tool=self.legal_corpus_tool,
                    )
                except Scenario2RunnerError as error:
                    return handle_scenario2_failure(
                        scenario2_error_code=SCENARIO2_RUNTIME_ERROR,
                        scenario2_error_message=str(error),
                        runner_mode=scenario2_runner_mode,
                        llm_stage_status="failed",
                        llm_executed=runner_started,
                        failure_stage="runner",
                        run_result=error.to_run_result(),
                    )
                except Exception as error:  # noqa: BLE001
                    return handle_scenario2_failure(
                        scenario2_error_code=SCENARIO2_RUNTIME_ERROR,
                        scenario2_error_message=str(error),
                        runner_mode=scenario2_runner_mode,
                        llm_stage_status="failed",
                        llm_executed=runner_started,
                        failure_stage="runner",
                        run_result=None,
                    )

                final_text = (
                    runner_result.final_text or scenario.scenario_placeholder or ""
                )
                try:
                    _write_scenario2_trace_artifact(
                        path=scenario2_trace_path,
                        trace_payload=build_success_trace_payload(
                            run_result=runner_result,
                            llm_executed=scenario2_llm_executed,
                        ),
                    )
                except Exception as error:  # noqa: BLE001
                    return handle_scenario2_failure(
                        scenario2_error_code=SCENARIO2_TRACE_PERSIST_ERROR,
                        scenario2_error_message=str(error),
                        runner_mode=scenario2_runner_mode,
                        llm_stage_status="failed",
                        llm_executed=runner_started,
                        run_result=runner_result,
                        failure_stage="trace_persistence",
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
                    status="completed",
                    error_code=None,
                    error_message=None,
                    run_log_path=run_artifacts.run_log_path,
                )
                _safe_update_manifest(
                    artifacts_root_path=run.artifacts_root_path,
                    run_log_path=run_artifacts.run_log_path,
                    updates={
                        "status": "completed",
                        "stages": {
                            "llm": {
                                "status": (
                                    "completed" if scenario2_llm_executed else "skipped"
                                ),
                                "updated_at": _utc_now(),
                            },
                            "finalize": {
                                "status": "completed",
                                "updated_at": _utc_now(),
                            },
                        },
                        "metrics": metrics,
                        "validation": {
                            "status": SCENARIO_2_VALIDATION_STATUS,
                            "errors": [SCENARIO_2_VALIDATION_MESSAGE],
                        },
                        **_scenario2_review_manifest_updates(
                            diagnostics=runner_result.diagnostics,
                        ),
                        **_scenario2_verifier_gate_manifest_updates(
                            diagnostics=runner_result.diagnostics,
                            verifier_policy=self.scenario2_verifier_policy,
                            llm_executed=scenario2_llm_executed,
                        ),
                        "artifacts": {
                            "llm": {
                                "trace_path": str(scenario2_trace_path.resolve()),
                                "runner_mode": scenario2_runner_mode,
                                "llm_executed": scenario2_llm_executed,
                            }
                        },
                        "error_code": None,
                        "error_message": None,
                    },
                )
                _append_run_log(
                    run_artifacts.run_log_path,
                    (
                        "Scenario 2 OpenAI runner completed."
                        if scenario2_llm_executed
                        else "Scenario 2 stub path completed."
                    ),
                )
            except Exception as error:  # noqa: BLE001
                return handle_scenario2_failure(
                    scenario2_error_code=SCENARIO2_RUNTIME_ERROR,
                    scenario2_error_message=str(error),
                    runner_mode=scenario2_runner_mode,
                    llm_stage_status="failed" if runner_started else "skipped",
                    llm_executed=runner_started,
                    run_result=runner_result,
                    failure_stage="runtime",
                )

            if final_text:
                response_raw_write_error = _safe_write_text_file(
                    path=llm_artifacts.response_raw_path,
                    payload=final_text,
                    label="scenario2_response_raw",
                    run_log_path=run_artifacts.run_log_path,
                )
            else:
                response_raw_write_error = None

            response_validation_error = _safe_write_text_file(
                path=llm_artifacts.validation_path,
                payload=json.dumps(
                    {
                        "status": SCENARIO_2_VALIDATION_STATUS,
                        "errors": [SCENARIO_2_VALIDATION_MESSAGE],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                label="scenario2_validation",
                run_log_path=run_artifacts.run_log_path,
            )
            final_error_code = None
            final_error_message = None
            persistence_errors: list[str | None] = [
                metrics_persist_error,
                status_persist_error,
                response_raw_write_error,
                response_validation_error,
            ]
            if any(item is not None for item in persistence_errors):
                final_error_code, final_error_message = _merge_persistence_error(
                    error_code="STORAGE_ERROR",
                    error_message="",
                    persistence_errors=persistence_errors,
                )
                _append_run_log(
                    run_artifacts.run_log_path,
                    f"Run completed with storage warnings: {final_error_message}",
                )
            if effective_scenario2_case_workspace_id is not None:
                diagnostics_dict = (
                    runner_result.diagnostics
                    if isinstance(runner_result.diagnostics, dict)
                    else {}
                )
                review_payload = build_scenario2_review_payload(
                    verifier_status=str(diagnostics_dict.get("verifier_status") or ""),
                    verifier_warnings=_extract_string_list(
                        diagnostics_dict.get("verifier_warnings")
                    ),
                )
                verifier_gate_payload = build_scenario2_verifier_gate_payload(
                    verifier_policy=self.scenario2_verifier_policy,
                    verifier_status=str(diagnostics_dict.get("verifier_status") or ""),
                    llm_executed=scenario2_llm_executed,
                    verifier_warnings=_extract_string_list(
                        diagnostics_dict.get("verifier_warnings")
                    ),
                )
                _safe_record_scenario2_analysis_run(
                    store=self.scenario2_case_workspace_store,
                    case_id=effective_scenario2_case_workspace_id,
                    session_id=session.session_id,
                    run_id=run.run_id,
                    scenario_id=scenario.scenario_id,
                    status="completed",
                    review_status=str(review_payload["status"]),
                    verifier_gate_status=str(verifier_gate_payload["status"]),
                    diagnostics=runner_result.diagnostics,
                    artifacts_root_path=str(run.artifacts_root_path),
                    run_log_path=run_artifacts.run_log_path,
                )

            return FullPipelineResult(
                session_id=session.session_id,
                run_id=run.run_id,
                run_status="completed",
                documents=ocr_stage.documents,
                critical_gaps_summary=[],
                next_questions_to_user=[],
                raw_json_text=final_text,
                parsed_json=None,
                validation_valid=True,
                validation_errors=[],
                metrics=metrics,
                error_code=final_error_code,
                error_message=final_error_message,
                scenario_id=scenario.scenario_id,
            )

        try:
            update_run_manifest(
                artifacts_root_path=run.artifacts_root_path,
                updates={
                    "stages": {"llm": {"status": "running", "updated_at": _utc_now()}}
                },
            )
            system_prompt, schema = self._load_prompt_assets(
                prompt_name=effective_prompt_name,
                prompt_version=effective_prompt_version,
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

            llm_client = self._resolve_llm_client(effective_provider)
            llm_result = run_with_retry(
                operation=lambda: llm_client.generate_json(
                    system_prompt=system_prompt,
                    user_content=packed_documents,
                    json_schema=schema,
                    model=effective_model,
                    params=llm_runtime_params,
                    run_meta={
                        "session_id": session.session_id,
                        "run_id": run.run_id,
                        "schema_name": f"{effective_prompt_name}_{effective_prompt_version}",
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
                    scenario_id=scenario.scenario_id,
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
                scenario_id=scenario.scenario_id,
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
                scenario_id=scenario.scenario_id,
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
                scenario_id=scenario.scenario_id,
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
                scenario_id=scenario.scenario_id,
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

        from app.utils.error_taxonomy import TechspecDriftError

        if not canonical_prompt_path.exists():
            raise TechspecDriftError("Canonical TechSpec system_prompt.txt is missing.")

        if not canonical_schema_path.exists():
            raise TechspecDriftError("Canonical TechSpec schema.json is missing.")

        canonical_prompt_text = canonical_prompt_path.read_text(encoding="utf-8")
        if system_prompt != canonical_prompt_text:
            raise TechspecDriftError(
                f"Requested prompt version '{prompt_version}' violates the byte-for-byte canonical TechSpec lock."
            )

        canonical_schema_text = canonical_schema_path.read_text(encoding="utf-8")
        try:
            canonical_schema_json = json.loads(canonical_schema_text)
        except json.JSONDecodeError as error:
            raise TechspecDriftError(f"Canonical JSON schema invalid: {error}")

        requested_schema_json = json.loads(schema_text)
        if requested_schema_json != canonical_schema_json:
            raise TechspecDriftError(
                f"Requested schema version '{prompt_version}' violates the exact canonical TechSpec lock."
            )

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


def _safe_write_text_file(
    *,
    path: Path,
    payload: str,
    label: str,
    run_log_path: Path,
) -> str | None:
    try:
        path.write_text(payload, encoding="utf-8")
        return None
    except Exception as error:  # noqa: BLE001
        details = build_error_details(error)
        _safe_append_run_log(
            run_log_path,
            f"Scenario 2 artifact write failed ({label}): {details}",
        )
        return details


def _write_scenario2_trace_artifact(
    *,
    path: Path,
    runner_result: Scenario2RunResult | None = None,
    trace_payload: dict[str, Any] | None = None,
) -> None:
    payload = trace_payload
    if payload is None:
        if runner_result is None:
            raise ValueError("No scenario2 trace payload provided.")
        payload = {
            "response_mode": runner_result.response_mode,
            "final_text": runner_result.final_text,
            "steps": runner_result.steps,
            "tool_trace": runner_result.tool_trace,
            "diagnostics": runner_result.diagnostics,
            "model": runner_result.model,
            "tool_round_count": runner_result.tool_round_count,
        }

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _elapsed_ms(started_at: float) -> float:
    return (time.perf_counter() - started_at) * 1000


def _extract_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _scenario2_review_manifest_updates(*, diagnostics: Any) -> dict[str, Any]:
    diagnostics_dict = diagnostics if isinstance(diagnostics, dict) else {}
    review_payload = build_scenario2_review_payload(
        verifier_status=str(diagnostics_dict.get("verifier_status") or ""),
        verifier_warnings=_extract_string_list(
            diagnostics_dict.get("verifier_warnings")
        ),
    )
    return {
        "review_status": review_payload["status"],
        "review": review_payload,
    }


def _scenario2_diagnostics_with_verifier_gate(
    *,
    diagnostics: Any,
    verifier_policy: str,
    llm_executed: bool,
) -> dict[str, Any]:
    diagnostics_dict = dict(diagnostics) if isinstance(diagnostics, dict) else {}
    gate_payload = build_scenario2_verifier_gate_payload(
        verifier_policy=verifier_policy,
        verifier_status=str(diagnostics_dict.get("verifier_status") or ""),
        llm_executed=llm_executed,
        verifier_warnings=_extract_string_list(
            diagnostics_dict.get("verifier_warnings")
        ),
    )
    diagnostics_dict.update(
        {
            "verifier_policy": gate_payload["policy"],
            "verifier_gate_status": gate_payload["status"],
            "verifier_gate_summary": gate_payload["summary"],
            "verifier_gate_warning_count": gate_payload["warnings_count"],
            "verifier_gate_blocking": gate_payload["blocking"],
        }
    )
    return diagnostics_dict


def _scenario2_verifier_gate_manifest_updates(
    *,
    diagnostics: Any,
    verifier_policy: str,
    llm_executed: bool,
) -> dict[str, Any]:
    diagnostics_dict = diagnostics if isinstance(diagnostics, dict) else {}
    gate_payload = build_scenario2_verifier_gate_payload(
        verifier_policy=verifier_policy,
        verifier_status=str(diagnostics_dict.get("verifier_status") or ""),
        llm_executed=llm_executed,
        verifier_warnings=_extract_string_list(
            diagnostics_dict.get("verifier_warnings")
        ),
    )
    return {
        "verifier_policy": gate_payload["policy"],
        "verifier_gate_status": gate_payload["status"],
        "verifier_gate": gate_payload,
    }


def _safe_record_scenario2_case_workspace_start(
    *,
    store: Any,
    case_id: str,
    session_id: str,
    run_id: str,
    scenario_id: str,
    input_paths: Sequence[Path],
    case_metadata: Scenario2CaseMetadata | None,
    artifacts_root_path: str,
    run_log_path: Path,
) -> None:
    if store is None:
        return
    try:
        effective_case_metadata = case_metadata or Scenario2CaseMetadata()
        store.ensure_workspace(
            case_id=case_id,
            **effective_case_metadata.to_workspace_fields(),
        )
        store.register_case_documents(case_id=case_id, input_paths=input_paths)
        store.ensure_case_facts_slot(case_id=case_id)
        store.record_analysis_run(
            case_id=case_id,
            run_id=run_id,
            session_id=session_id,
            scenario_id=scenario_id,
            status="running",
            review_status="not_applicable",
            verifier_gate_status="not_applicable",
            artifacts_root_path=artifacts_root_path,
            diagnostics={"stage": "bootstrap"},
        )
    except Exception as error:  # noqa: BLE001
        _safe_append_run_log(
            run_log_path,
            (
                "Scenario 2 case workspace persistence warning: "
                f"{build_error_details(error)}"
            ),
        )


def _safe_record_scenario2_analysis_run(
    *,
    store: Any,
    case_id: str,
    session_id: str,
    run_id: str,
    scenario_id: str,
    status: str,
    review_status: str,
    verifier_gate_status: str,
    diagnostics: dict[str, Any] | None,
    artifacts_root_path: str,
    run_log_path: Path,
) -> None:
    if store is None:
        return
    try:
        store.record_analysis_run(
            case_id=case_id,
            run_id=run_id,
            session_id=session_id,
            scenario_id=scenario_id,
            status=status,
            review_status=review_status,
            verifier_gate_status=verifier_gate_status,
            artifacts_root_path=artifacts_root_path,
            diagnostics=diagnostics,
        )
    except Exception as error:  # noqa: BLE001
        _safe_append_run_log(
            run_log_path,
            (
                "Scenario 2 case workspace persistence warning: "
                f"{build_error_details(error)}"
            ),
        )


def _build_manifest_inputs(
    *,
    provider: str,
    model: str,
    prompt_name: str,
    prompt_version: str,
    schema_version: str,
    ocr_options: OCROptions,
    llm_params: dict[str, Any],
    scenario_id: str,
    prompt_source_path: str | None = None,
    scenario2_case_workspace_id: str | None = None,
) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "case_workspace_id": scenario2_case_workspace_id,
        "provider": provider,
        "model": model,
        "prompt_name": prompt_name,
        "prompt_version": prompt_version,
        "schema_version": schema_version,
        "prompt_source_path": prompt_source_path,
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
