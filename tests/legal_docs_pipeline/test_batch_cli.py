from __future__ import annotations

from legal_docs_pipeline.batch_cli import build_argument_parser


def test_batch_cli_help_mentions_operator_commands() -> None:
    help_text = build_argument_parser().format_help()

    assert "prepare" in help_text
    assert "submit" in help_text
    assert "poll" in help_text
    assert "apply" in help_text
