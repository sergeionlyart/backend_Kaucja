from __future__ import annotations

import json
from pathlib import Path


def _load_schema() -> dict[str, object]:
    schema_path = Path("app/prompts/kaucja_gap_analysis/v001/schema.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def test_schema_v001_required_root_fields() -> None:
    schema = _load_schema()

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False

    required = set(schema["required"])
    assert {
        "case_facts",
        "checklist",
        "critical_gaps_summary",
        "next_questions_to_user",
        "conflicts_and_red_flags",
        "ocr_quality_warnings",
    }.issubset(required)


def test_schema_v001_case_facts_contract() -> None:
    schema = _load_schema()

    case_facts = schema["properties"]["case_facts"]

    assert case_facts["type"] == "object"
    assert case_facts["additionalProperties"] is False
    assert set(case_facts["required"]) == {
        "parties",
        "property_address",
        "lease_type",
        "key_dates",
        "money",
        "notes",
    }


def test_schema_v001_checklist_has_22_item_ids() -> None:
    schema = _load_schema()

    checklist_item = schema["$defs"]["checklist_item"]
    item_ids = checklist_item["properties"]["item_id"]["enum"]

    assert len(item_ids) == 22
    assert len(set(item_ids)) == 22
    assert "CONTRACT_EXISTS" in item_ids
    assert "TENANT_BANK_ACCOUNT_FOR_RETURN" in item_ids
