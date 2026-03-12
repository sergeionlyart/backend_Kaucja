from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Callable, Sequence

import gradio as gr

from app.agentic.case_workspace_store import Scenario2CaseMetadata
from app.agentic.scenario2_runtime_factory import build_scenario2_runtime
from app.agentic.scenario2_runner import StubScenario2Runner
from app.agentic.scenario2_verifier import (
    build_scenario2_review_payload,
    build_scenario2_verifier_gate_payload,
    normalize_scenario2_verifier_policy,
)
from app.config.settings import Settings, get_settings
from app.llm_client.gemini_client import GeminiLLMClient
from app.llm_client.openai_client import OpenAILLMClient
from app.ocr_client.mistral_ocr import MistralOCRClient
from app.ocr_client.types import OCROptions
from app.pipeline.orchestrator import FullPipelineResult, OCRPipelineOrchestrator
from app.pipeline.scenario_router import (
    SCENARIO_1_ID,
    SCENARIO_2_ID,
    SCENARIO_2_MODEL,
    SCENARIO_2_PROMPT_SOURCE_PATH,
    SCENARIO_2_PROVIDER,
    is_openai_tool_loop_mode,
    normalize_scenario2_runner_mode,
    scenario_choices,
    resolve_scenario_config,
)
from app.prompts.manager import PromptManager
from app.storage.artifact_reader import (
    safe_load_combined_markdown,
    safe_load_llm_parsed_json,
    safe_load_llm_raw_text,
    safe_load_llm_validation_json,
    safe_load_run_manifest,
    safe_read_json,
    safe_read_text,
)
from app.storage.repo import StorageRepo
from app.storage.restore import RestoreSafetyLimits, restore_run_bundle
from app.storage.zip_export import ZipExportError, export_run_bundle
from app.ui.result_helpers import (
    build_checklist_rows,
    build_gap_rows,
    checklist_item_ids,
    render_checklist_details,
)
from app.ui.run_comparison import compare_runs as compare_runs_payload
from app.utils.error_taxonomy import ERROR_FRIENDLY_MESSAGES

PreflightChecker = Callable[[str], str | None]
_HISTORY_REVIEW_STATUS_CHOICES = [
    "all",
    "passed",
    "needs_review",
    "not_applicable",
]


def run_full_pipeline(
    *,
    orchestrator: OCRPipelineOrchestrator,
    prompt_name: str,
    current_session_id: str,
    uploaded_files: Sequence[str | Path] | str | Path | None,
    provider: str,
    model: str,
    prompt_version: str,
    scenario_id: str = SCENARIO_1_ID,
    ocr_model: str,
    table_format: str,
    include_image_base64: bool,
    openai_reasoning_effort: str,
    gemini_thinking_level: str,
    preflight_checker: PreflightChecker,
    scenario2_case_workspace_id: str = "",
    scenario2_claim_amount: float | int | str | None = None,
    scenario2_currency: str = "",
    scenario2_lease_start: str = "",
    scenario2_lease_end: str = "",
    scenario2_move_out_date: str = "",
    scenario2_deposit_return_due_date: str = "",
) -> tuple[Any, ...]:
    paths = _normalize_uploaded_files(uploaded_files)
    if not paths:
        return _empty_ui_payload(
            status_message="No files uploaded. Please select at least one document.",
            session_id=current_session_id.strip(),
        )

    from app.config.settings import get_settings

    settings_guard = get_settings()
    scenario = resolve_scenario_config(
        scenario_id=scenario_id,
        requested_provider=provider,
        requested_model=model,
        requested_prompt_name=prompt_name,
        requested_prompt_version=prompt_version,
    )

    effective_provider = scenario.provider
    effective_model = scenario.model
    effective_prompt_name = scenario.prompt_name
    effective_prompt_version = scenario.prompt_version

    preflight_error = _preflight_error_for_selection(
        orchestrator=orchestrator,
        settings=settings_guard,
        scenario_id=scenario.scenario_id,
        effective_provider=effective_provider,
        preflight_checker=preflight_checker,
    )
    if preflight_error is not None:
        return _empty_ui_payload(
            status_message=preflight_error,
            session_id=current_session_id.strip(),
        )

    llm_providers_guard = settings_guard.providers_config.get("llm_providers", {})
    provider_config_guard = llm_providers_guard.get(effective_provider, {})
    valid_models_guard = provider_config_guard.get("models", {})
    if scenario.llm_stage_enabled and effective_model not in valid_models_guard:
        return _empty_ui_payload(
            status_message=(
                "Configuration error: Model "
                f"'{effective_model}' is not supported by provider "
                f"'{effective_provider}'."
            ),
            session_id=current_session_id.strip(),
        )

    result = orchestrator.run_full_pipeline(
        input_files=paths,
        session_id=current_session_id.strip() or None,
        provider=effective_provider,
        model=effective_model,
        prompt_name=effective_prompt_name,
        prompt_version=effective_prompt_version,
        scenario_id=scenario.scenario_id,
        ocr_options=OCROptions(
            model=ocr_model,
            table_format=table_format,
            include_image_base64=include_image_base64,
        ),
        llm_params={
            "openai_reasoning_effort": openai_reasoning_effort,
            "gemini_thinking_level": gemini_thinking_level,
        },
        scenario2_case_workspace_id=_scenario2_case_workspace_id_from_ui(
            scenario_id=scenario.scenario_id,
            requested_case_workspace_id=scenario2_case_workspace_id,
        ),
        scenario2_case_metadata=_scenario2_case_metadata_from_ui(
            scenario_id=scenario.scenario_id,
            claim_amount=scenario2_claim_amount,
            currency=scenario2_currency,
            lease_start=scenario2_lease_start,
            lease_end=scenario2_lease_end,
            move_out_date=scenario2_move_out_date,
            deposit_return_due_date=scenario2_deposit_return_due_date,
        ),
    )

    run_status = (
        f"Run finished. session_id={result.session_id} run_id={result.run_id} "
        f"status={result.run_status}"
    )
    if result.error_code:
        run_status += f" error_code={result.error_code}"

    artifacts_root = _resolve_artifacts_root(
        orchestrator=orchestrator,
        run_id=result.run_id,
    )
    is_scenario2 = result.scenario_id == SCENARIO_2_ID
    if is_scenario2:
        parsed_json = None
        details_selector = _details_selector_update([])
        details_text = "Details: not applicable for Scenario 2 foundation run."
        validation = "Validation: not_applicable (Scenario 2 foundation run)."
    else:
        parsed_json = _safe_parsed_json(
            raw_text=result.raw_json_text, parsed=result.parsed_json
        )
        details_selector, details_text = _details_payload(parsed_json=parsed_json)
        validation = _validation_text(result)

    if is_scenario2:
        summary_text = result.raw_json_text
        raw_json = ""
    else:
        summary_text = _human_summary(result)
        raw_json = _raw_json_text(result)

    progress = _build_progress_text(
        artifacts_root=artifacts_root,
        run_status=result.run_status,
    )
    live_manifest = None
    if is_scenario2 and artifacts_root:
        live_manifest, _ = safe_load_run_manifest(artifacts_root)
    runtime_log_tail, runtime_log_path = _read_runtime_log(
        artifacts_root=artifacts_root,
        line_count=30,
    )
    error_friendly, error_details = _render_error_messages(
        error_code=result.error_code,
        error_message=result.error_message,
    )
    scenario2_runner_mode = _scenario2_runner_mode_for_ui(
        orchestrator=orchestrator,
        settings=settings_guard,
    )
    scenario2_verifier_policy = _scenario2_verifier_policy_for_ui(
        orchestrator=orchestrator,
        settings=settings_guard,
    )
    (
        scenario2_diagnostics,
        scenario2_fragments,
        scenario2_review_status,
        scenario2_verifier_gate_status,
    ) = _scenario2_ui_payload(
        scenario_id=result.scenario_id,
        artifacts_root=artifacts_root,
        manifest=None,
        fallback_runner_mode=scenario2_runner_mode,
        fallback_verifier_policy=scenario2_verifier_policy,
        fallback_llm_executed=(
            False if not is_openai_tool_loop_mode(scenario2_runner_mode) else None
        ),
        run_status=result.run_status,
        error_code=result.error_code,
        error_message=result.error_message,
    )
    if is_scenario2:
        effective_case_workspace_id = _manifest_scenario2_case_workspace_id(
            manifest=live_manifest
        ) or (
            _scenario2_case_workspace_id_from_ui(
                scenario_id=scenario.scenario_id,
                requested_case_workspace_id=scenario2_case_workspace_id,
            )
            or result.session_id
        )
        run_status += (
            f" case_workspace_id={effective_case_workspace_id}"
            f" review_status={scenario2_review_status}"
            f" verifier_gate_status={scenario2_verifier_gate_status}"
        )

    return (
        run_status,
        result.session_id,
        result.run_id,
        result.session_id,
        artifacts_root,
        progress,
        runtime_log_tail,
        runtime_log_path,
        error_friendly,
        error_details,
        _ocr_rows(result),
        build_checklist_rows(parsed_json),
        build_gap_rows(parsed_json),
        details_selector,
        details_text,
        summary_text,
        raw_json,
        validation,
        json.dumps(result.metrics, ensure_ascii=False, indent=2),
        scenario2_diagnostics,
        scenario2_fragments,
        parsed_json,
    )


def _preflight_error_for_selection(
    *,
    orchestrator: OCRPipelineOrchestrator,
    settings: Settings,
    scenario_id: str,
    effective_provider: str,
    preflight_checker: PreflightChecker,
) -> str | None:
    providers = _preflight_providers_for_selection(
        orchestrator=orchestrator,
        settings=settings,
        scenario_id=scenario_id,
        effective_provider=effective_provider,
    )
    if scenario_id == SCENARIO_2_ID and is_openai_tool_loop_mode(
        _scenario2_runner_mode_for_ui(
            orchestrator=orchestrator,
            settings=settings,
        )
    ):
        readiness_error = _scenario2_openai_mode_readiness_error(
            orchestrator=orchestrator,
        )
        if readiness_error is not None:
            return readiness_error

    for provider_name in providers:
        preflight_error = preflight_checker(provider_name)
        if preflight_error is not None:
            return preflight_error
    return None


def _preflight_providers_for_selection(
    *,
    orchestrator: OCRPipelineOrchestrator,
    settings: Settings,
    scenario_id: str,
    effective_provider: str,
) -> list[str]:
    if scenario_id != SCENARIO_2_ID:
        return [effective_provider]

    runner_mode = _scenario2_runner_mode_for_ui(
        orchestrator=orchestrator,
        settings=settings,
    )
    if is_openai_tool_loop_mode(runner_mode):
        return ["mistral", "openai"]
    return ["mistral"]


def _scenario2_runner_mode_for_ui(
    *,
    orchestrator: OCRPipelineOrchestrator,
    settings: Settings,
) -> str:
    configured_mode = getattr(
        orchestrator,
        "scenario2_runner_mode",
        settings.scenario2_runner_mode,
    )
    return normalize_scenario2_runner_mode(configured_mode)


def _scenario2_verifier_policy_for_ui(
    *,
    orchestrator: OCRPipelineOrchestrator,
    settings: Settings,
) -> str:
    configured_policy = getattr(
        orchestrator,
        "scenario2_verifier_policy",
        settings.scenario2_verifier_policy,
    )
    return normalize_scenario2_verifier_policy(configured_policy)


def _scenario2_openai_mode_readiness_error(
    *,
    orchestrator: OCRPipelineOrchestrator,
) -> str | None:
    bootstrap_error = str(
        getattr(orchestrator, "scenario2_bootstrap_error", "") or ""
    ).strip()
    if bootstrap_error:
        return f"Runtime preflight failed: {bootstrap_error}"

    scenario2_runner = getattr(orchestrator, "scenario2_runner", None)
    if scenario2_runner is None or isinstance(scenario2_runner, StubScenario2Runner):
        return (
            "Runtime preflight failed: Scenario 2 openai_tool_loop mode "
            "requires a real Scenario2 runner injection."
        )
    if getattr(orchestrator, "legal_corpus_tool", None) is None:
        return (
            "Runtime preflight failed: Scenario 2 openai_tool_loop mode "
            "requires a legal_corpus_tool adapter."
        )
    return None


def list_history_rows(
    *,
    repo: StorageRepo,
    session_id: str,
    provider: str,
    model: str,
    prompt_version: str,
    date_from: str,
    date_to: str,
    limit: float | int,
    review_status: str = "all",
) -> list[list[str]]:
    runs = repo.list_runs(
        session_id=session_id.strip() or None,
        provider=provider.strip() or None,
        model=model.strip() or None,
        prompt_version=prompt_version.strip() or None,
        date_from=date_from.strip() or None,
        date_to=date_to.strip() or None,
        limit=_to_limit(limit),
    )

    rows: list[list[str]] = []
    selected_review_status = _normalize_history_review_status_filter(review_status)
    for run in runs:
        manifest, _manifest_error = safe_load_run_manifest(run.artifacts_root_path)
        scenario_id = _manifest_scenario_id(manifest=manifest)
        row_review_status = _scenario_review_status(
            scenario_id=scenario_id,
            manifest=manifest,
            artifacts_root=run.artifacts_root_path,
            fallback_llm_executed=_manifest_scenario2_llm_executed(manifest=manifest),
        )
        if not _history_review_status_matches(
            selected_review_status=selected_review_status,
            row_review_status=row_review_status,
        ):
            continue

        total_cost = ""
        if isinstance(run.cost_json, dict) and "total_cost_usd" in run.cost_json:
            total_cost = str(run.cost_json["total_cost_usd"])

        rows.append(
            [
                run.run_id,
                run.created_at,
                run.session_id,
                scenario_id,
                run.provider,
                run.model,
                run.prompt_version,
                run.status,
                row_review_status,
                total_cost,
            ]
        )
    return rows


def _scenario_config_mode_updates(
    *,
    selected_scenario_id: str,
    fallback_provider: str,
    fallback_model: str,
    fallback_prompt_name: str,
    fallback_prompt_version: str,
    scenario1_state: dict[str, Any] | None = None,
    previous_scenario_id: str = SCENARIO_1_ID,
) -> tuple[Any, Any, Any, Any, Any, dict[str, str], str]:
    selected = (selected_scenario_id or SCENARIO_1_ID).strip()
    previous = (previous_scenario_id or SCENARIO_1_ID).strip()
    if previous not in {SCENARIO_1_ID, SCENARIO_2_ID}:
        previous = SCENARIO_1_ID

    state = _normalize_scenario1_state(
        scenario1_state=scenario1_state,
        fallback_provider=fallback_provider,
        fallback_model=fallback_model,
        fallback_prompt_name=fallback_prompt_name,
        fallback_prompt_version=fallback_prompt_version,
    )

    if selected == SCENARIO_2_ID:
        if previous == SCENARIO_1_ID:
            state = _normalize_scenario1_state(
                scenario1_state={
                    "provider": fallback_provider,
                    "model": fallback_model,
                    "prompt_name": fallback_prompt_name,
                    "prompt_version": fallback_prompt_version,
                },
                fallback_provider=fallback_provider,
                fallback_model=fallback_model,
                fallback_prompt_name=fallback_prompt_name,
                fallback_prompt_version=fallback_prompt_version,
            )

        return (
            gr.update(value=fallback_provider, interactive=False),
            gr.update(value=fallback_model, interactive=False),
            gr.update(value=fallback_prompt_name, interactive=False),
            gr.update(value=fallback_prompt_version, interactive=False),
            gr.update(
                value=(
                    "Scenario 2 fixed config:\n"
                    f"provider={SCENARIO_2_PROVIDER}\n"
                    f"model={SCENARIO_2_MODEL}\n"
                    f"prompt source: {SCENARIO_2_PROMPT_SOURCE_PATH}"
                ),
                visible=True,
                interactive=False,
            ),
            state,
            selected,
        )

    return (
        gr.update(value=state["provider"], interactive=True),
        gr.update(value=state["model"], interactive=True),
        gr.update(value=state["prompt_name"], interactive=True),
        gr.update(value=state["prompt_version"], interactive=True),
        gr.update(value="", visible=False, interactive=False),
        state,
        selected,
    )


def _normalize_scenario1_state(
    *,
    scenario1_state: dict[str, Any] | None,
    fallback_provider: str,
    fallback_model: str,
    fallback_prompt_name: str,
    fallback_prompt_version: str,
) -> dict[str, str]:
    if not isinstance(scenario1_state, dict):
        scenario1_state = {}

    return {
        "provider": _coalesce_scenario_value(
            scenario1_state.get("provider"), fallback_provider
        ),
        "model": _coalesce_scenario_value(scenario1_state.get("model"), fallback_model),
        "prompt_name": _coalesce_scenario_value(
            scenario1_state.get("prompt_name"), fallback_prompt_name
        ),
        "prompt_version": _coalesce_scenario_value(
            scenario1_state.get("prompt_version"), fallback_prompt_version
        ),
    }


def _coalesce_scenario_value(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _scenario2_case_block_update(selected_scenario_id: str) -> Any:
    return gr.update(visible=selected_scenario_id == SCENARIO_2_ID)


def _scenario2_case_workspace_id_from_ui(
    *,
    scenario_id: str,
    requested_case_workspace_id: str,
) -> str | None:
    if scenario_id != SCENARIO_2_ID:
        return None
    text = str(requested_case_workspace_id or "").strip()
    return text or None


def _scenario2_case_metadata_from_ui(
    *,
    scenario_id: str,
    claim_amount: float | int | str | None,
    currency: str,
    lease_start: str,
    lease_end: str,
    move_out_date: str,
    deposit_return_due_date: str,
) -> Scenario2CaseMetadata | None:
    if scenario_id != SCENARIO_2_ID:
        return None
    return Scenario2CaseMetadata(
        claim_amount=_optional_claim_amount(claim_amount),
        currency=_optional_text(currency, uppercase=True),
        lease_start=_optional_text(lease_start),
        lease_end=_optional_text(lease_end),
        move_out_date=_optional_text(move_out_date),
        deposit_return_due_date=_optional_text(deposit_return_due_date),
    )


def _optional_claim_amount(value: float | int | str | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        numeric = float(value)
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            numeric = float(text.replace(",", "."))
        except ValueError:
            return None
    if math.isnan(numeric):
        return None
    return numeric


def _optional_text(value: Any, *, uppercase: bool = False) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text.upper() if uppercase else text


def refresh_history_for_ui(
    *,
    repo: StorageRepo,
    session_id: str,
    provider: str,
    model: str,
    prompt_version: str,
    date_from: str,
    date_to: str,
    limit: float | int,
    review_status: str = "all",
) -> tuple[list[list[str]], Any, Any]:
    rows = list_history_rows(
        repo=repo,
        session_id=session_id,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        review_status=review_status,
    )
    run_ids = [str(row[0]) for row in rows if row]
    default_a = run_ids[0] if run_ids else None
    default_b = run_ids[1] if len(run_ids) > 1 else default_a
    return (
        rows,
        gr.update(choices=run_ids, value=default_a),
        gr.update(choices=run_ids, value=default_b),
    )


def compare_history_runs(
    *,
    repo: StorageRepo,
    run_id_a: str | None,
    run_id_b: str | None,
) -> tuple[str, str, list[list[str]], str, str, str]:
    selected_a = (run_id_a or "").strip()
    selected_b = (run_id_b or "").strip()
    if not selected_a or not selected_b:
        return _empty_compare_payload(
            status_message="Comparison failed: select both run_id A and run_id B."
        )

    diff = compare_runs_payload(
        repo=repo,
        run_id_a=selected_a,
        run_id_b=selected_b,
    )
    return (
        _comparison_status_text(diff),
        _comparison_summary_text(diff),
        _comparison_checklist_rows(diff),
        _comparison_gaps_text(diff),
        _comparison_metrics_text(diff),
        json.dumps(diff, ensure_ascii=False, indent=2),
    )


def export_history_run_bundle(
    *,
    repo: StorageRepo,
    run_id: str,
    signing_key: str | None = None,
) -> tuple[str, str, str | None]:
    target_run_id = run_id.strip()
    if not target_run_id:
        return "Export failed: run_id is empty.", "", None

    run = repo.get_run(target_run_id)
    if run is None:
        return f"Export failed: run_id={target_run_id} not found.", "", None

    try:
        zip_path = export_run_bundle(
            artifacts_root_path=run.artifacts_root_path,
            signing_key=signing_key,
        )
    except (FileNotFoundError, NotADirectoryError, ZipExportError) as error:
        return f"Export failed: {error}", "", None
    except OSError as error:
        return f"Export failed: filesystem error: {error}", "", None

    status = f"Export completed. run_id={target_run_id}"
    return status, str(zip_path), str(zip_path)


def restore_history_run_bundle(
    *,
    repo: StorageRepo,
    zip_file_path: str | Path | None,
    overwrite_existing: bool,
    verify_only: bool = False,
    require_signature: bool = False,
    signing_key: str | None = None,
    safety_limits: RestoreSafetyLimits | None = None,
    session_id: str = "",
    provider: str = "",
    model: str = "",
    prompt_version: str = "",
    date_from: str = "",
    date_to: str = "",
    limit: float | int = 20,
    review_status: str = "all",
) -> tuple[str, str, str, str, list[list[str]], Any, Any, Any]:
    restore_limits = safety_limits or RestoreSafetyLimits()
    rows, compare_a, compare_b = refresh_history_for_ui(
        repo=repo,
        session_id=session_id,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        review_status=review_status,
    )
    run_id_update = gr.update()

    if zip_file_path is None:
        return (
            "Restore failed: ZIP file is not provided.",
            "technical_details=Upload a ZIP file before restore.",
            "",
            "",
            rows,
            compare_a,
            compare_b,
            run_id_update,
        )

    result = restore_run_bundle(
        repo=repo,
        zip_path=Path(zip_file_path),
        overwrite_existing=overwrite_existing,
        verify_only=verify_only,
        require_signature=require_signature,
        signing_key=signing_key,
        safety_limits=restore_limits,
    )

    rows, compare_a, compare_b = refresh_history_for_ui(
        repo=repo,
        session_id=session_id,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        review_status=review_status,
    )

    if result.status in {"restored", "verified"}:
        restored_run_id = result.run_id or ""
        action = (
            "Verification completed." if result.verify_only else "Restore completed."
        )
        status = (
            f"{action} run_id={restored_run_id} session_id={result.session_id or ''}"
        )
        details = (
            "technical_details="
            f"manifest_verification={result.manifest_verification_status} "
            f"files_checked={result.files_checked} "
            f"signature_verification={result.signature_verification_status} "
            f"archive_signed={result.archive_signed} "
            f"strict_mode={result.signature_required} "
            f"verify_only={result.verify_only} "
            f"warnings={len(result.warnings)} "
            f"errors={len(result.errors)} "
            f"rollback_attempted={result.rollback_attempted} "
            f"rollback_succeeded={result.rollback_succeeded}"
        )
        run_id_update = (
            gr.update(value=restored_run_id) if not result.verify_only else gr.update()
        )
        return (
            status,
            details,
            restored_run_id,
            result.artifacts_root_path or "",
            rows,
            compare_a,
            compare_b,
            run_id_update,
        )

    friendly_error = ERROR_FRIENDLY_MESSAGES.get(
        result.error_code or "",
        "Restore failed. Check technical details.",
    )
    details = (
        "technical_details="
        f"manifest_verification={result.manifest_verification_status} "
        f"files_checked={result.files_checked} "
        f"signature_verification={result.signature_verification_status} "
        f"archive_signed={result.archive_signed} "
        f"strict_mode={result.signature_required} "
        f"verify_only={result.verify_only} "
        f"rollback_attempted={result.rollback_attempted} "
        f"rollback_succeeded={result.rollback_succeeded} "
        f"error_code={result.error_code or ''} "
        f"error_message={result.error_message or ''} "
        f"errors={' | '.join(result.errors)}"
    )
    return (
        f"Restore failed. {friendly_error}",
        details,
        result.run_id or "",
        result.artifacts_root_path or "",
        rows,
        compare_a,
        compare_b,
        run_id_update,
    )


def delete_history_run(
    *,
    repo: StorageRepo,
    run_id: str,
    confirm_run_id: str,
    create_backup_zip: bool,
    signing_key: str | None = None,
    session_id: str = "",
    provider: str = "",
    model: str = "",
    prompt_version: str = "",
    date_from: str = "",
    date_to: str = "",
    limit: float | int = 20,
    review_status: str = "all",
) -> tuple[str, str, str, list[list[str]], Any, Any, Any, Any]:
    target_run_id = run_id.strip()
    confirmation = confirm_run_id.strip()
    rows, compare_a, compare_b = refresh_history_for_ui(
        repo=repo,
        session_id=session_id,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        review_status=review_status,
    )
    clear_run_id_update = gr.update()
    clear_confirm_update = gr.update()
    backup_path = ""

    if not target_run_id:
        return (
            "Delete failed: run_id is empty.",
            backup_path,
            "technical_details=Input run_id is empty.",
            rows,
            compare_a,
            compare_b,
            clear_run_id_update,
            clear_confirm_update,
        )

    if confirmation != target_run_id:
        return (
            "Delete failed: confirmation mismatch.",
            backup_path,
            (
                "technical_details=Type the exact run_id in confirmation field. "
                f"expected={target_run_id} got={confirmation or '(empty)'}"
            ),
            rows,
            compare_a,
            compare_b,
            clear_run_id_update,
            clear_confirm_update,
        )

    run = repo.get_run(target_run_id)
    if run is None:
        return (
            f"Delete failed. run_id={target_run_id}",
            backup_path,
            "technical_details=error_code=RUN_NOT_FOUND error_message=Run not found.",
            rows,
            compare_a,
            compare_b,
            clear_run_id_update,
            clear_confirm_update,
        )

    if create_backup_zip:
        try:
            zip_path = export_run_bundle(
                artifacts_root_path=run.artifacts_root_path,
                signing_key=signing_key,
            )
            backup_path = str(zip_path)
        except (FileNotFoundError, NotADirectoryError, ZipExportError) as error:
            return (
                f"Delete failed. run_id={target_run_id}",
                backup_path,
                (
                    "technical_details=error_code=BACKUP_EXPORT_FAILED "
                    f"error_message={error}"
                ),
                rows,
                compare_a,
                compare_b,
                clear_run_id_update,
                clear_confirm_update,
            )
        except OSError as error:
            return (
                f"Delete failed. run_id={target_run_id}",
                backup_path,
                (
                    "technical_details=error_code=BACKUP_EXPORT_FAILED "
                    f"error_message=filesystem error: {error}"
                ),
                rows,
                compare_a,
                compare_b,
                clear_run_id_update,
                clear_confirm_update,
            )

    result = repo.delete_run(target_run_id)
    rows, compare_a, compare_b = refresh_history_for_ui(
        repo=repo,
        session_id=session_id,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        review_status=review_status,
    )
    clear_run_id_update = gr.update(value="")
    clear_confirm_update = gr.update(value="")

    if result.deleted:
        technical = (
            "technical_details="
            f"artifacts_deleted={result.artifacts_deleted} "
            f"artifacts_missing={result.artifacts_missing}"
        )
        return (
            f"Delete completed. run_id={target_run_id}",
            backup_path,
            technical,
            rows,
            compare_a,
            compare_b,
            clear_run_id_update,
            clear_confirm_update,
        )

    details = (
        "technical_details="
        f"error_code={result.error_code or ''} "
        f"error_message={result.error_message or ''} "
        f"details={result.technical_details or ''}"
    )
    return (
        f"Delete failed. run_id={target_run_id}",
        backup_path,
        details,
        rows,
        compare_a,
        compare_b,
        clear_run_id_update,
        clear_confirm_update,
    )


def load_history_run(
    *,
    repo: StorageRepo,
    run_id: str,
) -> tuple[Any, ...]:
    target_run_id = run_id.strip()
    if not target_run_id:
        return _empty_ui_payload(status_message="History load failed: run_id is empty.")

    bundle = repo.get_run_bundle(target_run_id)
    if bundle is None:
        return _empty_ui_payload(
            status_message=f"History load failed: run_id={target_run_id} not found."
        )

    run = bundle.run
    artifacts_root = run.artifacts_root_path
    manifest, manifest_error = safe_load_run_manifest(artifacts_root)
    scenario_id = _manifest_scenario_id(manifest=manifest)
    raw_json_text = _load_raw_json_text(artifacts_root=artifacts_root, parsed_json=None)
    if scenario_id == SCENARIO_2_ID:
        parsed_json = None
    else:
        parsed_json = _load_parsed_json(bundle=bundle, artifacts_root=artifacts_root)
        raw_json_text = _load_raw_json_text(
            artifacts_root=artifacts_root,
            parsed_json=parsed_json,
        )
    validation_text = _load_validation_text(artifacts_root=artifacts_root)
    status_message = (
        f"History loaded. session_id={run.session_id} run_id={run.run_id} "
        f"status={run.status}"
    )
    if run.error_code:
        status_message += f" error_code={run.error_code}"
    if manifest_error:
        status_message += f" warning={manifest_error}"

    error_friendly, error_details = _render_error_messages(
        error_code=run.error_code,
        error_message=run.error_message,
    )
    progress = _build_progress_text(
        artifacts_root=artifacts_root,
        run_status=run.status,
    )
    runtime_log_tail, runtime_log_path = _read_runtime_log(
        artifacts_root=artifacts_root,
        line_count=30,
    )

    if scenario_id == SCENARIO_2_ID:
        parsed_json = None
        details_selector, details_text = (
            _details_selector_update([]),
            ("Details: not applicable for Scenario 2 foundation run."),
        )
    else:
        details_selector, details_text = _details_payload(parsed_json=parsed_json)

    if scenario_id == SCENARIO_2_ID:
        summary = raw_json_text
        raw_json_text = ""
    else:
        summary = _summary_from_payload(parsed_json if parsed_json is not None else {})

    (
        scenario2_diagnostics,
        scenario2_fragments,
        scenario2_review_status,
        scenario2_verifier_gate_status,
    ) = _scenario2_ui_payload(
        scenario_id=scenario_id,
        artifacts_root=artifacts_root,
        manifest=manifest,
        fallback_runner_mode=_manifest_scenario2_runner_mode(manifest=manifest),
        fallback_verifier_policy=_manifest_scenario2_verifier_policy(manifest=manifest),
        fallback_llm_executed=_manifest_scenario2_llm_executed(manifest=manifest),
        run_status=run.status,
        error_code=run.error_code,
        error_message=run.error_message,
    )
    if scenario_id == SCENARIO_2_ID:
        case_workspace_id = _manifest_scenario2_case_workspace_id(manifest=manifest)
        status_message += (
            (f" case_workspace_id={case_workspace_id}" if case_workspace_id else "")
            + f" review_status={scenario2_review_status}"
            + f" verifier_gate_status={scenario2_verifier_gate_status}"
        )

    return (
        status_message,
        run.session_id,
        run.run_id,
        run.session_id,
        artifacts_root,
        progress,
        runtime_log_tail,
        runtime_log_path,
        error_friendly,
        error_details,
        _history_ocr_rows(bundle=bundle),
        build_checklist_rows(parsed_json),
        build_gap_rows(parsed_json),
        details_selector,
        details_text,
        summary,
        raw_json_text,
        validation_text,
        _metrics_text_for_history(run=run, manifest=manifest),
        scenario2_diagnostics,
        scenario2_fragments,
        parsed_json,
    )


def _scenario2_ui_payload(
    *,
    scenario_id: str,
    artifacts_root: str,
    manifest: dict[str, Any] | None,
    fallback_runner_mode: str,
    fallback_verifier_policy: str,
    fallback_llm_executed: bool | None,
    run_status: str,
    error_code: str | None,
    error_message: str | None,
) -> tuple[str, str, str, str]:
    if scenario_id != SCENARIO_2_ID:
        return (
            _scenario2_not_applicable_diagnostics_text(),
            _scenario2_not_applicable_fragments_text(),
            "not_applicable",
            "not_applicable",
        )

    trace_payload, trace_error = _load_scenario2_trace_payload(
        artifacts_root=artifacts_root,
        manifest=manifest,
    )
    review_status = _scenario_review_status(
        scenario_id=scenario_id,
        manifest=manifest,
        trace_payload=trace_payload,
        artifacts_root=artifacts_root,
        fallback_llm_executed=fallback_llm_executed,
    )
    verifier_gate_status = _scenario2_verifier_gate_status(
        scenario_id=scenario_id,
        manifest=manifest,
        trace_payload=trace_payload,
        artifacts_root=artifacts_root,
        fallback_llm_executed=fallback_llm_executed,
        fallback_verifier_policy=fallback_verifier_policy,
    )
    if trace_payload is not None:
        return (
            _format_scenario2_diagnostics_text(
                trace_payload=trace_payload,
                run_status=run_status,
                fallback_runner_mode=fallback_runner_mode,
                fallback_verifier_policy=fallback_verifier_policy,
                fallback_llm_executed=fallback_llm_executed,
                fallback_error_code=error_code,
                fallback_error_message=error_message,
                review_status=review_status,
                verifier_gate_status=verifier_gate_status,
            ),
            _format_scenario2_fragments_text(trace_payload=trace_payload),
            review_status,
            verifier_gate_status,
        )

    return (
        _format_scenario2_fallback_diagnostics_text(
            runner_mode=fallback_runner_mode,
            verifier_policy=fallback_verifier_policy,
            llm_executed=fallback_llm_executed,
            run_status=run_status,
            error_code=error_code,
            error_message=error_message,
            trace_error=trace_error,
            review_status=review_status,
            verifier_gate_status=verifier_gate_status,
        ),
        _format_scenario2_fallback_fragments_text(trace_error=trace_error),
        review_status,
        verifier_gate_status,
    )


def _load_scenario2_trace_payload(
    *,
    artifacts_root: str,
    manifest: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, str | None]:
    if not artifacts_root:
        return None, "artifacts root is not available"

    trace_path = _scenario2_trace_path(
        artifacts_root=artifacts_root,
        manifest=manifest,
    )
    if trace_path is None:
        return None, "scenario2 trace path is not configured"

    payload, error = safe_read_json(trace_path)
    if error is not None:
        return None, error
    if not isinstance(payload, dict):
        return None, "scenario2 trace payload is not a JSON object"
    return payload, None


def _scenario2_trace_path(
    *,
    artifacts_root: str,
    manifest: dict[str, Any] | None,
) -> Path | None:
    if isinstance(manifest, dict):
        artifacts = manifest.get("artifacts")
        if isinstance(artifacts, dict):
            llm_artifacts = artifacts.get("llm")
            if isinstance(llm_artifacts, dict):
                trace_path = llm_artifacts.get("trace_path")
                if isinstance(trace_path, str) and trace_path.strip():
                    return Path(trace_path)
    return Path(artifacts_root) / "llm" / "scenario2_trace.json"


def _format_scenario2_diagnostics_text(
    *,
    trace_payload: dict[str, Any],
    run_status: str,
    fallback_runner_mode: str,
    fallback_verifier_policy: str,
    fallback_llm_executed: bool | None,
    fallback_error_code: str | None,
    fallback_error_message: str | None,
    review_status: str,
    verifier_gate_status: str,
) -> str:
    diagnostics = _trace_diagnostics(trace_payload=trace_payload)
    tool_trace = trace_payload.get("tool_trace")
    stage = _string_value(diagnostics.get("stage"))
    error_code = _string_value(diagnostics.get("error_code")) or fallback_error_code
    error_message = (
        _string_value(diagnostics.get("error_message")) or fallback_error_message
    )

    lines = [
        f"review_status: {review_status or 'not_applicable'}",
        f"runner_mode: {_string_value(trace_payload.get('runner_mode')) or fallback_runner_mode or 'unknown'}",
        (
            "verifier_policy: "
            f"{_string_value(diagnostics.get('verifier_policy')) or fallback_verifier_policy or 'informational'}"
        ),
        f"verifier_gate_status: {verifier_gate_status or 'not_applicable'}",
        f"llm_executed: {_bool_text(trace_payload.get('llm_executed', fallback_llm_executed))}",
        f"run_status: {run_status or 'unknown'}",
        f"fragment_grounding_status: {_string_value(diagnostics.get('fragment_grounding_status')) or 'none'}",
        f"citation_binding_status: {_string_value(diagnostics.get('citation_binding_status')) or 'none'}",
        f"verifier_status: {_string_value(diagnostics.get('verifier_status')) or 'none'}",
        (
            "citation_format_status: "
            f"{_string_value(diagnostics.get('citation_format_status')) or 'none'}"
        ),
        f"fetch_fragments_called: {_bool_text(diagnostics.get('fetch_fragments_called'))}",
        (
            "fetch_fragments_returned_usable_fragments: "
            f"{_bool_text(diagnostics.get('fetch_fragments_returned_usable_fragments'))}"
        ),
        f"repair_turn_used: {_bool_text(diagnostics.get('repair_turn_used'))}",
        (
            "legal_citation_count: "
            f"{_string_value(diagnostics.get('legal_citation_count')) or '0'}"
        ),
        (
            "user_doc_citation_count: "
            f"{_string_value(diagnostics.get('user_doc_citation_count')) or '0'}"
        ),
        (
            "citations_in_analysis_sections: "
            f"{_bool_text(diagnostics.get('citations_in_analysis_sections'))}"
        ),
        (
            "sources_section_present: "
            f"{_bool_text(diagnostics.get('sources_section_present'))}"
        ),
        (
            "fetched_sources_referenced: "
            f"{_bool_text(diagnostics.get('fetched_sources_referenced'))}"
        ),
        (
            "tool_round_count: "
            f"{_string_value(trace_payload.get('tool_round_count')) or _string_value(diagnostics.get('tool_round_count')) or '0'}"
        ),
    ]
    if stage:
        lines.append(f"stage: {stage}")
    if error_code:
        lines.append(f"error_code: {error_code}")
    if error_message:
        lines.append(f"error_message: {error_message}")

    lines.append("missing_sections:")
    lines.extend(_bullet_list(_string_list(diagnostics.get("missing_sections"))))
    lines.append("verifier_warnings:")
    lines.extend(_bullet_list(_string_list(diagnostics.get("verifier_warnings"))))
    lines.append("malformed_citation_warnings:")
    lines.extend(
        _bullet_list(_string_list(diagnostics.get("malformed_citation_warnings")))
    )
    lines.append("tool_trace_summary:")
    lines.extend(_tool_trace_summary_lines(tool_trace=tool_trace))
    return "\n".join(lines)


def _format_scenario2_fragments_text(*, trace_payload: dict[str, Any]) -> str:
    diagnostics = _trace_diagnostics(trace_payload=trace_payload)
    ledger = _scenario2_fragment_ledger(diagnostics=diagnostics)
    citations = _string_list(diagnostics.get("fetched_fragment_citations"))
    doc_uids = _string_list(diagnostics.get("fetched_fragment_doc_uids"))
    source_hashes = _string_list(diagnostics.get("fetched_fragment_source_hashes"))
    quote_checksums = _string_list(diagnostics.get("fetched_fragment_quote_checksums"))
    return "\n".join(
        [
            "fetched_fragment_ledger:",
            *_scenario2_fragment_ledger_lines(ledger=ledger),
            "",
            "fetched_fragment_citations:",
            *_bullet_list(citations),
            "",
            "fetched_fragment_doc_uids:",
            *_bullet_list(doc_uids),
            "",
            "fetched_fragment_source_hashes:",
            *_bullet_list(source_hashes),
            "",
            "fetched_fragment_quote_checksums:",
            *_bullet_list(quote_checksums),
        ]
    )


def _format_scenario2_fallback_diagnostics_text(
    *,
    runner_mode: str,
    verifier_policy: str,
    llm_executed: bool | None,
    run_status: str,
    error_code: str | None,
    error_message: str | None,
    trace_error: str | None,
    review_status: str,
    verifier_gate_status: str,
) -> str:
    stub_mode = normalize_scenario2_runner_mode(runner_mode) != "openai_tool_loop"
    lines = [
        f"review_status: {review_status or 'not_applicable'}",
        f"runner_mode: {runner_mode or 'unknown'}",
        f"verifier_policy: {verifier_policy or 'informational'}",
        f"verifier_gate_status: {verifier_gate_status or 'not_applicable'}",
        f"llm_executed: {_bool_text(llm_executed)}",
        f"run_status: {run_status or 'unknown'}",
        (
            "fragment_grounding_status: "
            f"{'not_applicable' if stub_mode else 'unavailable'}"
        ),
        (
            "citation_binding_status: "
            f"{'not_applicable' if stub_mode else 'unavailable'}"
        ),
        (f"verifier_status: {'not_applicable' if stub_mode else 'unavailable'}"),
        (f"citation_format_status: {'not_applicable' if stub_mode else 'unavailable'}"),
        f"fetch_fragments_called: {_bool_text(False if stub_mode else None)}",
        (
            "fetch_fragments_returned_usable_fragments: "
            f"{_bool_text(False if stub_mode else None)}"
        ),
        f"repair_turn_used: {_bool_text(False if stub_mode else None)}",
        f"legal_citation_count: {'0' if stub_mode else 'unavailable'}",
        f"user_doc_citation_count: {'0' if stub_mode else 'unavailable'}",
        (f"citations_in_analysis_sections: {_bool_text(False if stub_mode else None)}"),
        f"sources_section_present: {_bool_text(None if not stub_mode else None)}",
        f"fetched_sources_referenced: {_bool_text(None if not stub_mode else None)}",
        f"tool_round_count: {'0' if stub_mode else 'unavailable'}",
    ]
    if error_code:
        lines.append(f"error_code: {error_code}")
    if error_message:
        lines.append(f"error_message: {error_message}")
    if trace_error:
        lines.append(f"trace_status: unavailable ({trace_error})")
    lines.append("missing_sections:")
    lines.append("- none")
    lines.append("verifier_warnings:")
    lines.append("- none")
    lines.append("malformed_citation_warnings:")
    lines.append("- none")
    lines.append("tool_trace_summary:")
    lines.append("- none")
    return "\n".join(lines)


def _format_scenario2_fallback_fragments_text(*, trace_error: str | None) -> str:
    lines = [
        "fetched_fragment_ledger:",
        "- none",
        "",
        "fetched_fragment_citations:",
        "- none",
        "",
        "fetched_fragment_doc_uids:",
        "- none",
        "",
        "fetched_fragment_source_hashes:",
        "- none",
        "",
        "fetched_fragment_quote_checksums:",
        "- none",
    ]
    if trace_error:
        lines.extend(["", f"trace_status: unavailable ({trace_error})"])
    return "\n".join(lines)


def _scenario2_not_applicable_diagnostics_text() -> str:
    return (
        "Scenario 2 diagnostics: not applicable for Scenario 1.\n"
        "review_status: not_applicable\n"
        "verifier_policy: informational\n"
        "verifier_gate_status: not_applicable"
    )


def _scenario2_not_applicable_fragments_text() -> str:
    return "Scenario 2 fetched fragments: not applicable for Scenario 1."


def _trace_diagnostics(*, trace_payload: dict[str, Any]) -> dict[str, Any]:
    diagnostics = trace_payload.get("diagnostics")
    if isinstance(diagnostics, dict):
        return diagnostics
    return {}


def _tool_trace_summary_lines(*, tool_trace: Any) -> list[str]:
    if not isinstance(tool_trace, list) or not tool_trace:
        return ["- none"]

    lines: list[str] = []
    for item in tool_trace:
        if not isinstance(item, dict):
            continue
        tool = _string_value(item.get("tool")) or "unknown"
        status = _string_value(item.get("status")) or "unknown"
        lines.append(f"- {tool}: {status}")
    return lines or ["- none"]


def _scenario2_fragment_ledger(*, diagnostics: dict[str, Any]) -> list[dict[str, Any]]:
    ledger = diagnostics.get("fetched_fragment_ledger")
    if not isinstance(ledger, list):
        return []
    return [item for item in ledger if isinstance(item, dict)]


def _scenario2_fragment_ledger_lines(*, ledger: list[dict[str, Any]]) -> list[str]:
    if not ledger:
        return ["- none"]

    lines: list[str] = []
    for index, entry in enumerate(ledger, start=1):
        lines.append(f"- fragment_{index}:")
        lines.append(
            f"  display_citation: {_string_value(entry.get('display_citation')) or 'none'}"
        )
        lines.append(
            f"  text_excerpt: {_compact_text(_string_value(entry.get('text_excerpt'))) or 'none'}"
        )
        lines.append(f"  locator: {_scenario2_locator_text(entry.get('locator'))}")
        lines.append(
            "  locator_precision: "
            f"{_string_value(entry.get('locator_precision')) or 'none'}"
        )
        lines.append(
            "  page_truth_status: "
            f"{_string_value(entry.get('page_truth_status')) or 'none'}"
        )
        lines.append(
            f"  quote_checksum: {_string_value(entry.get('quote_checksum')) or 'none'}"
        )
        lines.append(f"  doc_uid: {_string_value(entry.get('doc_uid')) or 'none'}")
        lines.append(
            f"  source_hash: {_string_value(entry.get('source_hash')) or 'none'}"
        )
    return lines


def _scenario2_locator_text(value: Any) -> str:
    if isinstance(value, dict) and value:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return "none"


def _compact_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _string_value(item)
        if text:
            items.append(text)
    return items


def _bullet_list(items: list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text


def _bool_text(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "unknown"


def load_prompt_for_ui(
    *,
    prompt_manager: PromptManager,
    prompt_name: str,
    prompt_version: str | None = None,
) -> tuple[str, str, str]:
    versions = prompt_manager.list_versions(prompt_name)
    if not versions:
        return "", "", "Prompt versions not found."

    selected_version = prompt_version or versions[-1]
    if selected_version not in versions:
        selected_version = versions[-1]

    prompt_set = prompt_manager.load_prompt_set(
        prompt_name=prompt_name,
        version=selected_version,
    )
    return selected_version, prompt_set.system_prompt_text, prompt_set.schema_text


def on_prompt_name_change(
    *,
    prompt_manager: PromptManager,
    prompt_name: str,
) -> tuple[Any, Any, str, str, str]:
    versions = prompt_manager.list_versions(prompt_name)
    if not versions:
        return (
            gr.update(choices=[], value=None),
            gr.update(choices=[""], value=""),
            "",
            "",
            f"No versions found for prompt: {prompt_name}",
        )

    selected_version, system_prompt_text, schema_text = load_prompt_for_ui(
        prompt_manager=prompt_manager,
        prompt_name=prompt_name,
        prompt_version=versions[-1],
    )
    return (
        gr.update(choices=versions, value=selected_version),
        gr.update(choices=[""] + versions, value=""),
        system_prompt_text,
        schema_text,
        f"Loaded {prompt_name}/{selected_version}",
    )


def on_prompt_version_change(
    *,
    prompt_manager: PromptManager,
    prompt_name: str,
    prompt_version: str,
) -> tuple[str, str, str]:
    try:
        _, system_prompt_text, schema_text = load_prompt_for_ui(
            prompt_manager=prompt_manager,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
        )
    except Exception as error:  # noqa: BLE001
        return "", "", f"Failed to load prompt assets: {error}"

    return system_prompt_text, schema_text, f"Loaded {prompt_name}/{prompt_version}"


def save_prompt_as_new_version_for_ui(
    *,
    prompt_manager: PromptManager,
    prompt_name: str,
    source_version: str,
    system_prompt_text: str,
    schema_text: str,
    author: str,
    note: str,
) -> tuple[str, Any, Any]:
    try:
        new_version = prompt_manager.save_as_new_version(
            prompt_name=prompt_name,
            source_version=source_version,
            system_prompt_text=system_prompt_text,
            author=author,
            note=note,
            schema_text=schema_text,
        )
        versions = prompt_manager.list_versions(prompt_name)
        return (
            f"Saved new version: {prompt_name}/{new_version}",
            gr.update(choices=versions, value=new_version),
            gr.update(choices=[""] + versions, value=""),
        )
    except Exception as error:  # noqa: BLE001
        return (
            f"Save failed: {error}",
            gr.update(),
            gr.update(),
        )


def render_details_from_state(
    parsed_json_state: dict[str, Any] | None,
    selected_item_id: str | None,
) -> str:
    if not isinstance(parsed_json_state, dict):
        return "No details available for selected item."
    if not str(selected_item_id or "").strip():
        return "No details available for selected item."
    return render_checklist_details(parsed_json_state, selected_item_id)


def on_provider_change_ui(selected_provider: str) -> Any:
    from app.config.settings import get_settings

    settings = get_settings()
    choices = _build_model_choices(settings, selected_provider)
    llm_providers = settings.providers_config.get("llm_providers", {})
    provider_config = llm_providers.get(selected_provider, {})
    default_model = str(provider_config.get("default_model", ""))
    if default_model and default_model in choices:
        selected_model = default_model
    else:
        selected_model = choices[0] if choices else ""
    return gr.update(choices=choices, value=selected_model)


def build_app(
    repo: StorageRepo | None = None,
    orchestrator: OCRPipelineOrchestrator | None = None,
    preflight_checker: PreflightChecker | None = None,
) -> gr.Blocks:
    settings = get_settings()
    restore_safety_limits = RestoreSafetyLimits(
        max_entries=settings.restore_max_entries,
        max_total_uncompressed_bytes=settings.restore_max_total_uncompressed_bytes,
        max_single_file_bytes=settings.restore_max_single_file_bytes,
        max_compression_ratio=settings.restore_max_compression_ratio,
    )
    bundle_signing_key = settings.bundle_signing_key
    restore_require_signature_default = settings.restore_require_signature
    storage_repo = repo or StorageRepo(settings.resolved_sqlite_path)
    prompt_manager = PromptManager(settings.project_root / "app" / "prompts")

    prompt_names = prompt_manager.list_prompt_names()
    default_prompt_name = (
        settings.default_prompt_name
        if settings.default_prompt_name in prompt_names
        else (prompt_names[0] if prompt_names else settings.default_prompt_name)
    )
    prompt_versions = prompt_manager.list_versions(default_prompt_name)
    default_prompt_version = (
        settings.default_prompt_version
        if settings.default_prompt_version in prompt_versions
        else (
            prompt_versions[-1] if prompt_versions else settings.default_prompt_version
        )
    )

    try:
        _, initial_system_prompt, initial_schema_text = load_prompt_for_ui(
            prompt_manager=prompt_manager,
            prompt_name=default_prompt_name,
            prompt_version=default_prompt_version,
        )
    except Exception:
        initial_system_prompt = ""
        initial_schema_text = "{}"

    if orchestrator is None:
        scenario2_runtime = build_scenario2_runtime(settings=settings)
        full_orchestrator = OCRPipelineOrchestrator(
            repo=storage_repo,
            artifacts_manager=storage_repo.artifacts_manager,
            ocr_client=MistralOCRClient(api_key=settings.mistral_api_key),
            llm_clients={
                "openai": OpenAILLMClient(
                    api_key=settings.openai_api_key,
                    pricing_config=settings.pricing_config,
                ),
                "google": GeminiLLMClient(
                    api_key=settings.google_api_key,
                    pricing_config=settings.pricing_config,
                ),
            },
            prompt_root=settings.project_root / "app" / "prompts",
            scenario2_runner=scenario2_runtime.runner,
            legal_corpus_tool=scenario2_runtime.legal_corpus_tool,
            scenario2_case_workspace_store=getattr(
                scenario2_runtime, "case_workspace_store", None
            ),
            scenario2_runner_mode=settings.scenario2_runner_mode,
            scenario2_verifier_policy=settings.scenario2_verifier_policy,
            scenario2_bootstrap_error=scenario2_runtime.bootstrap_error,
        )
    else:
        full_orchestrator = orchestrator

    runtime_preflight = preflight_checker or _make_preflight_checker(settings)
    provider_choices = _build_provider_choices(settings)

    default_provider = (
        settings.default_provider
        if settings.default_provider in provider_choices
        else provider_choices[0]
    )

    model_choices = _build_model_choices(settings, provider=default_provider)
    ocr_model_choices = _build_ocr_model_choices(settings)

    provider_config = settings.providers_config.get("llm_providers", {}).get(
        default_provider, {}
    )
    explicit_default = provider_config.get("default_model")

    if explicit_default and explicit_default in model_choices:
        default_model = str(explicit_default)
    else:
        default_model = (
            settings.default_model
            if settings.default_model in model_choices
            else model_choices[0]
        )
    default_ocr_model = (
        settings.default_ocr_model
        if settings.default_ocr_model in ocr_model_choices
        else ocr_model_choices[0]
    )

    with gr.Blocks(title="Kaucja Case Sandbox") as app:
        gr.Markdown(
            "# Kaucja Case Sandbox - Iteration 8 (Run Comparison + DoD Audit)",
            elem_id="app_title",
        )
        gr.Markdown(
            "Analyze runs OCR -> LLM -> validate -> finalize with deterministic artifacts."
        )

        session_state = gr.State(value="")
        parsed_json_state = gr.State(value={})
        scenario1_state = gr.State(value={})
        previous_scenario_id_state = gr.State(value=SCENARIO_1_ID)

        with gr.Row():
            documents = gr.File(
                label="Documents",
                file_count="multiple",
                type="filepath",
            )

        with gr.Row():
            scenario = gr.Radio(
                label="Scenario",
                choices=scenario_choices(),
                value=SCENARIO_1_ID,
            )
            provider = gr.Dropdown(
                label="Provider",
                choices=provider_choices,
                value=default_provider,
            )
            model = gr.Dropdown(
                label="Model",
                choices=model_choices,
                value=default_model,
            )
            prompt_name = gr.Dropdown(
                label="Prompt Name",
                choices=prompt_names or [default_prompt_name],
                value=default_prompt_name,
            )
            prompt_version = gr.Dropdown(
                label="Prompt Version",
                choices=prompt_versions or [default_prompt_version],
                value=default_prompt_version,
            )
            scenario_config_summary = gr.Textbox(
                label="Scenario 2 fixed config",
                value="",
                visible=False,
                interactive=False,
            )

        with gr.Group(visible=False) as scenario2_case_group:
            gr.Markdown("### Scenario 2 Case Workspace")
            with gr.Row():
                scenario2_case_workspace_id = gr.Textbox(
                    label="Scenario 2 Case ID",
                    value="",
                    elem_id="scenario2_case_workspace_id",
                )
                scenario2_claim_amount = gr.Number(
                    label="Claim Amount",
                    value=None,
                    precision=2,
                    elem_id="scenario2_claim_amount",
                )
                scenario2_currency = gr.Textbox(
                    label="Currency",
                    value="",
                    elem_id="scenario2_currency",
                )
            with gr.Row():
                scenario2_lease_start = gr.Textbox(
                    label="Lease Start",
                    value="",
                    elem_id="scenario2_lease_start",
                )
                scenario2_lease_end = gr.Textbox(
                    label="Lease End",
                    value="",
                    elem_id="scenario2_lease_end",
                )
                scenario2_move_out_date = gr.Textbox(
                    label="Move Out Date",
                    value="",
                    elem_id="scenario2_move_out_date",
                )
                scenario2_deposit_return_due_date = gr.Textbox(
                    label="Deposit Return Due Date",
                    value="",
                    elem_id="scenario2_deposit_return_due_date",
                )

        with gr.Row():
            ocr_model = gr.Dropdown(
                label="OCR Model",
                choices=ocr_model_choices,
                value=default_ocr_model,
            )
            table_format = gr.Dropdown(
                label="Table Format",
                choices=["html", "markdown", "none"],
                value=settings.default_ocr_table_format,
            )
            include_image_base64 = gr.Checkbox(
                label="Include Image Base64",
                value=settings.default_ocr_include_image_base64,
            )
            openai_reasoning_effort = gr.Dropdown(
                label="OpenAI Reasoning Effort",
                choices=["auto", "low", "medium", "high"],
                value="auto",
            )
            gemini_thinking_level = gr.Dropdown(
                label="Gemini Thinking Level",
                choices=["auto", "low", "medium", "high"],
                value="auto",
            )

        with gr.Row():
            analyze_button = gr.Button(
                "Analyze",
                variant="primary",
                elem_id="analyze_button",
            )

        with gr.Row():
            status_box = gr.Textbox(
                label="Status",
                interactive=False,
                elem_id="run_status_box",
            )
            progress_box = gr.Textbox(
                label="Progress (OCR -> LLM -> validate -> finalize)",
                interactive=False,
                elem_id="run_progress_box",
            )
            error_box = gr.Textbox(
                label="User-friendly Error",
                interactive=False,
                elem_id="run_error_box",
            )

        with gr.Row():
            run_id_box = gr.Textbox(
                label="Run ID",
                interactive=False,
                elem_id="run_id_box",
            )
            session_id_box = gr.Textbox(
                label="Session ID",
                interactive=False,
                elem_id="session_id_box",
            )
            artifacts_root_box = gr.Textbox(
                label="Artifacts Root Path",
                interactive=False,
                elem_id="artifacts_root_box",
            )

        with gr.Row():
            runtime_log_path_box = gr.Textbox(label="Full Log Path", interactive=False)
        runtime_log_tail_box = gr.Textbox(
            label="Runtime Log Tail (last lines)",
            lines=8,
            interactive=False,
        )
        error_details_box = gr.Textbox(
            label="Error Details (error_code/error_message)",
            lines=4,
            interactive=False,
        )

        ocr_results = gr.Dataframe(
            headers=["doc_id", "ocr_status", "pages_count", "combined_md_path"],
            datatype=["str", "str", "str", "str"],
            interactive=False,
            wrap=True,
            label="OCR Results",
        )

        checklist_table = gr.Dataframe(
            headers=["item_id", "importance", "status", "confidence"],
            datatype=["str", "str", "str", "str"],
            interactive=False,
            wrap=True,
            label="Checklist",
        )

        gap_table = gr.Dataframe(
            headers=["item_id", "request_from_user.ask"],
            datatype=["str", "str"],
            interactive=False,
            wrap=True,
            label="Gap List",
        )

        with gr.Row():
            details_item_selector = gr.Dropdown(
                label="Details item_id",
                choices=[],
                value=None,
            )
            details_box = gr.Textbox(
                label="Details (findings/quotes/requests)",
                lines=12,
                interactive=False,
            )

        summary_box = gr.Textbox(
            label="Model Response / Summary",
            lines=8,
            interactive=False,
            elem_id="summary_box",
        )
        raw_json_box = gr.Textbox(
            label="Raw JSON",
            lines=12,
            interactive=False,
            elem_id="raw_json_box",
        )
        validation_box = gr.Textbox(
            label="Validation",
            lines=6,
            interactive=False,
            elem_id="validation_box",
        )
        metrics_box = gr.Textbox(
            label="Metrics",
            lines=8,
            interactive=False,
            elem_id="metrics_box",
        )
        with gr.Row():
            scenario2_diagnostics_box = gr.Textbox(
                label="Scenario 2 Diagnostics",
                lines=12,
                interactive=False,
                elem_id="scenario2_diagnostics_box",
            )
            scenario2_fragments_box = gr.Textbox(
                label="Scenario 2 Fetched Fragments",
                lines=12,
                interactive=False,
                elem_id="scenario2_fragments_box",
            )

        gr.Markdown("## Prompt Management")
        prompt_status_box = gr.Textbox(label="Prompt Status", interactive=False)
        system_prompt_editor = gr.Textbox(
            label="system_prompt.txt (editable)",
            lines=14,
            value=initial_system_prompt,
        )
        schema_viewer = gr.Code(
            label="schema.json (view)",
            language="json",
            value=initial_schema_text,
            interactive=False,
        )
        with gr.Row():
            prompt_author = gr.Textbox(label="Author", value="coder")
            prompt_note = gr.Textbox(label="Note", value="")
            save_prompt_button = gr.Button("Save as new version")
        save_prompt_box = gr.Textbox(label="Save Prompt Result", interactive=False)

        gr.Markdown("## Run History", elem_id="history_section")
        with gr.Row():
            history_session_id = gr.Textbox(
                label="Filter: session_id",
                value="",
                elem_id="history_session_filter",
            )
            history_provider = gr.Dropdown(
                label="Filter: provider",
                choices=[""] + provider_choices,
                value="",
                elem_id="history_provider_filter",
            )
            history_model = gr.Dropdown(
                label="Filter: model",
                choices=[""] + _build_model_choices(settings, provider=None),
                value="",
                elem_id="history_model_filter",
            )
            history_prompt_version = gr.Dropdown(
                label="Filter: prompt_version",
                choices=[""] + (prompt_versions or [default_prompt_version]),
                value="",
                elem_id="history_prompt_version_filter",
            )

        with gr.Row():
            history_date_from = gr.Textbox(
                label="Filter: date_from (YYYY-MM-DD)",
                elem_id="history_date_from_filter",
            )
            history_date_to = gr.Textbox(
                label="Filter: date_to (YYYY-MM-DD)",
                elem_id="history_date_to_filter",
            )
            history_limit = gr.Number(
                label="Limit",
                value=20,
                precision=0,
                elem_id="history_limit_filter",
            )
            history_review_status = gr.Dropdown(
                label="Filter: review_status",
                choices=_HISTORY_REVIEW_STATUS_CHOICES,
                value="all",
                elem_id="history_review_status_filter",
            )
            history_refresh_button = gr.Button(
                "Refresh History",
                elem_id="history_refresh_button",
            )

        history_table = gr.Dataframe(
            headers=[
                "run_id",
                "created_at",
                "session_id",
                "scenario_id",
                "provider",
                "model",
                "prompt_version",
                "status",
                "review_status",
                "total_cost_usd",
            ],
            datatype=[
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
                "str",
            ],
            interactive=False,
            wrap=True,
            label="Runs",
            elem_id="history_runs_table",
        )

        with gr.Row():
            history_run_id = gr.Textbox(
                label="Run ID to load",
                elem_id="history_run_id_input",
            )
            history_confirm_run_id = gr.Textbox(
                label="Confirm Run ID for Delete",
                value="",
                elem_id="history_confirm_run_id_input",
            )
            delete_with_backup = gr.Checkbox(
                label="Create backup ZIP before delete",
                value=False,
                elem_id="delete_with_backup_checkbox",
            )
            load_history_button = gr.Button(
                "Load Selected Run",
                elem_id="history_load_button",
            )
            export_history_button = gr.Button(
                "Export run bundle (zip)",
                elem_id="history_export_button",
            )
            delete_history_button = gr.Button(
                "Delete run",
                variant="stop",
                elem_id="history_delete_button",
            )

        with gr.Row():
            export_status_box = gr.Textbox(
                label="Export Status",
                interactive=False,
                elem_id="export_status_box",
            )
            export_path_box = gr.Textbox(
                label="Export ZIP Path",
                interactive=False,
                elem_id="export_path_box",
            )
        export_file_box = gr.File(
            label="Download ZIP",
            interactive=False,
            elem_id="export_file_box",
        )
        with gr.Row():
            restore_zip_file = gr.File(
                label="Restore ZIP File",
                type="filepath",
                elem_id="restore_zip_file_input",
            )
            restore_overwrite_existing = gr.Checkbox(
                label="Overwrite existing run",
                value=False,
                elem_id="restore_overwrite_checkbox",
            )
            restore_verify_only = gr.Checkbox(
                label="Verify only (no restore)",
                value=False,
                elem_id="restore_verify_only_checkbox",
            )
            restore_require_signature = gr.Checkbox(
                label="Require signature (strict)",
                value=restore_require_signature_default,
                elem_id="restore_require_signature_checkbox",
            )
            restore_button = gr.Button(
                "Restore run bundle",
                elem_id="restore_button",
            )
        with gr.Row():
            restore_status_box = gr.Textbox(
                label="Restore Status",
                interactive=False,
                elem_id="restore_status_box",
            )
            restore_details_box = gr.Textbox(
                label="Restore Technical Details",
                interactive=False,
                elem_id="restore_details_box",
            )
        with gr.Row():
            restore_run_id_box = gr.Textbox(
                label="Restored Run ID",
                interactive=False,
                elem_id="restore_run_id_box",
            )
            restore_artifacts_path_box = gr.Textbox(
                label="Restored Artifacts Path",
                interactive=False,
                elem_id="restore_artifacts_path_box",
            )
        with gr.Row():
            delete_status_box = gr.Textbox(
                label="Delete Status",
                interactive=False,
                elem_id="delete_status_box",
            )
            delete_backup_path_box = gr.Textbox(
                label="Delete Backup ZIP Path",
                interactive=False,
                elem_id="delete_backup_path_box",
            )
            delete_details_box = gr.Textbox(
                label="Delete Technical Details",
                interactive=False,
                elem_id="delete_details_box",
            )

        gr.Markdown("### Compare Runs", elem_id="compare_section")
        with gr.Row():
            compare_run_id_a = gr.Dropdown(
                label="Run ID A",
                choices=[],
                value=None,
                elem_id="compare_run_id_a",
            )
            compare_run_id_b = gr.Dropdown(
                label="Run ID B",
                choices=[],
                value=None,
                elem_id="compare_run_id_b",
            )
            compare_button = gr.Button(
                "Compare Selected Runs",
                elem_id="compare_button",
            )

        compare_status_box = gr.Textbox(
            label="Compare Status",
            interactive=False,
            elem_id="compare_status_box",
        )
        compare_summary_box = gr.Textbox(
            label="What Changed (improved/regressed/unchanged)",
            lines=6,
            interactive=False,
            elem_id="compare_summary_box",
        )
        compare_checklist_table = gr.Dataframe(
            headers=[
                "item_id",
                "status_a",
                "status_b",
                "confidence_a",
                "confidence_b",
                "findings_changed",
                "request_changed",
                "change",
            ],
            datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
            interactive=False,
            wrap=True,
            label="Checklist Comparison",
            elem_id="compare_checklist_table",
        )
        compare_gaps_box = gr.Textbox(
            label="Critical Gaps / Next Questions Comparison",
            lines=10,
            interactive=False,
            elem_id="compare_gaps_box",
        )
        compare_metrics_box = gr.Textbox(
            label="Metrics Comparison (tokens/cost/timings)",
            lines=10,
            interactive=False,
            elem_id="compare_metrics_box",
        )
        compare_json_box = gr.Textbox(
            label="Comparison Diff JSON",
            lines=14,
            interactive=False,
            elem_id="compare_json_box",
        )

        analyze_button.click(
            fn=lambda current_session_id, uploaded, selected_scenario_id, selected_provider, selected_model, selected_prompt_name, selected_prompt_version, selected_case_workspace_id, selected_claim_amount, selected_currency, selected_lease_start, selected_lease_end, selected_move_out_date, selected_deposit_return_due_date, selected_ocr_model, selected_table_format, selected_include_images, selected_reasoning, selected_thinking: (
                run_full_pipeline(
                    orchestrator=full_orchestrator,
                    prompt_name=selected_prompt_name,
                    current_session_id=current_session_id,
                    uploaded_files=uploaded,
                    scenario_id=selected_scenario_id,
                    provider=selected_provider,
                    model=selected_model,
                    prompt_version=selected_prompt_version,
                    ocr_model=selected_ocr_model,
                    table_format=selected_table_format,
                    include_image_base64=selected_include_images,
                    openai_reasoning_effort=selected_reasoning,
                    gemini_thinking_level=selected_thinking,
                    scenario2_case_workspace_id=selected_case_workspace_id,
                    scenario2_claim_amount=selected_claim_amount,
                    scenario2_currency=selected_currency,
                    scenario2_lease_start=selected_lease_start,
                    scenario2_lease_end=selected_lease_end,
                    scenario2_move_out_date=selected_move_out_date,
                    scenario2_deposit_return_due_date=selected_deposit_return_due_date,
                    preflight_checker=runtime_preflight,
                )
            ),
            inputs=[
                session_state,
                documents,
                scenario,
                provider,
                model,
                prompt_name,
                prompt_version,
                scenario2_case_workspace_id,
                scenario2_claim_amount,
                scenario2_currency,
                scenario2_lease_start,
                scenario2_lease_end,
                scenario2_move_out_date,
                scenario2_deposit_return_due_date,
                ocr_model,
                table_format,
                include_image_base64,
                openai_reasoning_effort,
                gemini_thinking_level,
            ],
            outputs=[
                status_box,
                session_state,
                run_id_box,
                session_id_box,
                artifacts_root_box,
                progress_box,
                runtime_log_tail_box,
                runtime_log_path_box,
                error_box,
                error_details_box,
                ocr_results,
                checklist_table,
                gap_table,
                details_item_selector,
                details_box,
                summary_box,
                raw_json_box,
                validation_box,
                metrics_box,
                scenario2_diagnostics_box,
                scenario2_fragments_box,
                parsed_json_state,
            ],
        )

        scenario.change(
            fn=lambda selected_scenario_id, selected_provider, selected_model, selected_prompt_name, selected_prompt_version, saved_state, previous_scenario: (
                _scenario_config_mode_updates(
                    selected_scenario_id=selected_scenario_id,
                    fallback_provider=selected_provider,
                    fallback_model=selected_model,
                    fallback_prompt_name=selected_prompt_name,
                    fallback_prompt_version=selected_prompt_version,
                    scenario1_state=saved_state,
                    previous_scenario_id=previous_scenario,
                )
            ),
            inputs=[
                scenario,
                provider,
                model,
                prompt_name,
                prompt_version,
                scenario1_state,
                previous_scenario_id_state,
            ],
            outputs=[
                provider,
                model,
                prompt_name,
                prompt_version,
                scenario_config_summary,
                scenario1_state,
                previous_scenario_id_state,
            ],
            api_name=False,
        )

        scenario.change(
            fn=_scenario2_case_block_update,
            inputs=[scenario],
            outputs=[scenario2_case_group],
            api_name=False,
        )

        provider.change(
            fn=on_provider_change_ui,
            inputs=[provider],
            outputs=[model],
            api_name=False,
        )

        details_item_selector.change(
            fn=render_details_from_state,
            inputs=[parsed_json_state, details_item_selector],
            outputs=[details_box],
        )

        history_refresh_button.click(
            fn=lambda session_filter, provider_filter, model_filter, prompt_filter, date_from_filter, date_to_filter, result_limit, selected_review_status: (
                refresh_history_for_ui(
                    repo=storage_repo,
                    session_id=session_filter,
                    provider=provider_filter,
                    model=model_filter,
                    prompt_version=prompt_filter,
                    date_from=date_from_filter,
                    date_to=date_to_filter,
                    limit=result_limit,
                    review_status=selected_review_status,
                )
            ),
            inputs=[
                history_session_id,
                history_provider,
                history_model,
                history_prompt_version,
                history_date_from,
                history_date_to,
                history_limit,
                history_review_status,
            ],
            outputs=[history_table, compare_run_id_a, compare_run_id_b],
        )

        load_history_button.click(
            fn=lambda selected_run_id: load_history_run(
                repo=storage_repo,
                run_id=selected_run_id,
            ),
            inputs=[history_run_id],
            outputs=[
                status_box,
                session_state,
                run_id_box,
                session_id_box,
                artifacts_root_box,
                progress_box,
                runtime_log_tail_box,
                runtime_log_path_box,
                error_box,
                error_details_box,
                ocr_results,
                checklist_table,
                gap_table,
                details_item_selector,
                details_box,
                summary_box,
                raw_json_box,
                validation_box,
                metrics_box,
                scenario2_diagnostics_box,
                scenario2_fragments_box,
                parsed_json_state,
            ],
        )

        export_history_button.click(
            fn=lambda selected_run_id: export_history_run_bundle(
                repo=storage_repo,
                run_id=selected_run_id,
                signing_key=bundle_signing_key,
            ),
            inputs=[history_run_id],
            outputs=[export_status_box, export_path_box, export_file_box],
        )

        restore_button.click(
            fn=lambda selected_zip_file, overwrite_existing_flag, verify_only_flag, require_signature_flag, session_filter, provider_filter, model_filter, prompt_filter, date_from_filter, date_to_filter, result_limit, selected_review_status: (
                restore_history_run_bundle(
                    repo=storage_repo,
                    zip_file_path=selected_zip_file,
                    overwrite_existing=overwrite_existing_flag,
                    verify_only=verify_only_flag,
                    require_signature=require_signature_flag,
                    signing_key=bundle_signing_key,
                    safety_limits=restore_safety_limits,
                    session_id=session_filter,
                    provider=provider_filter,
                    model=model_filter,
                    prompt_version=prompt_filter,
                    date_from=date_from_filter,
                    date_to=date_to_filter,
                    limit=result_limit,
                    review_status=selected_review_status,
                )
            ),
            inputs=[
                restore_zip_file,
                restore_overwrite_existing,
                restore_verify_only,
                restore_require_signature,
                history_session_id,
                history_provider,
                history_model,
                history_prompt_version,
                history_date_from,
                history_date_to,
                history_limit,
                history_review_status,
            ],
            outputs=[
                restore_status_box,
                restore_details_box,
                restore_run_id_box,
                restore_artifacts_path_box,
                history_table,
                compare_run_id_a,
                compare_run_id_b,
                history_run_id,
            ],
        )

        delete_history_button.click(
            fn=lambda selected_run_id, confirmed_run_id, create_backup_before_delete, session_filter, provider_filter, model_filter, prompt_filter, date_from_filter, date_to_filter, result_limit, selected_review_status: (
                delete_history_run(
                    repo=storage_repo,
                    run_id=selected_run_id,
                    confirm_run_id=confirmed_run_id,
                    create_backup_zip=create_backup_before_delete,
                    signing_key=bundle_signing_key,
                    session_id=session_filter,
                    provider=provider_filter,
                    model=model_filter,
                    prompt_version=prompt_filter,
                    date_from=date_from_filter,
                    date_to=date_to_filter,
                    limit=result_limit,
                    review_status=selected_review_status,
                )
            ),
            inputs=[
                history_run_id,
                history_confirm_run_id,
                delete_with_backup,
                history_session_id,
                history_provider,
                history_model,
                history_prompt_version,
                history_date_from,
                history_date_to,
                history_limit,
                history_review_status,
            ],
            outputs=[
                delete_status_box,
                delete_backup_path_box,
                delete_details_box,
                history_table,
                compare_run_id_a,
                compare_run_id_b,
                history_run_id,
                history_confirm_run_id,
            ],
        )

        compare_button.click(
            fn=lambda selected_run_id_a, selected_run_id_b: compare_history_runs(
                repo=storage_repo,
                run_id_a=selected_run_id_a,
                run_id_b=selected_run_id_b,
            ),
            inputs=[compare_run_id_a, compare_run_id_b],
            outputs=[
                compare_status_box,
                compare_summary_box,
                compare_checklist_table,
                compare_gaps_box,
                compare_metrics_box,
                compare_json_box,
            ],
        )

        prompt_name.change(
            fn=lambda selected_prompt_name: on_prompt_name_change(
                prompt_manager=prompt_manager,
                prompt_name=selected_prompt_name,
            ),
            inputs=[prompt_name],
            outputs=[
                prompt_version,
                history_prompt_version,
                system_prompt_editor,
                schema_viewer,
                prompt_status_box,
            ],
        )

        prompt_version.change(
            fn=lambda selected_prompt_name, selected_prompt_version: (
                on_prompt_version_change(
                    prompt_manager=prompt_manager,
                    prompt_name=selected_prompt_name,
                    prompt_version=selected_prompt_version,
                )
            ),
            inputs=[prompt_name, prompt_version],
            outputs=[system_prompt_editor, schema_viewer, prompt_status_box],
        )

        save_prompt_button.click(
            fn=lambda selected_prompt_name, selected_prompt_version, edited_prompt, current_schema, author, note: (
                save_prompt_as_new_version_for_ui(
                    prompt_manager=prompt_manager,
                    prompt_name=selected_prompt_name,
                    source_version=selected_prompt_version,
                    system_prompt_text=edited_prompt,
                    schema_text=current_schema,
                    author=author,
                    note=note,
                )
            ),
            inputs=[
                prompt_name,
                prompt_version,
                system_prompt_editor,
                schema_viewer,
                prompt_author,
                prompt_note,
            ],
            outputs=[save_prompt_box, prompt_version, history_prompt_version],
        )

    return app


def _empty_ui_payload(
    *,
    status_message: str,
    session_id: str = "",
) -> tuple[Any, ...]:
    return (
        status_message,
        session_id,
        "",
        session_id,
        "",
        "OCR: pending | LLM: pending | Validate: pending | Finalize: pending",
        "",
        "",
        "",
        "",
        [],
        [],
        [],
        _details_selector_update([]),
        "No details available for selected item.",
        "",
        "",
        "",
        "",
        _scenario2_not_applicable_diagnostics_text(),
        _scenario2_not_applicable_fragments_text(),
        {},
    )


def _empty_compare_payload(
    *, status_message: str
) -> tuple[str, str, list[list[str]], str, str, str]:
    return (
        status_message,
        "improved: 0 | regressed: 0 | unchanged: 0",
        [],
        "",
        "",
        "{}",
    )


def _resolve_artifacts_root(
    *,
    orchestrator: OCRPipelineOrchestrator,
    run_id: str,
) -> str:
    repo = getattr(orchestrator, "repo", None)
    if repo is None:
        return ""
    get_run = getattr(repo, "get_run", None)
    if not callable(get_run):
        return ""
    run = get_run(run_id)
    if run is None:
        return ""
    return run.artifacts_root_path


def _history_ocr_rows(*, bundle: Any) -> list[list[str]]:
    rows: list[list[str]] = []
    for document in bundle.documents:
        combined_path = (
            Path(document.ocr_artifacts_path) / "combined.md"
            if document.ocr_artifacts_path
            else None
        )
        if combined_path is None:
            combined_display = "combined.md path is not available"
        else:
            _, combined_error = safe_load_combined_markdown(document.ocr_artifacts_path)
            combined_display = (
                str(combined_path)
                if combined_error is None
                else f"{combined_path} ({combined_error})"
            )

        rows.append(
            [
                document.doc_id,
                document.ocr_status,
                "" if document.pages_count is None else str(document.pages_count),
                combined_display,
            ]
        )
    return rows


def _ocr_rows(result: FullPipelineResult) -> list[list[str]]:
    rows: list[list[str]] = []
    for document in result.documents:
        rows.append(
            [
                document.doc_id,
                document.ocr_status,
                "" if document.pages_count is None else str(document.pages_count),
                document.combined_markdown_path,
            ]
        )
    return rows


def _human_summary(result: FullPipelineResult) -> str:
    return _summary_lines(
        critical_gaps_summary=result.critical_gaps_summary,
        next_questions_to_user=result.next_questions_to_user,
    )


def _summary_from_payload(payload: dict[str, Any] | None) -> str:
    if not isinstance(payload, dict):
        return "critical_gaps_summary:\n- (unavailable)\n\nnext_questions_to_user:\n- (unavailable)"

    return _summary_lines(
        critical_gaps_summary=_to_string_list(payload.get("critical_gaps_summary")),
        next_questions_to_user=_to_string_list(payload.get("next_questions_to_user")),
    )


def _summary_lines(
    *,
    critical_gaps_summary: list[str],
    next_questions_to_user: list[str],
) -> str:
    lines: list[str] = ["critical_gaps_summary:"]
    if critical_gaps_summary:
        lines.extend(f"- {item}" for item in critical_gaps_summary)
    else:
        lines.append("- (empty)")

    lines.append("")
    lines.append("next_questions_to_user:")
    if next_questions_to_user:
        lines.extend(f"- {item}" for item in next_questions_to_user)
    else:
        lines.append("- (empty)")

    return "\n".join(lines)


def _raw_json_text(result: FullPipelineResult) -> str:
    if result.raw_json_text:
        return result.raw_json_text
    if result.parsed_json is None:
        return ""
    return json.dumps(result.parsed_json, ensure_ascii=False, indent=2)


def _validation_text(result: FullPipelineResult) -> str:
    if result.validation_valid:
        return "Validation: valid"

    lines = ["Validation: invalid"]
    lines.extend(f"- {error}" for error in result.validation_errors)
    return "\n".join(lines)


def _load_parsed_json(*, bundle: Any, artifacts_root: str) -> dict[str, Any] | None:
    if bundle.llm_output is not None:
        payload, error = safe_read_json(bundle.llm_output.response_json_path)
        if error is None and isinstance(payload, dict):
            return payload

    fallback_payload, fallback_error = safe_load_llm_parsed_json(artifacts_root)
    if fallback_error is None and isinstance(fallback_payload, dict):
        return fallback_payload

    raw_text, raw_error = safe_load_llm_raw_text(artifacts_root)
    if raw_error is None and raw_text is not None:
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return None

    return None


def _load_raw_json_text(
    *,
    artifacts_root: str,
    parsed_json: dict[str, Any] | None,
) -> str:
    raw_text, raw_error = safe_load_llm_raw_text(artifacts_root)
    if raw_error is None and raw_text is not None:
        return raw_text
    if parsed_json is None:
        return raw_error or ""
    return json.dumps(parsed_json, ensure_ascii=False, indent=2)


def _load_validation_text(*, artifacts_root: str) -> str:
    payload, error = safe_load_llm_validation_json(artifacts_root)
    if error is not None:
        return f"Validation artifact unavailable: {error}"
    if payload is None:
        return "Validation artifact unavailable."

    status = str(payload.get("status") or "").strip().lower()
    if status:
        status_errors = _validation_error_lines(payload)
        if status_errors:
            lines = [f"Validation: {status}"]
            lines.extend(f"- {error_text}" for error_text in status_errors)
            return "\n".join(lines)

        if status == "not_applicable":
            return "Validation: not_applicable"
        if status == "skipped":
            return "Validation: skipped"
        if status in {"completed", "valid"}:
            return "Validation: valid"
        if status in {"invalid", "failed"}:
            return "Validation: invalid"

    if status:
        return f"Validation: {status}"

    valid = bool(payload.get("valid"))
    if valid:
        return "Validation: valid"

    schema_errors = _validation_error_lines(payload)
    if not schema_errors:
        schema_errors = _to_string_list(payload.get("errors"))
    lines = ["Validation: invalid"]
    if not schema_errors:
        lines.append("- (no details)")
    else:
        lines.extend(f"- {error_text}" for error_text in schema_errors)
    return "\n".join(lines)


def _metrics_text_for_history(*, run: Any, manifest: dict[str, Any] | None) -> str:
    metrics = {
        "timings": run.timings_json or {},
        "usage": run.usage_json or {},
        "usage_normalized": run.usage_normalized_json or {},
        "cost": run.cost_json or {},
    }
    if isinstance(manifest, dict):
        manifest_metrics = manifest.get("metrics")
        if isinstance(manifest_metrics, dict):
            metrics = {
                "timings": manifest_metrics.get("timings", metrics["timings"]),
                "usage": manifest_metrics.get("usage", metrics["usage"]),
                "usage_normalized": manifest_metrics.get(
                    "usage_normalized", metrics["usage_normalized"]
                ),
                "cost": manifest_metrics.get("cost", metrics["cost"]),
            }
    return json.dumps(metrics, ensure_ascii=False, indent=2)


def _manifest_scenario_id(*, manifest: dict[str, Any] | None) -> str:
    if not isinstance(manifest, dict):
        return SCENARIO_1_ID

    inputs = manifest.get("inputs")
    if not isinstance(inputs, dict):
        return SCENARIO_1_ID

    scenario_id = inputs.get("scenario_id")
    if isinstance(scenario_id, str):
        return scenario_id

    return SCENARIO_1_ID


def _manifest_scenario2_runner_mode(*, manifest: dict[str, Any] | None) -> str:
    if not isinstance(manifest, dict):
        return normalize_scenario2_runner_mode("stub")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return normalize_scenario2_runner_mode("stub")

    llm_artifacts = artifacts.get("llm")
    if not isinstance(llm_artifacts, dict):
        return normalize_scenario2_runner_mode("stub")

    configured = llm_artifacts.get("runner_mode")
    return normalize_scenario2_runner_mode(configured)


def _manifest_scenario2_case_workspace_id(*, manifest: dict[str, Any] | None) -> str:
    if not isinstance(manifest, dict):
        return ""
    inputs = manifest.get("inputs")
    if not isinstance(inputs, dict):
        return ""
    return str(inputs.get("case_workspace_id") or "").strip()


def _manifest_scenario2_llm_executed(
    *,
    manifest: dict[str, Any] | None,
) -> bool | None:
    if not isinstance(manifest, dict):
        return None

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return None

    llm_artifacts = artifacts.get("llm")
    if not isinstance(llm_artifacts, dict):
        return None

    llm_executed = llm_artifacts.get("llm_executed")
    if isinstance(llm_executed, bool):
        return llm_executed
    return None


def _manifest_scenario2_verifier_policy(*, manifest: dict[str, Any] | None) -> str:
    if not isinstance(manifest, dict):
        return normalize_scenario2_verifier_policy("informational")
    return normalize_scenario2_verifier_policy(manifest.get("verifier_policy"))


def _scenario_review_status(
    *,
    scenario_id: str,
    manifest: dict[str, Any] | None,
    artifacts_root: str,
    trace_payload: dict[str, Any] | None = None,
    fallback_llm_executed: bool | None = None,
) -> str:
    if scenario_id != SCENARIO_2_ID:
        return "not_applicable"

    review_payload = _manifest_review_payload(manifest=manifest)
    review_status = _string_value(review_payload.get("status"))
    if review_status:
        return review_status

    effective_trace_payload = trace_payload
    if effective_trace_payload is None:
        effective_trace_payload, _ = _load_scenario2_trace_payload(
            artifacts_root=artifacts_root,
            manifest=manifest,
        )

    diagnostics = (
        _trace_diagnostics(trace_payload=effective_trace_payload)
        if effective_trace_payload is not None
        else {}
    )
    derived = build_scenario2_review_payload(
        verifier_status=_string_value(diagnostics.get("verifier_status")),
        verifier_warnings=_string_list(diagnostics.get("verifier_warnings")),
    )
    derived_status = _string_value(derived.get("status"))
    if derived_status:
        return derived_status

    if fallback_llm_executed is False:
        return "not_applicable"
    return "not_applicable"


def _scenario2_verifier_gate_status(
    *,
    scenario_id: str,
    manifest: dict[str, Any] | None,
    artifacts_root: str,
    trace_payload: dict[str, Any] | None = None,
    fallback_llm_executed: bool | None = None,
    fallback_verifier_policy: str = "informational",
) -> str:
    if scenario_id != SCENARIO_2_ID:
        return "not_applicable"

    direct = _manifest_verifier_gate_payload(manifest=manifest)
    gate_status = _string_value(direct.get("status"))
    if gate_status:
        return gate_status

    effective_trace_payload = trace_payload
    if effective_trace_payload is None:
        effective_trace_payload, _ = _load_scenario2_trace_payload(
            artifacts_root=artifacts_root,
            manifest=manifest,
        )

    diagnostics = (
        _trace_diagnostics(trace_payload=effective_trace_payload)
        if effective_trace_payload is not None
        else {}
    )
    derived = build_scenario2_verifier_gate_payload(
        verifier_policy=(
            _string_value(diagnostics.get("verifier_policy"))
            or _manifest_scenario2_verifier_policy(manifest=manifest)
            or fallback_verifier_policy
        ),
        verifier_status=_string_value(diagnostics.get("verifier_status")),
        llm_executed=fallback_llm_executed,
        verifier_warnings=_string_list(diagnostics.get("verifier_warnings")),
    )
    return _string_value(derived.get("status")) or "not_applicable"


def _manifest_review_payload(*, manifest: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        return {}

    review = manifest.get("review")
    if isinstance(review, dict):
        return review

    review_status = _string_value(manifest.get("review_status"))
    if review_status:
        return {"status": review_status}
    return {}


def _manifest_verifier_gate_payload(
    *,
    manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        return {}

    verifier_gate = manifest.get("verifier_gate")
    if isinstance(verifier_gate, dict):
        return verifier_gate

    verifier_gate_status = _string_value(manifest.get("verifier_gate_status"))
    if verifier_gate_status:
        return {"status": verifier_gate_status}
    return {}


def _normalize_history_review_status_filter(value: str) -> str:
    normalized = str(value or "all").strip()
    if normalized in _HISTORY_REVIEW_STATUS_CHOICES:
        return normalized
    return "all"


def _history_review_status_matches(
    *,
    selected_review_status: str,
    row_review_status: str,
) -> bool:
    if selected_review_status == "all":
        return True
    return row_review_status == selected_review_status


def _validation_error_lines(payload: dict[str, Any]) -> list[str]:
    schema_errors = _to_string_list(payload.get("schema_errors"))
    invariant_errors = _to_string_list(payload.get("invariant_errors"))
    errors = _to_string_list(payload.get("errors"))
    combined = schema_errors + invariant_errors + errors
    return [error_text for error_text in combined if error_text]


def _details_payload(parsed_json: dict[str, Any] | None) -> tuple[Any, str]:
    item_ids = checklist_item_ids(parsed_json)
    selector_update = _details_selector_update(item_ids)
    if not item_ids:
        return selector_update, "No details available for selected item."
    details_text = render_checklist_details(parsed_json, item_ids[0])
    return selector_update, details_text


def _details_selector_update(item_ids: list[str]) -> Any:
    return gr.update(choices=item_ids, value=(item_ids[0] if item_ids else None))


def _read_runtime_log(
    *,
    artifacts_root: str,
    line_count: int,
) -> tuple[str, str]:
    if not artifacts_root:
        return "Run log is not available.", ""

    log_path = Path(artifacts_root) / "logs" / "run.log"
    log_text, error = safe_read_text(log_path)
    if error is not None:
        return f"Run log is not available: {error}", str(log_path)

    lines = (log_text or "").splitlines()
    tail = "\n".join(lines[-line_count:]) if lines else "(empty)"
    return tail, str(log_path)


def _safe_parsed_json(
    *,
    raw_text: str,
    parsed: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if isinstance(parsed, dict):
        return parsed
    if not raw_text.strip():
        return None
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _render_error_messages(
    *,
    error_code: str | None,
    error_message: str | None,
) -> tuple[str, str]:
    if not error_code:
        return "No errors.", ""

    friendly = ERROR_FRIENDLY_MESSAGES.get(
        error_code,
        "Run failed. Check error details and run log.",
    )
    details = f"error_code={error_code}\nerror_message={error_message or ''}"
    return friendly, details


def _build_progress_text(
    *,
    artifacts_root: str,
    run_status: str,
) -> str:
    manifest, error = safe_load_run_manifest(artifacts_root)
    if error is None and isinstance(manifest, dict):
        stages = manifest.get("stages")
        validation = manifest.get("validation")
        if isinstance(stages, dict):
            ocr_status = _stage_status(stages=stages, stage_name="ocr")
            llm_status = _stage_status(stages=stages, stage_name="llm")
            finalize_status = _stage_status(stages=stages, stage_name="finalize")
            validate_status = _validation_stage_status(validation)
            return (
                f"OCR: {ocr_status} | "
                f"LLM: {llm_status} | "
                f"Validate: {validate_status} | "
                f"Finalize: {finalize_status}"
            )

    if run_status == "completed":
        return "OCR: completed | LLM: completed | Validate: completed | Finalize: completed"
    if run_status == "failed":
        return "OCR: completed | LLM: failed | Validate: failed | Finalize: failed"
    return "OCR: running | LLM: pending | Validate: pending | Finalize: pending"


def _validation_stage_status(validation: Any) -> str:
    if not isinstance(validation, dict):
        return "pending"
    status = str(validation.get("status") or "").strip().lower()
    if status in {"not_applicable", "skipped"}:
        return status
    if status in {"invalid", "failed"}:
        return "failed"
    if status in {"completed", "valid"}:
        return "completed"

    valid = validation.get("valid")
    if valid is True:
        return "completed"
    if valid is False:
        return "failed"
    return "pending"


def _stage_status(*, stages: dict[str, Any], stage_name: str) -> str:
    stage = stages.get(stage_name)
    if not isinstance(stage, dict):
        return "pending"
    status = stage.get("status")
    return str(status) if status else "pending"


def _normalize_uploaded_files(
    uploaded_files: Sequence[str | Path] | str | Path | None,
) -> list[Path]:
    if uploaded_files is None:
        return []
    if isinstance(uploaded_files, (str, Path)):
        return [Path(uploaded_files)]
    return [Path(file_path) for file_path in uploaded_files]


def _build_provider_choices(settings: Any) -> list[str]:
    llm_providers = settings.providers_config.get("llm_providers", {})
    return sorted(str(name) for name in llm_providers.keys())


def _build_model_choices(settings: Any, provider: str | None = None) -> list[str]:
    llm_providers = settings.providers_config.get("llm_providers", {})
    models: list[str] = []
    if provider and provider in llm_providers:
        model_map = llm_providers[provider].get("models", {})
        models.extend(str(model_name) for model_name in model_map.keys())
    else:
        for provider_data in llm_providers.values():
            model_map = provider_data.get("models", {})
            models.extend(str(model_name) for model_name in model_map.keys())
    return sorted(models)


def _build_ocr_model_choices(settings: Any) -> list[str]:
    ocr_providers = settings.providers_config.get("ocr_providers", {})
    models: list[str] = []
    for provider_data in ocr_providers.values():
        model_map = provider_data.get("models", {})
        models.extend(str(model_name) for model_name in model_map.keys())
    return sorted(models)


def _make_preflight_checker(settings: Settings) -> PreflightChecker:
    def _checker(provider: str) -> str | None:
        if settings.e2e_mode:
            return None

        if settings.mistral_api_key is None or not settings.mistral_api_key.strip():
            return "Runtime preflight failed: MISTRAL_API_KEY is not configured."
        if importlib.util.find_spec("mistralai") is None:
            return "Runtime preflight failed: mistralai package is not installed."

        if provider == "openai":
            if settings.openai_api_key is None or not settings.openai_api_key.strip():
                return "Runtime preflight failed: OPENAI_API_KEY is not configured."
            if importlib.util.find_spec("openai") is None:
                return "Runtime preflight failed: openai package is not installed."

        if provider == "google":
            if settings.google_api_key is None or not settings.google_api_key.strip():
                return "Runtime preflight failed: GOOGLE_API_KEY is not configured."
            if importlib.util.find_spec("google.genai") is None:
                return (
                    "Runtime preflight failed: google-genai package is not installed."
                )

        return None

    return _checker


def _to_limit(value: float | int) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return 20
    return max(limit, 1)


def _to_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _comparison_status_text(diff: dict[str, Any]) -> str:
    run_a = diff.get("run_a") if isinstance(diff.get("run_a"), dict) else {}
    run_b = diff.get("run_b") if isinstance(diff.get("run_b"), dict) else {}
    run_id_a = str(run_a.get("run_id") or "")
    run_id_b = str(run_b.get("run_id") or "")
    warnings = _to_string_list(diff.get("warnings"))
    exists_a = bool(run_a.get("exists"))
    exists_b = bool(run_b.get("exists"))

    status = f"Comparison ready. run_a={run_id_a} run_b={run_id_b}"
    if not exists_a or not exists_b:
        status = (
            f"Comparison completed with warnings. run_a={run_id_a} run_b={run_id_b}"
        )
    if warnings:
        status += f" warnings={len(warnings)}"
    return status


def _comparison_summary_text(diff: dict[str, Any]) -> str:
    scenario_mode = _comparison_mode_text(diff)
    if scenario_mode == "scenario2_pair":
        return _scenario2_comparison_summary_text(diff)
    if scenario_mode == "mixed":
        return _mixed_scenario_comparison_summary_text(diff)

    counts = (
        diff.get("summary_counts")
        if isinstance(diff.get("summary_counts"), dict)
        else {}
    )
    metadata = diff.get("metadata") if isinstance(diff.get("metadata"), dict) else {}
    warnings = _to_string_list(diff.get("warnings"))
    lines = [
        (
            f"improved: {int(counts.get('improved', 0))} | "
            f"regressed: {int(counts.get('regressed', 0))} | "
            f"unchanged: {int(counts.get('unchanged', 0))}"
        ),
        (
            f"added: {int(counts.get('added', 0))} | "
            f"removed: {int(counts.get('removed', 0))}"
        ),
        (
            f"provider_changed={bool(metadata.get('provider_changed'))}, "
            f"model_changed={bool(metadata.get('model_changed'))}, "
            f"prompt_version_changed={bool(metadata.get('prompt_version_changed'))}"
        ),
    ]

    if warnings:
        lines.append("")
        lines.append("warnings:")
        lines.extend(f"- {warning}" for warning in warnings)

    return "\n".join(lines)


def _comparison_checklist_rows(diff: dict[str, Any]) -> list[list[str]]:
    if _comparison_mode_text(diff) != "scenario1_pair":
        return []

    payload = diff.get("checklist_diff")
    if not isinstance(payload, list):
        return []

    rows: list[list[str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        rows.append(
            [
                str(item.get("item_id") or ""),
                str(item.get("status_a") or ""),
                str(item.get("status_b") or ""),
                str(item.get("confidence_a") or ""),
                str(item.get("confidence_b") or ""),
                "yes" if bool(item.get("findings_changed")) else "no",
                "yes" if bool(item.get("request_changed")) else "no",
                str(item.get("change") or ""),
            ]
        )
    return rows


def _comparison_gaps_text(diff: dict[str, Any]) -> str:
    scenario_mode = _comparison_mode_text(diff)
    if scenario_mode == "scenario2_pair":
        return _scenario2_comparison_gaps_text(diff)
    if scenario_mode == "mixed":
        return _mixed_scenario_comparison_gaps_text(diff)

    critical_diff = (
        diff.get("critical_gaps_diff")
        if isinstance(diff.get("critical_gaps_diff"), dict)
        else {}
    )
    question_diff = (
        diff.get("next_questions_diff")
        if isinstance(diff.get("next_questions_diff"), dict)
        else {}
    )
    lines = ["critical_gaps_summary:"]
    lines.extend(_comparison_list_lines(critical_diff))
    lines.append("")
    lines.append("next_questions_to_user:")
    lines.extend(_comparison_list_lines(question_diff))
    return "\n".join(lines)


def _comparison_list_lines(payload: dict[str, Any]) -> list[str]:
    only_in_a = _to_string_list(payload.get("only_in_a"))
    only_in_b = _to_string_list(payload.get("only_in_b"))
    common = _to_string_list(payload.get("common"))
    return [
        f"- only_in_a ({len(only_in_a)}): {', '.join(only_in_a) if only_in_a else '(empty)'}",
        f"- only_in_b ({len(only_in_b)}): {', '.join(only_in_b) if only_in_b else '(empty)'}",
        f"- common ({len(common)}): {', '.join(common) if common else '(empty)'}",
    ]


def _comparison_metrics_text(diff: dict[str, Any]) -> str:
    metrics = diff.get("metrics_diff")
    if not isinstance(metrics, dict):
        return "{}"

    run_a = metrics.get("run_a") if isinstance(metrics.get("run_a"), dict) else {}
    run_b = metrics.get("run_b") if isinstance(metrics.get("run_b"), dict) else {}
    delta_rows = metrics.get("delta") if isinstance(metrics.get("delta"), list) else []

    lines = [
        "run_a:",
        json.dumps(run_a, ensure_ascii=False, indent=2),
        "",
        "run_b:",
        json.dumps(run_b, ensure_ascii=False, indent=2),
        "",
        "delta (B - A):",
    ]
    for row in delta_rows:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "")
        value_a = row.get("value_a")
        value_b = row.get("value_b")
        delta = row.get("delta_b_minus_a")
        lines.append(f"- {key}: A={value_a} B={value_b} delta={delta}")

    return "\n".join(lines)


def _comparison_mode_text(diff: dict[str, Any]) -> str:
    scenario_comparison = (
        diff.get("scenario_comparison")
        if isinstance(diff.get("scenario_comparison"), dict)
        else {}
    )
    return str(scenario_comparison.get("mode") or "scenario1_pair")


def _scenario2_comparison_summary_text(diff: dict[str, Any]) -> str:
    scenario2_diff = (
        diff.get("scenario2_diff")
        if isinstance(diff.get("scenario2_diff"), dict)
        else {}
    )
    metadata = diff.get("metadata") if isinstance(diff.get("metadata"), dict) else {}
    warnings = _to_string_list(diff.get("warnings"))

    lines = [
        "Scenario 2 diagnostics comparison",
        _scalar_comparison_line(
            label="verifier_policy",
            payload=scenario2_diff.get("verifier_policy"),
        ),
        _scalar_comparison_line(
            label="verifier_gate_status",
            payload=scenario2_diff.get("verifier_gate_status"),
        ),
        _scalar_comparison_line(
            label="review_status",
            payload=scenario2_diff.get("review_status"),
        ),
        _scalar_comparison_line(
            label="runner_mode",
            payload=scenario2_diff.get("runner_mode"),
        ),
        _scalar_comparison_line(
            label="llm_executed",
            payload=scenario2_diff.get("llm_executed"),
        ),
        _scalar_comparison_line(
            label="fragment_grounding_status",
            payload=scenario2_diff.get("fragment_grounding_status"),
        ),
        _scalar_comparison_line(
            label="citation_binding_status",
            payload=scenario2_diff.get("citation_binding_status"),
        ),
        _scalar_comparison_line(
            label="verifier_status",
            payload=scenario2_diff.get("verifier_status"),
        ),
        _scalar_comparison_line(
            label="citation_format_status",
            payload=scenario2_diff.get("citation_format_status"),
        ),
        _scalar_comparison_line(
            label="fetch_fragments_called",
            payload=scenario2_diff.get("fetch_fragments_called"),
        ),
        _scalar_comparison_line(
            label="fetch_fragments_returned_usable_fragments",
            payload=scenario2_diff.get("fetch_fragments_returned_usable_fragments"),
        ),
        _scalar_comparison_line(
            label="repair_turn_used",
            payload=scenario2_diff.get("repair_turn_used"),
        ),
        _scalar_comparison_line(
            label="sources_section_present",
            payload=scenario2_diff.get("sources_section_present"),
        ),
        _scalar_comparison_line(
            label="fetched_sources_referenced",
            payload=scenario2_diff.get("fetched_sources_referenced"),
        ),
        _scalar_comparison_line(
            label="legal_citation_count",
            payload=scenario2_diff.get("legal_citation_count"),
        ),
        _scalar_comparison_line(
            label="user_doc_citation_count",
            payload=scenario2_diff.get("user_doc_citation_count"),
        ),
        _scalar_comparison_line(
            label="citations_in_analysis_sections",
            payload=scenario2_diff.get("citations_in_analysis_sections"),
        ),
        _tool_round_comparison_line(scenario2_diff.get("tool_round_count")),
        _setwise_comparison_summary_line(
            label="missing_sections",
            payload=scenario2_diff.get("missing_sections"),
        ),
        _setwise_comparison_summary_line(
            label="fetched_fragment_citations",
            payload=scenario2_diff.get("fetched_fragment_citations"),
        ),
        _setwise_comparison_summary_line(
            label="fetched_fragment_doc_uids",
            payload=scenario2_diff.get("fetched_fragment_doc_uids"),
        ),
        _setwise_comparison_summary_line(
            label="fetched_fragment_source_hashes",
            payload=scenario2_diff.get("fetched_fragment_source_hashes"),
        ),
        _setwise_comparison_summary_line(
            label="fetched_fragment_quote_checksums",
            payload=scenario2_diff.get("fetched_fragment_quote_checksums"),
        ),
        (
            f"provider_changed={bool(metadata.get('provider_changed'))}, "
            f"model_changed={bool(metadata.get('model_changed'))}, "
            f"prompt_version_changed={bool(metadata.get('prompt_version_changed'))}"
        ),
    ]
    if warnings:
        lines.append("")
        lines.append("warnings:")
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def _mixed_scenario_comparison_summary_text(diff: dict[str, Any]) -> str:
    scenario_comparison = (
        diff.get("scenario_comparison")
        if isinstance(diff.get("scenario_comparison"), dict)
        else {}
    )
    metadata = diff.get("metadata") if isinstance(diff.get("metadata"), dict) else {}
    warnings = _to_string_list(diff.get("warnings"))
    run_a = diff.get("run_a") if isinstance(diff.get("run_a"), dict) else {}
    run_b = diff.get("run_b") if isinstance(diff.get("run_b"), dict) else {}
    lines = [
        "Mixed scenario comparison",
        (
            "Structured checklist diff is not applicable across "
            "Scenario 1 and Scenario 2."
        ),
        (
            f"run_a={scenario_comparison.get('scenario_id_a') or SCENARIO_1_ID}, "
            f"run_b={scenario_comparison.get('scenario_id_b') or SCENARIO_1_ID}"
        ),
        (
            f"review_status_a={run_a.get('review_status') or 'not_applicable'}, "
            f"review_status_b={run_b.get('review_status') or 'not_applicable'}"
        ),
        (
            f"provider_changed={bool(metadata.get('provider_changed'))}, "
            f"model_changed={bool(metadata.get('model_changed'))}, "
            f"prompt_version_changed={bool(metadata.get('prompt_version_changed'))}"
        ),
    ]
    if warnings:
        lines.append("")
        lines.append("warnings:")
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def _scenario2_comparison_gaps_text(diff: dict[str, Any]) -> str:
    scenario2_diff = (
        diff.get("scenario2_diff")
        if isinstance(diff.get("scenario2_diff"), dict)
        else {}
    )
    lines = [
        "scenario2_diagnostics:",
        _scalar_comparison_line(
            label="verifier_policy",
            payload=scenario2_diff.get("verifier_policy"),
        ),
        _scalar_comparison_line(
            label="verifier_gate_status",
            payload=scenario2_diff.get("verifier_gate_status"),
        ),
        _scalar_comparison_line(
            label="review_status",
            payload=scenario2_diff.get("review_status"),
        ),
        _scalar_comparison_line(
            label="fragment_grounding_status",
            payload=scenario2_diff.get("fragment_grounding_status"),
        ),
        _scalar_comparison_line(
            label="citation_binding_status",
            payload=scenario2_diff.get("citation_binding_status"),
        ),
        _scalar_comparison_line(
            label="verifier_status",
            payload=scenario2_diff.get("verifier_status"),
        ),
        _scalar_comparison_line(
            label="citation_format_status",
            payload=scenario2_diff.get("citation_format_status"),
        ),
        _scalar_comparison_line(
            label="sources_section_present",
            payload=scenario2_diff.get("sources_section_present"),
        ),
        _scalar_comparison_line(
            label="fetched_sources_referenced",
            payload=scenario2_diff.get("fetched_sources_referenced"),
        ),
        _scalar_comparison_line(
            label="legal_citation_count",
            payload=scenario2_diff.get("legal_citation_count"),
        ),
        _scalar_comparison_line(
            label="user_doc_citation_count",
            payload=scenario2_diff.get("user_doc_citation_count"),
        ),
        _scalar_comparison_line(
            label="citations_in_analysis_sections",
            payload=scenario2_diff.get("citations_in_analysis_sections"),
        ),
        _tool_round_comparison_line(scenario2_diff.get("tool_round_count")),
        "",
        "missing_sections:",
        *_comparison_list_lines(scenario2_diff.get("missing_sections") or {}),
        "",
        "fetched_fragment_citations:",
        *_comparison_list_lines(scenario2_diff.get("fetched_fragment_citations") or {}),
        "",
        "fetched_fragment_doc_uids:",
        *_comparison_list_lines(scenario2_diff.get("fetched_fragment_doc_uids") or {}),
        "",
        "fetched_fragment_source_hashes:",
        *_comparison_list_lines(
            scenario2_diff.get("fetched_fragment_source_hashes") or {}
        ),
        "",
        "fetched_fragment_quote_checksums:",
        *_comparison_list_lines(
            scenario2_diff.get("fetched_fragment_quote_checksums") or {}
        ),
    ]
    return "\n".join(lines)


def _mixed_scenario_comparison_gaps_text(diff: dict[str, Any]) -> str:
    scenario_comparison = (
        diff.get("scenario_comparison")
        if isinstance(diff.get("scenario_comparison"), dict)
        else {}
    )
    return "\n".join(
        [
            "mixed_scenario_comparison:",
            (
                f"- run_a scenario={scenario_comparison.get('scenario_id_a') or SCENARIO_1_ID}"
            ),
            (
                f"- run_b scenario={scenario_comparison.get('scenario_id_b') or SCENARIO_1_ID}"
            ),
            (
                "- checklist / critical gaps diff is intentionally suppressed "
                "for mixed Scenario 1 vs Scenario 2 comparison"
            ),
        ]
    )


def _scalar_comparison_line(*, label: str, payload: Any) -> str:
    value_a = ""
    value_b = ""
    changed = False
    if isinstance(payload, dict):
        value_a = str(payload.get("value_a"))
        value_b = str(payload.get("value_b"))
        changed = bool(payload.get("changed"))
    return f"{label}: A={value_a} B={value_b} changed={changed}"


def _tool_round_comparison_line(payload: Any) -> str:
    if not isinstance(payload, dict):
        return "tool_round_count: A=0 B=0 delta=0 changed=False"
    return (
        "tool_round_count: "
        f"A={payload.get('value_a')} "
        f"B={payload.get('value_b')} "
        f"delta={payload.get('delta_b_minus_a')} "
        f"changed={bool(payload.get('changed'))}"
    )


def _setwise_comparison_summary_line(*, label: str, payload: Any) -> str:
    normalized = payload if isinstance(payload, dict) else {}
    only_in_a = _to_string_list(normalized.get("only_in_a"))
    only_in_b = _to_string_list(normalized.get("only_in_b"))
    common = _to_string_list(normalized.get("common"))
    return (
        f"{label}: added={len(only_in_b)} removed={len(only_in_a)} common={len(common)}"
    )


def _run_startup_checks(settings: Settings) -> None:
    print("=== Kaucja E2E Environment Checks ===")
    missing_critical = []
    if not settings.mistral_api_key:
        missing_critical.append("MISTRAL_API_KEY (Required for OCR)")
    if not settings.openai_api_key:
        print("[-] OPENAI_API_KEY is missing (OpenAI provider will be disabled)")
    if not settings.google_api_key:
        print("[-] GOOGLE_API_KEY is missing (Google Gemini provider will be disabled)")

    if missing_critical:
        print("\n[!] CRITICAL WARNING: Missing essential configuration:")
        for item in missing_critical:
            print(f"    - {item}")
        print("Please review your .env file before running pipelines.\n")
    else:
        print("[+] Environment looks healthy.\n")


def main() -> None:
    settings = get_settings()
    _run_startup_checks(settings)

    app = build_app()
    target_port = settings.gradio_server_port
    max_port = max(target_port, settings.gradio_server_port_max)

    for port in range(target_port, max_port + 1):
        try:
            print(f"Attempting to start Gradio app on port {port}...")
            app.launch(
                server_name=settings.gradio_server_name,
                server_port=port,
            )
            return
        except OSError as e:
            if "Cannot find empty port" in str(e) or "Address already in use" in str(e):
                print(f"[!] Port {port} is occupied. Trying next...")
            else:
                raise

    print(
        f"\n[ERROR] Failed to find an open port between {target_port} and {max_port}."
    )
    print("If you started multiple instances, please close them.")
    print(
        "Try checking occupied ports with: "
        f"`lsof -nP -iTCP:{target_port}-{max_port} -sTCP:LISTEN`"
    )


if __name__ == "__main__":
    main()
