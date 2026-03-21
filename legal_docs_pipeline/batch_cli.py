"""Operator CLI for annotate_original batch workflow."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .config import apply_cli_overrides, load_pipeline_config
from .constants import PipelineMode


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run operator-driven OpenAI batch workflow for annotate_original.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    _add_shared_prepare_arguments(prepare)

    submit = subparsers.add_parser("submit")
    _add_shared_runtime_arguments(submit)

    poll = subparsers.add_parser("poll")
    _add_shared_runtime_arguments(poll)
    poll.add_argument(
        "--wait",
        action="store_true",
        help="Poll until no in-flight batch jobs remain.",
    )

    apply = subparsers.add_parser("apply")
    _add_shared_runtime_arguments(apply)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    try:
        from .batch_runner import BatchAnalysisRunner, BatchRunOptions

        config = load_pipeline_config(Path(args.config))
        config = apply_cli_overrides(
            config,
            input_root=getattr(args, "input_root", None),
            mongo_uri=getattr(args, "mongo_uri", None),
            mongo_db=getattr(args, "mongo_db", None),
            mongo_collection=getattr(args, "mongo_collection", None),
            workers=None,
        )
        runner = BatchAnalysisRunner(config=config)
        if args.command == "prepare":
            summary = runner.prepare(
                options=BatchRunOptions(
                    mode=PipelineMode(args.mode),
                    limit=args.limit,
                    only_doc_id=args.only_doc_id,
                    from_relative_path=args.from_relative_path,
                    force_classifier_fallback=args.force_classifier_fallback,
                    log_level=args.log_level,
                )
            )
        elif args.command == "submit":
            summary = runner.submit(log_level=args.log_level)
        elif args.command == "poll":
            summary = runner.poll(log_level=args.log_level, wait=args.wait)
        else:
            summary = runner.apply(log_level=args.log_level)
    except Exception as error:  # pragma: no cover - CLI guardrail
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(json.dumps(summary.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


def _add_shared_prepare_arguments(parser: argparse.ArgumentParser) -> None:
    _add_shared_runtime_arguments(parser)
    parser.add_argument(
        "--mode",
        required=True,
        choices=[PipelineMode.FULL.value, PipelineMode.NEW.value],
        help="Batch prepare mode: full or new.",
    )
    parser.add_argument("--only-doc-id", help="Queue only one document.")
    parser.add_argument(
        "--from-relative-path",
        help="Start deterministic processing from this relative corpus path.",
    )
    parser.add_argument("--limit", type=int, help="Limit discovered documents.")
    parser.add_argument(
        "--force-classifier-fallback",
        action="store_true",
        help="Attempt LLM classifier even when rule-based routing already matched.",
    )


def _add_shared_runtime_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", required=True, help="Path to YAML config file.")
    parser.add_argument("--input-root", help="Optional override for input.root_path.")
    parser.add_argument("--mongo-uri", help="Optional override for mongo.uri.")
    parser.add_argument("--mongo-db", help="Optional override for mongo.database.")
    parser.add_argument(
        "--mongo-collection",
        help="Optional override for mongo.collection.",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Minimum JSONL log level.",
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
