from __future__ import annotations

from pydantic import Field

from app.legal_memo.models import StrictModel


class AnchorLocator(StrictModel):
    kind: str
    row: int | None = Field(default=None, ge=1)


class AnchorIndexItem(StrictModel):
    anchor_id: str
    parent_anchor: str | None = None
    type: str
    section_path: str
    order: int = Field(ge=1)
    synthetic: bool = False
    locator: AnchorLocator
    preview: str


class AnchorIndex(StrictModel):
    anchor_schema: str
    doc_id: str | None = None
    source_wrapper: str
    validation_warnings: list[str] = Field(default_factory=list)
    anchors: list[AnchorIndexItem] = Field(default_factory=list)


class UserAnchorCatalogItem(StrictModel):
    doc_id: str
    file_name: str
    anchor_id: str
    parent_anchor: str | None = None
    section_path: str
    anchor_type: str
    order: int = Field(ge=1)
    preview: str


class AnchoredUserDocument(StrictModel):
    doc_id: str
    file_name: str
    source_markdown: str
    annotated_markdown: str
    anchor_index: AnchorIndex
    validation_warnings: list[str] = Field(default_factory=list)
    user_anchor_catalog: list[UserAnchorCatalogItem] = Field(default_factory=list)
