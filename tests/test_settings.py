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


def test_settings_reads_restore_limits_and_signature_env(monkeypatch) -> None:
    monkeypatch.setenv("RESTORE_MAX_ENTRIES", "111")
    monkeypatch.setenv("RESTORE_MAX_TOTAL_UNCOMPRESSED_BYTES", "222")
    monkeypatch.setenv("RESTORE_MAX_SINGLE_FILE_BYTES", "333")
    monkeypatch.setenv("RESTORE_MAX_COMPRESSION_RATIO", "44.5")
    monkeypatch.setenv("RESTORE_REQUIRE_SIGNATURE", "true")
    monkeypatch.setenv("BUNDLE_SIGNING_KEY", "local-test-key")

    settings = Settings(_env_file=None)

    assert settings.restore_max_entries == 111
    assert settings.restore_max_total_uncompressed_bytes == 222
    assert settings.restore_max_single_file_bytes == 333
    assert settings.restore_max_compression_ratio == 44.5
    assert settings.restore_require_signature is True
    assert settings.bundle_signing_key == "local-test-key"
