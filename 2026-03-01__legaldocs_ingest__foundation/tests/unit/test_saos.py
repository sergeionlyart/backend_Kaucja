import json
from legal_ingest.parsers.saos import parse_saos, extract_saos_citations


def test_saos_payload_wrapper():
    # Simulate API wrapper structure
    payload = {
        "links": [{"rel": "self"}],
        "data": {
            "textContent": "Valid Content",
            "decision": "Valid Decision",
            "summary": "Valid Summary",
            "referencedRegulations": [
                {
                    "journalYear": 2021,
                    "journalEntry": 123,
                    "text": "Dz.U. 2021 poz. 123",
                }
            ],
        },
    }
    raw_bytes = json.dumps(payload).encode("utf-8")

    pages = parse_saos(raw_bytes, "doc1", "hash1")
    assert len(pages) > 0
    assert "Empty SAOS judgment" not in pages[0].text
    assert pages[0].text.strip() != ""

    citations = extract_saos_citations(raw_bytes, "doc1", "hash1")
    assert len(citations) == 1
    assert citations[0].raw_citation_text == "Dz.U. 2021 poz. 123"
