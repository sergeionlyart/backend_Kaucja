from __future__ import annotations

from pathlib import Path

from app.config.settings import Settings


def test_settings_reads_env_override(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "custom.sqlite3"
    monkeypatch.setenv("KAUCJA_SQLITE_PATH", str(db_path))

    settings = Settings(_env_file=None)

    assert settings.sqlite_path == db_path
    assert settings.resolved_sqlite_path == db_path.resolve()


def test_settings_loads_provider_config() -> None:
    settings = Settings(_env_file=None)

    providers = settings.providers_config

    assert "llm_providers" in providers
    assert "openai" in providers["llm_providers"]
