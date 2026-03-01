from unittest.mock import patch, MagicMock
from legal_ingest.fetch import expand_saos_search
from legal_ingest.config import SourceConfig, HttpConfig


@patch("legal_ingest.fetch.httpx.Client.get")
def test_expand_saos_search(mock_get):
    http_cfg = HttpConfig()
    source = SourceConfig(
        source_id="saos_search_test",
        url="https://www.saos.org.pl",
        fetch_strategy="saos_search",
        doc_type_hint="CASELAW",
        jurisdiction="PL",
        language="pl",
        saos_search_params={"all": "test"},
    )

    # Mock pagination: page 1 has items and a next link, page 2 has items and no next link
    mock_resp1 = MagicMock()
    mock_resp1.json.return_value = {
        "items": [{"id": 123}, {"id": 456}],
        "links": [{"rel": "next", "href": "..."}],
    }

    mock_resp2 = MagicMock()
    mock_resp2.json.return_value = {
        "items": [{"id": 789}, {"id": 123}],  # 123 is a duplicate
        "links": [{"rel": "self", "href": "..."}],
    }

    mock_get.side_effect = [mock_resp1, mock_resp2]

    new_sources = expand_saos_search(http_cfg, source)

    # Assert deduplication and successful iteration across pages
    assert len(new_sources) == 3
    assert new_sources[0].source_id == "saos_search_test_123"
    assert new_sources[0].external_ids["saos_id"] == "123"

    assert new_sources[1].source_id == "saos_search_test_456"
    assert new_sources[2].source_id == "saos_search_test_789"
