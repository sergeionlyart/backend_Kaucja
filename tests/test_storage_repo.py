from __future__ import annotations

import sqlite3
from pathlib import Path

from app.storage.repo import StorageRepo


def test_storage_repo_creates_required_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "kaucja.sqlite3"
    StorageRepo(db_path=db_path)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    table_names = {name for (name,) in rows}

    assert {"sessions", "runs", "documents", "llm_outputs"}.issubset(table_names)


def test_storage_repo_create_and_update_run(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session()

    run = repo.create_run(
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        schema_version="v001",
        status="created",
    )

    assert run.status == "created"
    artifacts_root = Path(run.artifacts_root_path)
    assert artifacts_root.exists()
    assert (artifacts_root / "logs" / "run.log").is_file()

    repo.update_run_status(run_id=run.run_id, status="running")
    updated_run = repo.get_run(run.run_id)

    assert updated_run is not None
    assert updated_run.status == "running"
