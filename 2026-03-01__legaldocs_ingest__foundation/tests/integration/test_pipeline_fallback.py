import pytest
from httpx import Response, TimeoutException
from unittest.mock import MagicMock, patch
from legal_ingest.config import PipelineConfig, SourceConfig, HttpConfig, RunConfig

@pytest.fixture
def mock_pipeline_config(tmp_path):
    rc = RunConfig(artifact_dir=str(tmp_path), dry_run=True, http=HttpConfig())
    sc = SourceConfig(
        source_id="test_saos",
        url="https://www.saos.org.pl/judgments/171957",
        fetch_strategy="saos_judgment",
        doc_type_hint="CASELAW",
        jurisdiction="PL",
        language="pl",
        external_ids={"saos_id": "171957"}
    )
    from legal_ingest.config import MongoConfig, ParsersConfig
    return PipelineConfig(run=rc, sources=[sc], mongo=MongoConfig(uri="mongodb://localhost:27017", db="test"), parsers=ParsersConfig())

@patch("legal_ingest.fetch.httpx.Client.get")
def test_pipeline_saos_fallback(mock_get, mock_pipeline_config):
    # First call is to API and fails via Timeout
    # Second call is fallback to HTML and succeeds
    def side_effect(*args, **kwargs):
        url = args[0]
        if "api/judgments" in url:
            raise TimeoutException("API Down")
        # HTML fallback
        long_text = "Good content " * 100 # > 1300 chars to avoid Restricted
        return Response(200, content=f"<html><body><h1>Test Judgment</h1><p>{long_text}</p></body></html>".encode("utf-8"), request=MagicMock(url=url), headers={"content-type": "text/html"})
        
    mock_get.side_effect = side_effect
    
    from legal_ingest.pipeline import run_pipeline
    stats = run_pipeline(mock_pipeline_config)
    
    assert stats["docs_error"] == 0
    assert stats["docs_ok"] == 1
    assert mock_get.call_count == 2
