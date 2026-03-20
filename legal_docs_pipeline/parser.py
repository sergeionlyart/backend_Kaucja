"""Markdown parser for the NormaDepo pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Protocol

from .reader import extract_title_from_text

MetadataValue = str | int | None

_METADATA_FIELD_MAP = {
    "entry index": "entry_index",
    "category": "category",
    "source id": "source_id",
    "original source system": "original_source_system",
    "resolved source system": "resolved_source_system",
    "original doc uid": "original_doc_uid",
    "canonical doc uid": "canonical_doc_uid",
    "original url": "original_url",
    "resolved url": "resolved_url",
    "final url": "final_url",
    "http status": "http_status",
    "fetch mode": "fetch_mode",
    "retrieved at": "retrieved_at",
    "content-type": "content_type",
    "resolution note": "resolution_note",
    "article focus": "article_focus",
}
_INT_METADATA_FIELDS = {"entry_index", "http_status"}
_METADATA_HEADER_RE = re.compile(r"^## Metadata\s*$", re.MULTILINE)
_CONTENT_HEADER_RE = re.compile(r"^## Content\s*$", re.MULTILINE)
_METADATA_LINE_RE = re.compile(r"^- (?P<label>[^:]+):\s*(?P<value>.*)$")


@dataclass(frozen=True, slots=True)
class ParsedMarkdownDocument:
    doc_metadata: dict[str, MetadataValue]
    content_markdown: str
    title: str | None
    had_metadata_block: bool
    had_content_block: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)


class MarkdownParser(Protocol):
    def parse(
        self,
        *,
        file_name: str,
        normalized_text: str,
    ) -> ParsedMarkdownDocument:
        """Parse markdown container and preserve raw text."""


class MarkdownParseError(ValueError):
    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class LegalMarkdownParser:
    def parse(
        self,
        *,
        file_name: str,
        normalized_text: str,
    ) -> ParsedMarkdownDocument:
        metadata_match = _METADATA_HEADER_RE.search(normalized_text)
        content_match = _CONTENT_HEADER_RE.search(normalized_text)
        is_service_document = _is_service_document(file_name)
        warnings: list[str] = []

        if content_match is None:
            if not is_service_document:
                raise MarkdownParseError(
                    code="parse_error",
                    message="Missing ## Content block.",
                )
            warnings.append("missing_content_block")
            content_markdown = normalized_text.strip()
        else:
            content_markdown = normalized_text[content_match.end() :].strip()
            if not content_markdown and not is_service_document:
                raise MarkdownParseError(
                    code="parse_error",
                    message="Empty ## Content block.",
                )

        if metadata_match is None or (
            content_match is not None and metadata_match.start() > content_match.start()
        ):
            warnings.append("missing_metadata_block")
            doc_metadata: dict[str, MetadataValue] = {}
        else:
            metadata_end = content_match.start() if content_match else len(normalized_text)
            metadata_block = normalized_text[metadata_match.end() : metadata_end].strip()
            doc_metadata = _parse_metadata_block(metadata_block)

        title = extract_title_from_text(content_markdown or normalized_text)
        return ParsedMarkdownDocument(
            doc_metadata=doc_metadata,
            content_markdown=content_markdown,
            title=title,
            had_metadata_block=metadata_match is not None,
            had_content_block=content_match is not None,
            warnings=tuple(dict.fromkeys(warnings)),
        )


def _parse_metadata_block(block: str) -> dict[str, MetadataValue]:
    metadata: dict[str, MetadataValue] = {}
    for line in block.splitlines():
        match = _METADATA_LINE_RE.match(line.strip())
        if match is None:
            continue

        label = match.group("label").strip().lower()
        value = match.group("value").strip()
        field_name = _METADATA_FIELD_MAP.get(label)
        if field_name is None:
            continue
        if field_name in _INT_METADATA_FIELDS:
            metadata[field_name] = int(value) if value.isdigit() else value
            continue
        metadata[field_name] = value or None
    return metadata


def _is_service_document(file_name: str) -> bool:
    upper_name = file_name.upper()
    return upper_name == "README.MD" or upper_name.endswith("_README.MD")
