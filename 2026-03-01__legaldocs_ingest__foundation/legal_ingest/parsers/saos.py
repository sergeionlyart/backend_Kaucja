import json
import hashlib
from ..store.models import (
    Page,
    PageExtraction,
    PageExtractionQuality,
    Citation,
    CitationTarget,
)
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


def extract_saos_citations(
    raw_bytes: bytes, doc_uid: str, source_hash: str
) -> list[Citation]:
    data = json.loads(raw_bytes.decode("utf-8"))
    refs = data.get("referencedRegulations", [])

    citations = []
    for ref in refs:
        text = ref.get("text", "")
        if not text:
            continue

        journal_year = ref.get("journalYear")
        journal_entry = ref.get("journalEntry")

        target = CitationTarget(jurisdiction="PL")
        target_ext_id = ""
        if journal_year and journal_entry:
            target_ext_id = f"DU/{journal_year}/{journal_entry}"
            target.external_id = target_ext_id

        from_node_id = "root"
        to_anchor = ""

        cit_str = f"{from_node_id}|{to_anchor}|{text}|{target_ext_id}"
        cit_uid = hashlib.sha256(cit_str.encode("utf-8")).hexdigest()

        _id = f"{doc_uid}|{source_hash}|cit:{cit_uid}"

        cit = Citation(
            _id=_id,
            doc_uid=doc_uid,
            source_hash=source_hash,
            from_node_id=from_node_id,
            raw_citation_text=text,
            target=target,
            confidence=1.0,
        )
        citations.append(cit)

    return citations
