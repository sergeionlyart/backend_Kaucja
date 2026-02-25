from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TableFormat = Literal["html", "markdown", "none"]


@dataclass(frozen=True, slots=True)
class OCROptions:
    model: str = "mistral-ocr-latest"
    table_format: TableFormat = "html"
    include_image_base64: bool = True
    extract_header: bool = False
    extract_footer: bool = False


@dataclass(frozen=True, slots=True)
class OCRResult:
    doc_id: str
    ocr_model: str
    pages_count: int
    combined_markdown_path: str
    raw_response_path: str
    tables_dir: str
    images_dir: str
    page_renders_dir: str
    quality_path: str
    quality_warnings: list[str]
