from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.pipeline.validate_output import validate_output


def _load_schema() -> dict[str, Any]:
    path = Path("app/prompts/kaucja_gap_analysis/v001/schema.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _fact() -> dict[str, Any]:
    return {
        "value": "x",
        "status": "confirmed",
        "sources": [{"doc_id": "0000001", "quote": "quote"}],
    }


def _valid_output(schema: dict[str, Any]) -> dict[str, Any]:
    item_ids = schema["$defs"]["checklist_item"]["properties"]["item_id"]["enum"]
    checklist = []
    for idx, item_id in enumerate(item_ids):
        status = "confirmed" if idx == 0 else "missing"
        findings = (
            [
                {
                    "doc_id": "0000001",
                    "quote": "quoted text",
                    "why_this_quote_matters": "reason",
                }
            ]
            if status == "confirmed"
            else []
        )
        checklist.append(
            {
                "item_id": item_id,
                "importance": "critical" if idx == 0 else "recommended",
                "status": status,
                "what_it_supports": "support",
                "findings": findings,
                "missing_what_exactly": "missing detail",
                "request_from_user": {
                    "type": "upload_document",
                    "ask": "please upload",
                    "examples": ["doc"],
                },
                "confidence": "high" if idx == 0 else "medium",
            }
        )

    return {
        "case_facts": {
            "parties": {"tenant": _fact()},
            "property_address": _fact(),
            "lease_type": _fact(),
            "key_dates": {"lease_start": _fact()},
            "money": {"kaucja": _fact()},
            "notes": [],
        },
        "checklist": checklist,
        "critical_gaps_summary": [],
        "next_questions_to_user": ["q1"],
        "conflicts_and_red_flags": [],
        "ocr_quality_warnings": [],
    }


def test_validate_output_accepts_valid_payload() -> None:
    schema = _load_schema()
    payload = _valid_output(schema)

    result = validate_output(parsed_json=payload, schema=schema)

    assert result.valid is True
    assert result.errors == []


def test_validate_output_rejects_duplicate_checklist_item_ids() -> None:
    schema = _load_schema()
    payload = _valid_output(schema)
    payload["checklist"][1]["item_id"] = payload["checklist"][0]["item_id"]

    result = validate_output(parsed_json=payload, schema=schema)

    assert result.valid is False
    assert any("duplicate checklist item_id" in message for message in result.errors)


def test_validate_output_rejects_confirmed_without_findings() -> None:
    schema = _load_schema()
    payload = _valid_output(schema)
    payload["checklist"][0]["findings"] = []

    result = validate_output(parsed_json=payload, schema=schema)

    assert result.valid is False
    assert any(
        "confirmed item must include findings" in message for message in result.errors
    )


def test_validate_output_rejects_missing_without_ask() -> None:
    schema = _load_schema()
    payload = _valid_output(schema)
    payload["checklist"][1]["request_from_user"]["ask"] = ""

    result = validate_output(parsed_json=payload, schema=schema)

    assert result.valid is False
    assert any(
        "missing item requires request_from_user.ask" in message
        for message in result.errors
    )


def test_validate_output_rejects_more_than_10_questions() -> None:
    schema = _load_schema()
    payload = _valid_output(schema)
    payload["next_questions_to_user"] = [f"q{i}" for i in range(11)]

    result = validate_output(parsed_json=payload, schema=schema)

    assert result.valid is False
    assert any("at most 10" in message for message in result.errors)
