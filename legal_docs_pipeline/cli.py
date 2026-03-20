"""CLI bootstrap for the NormaDepo foundation slice."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .config import apply_cli_overrides, load_pipeline_config
from .constants import PipelineMode, RerunScope
from .pipeline import AnnotationPipeline, PipelineRunOptions


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the isolated NormaDepo discovery, routing, and analysis pipeline.",
    )
    parser.add_argument("--config", required=True, help="Path to YAML config file.")
    parser.add_argument(
        "--mode",
        required=True,
        choices=[mode.value for mode in PipelineMode],
        help="Pipeline mode: full, new, or rerun.",
    )
    parser.add_argument(
        "--input-root",
        help="Optional override for input.root_path.",
    )
    parser.add_argument("--mongo-uri", help="Optional override for mongo.uri.")
    parser.add_argument("--mongo-db", help="Optional override for mongo.database.")
    parser.add_argument(
        "--mongo-collection",
        help="Optional override for mongo.collection.",
    )
    parser.add_argument(
        "--rerun-scope",
        choices=[scope.value for scope in RerunScope],
        help="Required with --mode rerun.",
    )
    parser.add_argument(
        "--only-doc-id",
        help="Process only one document by relative corpus path.",
    )
    parser.add_argument("--doc-id", dest="doc_id_alias", help=argparse.SUPPRESS)
    parser.add_argument(
        "--from-relative-path",
        help="Start deterministic processing from this relative corpus path.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of discovered documents.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run discovery, parsing, and routing without Mongo writes or LLM calls.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Override workers. Foundation slice supports only value 1.",
    )
    parser.add_argument(
        "--force-classifier-fallback",
        action="store_true",
        help="Attempt LLM classifier even when rule-based routing already matched.",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Minimum JSONL log level.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    mode, rerun_scope, only_doc_id = _validate_args(parser, args)

    try:
        config = load_pipeline_config(Path(args.config))
        config = apply_cli_overrides(
            config,
            input_root=args.input_root,
            mongo_uri=args.mongo_uri,
            mongo_db=args.mongo_db,
            mongo_collection=args.mongo_collection,
            workers=args.workers,
        )
        summary = AnnotationPipeline(config=config).run(
            options=PipelineRunOptions(
                mode=mode,
                limit=args.limit,
                only_doc_id=only_doc_id,
                from_relative_path=args.from_relative_path,
                force_classifier_fallback=args.force_classifier_fallback,
                log_level=args.log_level,
                dry_run=args.dry_run,
            ),
            rerun_scope=rerun_scope,
        )
    except Exception as error:  # pragma: no cover - CLI guardrail
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(json.dumps(summary.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


def _validate_args(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> tuple[PipelineMode, RerunScope | None, str | None]:
    mode = PipelineMode(args.mode)
    rerun_scope = RerunScope(args.rerun_scope) if args.rerun_scope else None
    only_doc_id = args.only_doc_id or args.doc_id_alias

    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be a positive integer.")
    if args.from_relative_path is not None and not args.from_relative_path.strip():
        parser.error("--from-relative-path must not be empty.")
    if args.only_doc_id and args.doc_id_alias and args.only_doc_id != args.doc_id_alias:
        parser.error("--only-doc-id and hidden --doc-id alias must match.")
    if args.dry_run and args.force_classifier_fallback:
        parser.error(
            "--dry-run cannot be combined with --force-classifier-fallback."
        )

    if mode is PipelineMode.RERUN and rerun_scope is None:
        parser.error("--rerun-scope is required when --mode rerun is used.")
    if mode is not PipelineMode.RERUN and rerun_scope is not None:
        parser.error("--rerun-scope can only be used with --mode rerun.")
    if rerun_scope is RerunScope.DOC_ID and not only_doc_id:
        parser.error("--only-doc-id is required when --rerun-scope doc-id is used.")
    if rerun_scope is not RerunScope.DOC_ID and only_doc_id is not None and mode is PipelineMode.RERUN:
        parser.error("--only-doc-id can only be used with --rerun-scope doc-id in rerun mode.")

    return mode, rerun_scope, only_doc_id


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
