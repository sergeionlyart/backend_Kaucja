"""Tests for mapper item_id coverage.

Ensures that every item_id from canonical_schema.json is mapped
in ITEM_ID_TO_FIELD. Fails if any item_id is missing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.api.mapper import ALL_ITEM_IDS, ITEM_ID_TO_FIELD

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent / "app" / "schemas" / "canonical_schema.json"
)


@pytest.fixture()
def schema_item_ids() -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    checklist_item = schema["$defs"]["checklist_item"]
    return checklist_item["properties"]["item_id"]["enum"]


def test_all_item_ids_listed(schema_item_ids: list[str]) -> None:
    """ALL_ITEM_IDS in mapper must match canonical schema enum exactly."""
    assert set(ALL_ITEM_IDS) == set(schema_item_ids)


def test_all_item_ids_mapped(schema_item_ids: list[str]) -> None:
    """Every item_id from schema must have a mapping in ITEM_ID_TO_FIELD."""
    unmapped = set(schema_item_ids) - set(ITEM_ID_TO_FIELD.keys())
    assert unmapped == set(), f"Unmapped item_ids: {unmapped}"


def test_mapping_values_are_valid_fields() -> None:
    """All mapped summary_field_ids must be valid."""
    valid_fields = {
        "lease_agreement",
        "deposit_amount",
        "deposit_payment_method",
        "handover_protocol",
        "move_out_date",
        "withholding_reason",
    }
    valid_doc_types = {
        "lease",
        "deposit_payment",
        "handover_protocol",
        "correspondence",
    }
    for item_id, (field_id, doc_type) in ITEM_ID_TO_FIELD.items():
        assert field_id in valid_fields, (
            f"item_id={item_id} maps to invalid field={field_id}"
        )
        assert doc_type in valid_doc_types, (
            f"item_id={item_id} maps to invalid doc_type={doc_type}"
        )


def test_count_matches_schema(schema_item_ids: list[str]) -> None:
    """Mapper must cover exactly 22 item_ids."""
    assert len(schema_item_ids) == 22
    assert len(ALL_ITEM_IDS) == 22
    assert len(ITEM_ID_TO_FIELD) == 22
