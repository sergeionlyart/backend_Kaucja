import json
from legal_ingest.pipeline import extract_metadata


def test_extract_saos_metadata_wrapper():
    payload = {
        "data": {
            "courtCases": [{"caseNumber": "V CSK 480/18"}],
            "judgmentType": "WYROK",
            "courtType": "SĄD NAJWYŻSZY",
            "judgmentDate": "2019-06-27",
        },
        "links": [{"rel": "self"}],
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    title, date_pub, date_dec = extract_metadata(
        [], "application/json", raw_bytes, "CASELAW"
    )
    assert title == "WYROK V CSK 480/18 (SĄD NAJWYŻSZY)"
    assert date_dec == "2019-06-27"
    assert date_pub is None
