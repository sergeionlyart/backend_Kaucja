import pytest
from legal_ingest.config import load_config
from pydantic import ValidationError


def test_load_config_valid(tmp_path):
    yml = """
    run:
      run_id: "auto"
    mongo:
      uri: "mongodb://localhost:27017"
      db: "test"
    parsers:
      pdf: {}
      html: {}
    sources:
      - source_id: "test1"
        url: "https://example.com"
        fetch_strategy: "direct"
        doc_type_hint: "STATUTE"
        jurisdiction: "PL"
        language: "pl"
    """
    p = tmp_path / "cfg.yml"
    p.write_text(yml)

    cfg = load_config(str(p))
    assert len(cfg.sources) == 1
    assert cfg.sources[0].source_id == "test1"


def test_load_config_invalid(tmp_path):
    yml = """
    run: {}
    # missing mongo
    parsers: {}
    sources: []
    """
    p = tmp_path / "cfg.yml"
    p.write_text(yml)

    with pytest.raises(ValidationError):
        load_config(str(p))


def test_load_config_extra_forbid(tmp_path):
    yml = """
    run:
      run_id: "auto"
    mongo:
      uri: "stub"
      db: "stub"
    parsers:
      pdf:
        unknown_field_123: true
      html: {}
    sources: []
    """
    p = tmp_path / "cfg.yml"
    p.write_text(yml)

    with pytest.raises(ValidationError) as exc_info:
        load_config(str(p))

    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_expand_env_vars_success(monkeypatch):
    monkeypatch.setenv("TEST_MONGO_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("TEST_RUN_ID", "12345")

    yaml_content = """run:
  run_id: "${TEST_RUN_ID}"
mongo:
  uri: "${TEST_MONGO_URI}"
"""
    from legal_ingest.config import expand_env_vars

    expanded = expand_env_vars(yaml_content)
    assert 'run_id: "12345"' in expanded
    assert 'uri: "mongodb://localhost:27017"' in expanded


def test_expand_env_vars_missing_fails():
    yaml_content = """run:
  run_id: "${MISSING_ENV_VAR}"
"""
    from legal_ingest.config import expand_env_vars

    with pytest.raises(
        ValueError,
        match="Environment variable 'MISSING_ENV_VAR' is required but not set.",
    ):
        expand_env_vars(yaml_content)
