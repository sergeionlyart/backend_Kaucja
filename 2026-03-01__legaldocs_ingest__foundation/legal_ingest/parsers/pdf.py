import fitz  # PyMuPDF
import os
import httpx
import logging
from ..config import PdfParserConfig, OcrConfig
from ..store.models import Page, PageExtraction, PageExtractionQuality
from ..ids import generate_page_id

logger = logging.getLogger("legal_ingest")


def parse_pdf(
    raw_bytes: bytes,
    doc_uid: str,
    source_hash: str,
    config: PdfParserConfig,
    ocr_config: OcrConfig,
    url: str,
) -> list[Page]:
    doc = fitz.open(stream=raw_bytes, filetype="pdf")
    pages = []

    total_chars = 0
    empty_pages = 0
    num_pages = len(doc)

    for page_idx in range(num_pages):
        page = doc[page_idx]
        text = page.get_text("text") or ""
        char_count = len(text.strip())
        total_chars += char_count
        if char_count == 0:
            empty_pages += 1

    avg_chars = total_chars / num_pages if num_pages > 0 else 0
    empty_ratio = empty_pages / num_pages if num_pages > 0 else 0

    needs_ocr = False
    if config.min_avg_chars_per_page and avg_chars < config.min_avg_chars_per_page:
        needs_ocr = True
    if config.max_empty_page_ratio and empty_ratio > config.max_empty_page_ratio:
        needs_ocr = True

    if needs_ocr and ocr_config.enabled:
        logger.info(
            "PDF quality threshold not met. Attempting Mistral OCR Fallback.",
            extra={
                "metrics": {"avg_chars": avg_chars, "empty_ratio": empty_ratio},
                "stage": "parse",
            },
        )
        ocr_pages = _run_mistral_ocr(doc_uid, source_hash, ocr_config, url)
        if ocr_pages is not None:
            doc.close()
            return ocr_pages
        logger.warning(
            "Mistral OCR Fallback failed. Proceeding with PyMuPDF standard extraction.",
            extra={"stage": "parse"},
        )

    for page_idx in range(num_pages):
        page = doc[page_idx]
        text = page.get_text("text") or ""

        # Simple quality metrics
        char_count = len(text)
        alpha_count = sum(1 for c in text if c.isalpha())
        alpha_ratio = alpha_count / char_count if char_count > 0 else 0.0
        is_empty = char_count == 0

        extraction = PageExtraction(
            method="PDF_TEXT",
            quality=PageExtractionQuality(alpha_ratio=alpha_ratio, empty=is_empty),
        )

        p = Page(
            _id=generate_page_id(doc_uid, source_hash, page_idx),
            doc_uid=doc_uid,
            source_hash=source_hash,
            page_index=page_idx,
            text=text,
            token_count_est=len(text.split()),  # rough est
            char_count=char_count,
            extraction=extraction,
        )
        pages.append(p)

    doc.close()
    return pages


def _run_mistral_ocr(
    doc_uid: str, source_hash: str, ocr_config: OcrConfig, url: str
) -> list[Page] | None:
    api_key = os.getenv(ocr_config.api_key_env)
    if not api_key:
        logger.error(
            f"Missing {ocr_config.api_key_env} in environment.",
            extra={"stage": "parse"},
        )
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "model": ocr_config.model,
        "document": {"type": "document_url", "documentUrl": url},
        "table_format": ocr_config.table_format,
        "include_image_base64": ocr_config.include_image_base64,
    }
    try:
        resp = httpx.post(
            ocr_config.endpoint, json=payload, headers=headers, timeout=120
        )
        resp.raise_for_status()
        data = resp.json()

        pages = []
        ocr_pages = data.get("pages", [])
        for idx, op in enumerate(ocr_pages):
            text = op.get("markdown", "")

            char_count = len(text)
            alpha_count = sum(1 for c in text if c.isalpha())
            alpha_ratio = alpha_count / char_count if char_count > 0 else 0.0

            extraction = PageExtraction(
                method="OCR3",
                quality=PageExtractionQuality(
                    alpha_ratio=alpha_ratio, empty=(char_count == 0)
                ),
                ocr_meta={"model": ocr_config.model, "provider": ocr_config.provider},
            )

            p = Page(
                _id=generate_page_id(doc_uid, source_hash, idx),
                doc_uid=doc_uid,
                source_hash=source_hash,
                page_index=idx,
                text=text,
                markdown=text,
                token_count_est=len(text.split()),
                char_count=char_count,
                extraction=extraction,
            )
            pages.append(p)

        return pages
    except Exception as e:
        logger.error(f"Mistral OCR POST error: {e}", extra={"stage": "parse"})
        return None
