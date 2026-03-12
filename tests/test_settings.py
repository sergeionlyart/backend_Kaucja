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
    monkeypatch.setenv("LIVE_SMOKE_REQUIRED_PROVIDERS", "openai,google")
    monkeypatch.setenv("LIVE_SMOKE_PROVIDER_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("E2E_MODE", "true")

    settings = Settings(_env_file=None)

    assert settings.restore_max_entries == 111
    assert settings.restore_max_total_uncompressed_bytes == 222
    assert settings.restore_max_single_file_bytes == 333
    assert settings.restore_max_compression_ratio == 44.5
    assert settings.restore_require_signature is True
    assert settings.bundle_signing_key == "local-test-key"
    assert settings.live_smoke_required_providers == "openai,google"
    assert settings.live_smoke_provider_timeout_seconds == 12.5
    assert settings.e2e_mode is True


def test_settings_reads_scenario2_local_corpus_env(monkeypatch, tmp_path: Path) -> None:
    corpus_root = tmp_path / "legal_collection"
    monkeypatch.setenv("SCENARIO2_LEGAL_CORPUS_BACKEND", "local")
    monkeypatch.setenv("SCENARIO2_LEGAL_CORPUS_LOCAL_ROOT", str(corpus_root))
    monkeypatch.setenv("SCENARIO2_VERIFIER_POLICY", "strict")

    settings = Settings(_env_file=None)

    assert settings.scenario2_verifier_policy == "strict"
    assert settings.scenario2_legal_corpus_backend == "local"
    assert settings.scenario2_legal_corpus_local_root == corpus_root
    assert settings.resolved_scenario2_legal_corpus_local_root == corpus_root.resolve()


def test_settings_reads_scenario2_mongo_env(monkeypatch) -> None:
    monkeypatch.setenv("SCENARIO2_LEGAL_CORPUS_BACKEND", "mongo")
    monkeypatch.setenv("SCENARIO2_LEGAL_CORPUS_MONGO_URI", "mongodb://mongo.example")
    monkeypatch.setenv("SCENARIO2_LEGAL_CORPUS_MONGO_DB", "legal_prod")
    monkeypatch.setenv("SCENARIO2_LEGAL_CORPUS_MONGO_AUTO_MATERIALIZE", "false")

    settings = Settings(_env_file=None)

    assert settings.scenario2_legal_corpus_backend == "mongo"
    assert settings.scenario2_legal_corpus_mongo_uri == "mongodb://mongo.example"
    assert settings.scenario2_legal_corpus_mongo_db == "legal_prod"
    assert settings.scenario2_legal_corpus_mongo_auto_materialize is False
