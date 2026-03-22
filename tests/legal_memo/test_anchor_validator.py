from __future__ import annotations

import pytest

from app.legal_memo.anchor_models import AnchorIndex
from app.legal_memo.anchor_validator import build_user_anchor_catalog, validate_anchor_output


def test_anchor_validator_accepts_matching_source_and_markdown() -> None:
    source = '<DOC_START id="doc-1">\n## Heading\n\nBody.\n<DOC_END>'
    annotated = (
        '<DOC_START id="doc-1">\n'
        "<!--anchor:s01-->\n## Heading\n\n<!--anchor:s01-p001-->\nBody.\n<DOC_END>"
    )
    anchor_index = AnchorIndex.model_validate(
        {
            "anchor_schema": "md-anchor-v0-proto",
            "doc_id": "doc-1",
            "source_wrapper": "doc_wrapper",
            "validation_warnings": [],
            "anchors": [
                {
                    "anchor_id": "s01",
                    "parent_anchor": None,
                    "type": "heading",
                    "section_path": "s01",
                    "order": 1,
                    "synthetic": False,
                    "locator": {"kind": "section", "row": None},
                    "preview": "Heading",
                },
                {
                    "anchor_id": "s01-p001",
                    "parent_anchor": None,
                    "type": "paragraph",
                    "section_path": "s01",
                    "order": 2,
                    "synthetic": False,
                    "locator": {"kind": "block", "row": None},
                    "preview": "Body.",
                },
            ],
        }
    )

    validate_anchor_output(
        source_markdown=source,
        anchor_index=anchor_index,
        annotated_markdown=annotated,
        expected_doc_id="doc-1",
    )
    catalog = build_user_anchor_catalog(
        doc_id="doc-1",
        file_name="case.md",
        anchor_index=anchor_index,
    )
    assert catalog[1].anchor_id == "s01-p001"


def test_anchor_validator_rejects_modified_source() -> None:
    anchor_index = AnchorIndex.model_validate(
        {
            "anchor_schema": "md-anchor-v0-proto",
            "doc_id": "doc-1",
            "source_wrapper": "doc_wrapper",
            "validation_warnings": [],
            "anchors": [],
        }
    )
    with pytest.raises(ValueError):
        validate_anchor_output(
            source_markdown="alpha",
            anchor_index=anchor_index,
            annotated_markdown="beta",
            expected_doc_id="doc-1",
        )
