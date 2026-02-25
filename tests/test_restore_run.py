from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import pytest

import app.storage.restore as restore_module
from app.storage.repo import StorageRepo
from app.storage.restore import restore_run_bundle
from app.storage.zip_export import export_run_bundle


def _seed_restorable_run(
    *,
    repo: StorageRepo,
    session_id: str,
) -> str:
    run = repo.create_run(
        session_id=session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        schema_version="v001",
        status="completed",
    )
    run_root = Path(run.artifacts_root_path)

    (run_root / "logs" / "run.log").write_text("log line\n", encoding="utf-8")

    doc_id = "0000001"
    original_dir = run_root / "documents" / doc_id / "original"
    ocr_dir = run_root / "documents" / doc_id / "ocr"
    original_dir.mkdir(parents=True, exist_ok=True)
    ocr_dir.mkdir(parents=True, exist_ok=True)

    original_file = original_dir / "contract.pdf"
    original_file.write_bytes(b"%PDF-1.4 fake")
    (ocr_dir / "combined.md").write_text("combined", encoding="utf-8")
    (ocr_dir / "raw_response.json").write_text("{}", encoding="utf-8")
    (ocr_dir / "quality.json").write_text(
        json.dumps({"warnings": [], "bad_pages": []}),
        encoding="utf-8",
    )

    llm_dir = run_root / "llm"
    llm_dir.mkdir(parents=True, exist_ok=True)
    parsed_path = llm_dir / "response_parsed.json"
    parsed_path.write_text(
        json.dumps(
            {
                "checklist": [],
                "critical_gaps_summary": [],
                "next_questions_to_user": [],
            }
        ),
        encoding="utf-8",
    )
    (llm_dir / "response_raw.txt").write_text("{}", encoding="utf-8")
    (llm_dir / "validation.json").write_text(
        json.dumps({"valid": True, "schema_errors": [], "invariant_errors": []}),
        encoding="utf-8",
    )

    repo.create_document(
        run_id=run.run_id,
        doc_id=doc_id,
        original_filename="contract.pdf",
        original_mime="application/pdf",
        original_path=str(original_file),
        ocr_status="ok",
        pages_count=1,
        ocr_artifacts_path=str(ocr_dir),
        ocr_error=None,
    )
    repo.upsert_llm_output(
        run_id=run.run_id,
        response_json_path=str(parsed_path),
        response_valid=True,
        schema_validation_errors_path=None,
    )
    repo.update_run_metrics(
        run_id=run.run_id,
        timings_json={"t_total_ms": 10.0},
        usage_json={"input_tokens": 11},
        usage_normalized_json={"total_tokens": 22},
        cost_json={"total_cost_usd": 0.012},
    )

    run_manifest = {
        "session_id": session_id,
        "run_id": run.run_id,
        "status": "completed",
        "inputs": {
            "provider": "openai",
            "model": "gpt-5.1",
            "prompt_name": "kaucja_gap_analysis",
            "prompt_version": "v001",
            "schema_version": "v001",
            "ocr_params": {"model": "mistral-ocr-latest"},
            "llm_params": {"openai_reasoning_effort": "auto"},
        },
        "artifacts": {
            "root": str(run_root),
            "run_log": str(run_root / "logs" / "run.log"),
            "documents": [
                {
                    "doc_id": doc_id,
                    "ocr_status": "ok",
                    "pages_count": 1,
                    "combined_markdown_path": str(ocr_dir / "combined.md"),
                    "ocr_artifacts_path": str(ocr_dir),
                    "ocr_error": None,
                }
            ],
            "llm": {
                "response_parsed_path": str(parsed_path),
                "response_raw_path": str(llm_dir / "response_raw.txt"),
                "validation_path": str(llm_dir / "validation.json"),
            },
        },
        "metrics": {
            "timings": {"t_total_ms": 10.0},
            "usage": {"input_tokens": 11},
            "usage_normalized": {"total_tokens": 22},
            "cost": {"total_cost_usd": 0.012},
        },
        "validation": {"valid": True, "errors": []},
        "error_code": None,
        "error_message": None,
        "created_at": "2026-02-25T00:00:00+00:00",
        "updated_at": "2026-02-25T00:00:00+00:00",
    }
    (run_root / "run.json").write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return run.run_id


def test_restore_run_success(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session_id = "session-restore"
    run_id = _seed_restorable_run(repo=repo, session_id=session_id)
    source_run = repo.get_run(run_id)
    assert source_run is not None

    zip_path = export_run_bundle(artifacts_root_path=source_run.artifacts_root_path)
    delete_result = repo.delete_run(run_id)
    assert delete_result.deleted is True

    result = restore_run_bundle(repo=repo, zip_path=zip_path)

    assert result.status == "restored"
    assert result.error_code is None
    assert result.run_id == run_id
    assert result.session_id == session_id
    restored_run = repo.get_run(run_id)
    assert restored_run is not None
    assert restored_run.provider == "openai"
    assert Path(restored_run.artifacts_root_path).is_dir()
    assert len(repo.list_documents(run_id=run_id)) == 1
    assert repo.get_llm_output(run_id=run_id) is not None


def test_restore_rejects_invalid_archive_traversal(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    zip_path = tmp_path / "bad.zip"
    with ZipFile(zip_path, "w") as archive:
        archive.writestr("run.json", json.dumps({"run_id": "x", "session_id": "s"}))
        archive.writestr("../escape.txt", "boom")
        archive.writestr("logs/run.log", "line")

    result = restore_run_bundle(repo=repo, zip_path=zip_path)

    assert result.status == "failed"
    assert result.error_code == "RESTORE_INVALID_ARCHIVE"


def test_restore_fails_when_run_exists_without_overwrite(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session_id = "session-exists"
    run_id = _seed_restorable_run(repo=repo, session_id=session_id)
    run = repo.get_run(run_id)
    assert run is not None
    zip_path = export_run_bundle(artifacts_root_path=run.artifacts_root_path)

    result = restore_run_bundle(repo=repo, zip_path=zip_path, overwrite_existing=False)

    assert result.status == "failed"
    assert result.error_code == "RESTORE_RUN_EXISTS"
    assert repo.get_run(run_id) is not None


def test_restore_overwrite_existing_flow(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session_id = "session-overwrite"
    run_id = _seed_restorable_run(repo=repo, session_id=session_id)
    run = repo.get_run(run_id)
    assert run is not None
    zip_path = export_run_bundle(artifacts_root_path=run.artifacts_root_path)

    # mutate existing metadata so restore has observable overwrite effect
    repo.update_run_status(
        run_id=run_id, status="failed", error_code="X", error_message="Y"
    )

    result = restore_run_bundle(repo=repo, zip_path=zip_path, overwrite_existing=True)

    assert result.status == "restored"
    restored_run = repo.get_run(run_id)
    assert restored_run is not None
    assert restored_run.status == "completed"
    assert restored_run.error_code is None


def test_restore_handles_fs_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session_id = "session-fs"
    run_id = _seed_restorable_run(repo=repo, session_id=session_id)
    run = repo.get_run(run_id)
    assert run is not None
    zip_path = export_run_bundle(artifacts_root_path=run.artifacts_root_path)
    repo.delete_run(run_id)

    def _raise_fs_error(*, extract_root: Path, target_root: Path) -> None:
        raise OSError("no write permission")

    monkeypatch.setattr(restore_module, "_move_extracted_tree", _raise_fs_error)

    result = restore_run_bundle(repo=repo, zip_path=zip_path)

    assert result.status == "failed"
    assert result.error_code == "RESTORE_FS_ERROR"


def test_restore_handles_db_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session_id = "session-db"
    run_id = _seed_restorable_run(repo=repo, session_id=session_id)
    run = repo.get_run(run_id)
    assert run is not None
    zip_path = export_run_bundle(artifacts_root_path=run.artifacts_root_path)
    repo.delete_run(run_id)

    def _metadata_failure(
        *,
        repo: StorageRepo,
        manifest: dict[str, object],
        target_root: Path,
        session_id: str,
        run_id: str,
    ) -> tuple[list[str], list[str]]:
        return ["warning"], ["db failed"]

    monkeypatch.setattr(restore_module, "_restore_metadata", _metadata_failure)

    result = restore_run_bundle(repo=repo, zip_path=zip_path)

    assert result.status == "failed"
    assert result.error_code == "RESTORE_DB_ERROR"
    assert "db failed" in result.errors[0]
