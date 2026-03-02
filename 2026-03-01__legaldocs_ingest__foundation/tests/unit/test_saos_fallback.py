import pytest
from httpx import Response
from unittest.mock import MagicMock
from legal_ingest.config import SourceConfig, HttpConfig
from legal_ingest.fetch import fetch_saos_judgment, expand_saos_search

def test_fetch_saos_judgment_api_success():
    client = MagicMock()
    # Return valid JSON
    client.get.return_value = Response(200, json={"content": "some text"}, request=MagicMock(url="api_url"), headers={"content-type": "application/json"})
    
    source = SourceConfig(
        source_id="test", 
        url="https://saos.org.pl", 
        fetch_strategy="saos_judgment", 
        doc_type_hint="CASELAW", 
        jurisdiction="PL",
        language="pl",
        external_ids={"saos_id": "123"}
    )
    
    result = fetch_saos_judgment(client, source)
    assert result.status_code == 200
    assert client.get.call_count == 1
    assert "api/judgments" in client.get.call_args[0][0]

def test_fetch_saos_judgment_fallback_on_html_from_api():
    client = MagicMock()
    
    def side_effect(*args, **kwargs):
        url = args[0]
        if "api/" in url:
            return Response(200, content=b"<html>maintenance</html>", request=MagicMock(url=url), headers={"content-type": "text/html"})
        else:
            return Response(200, content=b"<html>good page</html>", request=MagicMock(url=url), headers={"content-type": "text/html"})
            
    client.get.side_effect = side_effect
    
    source = SourceConfig(
        source_id="test", 
        url="https://saos.org.pl", 
        fetch_strategy="saos_judgment", 
        doc_type_hint="CASELAW", 
        jurisdiction="PL",
        language="pl",
        external_ids={"saos_id": "123"}
    )
    result = fetch_saos_judgment(client, source)
    
    assert result.status_code == 200
    assert result.raw_bytes == b"<html>good page</html>"
    assert client.get.call_count == 2 # 1 for API, 1 for HTML fallback
