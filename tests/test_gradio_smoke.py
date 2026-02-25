from __future__ import annotations

from pathlib import Path

import gradio as gr

from app.storage.repo import StorageRepo
from app.ui.gradio_app import build_app, create_empty_run


def test_build_app_returns_blocks(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")

    app = build_app(repo=repo)

    assert isinstance(app, gr.Blocks)


def test_create_empty_run_persists_running_status(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")

    _, session_id, run_id, _ = create_empty_run(
        repo=repo,
        current_session_id="",
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
    )

    run = repo.get_run(run_id)

    assert session_id
    assert run is not None
    assert run.status == "running"
    artifacts_root = Path(run.artifacts_root_path)
    assert artifacts_root.exists()
    assert (artifacts_root / "logs" / "run.log").is_file()
