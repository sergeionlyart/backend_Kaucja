from __future__ import annotations

from legal_docs_pipeline.batch_cli import build_argument_parser


def test_batch_cli_help_mentions_operator_commands() -> None:
    help_text = build_argument_parser().format_help()

    assert "prepare" in help_text
    assert "submit" in help_text
    assert "poll" in help_text
    assert "apply" in help_text


def test_batch_cli_poll_accepts_wait_flag() -> None:
    parser = build_argument_parser()

    args = parser.parse_args(
        ["poll", "--config", "config/pipeline.yaml", "--wait"]
    )

    assert args.command == "poll"
    assert args.wait is True


def test_batch_cli_submit_accepts_runtime_overrides() -> None:
    parser = build_argument_parser()

    args = parser.parse_args(
        [
            "submit",
            "--config",
            "config/pipeline.yaml",
            "--input-root",
            "/tmp/input",
            "--mongo-uri",
            "mongodb://localhost:27017",
            "--mongo-db",
            "kaucja_legal_corpus",
            "--mongo-collection",
            "documents_cas_law_v2_2_prod_v3",
        ]
    )

    assert args.command == "submit"
    assert args.input_root == "/tmp/input"
    assert args.mongo_collection == "documents_cas_law_v2_2_prod_v3"
