from __future__ import annotations

import argparse
from pathlib import Path

from legal_ingest.audit import build_audit_report, write_audit_artifacts
from legal_ingest.backup import run_backup
from legal_ingest.config import ArtifactConfig, MongoConfig
from legal_ingest.metadata_migration import run_metadata_migration
from legal_ingest.migration_plan import write_migration_map
from legal_ingest.mongo import MongoRuntime
from legal_ingest.required_fetch import run_required_fetch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="legal_ingest",
        description="TechSpec 3.1 legal ingest CLI for backup, audit, fetch, and metadata migration.",
    )
    parser.set_defaults(handler=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = _build_shared_parser("backup", subparsers)
    backup_parser.set_defaults(handler=handle_backup)

    audit_parser = _build_shared_parser("audit", subparsers)
    audit_parser.add_argument(
        "--migration-map",
        type=Path,
        default=None,
        help="Optional path to a versioned migration map JSON.",
    )
    audit_parser.set_defaults(handler=handle_audit)

    required_fetch_parser = _build_shared_parser("required-fetch", subparsers)
    _add_apply_flags(required_fetch_parser)
    required_fetch_parser.set_defaults(handler=handle_required_fetch)

    metadata_parser = _build_shared_parser("metadata-migrate", subparsers)
    _add_apply_flags(metadata_parser)
    metadata_parser.add_argument(
        "--migration-map",
        type=Path,
        default=None,
        help="Optional path to a versioned migration map JSON.",
    )
    metadata_parser.add_argument(
        "--scope",
        choices=("required", "full"),
        default="required",
        help="Metadata migration scope. 'required' keeps the Iteration 2 slice; 'full' normalizes the whole corpus.",
    )
    metadata_parser.set_defaults(handler=handle_metadata_migrate)

    migration_parser = subparsers.add_parser(
        "migration-plan",
        help="Write versioned migration map for TechSpec 3.1.",
    )
    migration_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path. Defaults to legal_ingest/data/migration_map_v3_1.json.",
    )
    migration_parser.set_defaults(handler=handle_migration_plan)
    return parser


def _build_shared_parser(
    name: str,
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    subparser = subparsers.add_parser(name)
    subparser.add_argument(
        "--mongo-uri",
        default=MongoConfig().uri,
        help="MongoDB URI. Defaults to mongodb://localhost:27017 or LEGAL_INGEST_MONGO_URI.",
    )
    subparser.add_argument(
        "--mongo-db",
        default=MongoConfig().db_name,
        help="MongoDB database name. Defaults to legal_rag_runtime or LEGAL_INGEST_MONGO_DB.",
    )
    subparser.add_argument(
        "--artifact-dir",
        type=Path,
        default=ArtifactConfig().root_dir,
        help="Artifact root directory for backup/audit outputs.",
    )
    return subparser


def _add_apply_flags(parser: argparse.ArgumentParser) -> None:
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect and report actions without mutating MongoDB.",
    )
    mode_group.add_argument(
        "--apply",
        action="store_true",
        help="Apply idempotent MongoDB changes after taking a backup.",
    )


def handle_backup(args: argparse.Namespace) -> int:
    mongo_config = MongoConfig(uri=args.mongo_uri, db_name=args.mongo_db)
    artifact_config = ArtifactConfig(root_dir=args.artifact_dir)
    with MongoRuntime(mongo_config) as runtime:
        manifest = run_backup(runtime, artifact_config=artifact_config)
    print(manifest["manifest_path"])
    return 0


def handle_audit(args: argparse.Namespace) -> int:
    mongo_config = MongoConfig(uri=args.mongo_uri, db_name=args.mongo_db)
    artifact_config = ArtifactConfig(root_dir=args.artifact_dir)
    with MongoRuntime(mongo_config) as runtime:
        report = build_audit_report(runtime, migration_map_path=args.migration_map)
    paths = write_audit_artifacts(report, artifact_config=artifact_config)
    print(paths["json_path"])
    print(paths["markdown_path"])
    return 0


def handle_migration_plan(args: argparse.Namespace) -> int:
    output_path = write_migration_map(args.output)
    print(output_path)
    return 0


def handle_required_fetch(args: argparse.Namespace) -> int:
    mongo_config = MongoConfig(uri=args.mongo_uri, db_name=args.mongo_db)
    artifact_config = ArtifactConfig(root_dir=args.artifact_dir)
    with MongoRuntime(mongo_config) as runtime:
        report = run_required_fetch(
            runtime,
            artifact_config=artifact_config,
            apply_changes=bool(args.apply),
        )
    print(report["report_path"])
    return 0


def handle_metadata_migrate(args: argparse.Namespace) -> int:
    mongo_config = MongoConfig(uri=args.mongo_uri, db_name=args.mongo_db)
    artifact_config = ArtifactConfig(root_dir=args.artifact_dir)
    with MongoRuntime(mongo_config) as runtime:
        report = run_metadata_migration(
            runtime,
            artifact_config=artifact_config,
            apply_changes=bool(args.apply),
            migration_map_path=None
            if args.migration_map is None
            else str(args.migration_map),
            scope=str(args.scope),
        )
    print(report["report_path"])
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1
    return int(handler(args))
