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
from app.storage.artifact_reader import (
    safe_load_combined_markdown,
    safe_load_llm_parsed_json,
    safe_load_llm_raw_text,
    safe_load_llm_validation_json,
    safe_load_run_manifest,
    safe_read_json,
)
from app.storage.repo import StorageRepo

PreflightChecker = Callable[[str], str | None]

_ANALYZE_OUTPUT_EMPTY = (
    "",
    "",
    "",
    "",
    "",
    [],
    "",
    "",
    "",
    "",
)


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
) -> tuple[str, str, str, str, str, list[list[str]], str, str, str, str]:
    paths = _normalize_uploaded_files(uploaded_files)
    if not paths:
        session_id = current_session_id.strip()
        return (
            "No files uploaded. Please select at least one document.",
            session_id,
            "",
            session_id,
            "",
            [],
            "",
            "",
            "",
            "",
        )

    preflight_error = preflight_checker(provider)
    if preflight_error is not None:
        session_id = current_session_id.strip()
        return (
            preflight_error,
            session_id,
            "",
            session_id,
            "",
            [],
            "",
            "",
            "",
            "",
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

    rows = _ocr_rows(result)
    summary_text = _human_summary(result)
    raw_json = _raw_json_text(result)
    validation_text = _validation_text(result)
    metrics_text = json.dumps(result.metrics, ensure_ascii=False, indent=2)
    artifacts_root = _resolve_artifacts_root(
        orchestrator=orchestrator, run_id=result.run_id
    )

    status_message = (
        f"Run finished. session_id={result.session_id} run_id={result.run_id} "
        f"status={result.run_status}"
    )
    if result.error_code:
        status_message += f" error_code={result.error_code}"

    return (
        status_message,
        result.session_id,
        result.run_id,
        result.session_id,
        artifacts_root,
        rows,
        summary_text,
        raw_json,
        validation_text,
        metrics_text,
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


def load_history_run(
    *,
    repo: StorageRepo,
    run_id: str,
) -> tuple[str, str, str, str, str, list[list[str]], str, str, str, str]:
    target_run_id = run_id.strip()
    if not target_run_id:
        return (
            "History load failed: run_id is empty.",
            *_ANALYZE_OUTPUT_EMPTY[1:],
        )

    bundle = repo.get_run_bundle(target_run_id)
    if bundle is None:
        return (
            f"History load failed: run_id={target_run_id} not found.",
            *_ANALYZE_OUTPUT_EMPTY[1:],
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
    ocr_rows = _history_ocr_rows(bundle=bundle)

    summary_text = _summary_from_payload(parsed_json)
    metrics_text = _metrics_text_for_history(run=run, manifest=manifest)
    status_message = (
        f"History loaded. session_id={run.session_id} run_id={run.run_id} "
        f"status={run.status}"
    )
    if run.error_code:
        status_message += f" error_code={run.error_code}"
    if manifest_error:
        status_message += f" warning={manifest_error}"

    return (
        status_message,
        run.session_id,
        run.run_id,
        run.session_id,
        artifacts_root,
        ocr_rows,
        summary_text,
        raw_json_text,
        validation_text,
        metrics_text,
    )


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


def build_app(
    repo: StorageRepo | None = None,
    orchestrator: OCRPipelineOrchestrator | None = None,
    preflight_checker: PreflightChecker | None = None,
) -> gr.Blocks:
    settings = get_settings()
    storage_repo = repo or StorageRepo(settings.resolved_sqlite_path)

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
        gr.Markdown("# Kaucja Case Sandbox - Iteration 5 (Run Manifest + History)")
        gr.Markdown("Analyze runs OCR -> pack -> LLM -> validate -> persist.")

        session_state = gr.State(value="")

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
            prompt_version = gr.Dropdown(
                label="Prompt Version",
                choices=["v001"],
                value=settings.default_prompt_version,
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

        with gr.Row():
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

        analyze_button = gr.Button("Analyze", variant="primary")

        status_box = gr.Textbox(label="Status", interactive=False)
        run_id_box = gr.Textbox(label="Run ID", interactive=False)
        session_id_box = gr.Textbox(label="Session ID", interactive=False)
        artifacts_root_box = gr.Textbox(label="Artifacts Root Path", interactive=False)

        ocr_results = gr.Dataframe(
            headers=["doc_id", "ocr_status", "pages_count", "combined_md_path"],
            datatype=["str", "str", "str", "str"],
            interactive=False,
            wrap=True,
            label="OCR Results",
        )

        summary_box = gr.Textbox(
            label="Summary (critical gaps + next questions)",
            lines=8,
            interactive=False,
        )
        raw_json_box = gr.Textbox(label="Raw JSON", lines=12, interactive=False)
        validation_box = gr.Textbox(label="Validation", lines=6, interactive=False)
        metrics_box = gr.Textbox(label="Metrics", lines=8, interactive=False)

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
                choices=["", "v001"],
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
            load_history_button = gr.Button("Load Selected Run")

        analyze_button.click(
            fn=lambda current_session_id,
            uploaded,
            selected_provider,
            selected_model,
            selected_prompt_version,
            selected_ocr_model,
            selected_table_format,
            selected_include_images,
            selected_reasoning,
            selected_thinking: run_full_pipeline(
                orchestrator=full_orchestrator,
                prompt_name=settings.default_prompt_name,
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
                ocr_results,
                summary_box,
                raw_json_box,
                validation_box,
                metrics_box,
            ],
        )

        history_refresh_button.click(
            fn=lambda session_filter,
            provider_filter,
            model_filter,
            prompt_filter,
            date_from_filter,
            date_to_filter,
            result_limit: list_history_rows(
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
            outputs=[history_table],
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
                ocr_results,
                summary_box,
                raw_json_box,
                validation_box,
                metrics_box,
            ],
        )

    return app


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


def _history_ocr_rows(*, bundle: Any) -> list[list[str]]:
    rows: list[list[str]] = []
    for document in bundle.documents:
        combined_path = (
            Path(document.ocr_artifacts_path) / "combined.md"
            if document.ocr_artifacts_path
            else None
        )
        combined_display = ""
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
    if fallback_error is not None:
        return None
    return fallback_payload


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


def main() -> None:
    settings = get_settings()
    app = build_app()
    app.launch(
        server_name=settings.gradio_server_name,
        server_port=settings.gradio_server_port,
    )


if __name__ == "__main__":
    main()
