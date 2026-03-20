"""Reader and soft normalizer for markdown legal documents."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import html
import re

from .constants import DEFAULT_MAX_FILE_SIZE_BYTES
from .scanner import DiscoveredDocument

_HTML_TAG_PATTERNS = (
    re.compile(r"<br\s*/?>", re.IGNORECASE),
    re.compile(r"</?div[^>]*>", re.IGNORECASE),
    re.compile(r"</?span[^>]*>", re.IGNORECASE),
)
_NON_TITLE_PATTERNS = (
    re.compile(r"^#+\s*#+\s*page\s+\d+$", re.IGNORECASE),
    re.compile(r"^page\s+\d+$", re.IGNORECASE),
    re.compile(r"^s\.\s*\d+/\d+$", re.IGNORECASE),
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(r"^dz\.\s*u\.", re.IGNORECASE),
    re.compile(r"^©"),
    re.compile(r"^[\-\|_ ]+$"),
)


@dataclass(frozen=True, slots=True)
class TextStats:
    chars: int
    lines: int
    words: int


@dataclass(frozen=True, slots=True)
class ReadDocumentResult:
    raw_markdown: str
    normalized_text: str
    normalized_text_sha256: str
    title: str | None
    text_stats: TextStats
    encoding: str = "utf-8"


class ReadDocumentError(ValueError):
    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class MarkdownReader:
    def __init__(
        self,
        *,
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    ) -> None:
        self._max_file_size_bytes = max_file_size_bytes

    def read(self, document: DiscoveredDocument) -> ReadDocumentResult:
        if document.size_bytes > self._max_file_size_bytes:
            raise ReadDocumentError(
                code="file_too_large",
                message=(
                    f"File exceeds {self._max_file_size_bytes} bytes: "
                    f"{document.relative_path.as_posix()}"
                ),
            )

        try:
            decoded = document.absolute_path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as error:
            raise ReadDocumentError(
                code="utf8_decode_error",
                message=str(error),
            ) from error

        raw_markdown = _normalize_newlines(decoded.lstrip("\ufeff"))
        normalized_text = soft_normalize_text(raw_markdown)
        normalized_text_sha256 = hashlib.sha256(
            normalized_text.encode("utf-8")
        ).hexdigest()
        return ReadDocumentResult(
            raw_markdown=raw_markdown,
            normalized_text=normalized_text,
            normalized_text_sha256=normalized_text_sha256,
            title=extract_title_from_text(normalized_text),
            text_stats=_build_text_stats(normalized_text),
        )


def soft_normalize_text(text: str) -> str:
    normalized = html.unescape(text).replace("\xa0", " ")
    normalized = _normalize_newlines(normalized)
    for pattern in _HTML_TAG_PATTERNS:
        normalized = pattern.sub("" if pattern.pattern != r"<br\s*/?>" else "\n", normalized)
    normalized = re.sub(r"^\s*style=\"[^\"]*\"\s*/?>\s*$", "", normalized, flags=re.MULTILINE)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = "\n".join(line.rstrip() for line in normalized.splitlines())
    return normalized.strip()


def extract_title_from_text(text: str) -> str | None:
    search_space = _slice_after_content_heading(text)
    for line in search_space.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        candidate = re.sub(r"^#+\s*", "", stripped).strip()
        candidate = re.sub(r"\s+", " ", candidate)
        if not candidate:
            continue
        if any(pattern.match(candidate) for pattern in _NON_TITLE_PATTERNS):
            continue
        if candidate in {"Metadata", "Content"}:
            continue
        return candidate[:300]
    return None


def _slice_after_content_heading(text: str) -> str:
    marker = "\n## Content\n"
    if marker in text:
        return text.split(marker, maxsplit=1)[1]
    return text


def _build_text_stats(text: str) -> TextStats:
    return TextStats(
        chars=len(text),
        lines=len(text.splitlines()),
        words=len(re.findall(r"\b\w+\b", text, flags=re.UNICODE)),
    )


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")
