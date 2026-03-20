from __future__ import annotations

from legal_docs_pipeline.router import RoutingInput, RuleBasedDocumentRouter


def test_router_classifies_corpus_readme() -> None:
    router = RuleBasedDocumentRouter(router_version="1.0.0")

    result = router.route(
        RoutingInput(
            relative_path="README.md",
            file_name="README.md",
            title="Corpus README",
            metadata={},
            normalized_text="# markdown export\n\nGenerated at: 2026-03-16\n",
        )
    )

    assert result.document_family.value == "corpus_readme"
    assert result.prompt_profile.value == "skip_non_target"
    assert result.annotatable is False


def test_router_classifies_normative_act() -> None:
    router = RuleBasedDocumentRouter(router_version="1.0.0")

    result = router.route(
        RoutingInput(
            relative_path="eu_acts/25_eu_eurlex_eli_dir_1993_13_oj_eng.md",
            file_name="25_eu_eurlex_eli_dir_1993_13_oj_eng.md",
            title="COUNCIL DIRECTIVE 93/13/EEC",
            metadata={"original_source_system": "eurlex_eu"},
            normalized_text="## Content\n\nArticle 1\nConsumer contracts.\n",
        )
    )

    assert result.document_family.value == "normative_act"
    assert result.prompt_profile.value == "addon_normative"
    assert result.document_type_code == "eu_directive"


def test_router_classifies_judicial_decision() -> None:
    router = RuleBasedDocumentRouter(router_version="1.0.0")

    result = router.route(
        RoutingInput(
            relative_path="pl_cases/doc.md",
            file_name="doc.md",
            title="WYROK",
            metadata={"original_source_system": "saos_pl"},
            normalized_text="Sygn. akt I C 1/20\nWYROK\n",
        )
    )

    assert result.document_family.value == "judicial_decision"
    assert result.prompt_profile.value == "addon_case_law"
    assert result.annotatable is True
    assert result.document_type_code == "pl_judgment"


def test_router_classifies_discovery_reference() -> None:
    router = RuleBasedDocumentRouter(router_version="1.0.0")

    result = router.route(
        RoutingInput(
            relative_path="search/results.md",
            file_name="results.md",
            title="Relevant Links Snapshot",
            metadata={},
            normalized_text=(
                "This entry is a search/discovery page.\n"
                "Result Links\n"
                "https://example.com/1\nhttps://example.com/2\nhttps://example.com/3\n"
            ),
        )
    )

    assert result.document_family.value == "discovery_reference"
    assert result.prompt_profile.value == "addon_discovery"


def test_router_classifies_focused_normative_excerpt_with_metadata_urls() -> None:
    router = RuleBasedDocumentRouter(router_version="1.0.0")

    result = router.route(
        RoutingInput(
            relative_path="pl_acts/05_pl_lex_118.md",
            file_name="05_pl_lex_118.md",
            title="Focused Excerpt",
            metadata={
                "original_source_system": "lex_pl",
                "resolved_source_system": "isap_pl",
                "article_focus": "Art. 118.",
                "original_url": "https://sip.lex.pl/example/118",
                "resolved_url": "https://isap.sejm.gov.pl/example/118",
                "final_url": "https://isap.sejm.gov.pl/example/118.pdf",
            },
            normalized_text="\n".join(
                [
                    "## Metadata",
                    "",
                    "- Original source system: lex_pl",
                    "- Resolved source system: isap_pl",
                    "- Original URL: https://sip.lex.pl/example/118",
                    "- Resolved URL: https://isap.sejm.gov.pl/example/118",
                    "- Final URL: https://isap.sejm.gov.pl/example/118.pdf",
                    "- Article focus: Art. 118.",
                    "",
                    "## Content",
                    "",
                    "## Focused Excerpt",
                    "",
                    "Art. 118. Jeżeli przepis szczególny nie stanowi inaczej.",
                ]
            ),
        )
    )

    assert result.document_family.value == "normative_act"
    assert result.prompt_profile.value == "addon_normative"
    assert result.annotatable is True


def test_router_keeps_discovery_page_with_three_body_urls() -> None:
    router = RuleBasedDocumentRouter(router_version="1.0.0")

    result = router.route(
        RoutingInput(
            relative_path="search/discovery_results.md",
            file_name="discovery_results.md",
            title="Relevant Links Snapshot",
            metadata={"original_source_system": "lex_pl"},
            normalized_text="\n".join(
                [
                    "## Metadata",
                    "",
                    "- Original source system: lex_pl",
                    "",
                    "## Content",
                    "",
                    "This entry is a search/discovery page.",
                    "Result Links",
                    "https://example.com/1",
                    "https://example.com/2",
                    "https://example.com/3",
                ]
            ),
        )
    )

    assert result.document_family.value == "discovery_reference"
    assert result.prompt_profile.value == "addon_discovery"


def test_router_keeps_judicial_source_with_metadata_urls_out_of_discovery() -> None:
    router = RuleBasedDocumentRouter(router_version="1.0.0")

    result = router.route(
        RoutingInput(
            relative_path="pl_cases/saos_case_with_metadata_urls.md",
            file_name="saos_case_with_metadata_urls.md",
            title="WYROK",
            metadata={
                "original_source_system": "saos_pl",
                "original_url": "https://www.saos.org.pl/example/1",
                "resolved_url": "https://www.saos.org.pl/example/2",
                "final_url": "https://www.saos.org.pl/example/3",
            },
            normalized_text="\n".join(
                [
                    "## Metadata",
                    "",
                    "- Original source system: saos_pl",
                    "- Original URL: https://www.saos.org.pl/example/1",
                    "- Resolved URL: https://www.saos.org.pl/example/2",
                    "- Final URL: https://www.saos.org.pl/example/3",
                    "",
                    "## Content",
                    "",
                    "WYROK",
                    "Sygn. akt II Ca 886/14",
                ]
            ),
        )
    )

    assert result.document_family.value == "judicial_decision"
    assert result.prompt_profile.value == "addon_case_law"


def test_router_prefers_primary_wyrok_over_late_uchwala_quote() -> None:
    router = RuleBasedDocumentRouter(router_version="1.0.0")

    result = router.route(
        RoutingInput(
            relative_path="pl_sn/07_pl_sn_ii_csk_862_14.md",
            file_name="07_pl_sn_ii_csk_862_14.md",
            title="Sygn. akt II CSK 862/14",
            metadata={"original_source_system": "sn_pl"},
            normalized_text="\n".join(
                [
                    "## Metadata",
                    "",
                    "- Original source system: sn_pl",
                    "",
                    "## Content",
                    "",
                    "Sygn. akt II CSK 862/14",
                    "WYROK",
                    "W IMIENIU RZECZYPOSPOLITEJ POLSKIEJ",
                    "",
                    "Dalsza część uzasadnienia cytuje uchwała Sądu Najwyższego.",
                ]
            ),
        )
    )

    assert result.document_family.value == "judicial_decision"
    assert result.document_type_code == "pl_judgment"


def test_router_classifies_true_uchwala_as_resolution() -> None:
    router = RuleBasedDocumentRouter(router_version="1.0.0")

    result = router.route(
        RoutingInput(
            relative_path="pl_sn/uchwala.md",
            file_name="uchwala.md",
            title="UCHWAŁA",
            metadata={"original_source_system": "sn_pl"},
            normalized_text="\n".join(
                [
                    "## Content",
                    "",
                    "Sygn. akt III CZP 58/02",
                    "UCHWAŁA",
                    "Sąd Najwyższy rozstrzyga zagadnienie prawne.",
                ]
            ),
        )
    )

    assert result.document_family.value == "judicial_decision"
    assert result.document_type_code == "pl_resolution"


def test_router_classifies_true_postanowienie_as_order() -> None:
    router = RuleBasedDocumentRouter(router_version="1.0.0")

    result = router.route(
        RoutingInput(
            relative_path="pl_sn/postanowienie.md",
            file_name="postanowienie.md",
            title="POSTANOWIENIE",
            metadata={"original_source_system": "sn_pl"},
            normalized_text="\n".join(
                [
                    "## Content",
                    "",
                    "Sygn. akt I CNP 31/13",
                    "POSTANOWIENIE",
                    "Sąd Najwyższy odmawia przyjęcia skargi do rozpoznania.",
                ]
            ),
        )
    )

    assert result.document_family.value == "judicial_decision"
    assert result.document_type_code == "pl_order"


def test_router_returns_unknown_when_no_signals_match() -> None:
    router = RuleBasedDocumentRouter(router_version="1.0.0")

    result = router.route(
        RoutingInput(
            relative_path="misc/doc.md",
            file_name="doc.md",
            title=None,
            metadata={},
            normalized_text="12345\n%%%%\n",
        )
    )

    assert result.document_family.value == "unknown"
    assert result.skip_reason == "rule_router_no_match"
