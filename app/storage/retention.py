from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.storage.artifacts import ArtifactsManager
from app.storage.models import RetentionCleanupResult
from app.storage.repo import StorageRepo
from app.storage.zip_export import ZipExportError, export_run_bundle


def purge_runs_older_than_days(
    *,
    repo: StorageRepo,
    days: int,
    now: datetime | None = None,
    dry_run: bool = False,
    export_before_delete: bool = False,
    export_dir: Path | str | None = None,
    report_path: Path | str | None = None,
    report_dir: Path | str | None = None,
) -> RetentionCleanupResult:
    if days < 0:
        raise ValueError("days must be >= 0")

    reference_time = now or datetime.now(tz=timezone.utc)
    cutoff = reference_time - timedelta(days=days)
    cutoff_iso = cutoff.isoformat()

    runs = repo.list_runs(date_to=cutoff_iso, limit=1_000_000)
    candidates = sorted(runs, key=lambda run: (run.created_at, run.run_id))

    deleted_run_ids: list[str] = []
    audit_entries: list[dict[str, str | None]] = []
    errors: list[str] = []

    deleted_runs = 0
    failed_runs = 0
    skipped_runs = 0

    normalized_export_dir = (
        None if export_dir is None else str(Path(export_dir).resolve())
    )
    resolved_report_path = _resolve_report_path(
        repo=repo,
        reference_time=reference_time,
        report_path=report_path,
        report_dir=report_dir,
    )

    for run in candidates:
        if dry_run:
            audit_entries.append(
                {
                    "run_id": run.run_id,
                    "created_at": run.created_at,
                    "action": "dry_run_candidate",
                    "status": "candidate",
                    "error": None,
                    "backup_zip_path": None,
                }
            )
            continue

        backup_zip_path: str | None = None
        if export_before_delete:
            try:
                zip_path = export_run_bundle(
                    artifacts_root_path=run.artifacts_root_path,
                    output_dir=export_dir,
                )
                backup_zip_path = str(zip_path)
            except (
                FileNotFoundError,
                NotADirectoryError,
                ZipExportError,
                OSError,
            ) as error:
                details = f"{error.__class__.__name__}: {error}"
                failed_runs += 1
                skipped_runs += 1
                errors.append(
                    f"run_id={run.run_id} code=BACKUP_EXPORT_FAILED details={details}"
                )
                audit_entries.append(
                    {
                        "run_id": run.run_id,
                        "created_at": run.created_at,
                        "action": "skip_delete_backup_failed",
                        "status": "failed",
                        "error": details,
                        "backup_zip_path": None,
                    }
                )
                continue

        result = repo.delete_run(run.run_id)
        if result.deleted:
            deleted_runs += 1
            deleted_run_ids.append(run.run_id)
            audit_entries.append(
                {
                    "run_id": run.run_id,
                    "created_at": run.created_at,
                    "action": (
                        "backup_then_delete"
                        if export_before_delete
                        else "delete_without_backup"
                    ),
                    "status": "deleted",
                    "error": None,
                    "backup_zip_path": backup_zip_path,
                }
            )
            continue

        failed_runs += 1
        error_code = result.error_code or "UNKNOWN"
        details = result.technical_details or result.error_message or "Unknown error"
        errors.append(f"run_id={run.run_id} code={error_code} details={details}")
        audit_entries.append(
            {
                "run_id": run.run_id,
                "created_at": run.created_at,
                "action": (
                    "backup_then_delete"
                    if export_before_delete
                    else "delete_without_backup"
                ),
                "status": "failed",
                "error": details,
                "backup_zip_path": backup_zip_path,
            }
        )

    result = RetentionCleanupResult(
        cutoff_created_at=cutoff_iso,
        dry_run=dry_run,
        export_before_delete=export_before_delete,
        export_dir=normalized_export_dir,
        report_path=str(resolved_report_path),
        scanned_runs=len(candidates),
        deleted_runs=deleted_runs,
        failed_runs=failed_runs,
        skipped_runs=skipped_runs,
        deleted_run_ids=deleted_run_ids,
        audit_entries=audit_entries,
        errors=errors,
    )

    _write_retention_report(report_path=resolved_report_path, result=result)
    return result


def _build_repo(*, db_path: Path, data_dir: Path | None) -> StorageRepo:
    if data_dir is None:
        return StorageRepo(db_path=db_path)
    return StorageRepo(db_path=db_path, artifacts_manager=ArtifactsManager(data_dir))


def _resolve_report_path(
    *,
    repo: StorageRepo,
    reference_time: datetime,
    report_path: Path | str | None,
    report_dir: Path | str | None,
) -> Path:
    if report_path is not None:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    if report_dir is not None:
        directory = Path(report_dir)
    else:
        directory = repo.artifacts_manager.data_dir / "retention_reports"
    directory.mkdir(parents=True, exist_ok=True)

    timestamp = reference_time.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return directory / f"{timestamp}.json"


def _write_retention_report(
    *,
    report_path: Path,
    result: RetentionCleanupResult,
) -> None:
    payload = asdict(result)
    report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete runs older than N days (best effort)."
    )
    parser.add_argument(
        "--db-path",
        default="data/kaucja.sqlite3",
        help="Path to SQLite database file.",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Optional artifacts data directory override.",
    )
    parser.add_argument(
        "--days",
        type=int,
        required=True,
        help="Delete runs with created_at <= now - days.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List candidates without deleting any run.",
    )
    parser.add_argument(
        "--export-before-delete",
        action="store_true",
        help="Create backup ZIP before each delete operation.",
    )
    parser.add_argument(
        "--export-dir",
        default=None,
        help="Directory for backup ZIP files when export-before-delete is enabled.",
    )
    parser.add_argument(
        "--report-dir",
        default=None,
        help="Directory for retention report JSON file.",
    )
    parser.add_argument(
        "--report-path",
        default=None,
        help="Exact path for retention report JSON file.",
    )

    args = parser.parse_args()
    repo = _build_repo(
        db_path=Path(args.db_path),
        data_dir=(Path(args.data_dir) if args.data_dir else None),
    )
    result = purge_runs_older_than_days(
        repo=repo,
        days=args.days,
        dry_run=bool(args.dry_run),
        export_before_delete=bool(args.export_before_delete),
        export_dir=(Path(args.export_dir) if args.export_dir else None),
        report_dir=(Path(args.report_dir) if args.report_dir else None),
        report_path=(Path(args.report_path) if args.report_path else None),
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
