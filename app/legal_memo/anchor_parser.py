from __future__ import annotations

import json
import re

from app.legal_memo.anchor_models import AnchorIndex


_ANCHOR_RESPONSE_RE = re.compile(
    r"\s*<BEGIN_ANCHOR_INDEX>\s*(?P<index>.*?)\s*<END_ANCHOR_INDEX>\s*"
    r"<BEGIN_ANNOTATED_MARKDOWN>\s*(?P<markdown>.*?)\s*<END_ANNOTATED_MARKDOWN>\s*",
    re.DOTALL,
)


def parse_anchor_response(raw_text: str) -> tuple[AnchorIndex, str]:
    match = _ANCHOR_RESPONSE_RE.fullmatch(raw_text)
    if match is None:
        raise ValueError("anchor response must contain exactly two required blocks")

    try:
        parsed_index = json.loads(match.group("index"))
    except json.JSONDecodeError as error:
        raise ValueError(f"anchor index is not valid JSON: {error}") from error

    anchor_index = AnchorIndex.model_validate(parsed_index)
    annotated_markdown = match.group("markdown")
    return anchor_index, annotated_markdown
