from __future__ import annotations

from typing import Any

import gradio as gr

from app.config.settings import get_settings
from app.storage.repo import StorageRepo


def create_empty_run(
    *,
    repo: StorageRepo,
    current_session_id: str,
    provider: str,
    model: str,
    prompt_version: str,
) -> tuple[str, str, str, str]:
    session_id = current_session_id.strip()
    if not session_id:
        session = repo.create_session()
        session_id = session.session_id
    else:
        repo.create_session(session_id=session_id)

    run = repo.create_run(
        session_id=session_id,
        provider=provider,
        model=model,
        prompt_name="kaucja_gap_analysis",
        prompt_version=prompt_version,
        schema_version=prompt_version,
        status="running",
    )

    message = (
        f"Run initialized. session_id={session_id} run_id={run.run_id} "
        f"status={run.status}"
    )

    return message, session_id, run.run_id, session_id


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


def build_app(repo: StorageRepo | None = None) -> gr.Blocks:
    settings = get_settings()
    storage_repo = repo or StorageRepo(settings.resolved_sqlite_path)

    provider_choices = _build_provider_choices(settings)
    model_choices = _build_model_choices(settings)

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

    with gr.Blocks(title="Kaucja Case Sandbox") as app:
        gr.Markdown("# Kaucja Case Sandbox - Iteration 0")
        gr.Markdown("Analyze creates an empty run record in SQLite.")

        session_state = gr.State(value="")

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

        analyze_button = gr.Button("Analyze", variant="primary")

        status_box = gr.Textbox(label="Status", interactive=False)
        run_id_box = gr.Textbox(label="Run ID", interactive=False)
        session_id_box = gr.Textbox(label="Session ID", interactive=False)

        analyze_button.click(
            fn=lambda current_session_id,
            selected_provider,
            selected_model,
            selected_prompt_version: create_empty_run(
                repo=storage_repo,
                current_session_id=current_session_id,
                provider=selected_provider,
                model=selected_model,
                prompt_version=selected_prompt_version,
            ),
            inputs=[session_state, provider, model, prompt_version],
            outputs=[status_box, session_state, run_id_box, session_id_box],
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
