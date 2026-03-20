from __future__ import annotations

from legal_docs_pipeline.canonicalize import build_canonical_text
from legal_docs_pipeline.parser import ParsedMarkdownDocument
from legal_docs_pipeline.reader import ReadDocumentResult, TextStats


def test_canonicalize_eurlex_html_heavy_document_strips_markup() -> None:
    read_result = ReadDocumentResult(
        raw_markdown="",
        normalized_text="",
        normalized_text_sha256="raw-sha",
        title="Regulation",
        text_stats=TextStats(chars=120, lines=4, words=20),
    )
    parse_result = ParsedMarkdownDocument(
        doc_metadata={"original_source_system": "eurlex_eu"},
        content_markdown="""
<html><body>
<!-- comment -->
<div class="eli-container">
<div>Official Journal</div>
<h1>REGULATION (EC) No 861/2007</h1>
<div>Article 1</div>
<p>This Regulation establishes a European Small Claims Procedure.</p>
</div>
</body></html>
""".strip(),
        title="REGULATION (EC) No 861/2007",
        had_metadata_block=True,
        had_content_block=True,
        warnings=(),
    )

    canonical = build_canonical_text(
        file_name="eu_acts/28_eu_eurlex_eli_reg_2007_861_oj_eng.md",
        parse_result=parse_result,
        read_result=read_result,
    )

    assert canonical.strategy == "html_heavy_visible_text"
    assert "REGULATION (EC) No 861/2007" in canonical.canonical_text
    assert "Article 1" in canonical.canonical_text
    assert "Official Journal" not in canonical.canonical_text
    assert "<div" not in canonical.canonical_text
