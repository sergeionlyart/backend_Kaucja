from __future__ import annotations

import re
from collections.abc import Iterable

from app.legal_memo.anchor_models import AnchorIndex, UserAnchorCatalogItem


CANONICAL_ANCHOR_RE = re.compile(r"<!--anchor:([a-z0-9-]+)-->")
CANONICAL_ANCHOR_LINE_RE = re.compile(r"^[ \t]*<!--anchor:[a-z0-9-]+-->[ \t]*\n?", re.MULTILINE)


def strip_canonical_anchors(markdown: str) -> str:
    without_anchor_lines = CANONICAL_ANCHOR_LINE_RE.sub("", markdown)
    return CANONICAL_ANCHOR_RE.sub("", without_anchor_lines)


def validate_anchor_output(
    *,
    source_markdown: str,
    anchor_index: AnchorIndex,
    annotated_markdown: str,
    expected_doc_id: str | None,
) -> None:
    anchor_ids = [item.anchor_id for item in anchor_index.anchors]
    if len(anchor_ids) != len(set(anchor_ids)):
        raise ValueError("anchor_index contains duplicate anchor_id values")

    if expected_doc_id is not None and anchor_index.doc_id != expected_doc_id:
        raise ValueError(
            "anchor_index doc_id does not match the requested document id: "
            f"{anchor_index.doc_id!r} != {expected_doc_id!r}"
        )

    source_without_anchors = strip_canonical_anchors(source_markdown)
    annotated_without_anchors = strip_canonical_anchors(annotated_markdown)
    if annotated_without_anchors != source_without_anchors:
        raise ValueError("annotated markdown changes source content beyond anchor insertion")

    markdown_anchor_ids = [match.group(1) for match in CANONICAL_ANCHOR_RE.finditer(annotated_markdown)]
    if markdown_anchor_ids != anchor_ids:
        raise ValueError("anchor index order does not match anchor order in markdown")

    expected_orders = list(range(1, len(anchor_index.anchors) + 1))
    actual_orders = [item.order for item in anchor_index.anchors]
    if actual_orders != expected_orders:
        raise ValueError("anchor_index order values must be contiguous and start at 1")


def build_user_anchor_catalog(
    *,
    doc_id: str,
    file_name: str,
    anchor_index: AnchorIndex,
) -> list[UserAnchorCatalogItem]:
    return [
        UserAnchorCatalogItem(
            doc_id=doc_id,
            file_name=file_name,
            anchor_id=item.anchor_id,
            parent_anchor=item.parent_anchor,
            section_path=item.section_path,
            anchor_type=item.type,
            order=item.order,
            preview=item.preview,
        )
        for item in anchor_index.anchors
    ]


def build_anchor_preview_lookup(
    catalog: Iterable[UserAnchorCatalogItem],
) -> dict[tuple[str, str], str]:
    return {(item.doc_id, item.anchor_id): item.preview for item in catalog}
