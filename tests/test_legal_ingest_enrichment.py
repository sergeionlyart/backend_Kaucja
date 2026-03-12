from __future__ import annotations

from datetime import datetime, timezone

from legal_ingest.enrichment import build_section5_enrichment


def test_build_section5_enrichment_for_official_act() -> None:
    document = {
        "doc_uid": "eli_pl:DU/1964/296",
        "source_system": "eli_pl",
        "doc_type": "STATUTE",
        "title": "Kodeks postepowania cywilnego",
        "updated_at": datetime(2026, 3, 7, tzinfo=timezone.utc),
    }

    enrichment = build_section5_enrichment(
        document=document,
        current_source=None,
        document_kind="STATUTE",
        status="canonical",
        legal_role="PROCESS_NORM",
        canonical_title="Kodeks postepowania cywilnego",
        source_url="https://eli.gov.pl/api/acts/DU/1964/296/text/U/D19640296Lj.pdf",
        external_id="eli:DU/1964/296",
        act_id="eli:DU/1964/296",
        act_short_name="Kodeks postepowania cywilnego",
        canonical_doc_uid="eli_pl:DU/1964/296",
        duplicate_owner_doc_uid=None,
        same_case_group_id=None,
    )

    assert enrichment["title_short"] == "Kodeks postepowania cywilnego"
    assert enrichment["issue_tags"] == ["act", "civil_procedure"]
    assert enrichment["summary_1line"] == (
        "Normative corpus record: Kodeks postepowania cywilnego."
    )
    assert enrichment["relevance_score"] == 100
    assert enrichment["is_search_page"] is False


def test_build_section5_enrichment_for_saos_case() -> None:
    document = {
        "doc_uid": "saos_pl:10138",
        "source_system": "saos_pl",
        "doc_type": "CASELAW",
        "title": "SENTENCE II Ca 34/13 (COMMON)",
        "date_decision": "2013-03-19",
        "updated_at": datetime(2026, 3, 7, tzinfo=timezone.utc),
    }

    enrichment = build_section5_enrichment(
        document=document,
        current_source=None,
        document_kind="CASELAW",
        status="active",
        legal_role="GENERAL_CASELAW",
        canonical_title="SENTENCE II Ca 34/13 (COMMON)",
        source_url="https://www.saos.org.pl/",
        external_id="saos:10138",
        act_id=None,
        act_short_name=None,
        canonical_doc_uid=None,
        duplicate_owner_doc_uid=None,
        same_case_group_id=None,
    )

    assert enrichment["title_short"] == "II CA 34/13"
    assert enrichment["case_signature"] == "II CA 34/13"
    assert enrichment["judgment_date"] == "2013-03-19"
    assert enrichment["court_name"] == "Sad powszechny (SAOS)"
    assert enrichment["court_level"] == "common_court"
    assert enrichment["artifact_type"] == "judgment"
    assert enrichment["same_case_group_id"].startswith("same_case:singleton:")


def test_build_section5_enrichment_for_portal_mirror() -> None:
    document = {
        "doc_uid": "courts_pl:urlsha:20c9c82554a6e7f2",
        "source_system": "courts_pl",
        "doc_type": "CASELAW",
        "title": "Wyrok I Ca 56/18",
        "pageindex_tree": [
            {
                "title": "Root Document",
                "nodes": [
                    {
                        "title": (
                            "I Ca 56/18 - wyrok z uzasadnieniem "
                            "Sad Okregowy we Wloclawku z 2018-05-08"
                        ),
                        "nodes": [],
                    }
                ],
            }
        ],
        "updated_at": datetime(2026, 3, 7, tzinfo=timezone.utc),
    }

    enrichment = build_section5_enrichment(
        document=document,
        current_source=None,
        document_kind="CASELAW",
        status="alias",
        legal_role="SECONDARY_SOURCE",
        canonical_title="Wyrok I Ca 56/18",
        source_url=(
            "https://orzeczenia.wloclawek.so.gov.pl/content/"
            "$N/151030000000503_I_Ca_000056_2018_Uz_2018-05-08_001"
        ),
        external_id="case:I Ca 56/18",
        act_id=None,
        act_short_name=None,
        canonical_doc_uid="saos_pl:360096",
        duplicate_owner_doc_uid="saos_pl:360096",
        same_case_group_id="same_case:i_ca_56_18",
    )

    assert enrichment["case_signature"] == "I CA 56/18"
    assert enrichment["court_name"] == "Sad Okregowy we Wloclawku"
    assert enrichment["court_level"] == "regional"
    assert enrichment["artifact_type"] == "judgment_with_reasons"
    assert enrichment["holding_1line"].startswith("Secondary corpus record")
    assert enrichment["superseded_by"] == "saos_pl:360096"


def test_build_section5_enrichment_uses_page_text_for_dates_and_court_name() -> None:
    document = {
        "doc_uid": "uokik_pl:urlsha:5efe92f726049194",
        "source_system": "uokik_pl",
        "doc_type": "CASELAW",
        "title": "AmC 86/2003",
        "pageindex_tree": [
            {"title": "Root Document", "nodes": [{"title": "WYROK", "nodes": []}]}
        ],
        "_source_text_blob": (
            "Sygn. akt XVII Amc 86/03 WYROK W IMIENIU RZECZYPOSPOLITEJ POLSKIEJ "
            "Dnia 18 maja 2005 r. Sąd Okręgowy w Warszawie , "
            "Sąd Ochrony Konkurencji i Konsumentów w składzie:"
        ),
        "updated_at": datetime(2026, 3, 7, tzinfo=timezone.utc),
    }

    enrichment = build_section5_enrichment(
        document=document,
        current_source=None,
        document_kind="CASELAW",
        status="excluded",
        legal_role="INVENTORY_ONLY",
        canonical_title="AmC 86/2003",
        source_url="https://rejestr.uokik.gov.pl/uzasadnienia/891/AmC%20_86_2003.pdf",
        external_id="case:AmC 86/03",
        act_id=None,
        act_short_name=None,
        canonical_doc_uid=None,
        duplicate_owner_doc_uid=None,
        same_case_group_id=None,
    )

    assert enrichment["judgment_date"] == "2005-05-18"
    assert enrichment["court_name"] == (
        "Sąd Okręgowy w Warszawie, Sąd Ochrony Konkurencji i Konsumentów"
    )
    assert enrichment["court_level"] == "regional"


def test_build_section5_enrichment_applies_curated_required_runtime_override() -> None:
    document = {
        "doc_uid": "saos_pl:171957",
        "source_system": "saos_pl",
        "doc_type": "CASELAW",
        "title": "Wyrok II Ca 886/14",
        "date_decision": "2015-05-13",
        "updated_at": datetime(2026, 3, 7, tzinfo=timezone.utc),
    }

    enrichment = build_section5_enrichment(
        document=document,
        current_source=None,
        document_kind="CASELAW",
        status="canonical",
        legal_role="FACTUAL_CASE",
        canonical_title="Wyrok II Ca 886/14",
        source_url="https://www.saos.org.pl/judgments/171957",
        external_id="saos:171957",
        act_id=None,
        act_short_name=None,
        canonical_doc_uid="saos_pl:171957",
        duplicate_owner_doc_uid=None,
        same_case_group_id=None,
    )

    assert enrichment["holding_1line"] == (
        "Under art. 6 ust. 4 u.o.p.l., the deposit should be returned within "
        "one month after vacating, after deducting only tenancy-based claims."
    )
    assert enrichment["facts_tags"] == [
        "deposit_return_deadline",
        "vacating_of_flat",
    ]
    assert enrichment["related_provisions"] == [
        "art. 6 ust. 4 ustawy o ochronie praw lokatorow"
    ]


def test_build_section5_enrichment_for_excluded_broken_inventory_record() -> None:
    document = {
        "doc_uid": "curia_eu:urlsha:broken",
        "source_system": "curia_eu",
        "doc_type": "CASELAW",
        "title": "C-488/11 Asbeek Brusse and Katarina de Man Garabito",
        "status": "excluded",
        "legal_role": "INVENTORY_ONLY",
        "exclusion_reason": (
            "Broken imported artifact retained for inventory only. "
            "Reasons: invalid checksum sentinel."
        ),
        "checksum_sha256": "ERROR",
        "storage_uri": "docs/curia_eu:urlsha:broken/raw/ERROR/original.bin",
        "updated_at": datetime(2026, 3, 7, tzinfo=timezone.utc),
    }

    enrichment = build_section5_enrichment(
        document=document,
        current_source=None,
        document_kind="CASELAW",
        status="excluded",
        legal_role="INVENTORY_ONLY",
        canonical_title="C-488/11 Asbeek Brusse and Katarina de Man Garabito",
        source_url="https://curia.europa.eu/juris/document/document.jsf?docid=137830&doclang=EN",
        external_id="curia:137830",
        act_id=None,
        act_short_name=None,
        canonical_doc_uid=None,
        duplicate_owner_doc_uid=None,
        same_case_group_id=None,
    )

    assert enrichment["summary_1line"].startswith(
        "Excluded inventory record retained for traceability"
    )
    assert "inventory_only" in enrichment["issue_tags"]
    assert enrichment["facts_tags"] == ["broken_artifact_inventory"]
    assert enrichment["superseded_by"] == "inventory_only"
