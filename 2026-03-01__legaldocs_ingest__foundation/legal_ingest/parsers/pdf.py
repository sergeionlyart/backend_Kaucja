import fitz  # PyMuPDF
from ..config import PdfParserConfig
from ..store.models import Page, PageExtraction, PageExtractionQuality
from ..ids import generate_page_id


def parse_pdf(
    raw_bytes: bytes, doc_uid: str, source_hash: str, config: PdfParserConfig
) -> list[Page]:
    doc = fitz.open(stream=raw_bytes, filetype="pdf")
    pages = []

    for page_idx in range(len(doc)):
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

        # NOTE: Mistral OCR fallback is OUT OF SCOPE for Iteration 1 according to requirements.
        # We just assume PyMuPDF is sufficient.

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
