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
