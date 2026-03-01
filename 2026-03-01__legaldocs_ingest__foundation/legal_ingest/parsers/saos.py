import json
from ..store.models import Page, PageExtraction, PageExtractionQuality
from ..ids import generate_page_id


def parse_saos(raw_bytes: bytes, doc_uid: str, source_hash: str) -> list[Page]:
    data = json.loads(raw_bytes.decode("utf-8"))

    # Extract decision, summary, and textContent
    decision = data.get("decision") or ""
    summary = data.get("summary") or ""
    text_content = data.get("textContent") or ""

    chunks = []

    if decision.strip():
        chunks.append(f"# Decision\n{decision}")
    if summary.strip():
        chunks.append(f"# Summary\n{summary}")
    if text_content.strip():
        chunks.append(f"# Text\n{text_content}")

    if not chunks:
        chunks.append("Empty SAOS judgment")

    pages = []
    for idx, text in enumerate(chunks):
        extraction = PageExtraction(
            method="SAOS_JSON",
            quality=PageExtractionQuality(alpha_ratio=1.0, empty=False),
        )
        p = Page(
            _id=generate_page_id(doc_uid, source_hash, idx),
            doc_uid=doc_uid,
            source_hash=source_hash,
            page_index=idx,
            text=text,
            token_count_est=len(text.split()),
            char_count=len(text),
            extraction=extraction,
        )
        pages.append(p)

    return pages
