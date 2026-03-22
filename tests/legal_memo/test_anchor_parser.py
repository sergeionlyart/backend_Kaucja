from __future__ import annotations

import pytest

from app.legal_memo.anchor_parser import parse_anchor_response


def test_parse_anchor_response_extracts_two_blocks() -> None:
    raw_text = """
<BEGIN_ANCHOR_INDEX>
{"anchor_schema":"md-anchor-v0-proto","doc_id":"doc-1","source_wrapper":"doc_wrapper","validation_warnings":[],"anchors":[{"anchor_id":"s01","parent_anchor":null,"type":"heading","section_path":"s01","order":1,"synthetic":false,"locator":{"kind":"section","row":null},"preview":"Heading"}]}
<END_ANCHOR_INDEX>
<BEGIN_ANNOTATED_MARKDOWN>
<!--anchor:s01-->
## Heading
<END_ANNOTATED_MARKDOWN>
""".strip()

    anchor_index, markdown = parse_anchor_response(raw_text)
    assert anchor_index.doc_id == "doc-1"
    assert markdown.startswith("<!--anchor:s01-->")


def test_parse_anchor_response_rejects_extra_text() -> None:
    raw_text = "oops\n<BEGIN_ANCHOR_INDEX>{}</END_ANCHOR_INDEX>"
    with pytest.raises(ValueError):
        parse_anchor_response(raw_text)
