from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import gradio as gr

from app.config.settings import get_settings
from app.ocr_client.mistral_ocr import MistralOCRClient
from app.ocr_client.types import OCROptions
from app.pipeline.orchestrator import OCRPipelineOrchestrator
from app.storage.repo import StorageRepo


def run_ocr_pipeline(
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
) -> tuple[str, str, str, str, list[list[str]]]:
    paths = _normalize_uploaded_files(uploaded_files)
    if not paths:
        session_id = current_session_id.strip()
        return (
            "No files uploaded. Please select at least one document.",
            session_id,
            "",
            session_id,
            [],
        )

    result = orchestrator.run_ocr_stage(
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
    )

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

    message = (
        f"OCR stage finished. session_id={result.session_id} "
        f"run_id={result.run_id} status={result.run_status}"
    )

    return message, result.session_id, result.run_id, result.session_id, rows


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


def build_app(
    repo: StorageRepo | None = None,
    orchestrator: OCRPipelineOrchestrator | None = None,
) -> gr.Blocks:
    settings = get_settings()
    storage_repo = repo or StorageRepo(settings.resolved_sqlite_path)
    artifacts_manager = storage_repo.artifacts_manager

    ocr_pipeline = orchestrator or OCRPipelineOrchestrator(
        repo=storage_repo,
        artifacts_manager=artifacts_manager,
        ocr_client=MistralOCRClient(api_key=settings.mistral_api_key),
    )

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
        gr.Markdown("# Kaucja Case Sandbox - Iteration 2 (OCR Stage)")
        gr.Markdown("Analyze runs OCR-only stage and persists artifacts + DB records.")

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

        analyze_button.click(
            fn=lambda current_session_id,
            uploaded,
            selected_provider,
            selected_model,
            selected_prompt_version,
            selected_ocr_model,
            selected_table_format,
            selected_include_images: run_ocr_pipeline(
                orchestrator=ocr_pipeline,
                prompt_name=settings.default_prompt_name,
                current_session_id=current_session_id,
                uploaded_files=uploaded,
                provider=selected_provider,
                model=selected_model,
                prompt_version=selected_prompt_version,
                ocr_model=selected_ocr_model,
                table_format=selected_table_format,
                include_image_base64=selected_include_images,
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
            ],
            outputs=[
                status_box,
                session_state,
                run_id_box,
                session_id_box,
                ocr_results,
            ],
        )

    return app


def main() -> None:
    settings = get_settings()
    app = build_app()
    app.launch(
        server_name=settings.gradio_server_name,
        server_port=settings.gradio_server_port,
    )


if __name__ == "__main__":
    main()
