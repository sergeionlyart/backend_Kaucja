"""Deterministic canonical text preparation for legal markdown documents."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import html
import re

from .constants import (
    PACKED_SECTION_MAX_CHARS,
    TEXT_PREVIEW_CHARS,
)
from .parser import ParsedMarkdownDocument
from .reader import ReadDocumentResult, TextStats

_HTML_HEAVY_TAG_RE = re.compile(
    r"</?(?:html|body|div|span|table|tbody|tr|td|th|p|a|colgroup|col|style)[^>]*>",
    re.IGNORECASE,
)
_SCRIPT_STYLE_RE = re.compile(
    r"<(?:script|style)[^>]*>.*?</(?:script|style)>",
    re.IGNORECASE | re.DOTALL,
)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_HTML_BREAK_RE = re.compile(
    r"</?(?:br|p|div|tr|li|ul|ol|table|tbody|thead|tfoot|h[1-6]|section)[^>]*>",
    re.IGNORECASE,
)
_HTML_CELL_RE = re.compile(r"</?(?:td|th)[^>]*>", re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_ANGLE_BRACKET_RE = re.compile(r"<[^>\n]{1,120}>")
_WHITESPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_SECTION_HEADING_RE = re.compile(
    r"^(?:#{1,6}\s+.+|CHAPTER\s+[IVXLC]+|TITLE\s+[IVXLC]+|SECTION\s+\d+|"
    r"Article\s+\d+[A-Za-z-]*|Art\.\s*\d+[A-Za-z-]*|§\s*\d+|ANNEX(?:\s+[IVXLC]+)?|"
    r"[A-Z][A-Z0-9 ,:;()/'\-.]{8,})$"
)
_EURLEX_DROP_LINE_PATTERNS = (
    re.compile(r"^[-]{10,}$"),
    re.compile(r"^This text is meant purely as a documentation tool", re.IGNORECASE),
    re.compile(r"^The authentic versions of the relevant acts", re.IGNORECASE),
    re.compile(r"^Those official texts are directly accessible", re.IGNORECASE),
    re.compile(r"^Amended by:?$", re.IGNORECASE),
    re.compile(r"^Corrected by:?$", re.IGNORECASE),
    re.compile(r"^Official Journal$", re.IGNORECASE),
    re.compile(r"^(?:No|page|date)$", re.IGNORECASE),
    re.compile(r"^[▼►][A-Z0-9().-]+$"),
    re.compile(r"^\(?OJ\s+[A-Z]\s+\d+"),
    re.compile(r"^http[s]?://", re.IGNORECASE),
)


@dataclass(frozen=True, slots=True)
class CanonicalSection:
    section_id: str
    heading: str | None
    text: str
    char_count: int


@dataclass(frozen=True, slots=True)
class CanonicalTextResult:
    canonical_text: str
    canonical_text_sha256: str
    text_preview: str
    text_stats_raw: TextStats
    text_stats_canonical: TextStats
    strategy: str
    sections: tuple[CanonicalSection, ...]


class CanonicalizeDocumentError(ValueError):
    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def build_canonical_text(
    *,
    file_name: str,
    parse_result: ParsedMarkdownDocument,
    read_result: ReadDocumentResult,
) -> CanonicalTextResult:
    raw_content = (parse_result.content_markdown or read_result.normalized_text).strip()
    strategy = "plain_markdown"
    if _is_html_heavy(
        text=raw_content,
        parse_result=parse_result,
        read_result=read_result,
    ):
        canonical_text = _canonicalize_html_heavy(raw_content)
        strategy = "html_heavy_visible_text"
    else:
        canonical_text = _canonicalize_plain_markdown(raw_content)

    if not canonical_text:
        raise CanonicalizeDocumentError(
            code="canonicalization_error",
            message=f"Canonical text is empty after normalization: {file_name}",
        )

    sections = _build_sections(canonical_text)
    return CanonicalTextResult(
        canonical_text=canonical_text,
        canonical_text_sha256=hashlib.sha256(
            canonical_text.encode("utf-8")
        ).hexdigest(),
        text_preview=canonical_text[:TEXT_PREVIEW_CHARS],
        text_stats_raw=read_result.text_stats,
        text_stats_canonical=_build_text_stats(canonical_text),
        strategy=strategy,
        sections=sections,
    )


def _is_html_heavy(
    *,
    text: str,
    parse_result: ParsedMarkdownDocument,
    read_result: ReadDocumentResult,
) -> bool:
    source_system = str(
        parse_result.doc_metadata.get("original_source_system")
        or parse_result.doc_metadata.get("resolved_source_system")
        or ""
    ).strip()
    if source_system == "eurlex_eu" and len(_HTML_HEAVY_TAG_RE.findall(text)) >= 10:
        return True
    tag_count = len(_ANGLE_BRACKET_RE.findall(text))
    if not text:
        return False
    return tag_count >= 20 and (tag_count * 20) >= len(text)


def _canonicalize_plain_markdown(text: str) -> str:
    normalized = html.unescape(text).replace("\xa0", " ")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.splitlines())
    normalized = _MULTI_NEWLINE_RE.sub("\n\n", normalized)
    return normalized.strip()


def _canonicalize_html_heavy(text: str) -> str:
    working = _extract_eurlex_body(text)
    working = html.unescape(working).replace("\xa0", " ")
    working = _HTML_COMMENT_RE.sub("", working)
    working = _SCRIPT_STYLE_RE.sub("", working)
    working = _HTML_BREAK_RE.sub("\n", working)
    working = _HTML_CELL_RE.sub(" | ", working)
    working = _HTML_TAG_RE.sub("", working)
    working = working.replace("\r\n", "\n").replace("\r", "\n")
    cleaned_lines: list[str] = []
    for raw_line in working.splitlines():
        line = _WHITESPACE_RE.sub(" ", raw_line).strip(" |")
        if not line:
            if cleaned_lines and cleaned_lines[-1]:
                cleaned_lines.append("")
            continue
        if any(pattern.search(line) for pattern in _EURLEX_DROP_LINE_PATTERNS):
            continue
        cleaned_lines.append(line)
    canonical = "\n".join(cleaned_lines).strip()
    canonical = _MULTI_NEWLINE_RE.sub("\n\n", canonical)
    return canonical.strip()


def _extract_eurlex_body(text: str) -> str:
    markers = (
        '<div class="eli-container"',
        "<div class='eli-container'",
        '<div id="enc_1"',
        '<div id="art_1"',
    )
    for marker in markers:
        if marker in text:
            return text[text.index(marker) :]
    return text


def _build_sections(text: str) -> tuple[CanonicalSection, ...]:
    lines = text.splitlines()
    sections: list[CanonicalSection] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_heading, current_lines
        payload = "\n".join(current_lines).strip()
        if not payload:
            current_lines = []
            current_heading = None
            return
        for chunk in _chunk_text(payload):
            section_id = f"s{len(sections) + 1:03d}"
            sections.append(
                CanonicalSection(
                    section_id=section_id,
                    heading=current_heading,
                    text=chunk,
                    char_count=len(chunk),
                )
            )
        current_lines = []
        current_heading = None

    for line in lines:
        stripped = line.strip()
        if _SECTION_HEADING_RE.match(stripped):
            flush()
            current_heading = stripped
            current_lines.append(stripped)
            continue
        if not stripped and current_lines and current_lines[-1] == "":
            continue
        current_lines.append(stripped)
    flush()

    if sections:
        return tuple(sections)
    return (
        CanonicalSection(
            section_id="s001",
            heading=None,
            text=text,
            char_count=len(text),
        ),
    )


def _chunk_text(text: str) -> tuple[str, ...]:
    if len(text) <= PACKED_SECTION_MAX_CHARS:
        return (text,)

    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= PACKED_SECTION_MAX_CHARS:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        if len(paragraph) <= PACKED_SECTION_MAX_CHARS:
            current = paragraph
            continue
        for start in range(0, len(paragraph), PACKED_SECTION_MAX_CHARS):
            chunks.append(paragraph[start : start + PACKED_SECTION_MAX_CHARS].strip())
    if current:
        chunks.append(current)
    return tuple(chunk for chunk in chunks if chunk)


def _build_text_stats(text: str) -> TextStats:
    return TextStats(
        chars=len(text),
        lines=len(text.splitlines()),
        words=len(re.findall(r"\b\w+\b", text, flags=re.UNICODE)),
    )
