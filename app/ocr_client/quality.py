from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class OCRQualityReport:
    warnings: list[str]
    bad_pages: list[int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "warnings": self.warnings,
            "bad_pages": self.bad_pages,
        }


def evaluate_ocr_quality(
    page_markdowns: list[str], min_chars: int = 200
) -> OCRQualityReport:
    warnings: list[str] = []
    bad_pages: list[int] = []

    for index, markdown in enumerate(page_markdowns, start=1):
        page_warnings = _evaluate_page(
            markdown=markdown, page_index=index, min_chars=min_chars
        )
        if page_warnings:
            warnings.extend(page_warnings)
            bad_pages.append(index)

    return OCRQualityReport(warnings=warnings, bad_pages=bad_pages)


def _evaluate_page(*, markdown: str, page_index: int, min_chars: int) -> list[str]:
    normalized = markdown.strip()
    page_warnings: list[str] = []

    if len(normalized) < min_chars:
        page_warnings.append(
            f"Page {page_index}: markdown length below threshold ({len(normalized)} < {min_chars})."
        )

    if normalized:
        letters = sum(character.isalpha() for character in normalized)
        letter_ratio = letters / len(normalized)
        if letter_ratio < 0.2:
            page_warnings.append(
                f"Page {page_index}: low alphabetic ratio ({letter_ratio:.2f})."
            )

        replacement_count = normalized.count("�")
        if replacement_count > 0:
            page_warnings.append(
                f"Page {page_index}: contains replacement characters ({replacement_count})."
            )

    placeholder_only = _placeholder_only_content(normalized)
    if placeholder_only:
        page_warnings.append(f"Page {page_index}: mostly placeholder-only OCR content.")

    return page_warnings


def _placeholder_only_content(markdown: str) -> bool:
    if not markdown:
        return False

    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    if not lines:
        return False

    placeholder_lines = 0
    for line in lines:
        if line.startswith("![") and "](" in line:
            placeholder_lines += 1
            continue
        if line.startswith("[") and "](" in line:
            placeholder_lines += 1

    ratio = placeholder_lines / len(lines)
    return ratio > 0.7
