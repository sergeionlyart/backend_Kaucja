from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

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


def test_storage_repo_document_crud(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session()
    run = repo.create_run(
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        schema_version="v001",
        status="running",
    )

    created = repo.create_document(
        run_id=run.run_id,
        doc_id="0000001",
        original_filename="contract.pdf",
        original_mime="application/pdf",
        original_path=str(tmp_path / "contract.pdf"),
        ocr_status="pending",
        ocr_artifacts_path=str(tmp_path / "ocr"),
    )

    assert created.ocr_status == "pending"

    repo.update_document_ocr(
        run_id=run.run_id,
        doc_id="0000001",
        ocr_status="ok",
        ocr_model="mistral-ocr-latest",
        pages_count=3,
        ocr_artifacts_path=str(tmp_path / "ocr"),
        ocr_error=None,
    )

    fetched = repo.get_document(run_id=run.run_id, doc_id="0000001")
    assert fetched is not None
    assert fetched.ocr_status == "ok"
    assert fetched.pages_count == 3


def test_storage_repo_rejects_duplicate_doc_id_in_same_run(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session()
    run = repo.create_run(
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        schema_version="v001",
        status="running",
    )

    repo.create_document(
        run_id=run.run_id,
        doc_id="0000001",
        original_filename="contract.pdf",
        original_mime="application/pdf",
        original_path=str(tmp_path / "contract.pdf"),
        ocr_status="pending",
        ocr_artifacts_path=str(tmp_path / "ocr"),
    )

    with pytest.raises(sqlite3.IntegrityError):
        repo.create_document(
            run_id=run.run_id,
            doc_id="0000001",
            original_filename="contract_copy.pdf",
            original_mime="application/pdf",
            original_path=str(tmp_path / "contract_copy.pdf"),
            ocr_status="pending",
            ocr_artifacts_path=str(tmp_path / "ocr"),
        )


def test_storage_repo_updates_run_metrics(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session()
    run = repo.create_run(
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        schema_version="v001",
        status="running",
    )

    repo.update_run_metrics(
        run_id=run.run_id,
        timings_json={"t_total_ms": 100.0},
        usage_json={"raw": 1},
        usage_normalized_json={"total_tokens": 10},
        cost_json={"llm_cost_usd": 0.1},
    )

    updated = repo.get_run(run.run_id)
    assert updated is not None
    assert updated.timings_json == {"t_total_ms": 100.0}
    assert updated.usage_json == {"raw": 1}
    assert updated.usage_normalized_json == {"total_tokens": 10}
    assert updated.cost_json == {"llm_cost_usd": 0.1}


def test_storage_repo_upsert_llm_output(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session()
    run = repo.create_run(
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        schema_version="v001",
        status="running",
    )

    repo.upsert_llm_output(
        run_id=run.run_id,
        response_json_path=str(tmp_path / "parsed.json"),
        response_valid=False,
        schema_validation_errors_path=str(tmp_path / "validation.json"),
    )
    repo.upsert_llm_output(
        run_id=run.run_id,
        response_json_path=str(tmp_path / "parsed_v2.json"),
        response_valid=True,
        schema_validation_errors_path=None,
    )

    llm_output = repo.get_llm_output(run_id=run.run_id)
    assert llm_output is not None
    assert llm_output.response_json_path.endswith("parsed_v2.json")
    assert llm_output.response_valid is True
    assert llm_output.schema_validation_errors_path is None
