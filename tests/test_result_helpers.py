from __future__ import annotations

from app.ui.result_helpers import (
    build_checklist_rows,
    build_gap_rows,
    checklist_item_ids,
    render_checklist_details,
)


def _parsed_payload() -> dict[str, object]:
    return {
        "checklist": [
            {
                "item_id": "lease_signed",
                "importance": "critical",
                "status": "confirmed",
                "confidence": "high",
                "what_it_supports": "proof",
                "missing_what_exactly": "",
                "request_from_user": {"type": "none", "ask": "", "examples": []},
                "findings": [
                    {
                        "doc_id": "0000001",
                        "quote": "Signed lease agreement",
                        "why_this_quote_matters": "confirms contract",
                    }
                ],
            },
            {
                "item_id": "deposit_transfer",
                "importance": "critical",
                "status": "missing",
                "confidence": "medium",
                "what_it_supports": "payment proof",
                "missing_what_exactly": "transfer receipt",
                "request_from_user": {
                    "type": "upload_document",
                    "ask": "Upload bank transfer confirmation",
                    "examples": ["bank statement", "payment receipt"],
                },
                "findings": [],
            },
        ]
    }


def test_build_checklist_rows_and_item_ids() -> None:
    payload = _parsed_payload()

    rows = build_checklist_rows(payload)
    assert rows == [
        ["lease_signed", "critical", "confirmed", "high"],
        ["deposit_transfer", "critical", "missing", "medium"],
    ]
    assert checklist_item_ids(payload) == ["lease_signed", "deposit_transfer"]


def test_build_gap_rows_uses_request_ask() -> None:
    payload = _parsed_payload()

    rows = build_gap_rows(payload)
    assert rows == [["deposit_transfer", "Upload bank transfer confirmation"]]


def test_render_checklist_details_includes_findings_and_requests() -> None:
    payload = _parsed_payload()

    details = render_checklist_details(payload, "deposit_transfer")

    assert "item_id: deposit_transfer" in details
    assert "ask: Upload bank transfer confirmation" in details
    assert "examples:" in details
    assert "findings:" in details
