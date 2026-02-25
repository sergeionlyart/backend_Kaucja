from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Callable, Sequence

import gradio as gr

from app.config.settings import Settings, get_settings
from app.llm_client.gemini_client import GeminiLLMClient
from app.llm_client.openai_client import OpenAILLMClient
from app.ocr_client.mistral_ocr import MistralOCRClient
from app.ocr_client.types import OCROptions
from app.pipeline.orchestrator import FullPipelineResult, OCRPipelineOrchestrator
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


def run_full_pipeline(
    *,
    orchestrator: OCRPipelineOrchestrator,
    prompt_name: str,
    current_session_id: str,
    uploaded_files: Sequence[str | Path] | str | Path | None,
    provider: str,
    model: str,
    prompt_version: str,
    ocr_model: str,
    table_format: str,
    include_image_base64: bool,
    openai_reasoning_effort: str,
    gemini_thinking_level: str,
    preflight_checker: PreflightChecker,
) -> tuple[Any, ...]:
    paths = _normalize_uploaded_files(uploaded_files)
    if not paths:
        return _empty_ui_payload(
            status_message="No files uploaded. Please select at least one document.",
            session_id=current_session_id.strip(),
        )

    preflight_error = preflight_checker(provider)
    if preflight_error is not None:
        return _empty_ui_payload(
            status_message=preflight_error,
            session_id=current_session_id.strip(),
        )

    result = orchestrator.run_full_pipeline(
        input_files=paths,
        session_id=current_session_id.strip() or None,
        provider=provider,
        model=model,
        prompt_name=prompt_name,
        prompt_version=prompt_version,
        ocr_options=OCROptions(
            model=ocr_model,
            table_format=table_format,
            include_image_base64=include_image_base64,
        ),
        llm_params={
            "openai_reasoning_effort": openai_reasoning_effort,
            "gemini_thinking_level": gemini_thinking_level,
        },
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
    parsed_json = _safe_parsed_json(
        raw_text=result.raw_json_text, parsed=result.parsed_json
    )
    progress = _build_progress_text(
        artifacts_root=artifacts_root,
        run_status=result.run_status,
    )
    runtime_log_tail, runtime_log_path = _read_runtime_log(
        artifacts_root=artifacts_root,
        line_count=30,
    )
    error_friendly, error_details = _render_error_messages(
        error_code=result.error_code,
        error_message=result.error_message,
    )
    details_selector, details_text = _details_payload(parsed_json=parsed_json)

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
        _human_summary(result),
        _raw_json_text(result),
        _validation_text(result),
        json.dumps(result.metrics, ensure_ascii=False, indent=2),
        parsed_json,
    )


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
    for run in runs:
        total_cost = ""
        if isinstance(run.cost_json, dict) and "total_cost_usd" in run.cost_json:
            total_cost = str(run.cost_json["total_cost_usd"])

        rows.append(
            [
                run.run_id,
                run.created_at,
                run.session_id,
                run.provider,
                run.model,
                run.prompt_version,
                run.status,
                total_cost,
            ]
        )
    return rows


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
    run_id_a: str,
    run_id_b: str,
) -> tuple[str, str, list[list[str]], str, str, str]:
    selected_a = run_id_a.strip()
    selected_b = run_id_b.strip()
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
    details_selector, details_text = _details_payload(parsed_json=parsed_json)

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
        _summary_from_payload(parsed_json),
        raw_json_text,
        validation_text,
        _metrics_text_for_history(run=run, manifest=manifest),
        parsed_json,
    )


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
    selected_item_id: str,
) -> str:
    return render_checklist_details(parsed_json_state, selected_item_id)


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

    full_orchestrator = orchestrator or OCRPipelineOrchestrator(
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
    )

    runtime_preflight = preflight_checker or _make_preflight_checker(settings)
    provider_choices = _build_provider_choices(settings)
    model_choices = _build_model_choices(settings)
    ocr_model_choices = _build_ocr_model_choices(settings)

    default_provider = (
        settings.default_provider
        if settings.default_provider in provider_choices
        else provider_choices[0]
    )
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
        gr.Markdown("# Kaucja Case Sandbox - Iteration 8 (Run Comparison + DoD Audit)")
        gr.Markdown(
            "Analyze runs OCR -> LLM -> validate -> finalize with deterministic artifacts."
        )

        session_state = gr.State(value="")
        parsed_json_state = gr.State(value={})

        with gr.Row():
            documents = gr.File(
                label="Documents",
                file_count="multiple",
                type="filepath",
            )

        with gr.Row():
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
            analyze_button = gr.Button("Analyze", variant="primary")

        with gr.Row():
            status_box = gr.Textbox(label="Status", interactive=False)
            progress_box = gr.Textbox(
                label="Progress (OCR -> LLM -> validate -> finalize)", interactive=False
            )
            error_box = gr.Textbox(label="User-friendly Error", interactive=False)

        with gr.Row():
            run_id_box = gr.Textbox(label="Run ID", interactive=False)
            session_id_box = gr.Textbox(label="Session ID", interactive=False)
            artifacts_root_box = gr.Textbox(
                label="Artifacts Root Path", interactive=False
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
            label="Summary (critical gaps + next questions)",
            lines=8,
            interactive=False,
        )
        raw_json_box = gr.Textbox(label="Raw JSON", lines=12, interactive=False)
        validation_box = gr.Textbox(label="Validation", lines=6, interactive=False)
        metrics_box = gr.Textbox(label="Metrics", lines=8, interactive=False)

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

        gr.Markdown("## Run History")
        with gr.Row():
            history_session_id = gr.Textbox(label="Filter: session_id", value="")
            history_provider = gr.Dropdown(
                label="Filter: provider",
                choices=[""] + provider_choices,
                value="",
            )
            history_model = gr.Dropdown(
                label="Filter: model",
                choices=[""] + model_choices,
                value="",
            )
            history_prompt_version = gr.Dropdown(
                label="Filter: prompt_version",
                choices=[""] + (prompt_versions or [default_prompt_version]),
                value="",
            )

        with gr.Row():
            history_date_from = gr.Textbox(label="Filter: date_from (YYYY-MM-DD)")
            history_date_to = gr.Textbox(label="Filter: date_to (YYYY-MM-DD)")
            history_limit = gr.Number(label="Limit", value=20, precision=0)
            history_refresh_button = gr.Button("Refresh History")

        history_table = gr.Dataframe(
            headers=[
                "run_id",
                "created_at",
                "session_id",
                "provider",
                "model",
                "prompt_version",
                "status",
                "total_cost_usd",
            ],
            datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
            interactive=False,
            wrap=True,
            label="Runs",
        )

        with gr.Row():
            history_run_id = gr.Textbox(label="Run ID to load")
            history_confirm_run_id = gr.Textbox(
                label="Confirm Run ID for Delete",
                value="",
            )
            delete_with_backup = gr.Checkbox(
                label="Create backup ZIP before delete",
                value=False,
            )
            load_history_button = gr.Button("Load Selected Run")
            export_history_button = gr.Button("Export run bundle (zip)")
            delete_history_button = gr.Button("Delete run", variant="stop")

        with gr.Row():
            export_status_box = gr.Textbox(label="Export Status", interactive=False)
            export_path_box = gr.Textbox(label="Export ZIP Path", interactive=False)
        export_file_box = gr.File(label="Download ZIP", interactive=False)
        with gr.Row():
            restore_zip_file = gr.File(label="Restore ZIP File", type="filepath")
            restore_overwrite_existing = gr.Checkbox(
                label="Overwrite existing run",
                value=False,
            )
            restore_verify_only = gr.Checkbox(
                label="Verify only (no restore)",
                value=False,
            )
            restore_require_signature = gr.Checkbox(
                label="Require signature (strict)",
                value=restore_require_signature_default,
            )
            restore_button = gr.Button("Restore run bundle")
        with gr.Row():
            restore_status_box = gr.Textbox(label="Restore Status", interactive=False)
            restore_details_box = gr.Textbox(
                label="Restore Technical Details",
                interactive=False,
            )
        with gr.Row():
            restore_run_id_box = gr.Textbox(label="Restored Run ID", interactive=False)
            restore_artifacts_path_box = gr.Textbox(
                label="Restored Artifacts Path",
                interactive=False,
            )
        with gr.Row():
            delete_status_box = gr.Textbox(label="Delete Status", interactive=False)
            delete_backup_path_box = gr.Textbox(
                label="Delete Backup ZIP Path",
                interactive=False,
            )
            delete_details_box = gr.Textbox(
                label="Delete Technical Details",
                interactive=False,
            )

        gr.Markdown("### Compare Runs")
        with gr.Row():
            compare_run_id_a = gr.Dropdown(
                label="Run ID A",
                choices=[],
                value=None,
            )
            compare_run_id_b = gr.Dropdown(
                label="Run ID B",
                choices=[],
                value=None,
            )
            compare_button = gr.Button("Compare Selected Runs")

        compare_status_box = gr.Textbox(label="Compare Status", interactive=False)
        compare_summary_box = gr.Textbox(
            label="What Changed (improved/regressed/unchanged)",
            lines=6,
            interactive=False,
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
        )
        compare_gaps_box = gr.Textbox(
            label="Critical Gaps / Next Questions Comparison",
            lines=10,
            interactive=False,
        )
        compare_metrics_box = gr.Textbox(
            label="Metrics Comparison (tokens/cost/timings)",
            lines=10,
            interactive=False,
        )
        compare_json_box = gr.Textbox(
            label="Comparison Diff JSON",
            lines=14,
            interactive=False,
        )

        analyze_button.click(
            fn=lambda current_session_id,
            uploaded,
            selected_provider,
            selected_model,
            selected_prompt_name,
            selected_prompt_version,
            selected_ocr_model,
            selected_table_format,
            selected_include_images,
            selected_reasoning,
            selected_thinking: run_full_pipeline(
                orchestrator=full_orchestrator,
                prompt_name=selected_prompt_name,
                current_session_id=current_session_id,
                uploaded_files=uploaded,
                provider=selected_provider,
                model=selected_model,
                prompt_version=selected_prompt_version,
                ocr_model=selected_ocr_model,
                table_format=selected_table_format,
                include_image_base64=selected_include_images,
                openai_reasoning_effort=selected_reasoning,
                gemini_thinking_level=selected_thinking,
                preflight_checker=runtime_preflight,
            ),
            inputs=[
                session_state,
                documents,
                provider,
                model,
                prompt_name,
                prompt_version,
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
                parsed_json_state,
            ],
        )

        details_item_selector.change(
            fn=render_details_from_state,
            inputs=[parsed_json_state, details_item_selector],
            outputs=[details_box],
        )

        history_refresh_button.click(
            fn=lambda session_filter,
            provider_filter,
            model_filter,
            prompt_filter,
            date_from_filter,
            date_to_filter,
            result_limit: refresh_history_for_ui(
                repo=storage_repo,
                session_id=session_filter,
                provider=provider_filter,
                model=model_filter,
                prompt_version=prompt_filter,
                date_from=date_from_filter,
                date_to=date_to_filter,
                limit=result_limit,
            ),
            inputs=[
                history_session_id,
                history_provider,
                history_model,
                history_prompt_version,
                history_date_from,
                history_date_to,
                history_limit,
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
            fn=lambda selected_zip_file,
            overwrite_existing_flag,
            verify_only_flag,
            require_signature_flag,
            session_filter,
            provider_filter,
            model_filter,
            prompt_filter,
            date_from_filter,
            date_to_filter,
            result_limit: restore_history_run_bundle(
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
            fn=lambda selected_run_id,
            confirmed_run_id,
            create_backup_before_delete,
            session_filter,
            provider_filter,
            model_filter,
            prompt_filter,
            date_from_filter,
            date_to_filter,
            result_limit: delete_history_run(
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
            fn=lambda selected_prompt_name,
            selected_prompt_version: on_prompt_version_change(
                prompt_manager=prompt_manager,
                prompt_name=selected_prompt_name,
                prompt_version=selected_prompt_version,
            ),
            inputs=[prompt_name, prompt_version],
            outputs=[system_prompt_editor, schema_viewer, prompt_status_box],
        )

        save_prompt_button.click(
            fn=lambda selected_prompt_name,
            selected_prompt_version,
            edited_prompt,
            current_schema,
            author,
            note: save_prompt_as_new_version_for_ui(
                prompt_manager=prompt_manager,
                prompt_name=selected_prompt_name,
                source_version=selected_prompt_version,
                system_prompt_text=edited_prompt,
                schema_text=current_schema,
                author=author,
                note=note,
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

    valid = bool(payload.get("valid"))
    if valid:
        return "Validation: valid"

    schema_errors = _to_string_list(payload.get("schema_errors"))
    invariant_errors = _to_string_list(payload.get("invariant_errors"))
    combined_errors = schema_errors + invariant_errors
    lines = ["Validation: invalid"]
    if not combined_errors:
        lines.append("- (no details)")
    else:
        lines.extend(f"- {error_text}" for error_text in combined_errors)
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


def _build_model_choices(settings: Any) -> list[str]:
    llm_providers = settings.providers_config.get("llm_providers", {})
    models: list[str] = []
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


def main() -> None:
    settings = get_settings()
    app = build_app()
    app.launch(
        server_name=settings.gradio_server_name,
        server_port=settings.gradio_server_port,
    )


if __name__ == "__main__":
    main()
