from __future__ import annotations

from app.pipeline.pack_documents import DocumentMarkdown, pack_documents


def test_pack_documents_preserves_placeholders_and_structure() -> None:
    payload = pack_documents(
        [
            DocumentMarkdown(
                doc_id="0000001",
                markdown="Text [tbl-0.html](tbl-0.html) ![img-0.png](img-0.png)",
            ),
            DocumentMarkdown(
                doc_id="0000002",
                markdown="Second document",
            ),
        ]
    )

    assert payload.startswith("<BEGIN_DOCUMENTS>\n")
    assert '<DOC_START id="0000001">' in payload
    assert "[tbl-0.html](tbl-0.html)" in payload
    assert "![img-0.png](img-0.png)" in payload
    assert payload.endswith("<END_DOCUMENTS>")
