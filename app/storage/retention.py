from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.storage.artifacts import ArtifactsManager
from app.storage.models import RetentionCleanupResult
from app.storage.repo import StorageRepo


def purge_runs_older_than_days(
    *,
    repo: StorageRepo,
    days: int,
    now: datetime | None = None,
) -> RetentionCleanupResult:
    if days < 0:
        raise ValueError("days must be >= 0")

    reference_time = now or datetime.now(tz=timezone.utc)
    cutoff = reference_time - timedelta(days=days)
    cutoff_iso = cutoff.isoformat()

    candidates = repo.list_runs(date_to=cutoff_iso, limit=1_000_000)
    deleted_run_ids: list[str] = []
    errors: list[str] = []

    for run in candidates:
        result = repo.delete_run(run.run_id)
        if result.deleted:
            deleted_run_ids.append(run.run_id)
            continue

        details = result.technical_details or result.error_message or "Unknown error"
        code = result.error_code or "UNKNOWN"
        errors.append(f"run_id={run.run_id} code={code} details={details}")

    return RetentionCleanupResult(
        cutoff_created_at=cutoff_iso,
        scanned_runs=len(candidates),
        deleted_runs=len(deleted_run_ids),
        failed_runs=len(errors),
        deleted_run_ids=deleted_run_ids,
        errors=errors,
    )


def _build_repo(*, db_path: Path, data_dir: Path | None) -> StorageRepo:
    if data_dir is None:
        return StorageRepo(db_path=db_path)
    return StorageRepo(db_path=db_path, artifacts_manager=ArtifactsManager(data_dir))


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

    args = parser.parse_args()
    repo = _build_repo(
        db_path=Path(args.db_path),
        data_dir=(Path(args.data_dir) if args.data_dir else None),
    )
    result = purge_runs_older_than_days(repo=repo, days=args.days)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
