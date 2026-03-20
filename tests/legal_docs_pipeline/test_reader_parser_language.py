from __future__ import annotations

from datetime import datetime, timezone
from pathlib import PurePosixPath

import pytest

from legal_docs_pipeline.language import HeuristicLanguageDetector
from legal_docs_pipeline.parser import LegalMarkdownParser, MarkdownParseError
from legal_docs_pipeline.reader import MarkdownReader, ReadDocumentError
from legal_docs_pipeline.scanner import DiscoveredDocument


def test_reader_normalizes_bom_html_and_text_stats(tmp_path) -> None:
    document_path = tmp_path / "doc.md"
    document_path.write_text(
        "\ufeff## Content\r\n\r\n<div>Art.&nbsp;6</div>\r\n\r\n\r\nUCHWAŁA\r\n",
        encoding="utf-8",
    )
    discovered = DiscoveredDocument(
        absolute_path=document_path,
        relative_path=PurePosixPath("doc.md"),
        file_name="doc.md",
        size_bytes=document_path.stat().st_size,
        modified_at=datetime.now(tz=timezone.utc),
        sha256_hex="sha256",
        top_level_dir="",
    )

    result = MarkdownReader().read(discovered)

    assert "\ufeff" not in result.raw_markdown
    assert "\r" not in result.raw_markdown
    assert "Art. 6" in result.normalized_text
    assert "UCHWAŁA" in result.normalized_text
    assert result.text_stats.lines >= 2


def test_reader_rejects_file_too_large(tmp_path) -> None:
    document_path = tmp_path / "big.md"
    document_path.write_text("0123456789ABCDEF", encoding="utf-8")
    discovered = DiscoveredDocument(
        absolute_path=document_path,
        relative_path=PurePosixPath("big.md"),
        file_name="big.md",
        size_bytes=document_path.stat().st_size,
        modified_at=datetime.now(tz=timezone.utc),
        sha256_hex="sha256",
        top_level_dir="",
    )

    reader = MarkdownReader(max_file_size_bytes=4)
    with pytest.raises(ReadDocumentError) as error:
        reader.read(discovered)

    assert error.value.code == "file_too_large"


def test_parser_extracts_metadata_and_content() -> None:
    normalized_text = (
        "## Metadata\n\n"
        "- Entry index: 1\n"
        "- Original source system: saos_pl\n"
        "- Canonical doc UID: saos_pl:123\n\n"
        "## Content\n\n"
        "# WYROK\n\nSygn. akt I C 1/20\n"
    )

    parsed = LegalMarkdownParser().parse(
        file_name="sample.md",
        normalized_text=normalized_text,
    )

    assert parsed.doc_metadata["entry_index"] == 1
    assert parsed.doc_metadata["original_source_system"] == "saos_pl"
    assert parsed.doc_metadata["canonical_doc_uid"] == "saos_pl:123"
    assert "Sygn. akt I C 1/20" in parsed.content_markdown
    assert parsed.title == "WYROK"


def test_parser_allows_service_readme_without_metadata() -> None:
    parsed = LegalMarkdownParser().parse(
        file_name="README.md",
        normalized_text="# cas_law_V_2.2 markdown export\n\nGenerated at: 2026-03-12\n",
    )

    assert "missing_metadata_block" in parsed.warnings
    assert parsed.had_content_block is False
    assert parsed.title == "cas_law_V_2.2 markdown export"


def test_parser_raises_on_missing_content_for_substantive_doc() -> None:
    with pytest.raises(MarkdownParseError) as error:
        LegalMarkdownParser().parse(
            file_name="substantive.md",
            normalized_text="## Metadata\n\n- Entry index: 1\n",
        )

    assert error.value.code == "parse_error"


@pytest.mark.parametrize(
    ("relative_path", "doc_metadata", "title", "normalized_text", "expected_language"),
    [
        (
            "pl_sn/doc.md",
            {"original_source_system": "saos_pl"},
            "WYROK",
            "Sygn. akt I C 1/20\nkaucja najmu lokatora",
            "pl",
        ),
        (
            "eu_acts/doc.md",
            {"original_source_system": "eurlex_eu"},
            "COUNCIL DIRECTIVE 93/13/EEC",
            "This entry is about consumer contracts and unfair terms.",
            "en",
        ),
        (
            "misc/doc.md",
            {},
            None,
            "12345\n%%%%\n",
            "und",
        ),
        (
            "pl_saos/search_snapshot.md",
            {"original_source_system": "saos_pl"},
            "SAOS Search Snapshot",
            (
                "Query URL: https://www.saos.org.pl/search?keywords=kaucja\n"
                "This entry is a search/discovery page, not a primary legal "
                "document.\n"
                "## Result Links\n"
                "- I C 1/20 - https://www.saos.org.pl/judgments/1\n"
            ),
            "en",
        ),
    ],
)
def test_language_detector_heuristics(
    relative_path: str,
    doc_metadata: dict[str, object],
    title: str | None,
    normalized_text: str,
    expected_language: str,
) -> None:
    result = HeuristicLanguageDetector().detect(
        normalized_text=normalized_text,
        doc_metadata=doc_metadata,
        relative_path=relative_path,
        title=title,
    )

    assert result.language_code == expected_language
