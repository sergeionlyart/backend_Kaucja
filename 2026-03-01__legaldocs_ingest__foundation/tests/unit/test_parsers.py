from legal_ingest.parsers.html import parse_html
from legal_ingest.config import HtmlParserConfig


def test_parse_html():
    cfg = HtmlParserConfig(max_tokens_per_virtual_page=100)
    html = b"<html><body><h1>Title</h1><p>Paragraph 1</p><h2>Section</h2><p>Part 2</p></body></html>"

    pages = parse_html(html, "doc1", "hash1", cfg)

    assert len(pages) == 2
    assert "Title" in pages[0].text
    assert "Section" in pages[1].text
