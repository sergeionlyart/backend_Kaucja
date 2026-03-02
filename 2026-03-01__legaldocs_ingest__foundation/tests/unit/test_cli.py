import sys
from unittest.mock import MagicMock, patch

import pytest

from legal_ingest.cli import main


def test_cli_ingest_strict_ok_exits_non_zero_on_restricted(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "legal_ingest",
            "--env-file",
            ".env",
            "ingest",
            "--config",
            "configs/config.full.runtime.yml",
            "--strict-ok",
        ],
    )

    with (
        patch("legal_ingest.cli.os.path.exists", return_value=False),
        patch("legal_ingest.cli.load_config", return_value=MagicMock()),
        patch(
            "legal_ingest.cli.run_pipeline",
            return_value={"docs_restricted": 1, "docs_error": 0},
        ),
    ):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1


def test_cli_ingest_strict_ok_passes_on_all_ok(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "legal_ingest",
            "--env-file",
            ".env",
            "ingest",
            "--config",
            "configs/config.full.runtime.yml",
            "--strict-ok",
        ],
    )

    with (
        patch("legal_ingest.cli.os.path.exists", return_value=False),
        patch("legal_ingest.cli.load_config", return_value=MagicMock()),
        patch(
            "legal_ingest.cli.run_pipeline",
            return_value={"docs_restricted": 0, "docs_error": 0},
        ),
    ):
        main()
