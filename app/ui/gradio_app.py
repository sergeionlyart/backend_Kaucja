from __future__ import annotations

import json
import importlib.util
from pathlib import Path
from typing import Any, Callable, Sequence

import gradio as gr

from app.config.settings import Settings, get_settings
from app.llm_client.gemini_client import GeminiLLMClient
from app.llm_client.openai_client import OpenAILLMClient
from app.ocr_client.mistral_ocr import MistralOCRClient
from app.ocr_client.types import OCROptions
from app.pipeline.orchestrator import FullPipelineResult, OCRPipelineOrchestrator
from app.storage.repo import StorageRepo

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
) -> tuple[str, str, str, str, list[list[str]], str, str, str, str]:
    paths = _normalize_uploaded_files(uploaded_files)
    if not paths:
        session_id = current_session_id.strip()
        return (
            "No files uploaded. Please select at least one document.",
            session_id,
            "",
            session_id,
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
        rows,
        summary_text,
        raw_json,
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
        gr.Markdown("# Kaucja Case Sandbox - Iteration 4 (Full E2E)")
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
                ocr_results,
                summary_box,
                raw_json_box,
                validation_box,
                metrics_box,
            ],
        )

    return app


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
    lines: list[str] = ["critical_gaps_summary:"]
    if result.critical_gaps_summary:
        lines.extend(f"- {item}" for item in result.critical_gaps_summary)
    else:
        lines.append("- (empty)")

    lines.append("")
    lines.append("next_questions_to_user:")
    if result.next_questions_to_user:
        lines.extend(f"- {item}" for item in result.next_questions_to_user)
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


def main() -> None:
    settings = get_settings()
    app = build_app()
    app.launch(
        server_name=settings.gradio_server_name,
        server_port=settings.gradio_server_port,
    )


if __name__ == "__main__":
    main()
