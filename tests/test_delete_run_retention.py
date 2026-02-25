from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

import app.storage.retention as retention_module
from app.storage.db import connection
from app.storage.models import DeleteRunResult
from app.storage.repo import StorageRepo
from app.storage.retention import purge_runs_older_than_days
from app.storage.zip_export import ZipExportError


def _create_run(
    repo: StorageRepo,
    *,
    session_id: str,
    artifacts_root: str | None = None,
):
    run = repo.create_run(
        session_id=session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        schema_version="v001",
        status="completed",
        artifacts_root_path=artifacts_root,
    )
    root = Path(run.artifacts_root_path)
    (root / "run.json").write_text('{"run_id":"x"}', encoding="utf-8")
    (root / "logs" / "run.log").write_text("line\n", encoding="utf-8")
    doc_ocr_dir = root / "documents" / "0000001" / "ocr"
    doc_ocr_dir.mkdir(parents=True, exist_ok=True)
    (doc_ocr_dir / "combined.md").write_text("content", encoding="utf-8")

    repo.create_document(
        run_id=run.run_id,
        doc_id="0000001",
        original_filename="doc.pdf",
        original_mime="application/pdf",
        original_path=str(root / "documents" / "0000001" / "original" / "doc.pdf"),
        ocr_status="ok",
        pages_count=1,
        ocr_artifacts_path=str(doc_ocr_dir),
    )
    llm_path = root / "llm"
    llm_path.mkdir(parents=True, exist_ok=True)
    parsed_path = llm_path / "response_parsed.json"
    parsed_path.write_text("{}", encoding="utf-8")
    repo.upsert_llm_output(
        run_id=run.run_id,
        response_json_path=str(parsed_path),
        response_valid=True,
        schema_validation_errors_path=None,
    )
    return run


def _set_run_created_at(*, repo: StorageRepo, run_id: str, created_at: str) -> None:
    with connection(repo.db_path) as conn:
        conn.execute(
            "UPDATE runs SET created_at = ? WHERE run_id = ?",
            (created_at, run_id),
        )


def test_delete_run_success_removes_db_and_artifacts(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-delete")
    run = _create_run(repo, session_id=session.session_id)
    artifacts_root = Path(run.artifacts_root_path)

    result = repo.delete_run(run.run_id)

    assert result.deleted is True
    assert result.error_code is None
    assert result.artifacts_deleted is True
    assert repo.get_run(run.run_id) is None
    assert repo.get_llm_output(run_id=run.run_id) is None
    assert repo.list_documents(run_id=run.run_id) == []
    assert not artifacts_root.exists()


def test_delete_run_returns_not_found_for_missing_run(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")

    result = repo.delete_run("missing-run")

    assert result.deleted is False
    assert result.error_code == "RUN_NOT_FOUND"


def test_delete_run_blocks_artifacts_path_outside_data_root(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-unsafe")
    outside_root = tmp_path / "outside" / "run"
    run = _create_run(
        repo,
        session_id=session.session_id,
        artifacts_root=str(outside_root),
    )

    result = repo.delete_run(run.run_id)

    assert result.deleted is False
    assert result.error_code == "DELETE_PATH_INVALID"
    assert repo.get_run(run.run_id) is not None
    assert outside_root.exists()


def test_delete_run_returns_fs_error_when_artifacts_delete_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-fs-error")
    run = _create_run(repo, session_id=session.session_id)

    def _raise_fs_error(*, artifacts_root: Path) -> tuple[bool, bool]:
        raise OSError("permission denied")

    monkeypatch.setattr(repo, "_delete_artifacts_tree", _raise_fs_error)

    result = repo.delete_run(run.run_id)

    assert result.deleted is False
    assert result.error_code == "DELETE_FS_ERROR"
    assert repo.get_run(run.run_id) is not None


def test_delete_run_returns_db_error_when_metadata_delete_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-db-error")
    run = _create_run(repo, session_id=session.session_id)

    def _raise_db_error(*, run_id: str) -> bool:
        raise sqlite3.Error("db locked")

    monkeypatch.setattr(repo, "_delete_run_metadata", _raise_db_error)

    result = repo.delete_run(run.run_id)

    assert result.deleted is False
    assert result.error_code == "DELETE_DB_ERROR"
    assert result.artifacts_deleted is True
    assert repo.get_run(run.run_id) is not None


def test_delete_run_rejects_symlink_inside_artifacts(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-symlink")
    run = _create_run(repo, session_id=session.session_id)
    artifacts_root = Path(run.artifacts_root_path)
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("outside", encoding="utf-8")
    symlink_path = artifacts_root / "documents" / "0000001" / "ocr" / "outside-link"

    try:
        symlink_path.symlink_to(outside_file)
    except OSError:
        pytest.skip("Symlink creation is not available in this environment")

    result = repo.delete_run(run.run_id)

    assert result.deleted is False
    assert result.error_code == "DELETE_FS_ERROR"
    assert repo.get_run(run.run_id) is not None


def test_retention_dry_run_does_not_delete_candidates(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-retention-dry")
    old_run = _create_run(repo, session_id=session.session_id)
    fresh_run = _create_run(repo, session_id=session.session_id)

    _set_run_created_at(
        repo=repo,
        run_id=old_run.run_id,
        created_at="2025-01-01T00:00:00+00:00",
    )
    _set_run_created_at(
        repo=repo,
        run_id=fresh_run.run_id,
        created_at="2026-02-01T00:00:00+00:00",
    )

    report = purge_runs_older_than_days(
        repo=repo,
        days=30,
        now=datetime(2026, 2, 25, tzinfo=timezone.utc),
        dry_run=True,
        report_dir=tmp_path / "retention-reports",
    )

    assert report.dry_run is True
    assert report.scanned_runs == 1
    assert report.deleted_runs == 0
    assert report.failed_runs == 0
    assert report.skipped_runs == 0
    assert report.audit_entries[0]["action"] == "dry_run_candidate"
    assert report.audit_entries[0]["status"] == "candidate"
    assert repo.get_run(old_run.run_id) is not None
    assert repo.get_run(fresh_run.run_id) is not None
    assert Path(report.report_path).is_file()


def test_retention_export_before_delete_success(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-retention-export")
    old_run = _create_run(repo, session_id=session.session_id)
    _set_run_created_at(
        repo=repo,
        run_id=old_run.run_id,
        created_at="2025-01-01T00:00:00+00:00",
    )

    report = purge_runs_older_than_days(
        repo=repo,
        days=30,
        now=datetime(2026, 2, 25, tzinfo=timezone.utc),
        export_before_delete=True,
        export_dir=tmp_path / "backups",
        report_dir=tmp_path / "retention-reports",
    )

    assert report.export_before_delete is True
    assert report.deleted_runs == 1
    assert report.failed_runs == 0
    assert report.skipped_runs == 0
    assert report.audit_entries[0]["action"] == "backup_then_delete"
    assert report.audit_entries[0]["status"] == "deleted"
    backup_path = report.audit_entries[0]["backup_zip_path"]
    assert isinstance(backup_path, str)
    assert Path(backup_path).is_file()
    assert repo.get_run(old_run.run_id) is None


def test_retention_export_failure_skips_delete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-retention-export-fail")
    old_run = _create_run(repo, session_id=session.session_id)
    _set_run_created_at(
        repo=repo,
        run_id=old_run.run_id,
        created_at="2025-01-01T00:00:00+00:00",
    )

    def _raise_export_error(*, artifacts_root_path: str, output_dir: str | None = None):
        raise ZipExportError("export failed")

    monkeypatch.setattr(retention_module, "export_run_bundle", _raise_export_error)

    report = purge_runs_older_than_days(
        repo=repo,
        days=30,
        now=datetime(2026, 2, 25, tzinfo=timezone.utc),
        export_before_delete=True,
        export_dir=tmp_path / "backups",
        report_dir=tmp_path / "retention-reports",
    )

    assert report.deleted_runs == 0
    assert report.failed_runs == 1
    assert report.skipped_runs == 1
    assert report.audit_entries[0]["action"] == "skip_delete_backup_failed"
    assert report.audit_entries[0]["status"] == "failed"
    assert "BACKUP_EXPORT_FAILED" in report.errors[0]
    assert repo.get_run(old_run.run_id) is not None


def test_retention_report_written_to_custom_path(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-report-file")
    old_run = _create_run(repo, session_id=session.session_id)
    _set_run_created_at(
        repo=repo,
        run_id=old_run.run_id,
        created_at="2025-01-01T00:00:00+00:00",
    )

    report_file = tmp_path / "reports" / "custom-retention.json"
    report = purge_runs_older_than_days(
        repo=repo,
        days=30,
        now=datetime(2026, 2, 25, tzinfo=timezone.utc),
        dry_run=True,
        report_path=report_file,
    )

    assert report.report_path == str(report_file)
    assert report_file.is_file()
    payload = json.loads(report_file.read_text(encoding="utf-8"))
    assert payload["report_path"] == str(report_file)
    assert payload["dry_run"] is True
    assert payload["audit_entries"][0]["run_id"] == old_run.run_id


def test_retention_best_effort_reports_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-retention-fail")
    run_a = _create_run(repo, session_id=session.session_id)
    run_b = _create_run(repo, session_id=session.session_id)

    for run_id in (run_a.run_id, run_b.run_id):
        _set_run_created_at(
            repo=repo,
            run_id=run_id,
            created_at="2024-01-01T00:00:00+00:00",
        )

    original_delete = repo.delete_run

    def _delete_with_failure(run_id: str) -> DeleteRunResult:
        if run_id == run_b.run_id:
            return DeleteRunResult(
                run_id=run_id,
                deleted=False,
                error_code="DELETE_DB_ERROR",
                error_message="db error",
                technical_details="db locked",
                artifacts_deleted=False,
                artifacts_missing=False,
            )
        return original_delete(run_id)

    monkeypatch.setattr(repo, "delete_run", _delete_with_failure)

    report = purge_runs_older_than_days(
        repo=repo,
        days=1,
        now=datetime(2026, 2, 25, tzinfo=timezone.utc),
        report_dir=tmp_path / "retention-reports",
    )

    assert report.scanned_runs == 2
    assert report.deleted_runs == 1
    assert report.failed_runs == 1
    assert report.skipped_runs == 0
    assert any(run_b.run_id in item for item in report.errors)
