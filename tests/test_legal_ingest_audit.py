from __future__ import annotations

from legal_ingest.audit import (
    build_required_presence_report,
    collect_broken_inventory_exemptions,
    compute_artifact_integrity,
    compute_baseline_metadata_validity,
    compute_section5_enrichment_coverage,
    compute_required_runtime_section5_placeholder_metrics,
    compute_section5_placeholder_metrics,
    find_canonical_invariant_violations,
    find_bad_titles,
    group_duplicate_final_urls,
    group_same_case_candidates,
)
from legal_ingest.normalization import BROKEN_ARTIFACT_EXCLUSION_REASON


def test_build_required_presence_report_detects_missing_and_noncanonical() -> None:
    documents = [
        {
            "doc_uid": "eurlex_eu:urlsha:252f802534879b95",
            "title": "C_2019323EN.01000401.xml",
            "source_urls": [
                "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?from=FR&uri=CELEX:52019XC0927(01)"
            ],
        },
        {
            "doc_uid": "sn_pl:III_CZP_58-02",
            "status": "canonical",
            "canonical_doc_uid": "sn_pl:III_CZP_58-02",
            "canonical_title": "Uchwala SN z dnia 26 wrzesnia 2002 r., III CZP 58/02",
            "source_urls": [
                "https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf"
            ],
        },
    ]
    required_entries = [
        {
            "entry_id": "commission-notice",
            "canonical_title": "Commission Notice",
            "canonical_doc_uid": "eurlex_eu:celex:52019XC0927(01)",
            "status": "canonical",
            "notes": "Must be present.",
            "match_doc_uids": [
                "eurlex_eu:celex:52019XC0927(01)",
                "eurlex_eu:urlsha:252f802534879b95",
            ],
            "match_source_urls": [
                "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?from=FR&uri=CELEX:52019XC0927(01)"
            ],
        },
        {
            "entry_id": "kpc",
            "canonical_title": "Kodeks postepowania cywilnego",
            "canonical_doc_uid": None,
            "status": "missing_fetch",
            "notes": "Mandatory fetch.",
            "match_doc_uids": [],
            "match_source_urls": [],
        },
        {
            "entry_id": "iii-czp-58-02",
            "canonical_title": "Uchwala SN z dnia 26 wrzesnia 2002 r., III CZP 58/02",
            "canonical_doc_uid": "sn_pl:III_CZP_58-02",
            "status": "canonical",
            "notes": "Already canonical.",
            "source_url": "https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf",
            "match_doc_uids": ["sn_pl:III_CZP_58-02"],
            "match_source_urls": [],
        },
    ]

    report = build_required_presence_report(documents, required_entries)

    assert [item["canonical_title"] for item in report["missing"]] == [
        "Kodeks postepowania cywilnego"
    ]
    assert [item["canonical_title"] for item in report["present_canonical"]] == [
        "Uchwala SN z dnia 26 wrzesnia 2002 r., III CZP 58/02"
    ]
    assert [item["canonical_title"] for item in report["present_noncanonical"]] == [
        "Commission Notice"
    ]


def test_group_duplicate_final_urls_groups_by_normalized_final_url() -> None:
    document_sources = [
        {
            "doc_uid": "eurlex_eu:dir/1993/13/oj/eng",
            "final_url": "https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng",
            "source_hash": "hash-a",
        },
        {
            "doc_uid": "eurlex_eu:urlsha:8f4d90b5081ec765",
            "final_url": "https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng",
            "source_hash": "hash-b",
        },
        {
            "doc_uid": "courts_pl:urlsha:20c9c82554a6e7f2",
            "final_url": "https://orzeczenia.wloclawek.so.gov.pl/content/$N/151030000000503_I_Ca_000056_2018_Uz_2018-05-08_001",
            "source_hash": "hash-c",
        },
        {
            "doc_uid": "courts_pl:urlsha:20c9c82554a6e7f2",
            "final_url": "https://orzeczenia.wloclawek.so.gov.pl/content/$N/151030000000503_I_Ca_000056_2018_Uz_2018-05-08_001",
            "source_hash": "hash-d",
        },
    ]

    groups = group_duplicate_final_urls(document_sources)

    assert len(groups) == 2
    assert groups[0]["kind"] == "multi_doc_duplicate"
    assert groups[0]["distinct_doc_uids"] == [
        "eurlex_eu:dir/1993/13/oj/eng",
        "eurlex_eu:urlsha:8f4d90b5081ec765",
    ]
    assert groups[1]["kind"] == "reingest_same_doc"
    assert groups[1]["distinct_doc_uids"] == ["courts_pl:urlsha:20c9c82554a6e7f2"]


def test_group_same_case_candidates_matches_saos_and_portal_documents() -> None:
    documents = [
        {
            "doc_uid": "saos_pl:385394",
            "source_system": "saos_pl",
            "title": "REASONS III Ca 1707/18 (COMMON)",
            "source_urls": ["https://www.saos.org.pl/"],
            "same_case_group_id": "same_case:iii_ca_1707_18",
        },
        {
            "doc_uid": "courts_pl:urlsha:74cfe0dfc8b4592a",
            "source_system": "courts_pl",
            "title": "Tresc orzeczenia III Ca 1707/18 - Portal Orzeczen Sadow Powszechnych",
            "source_urls": [
                "https://orzeczenia.ms.gov.pl/content/$N/152510000001503_III_Ca_001707_2018_Uz_2019-02-28_001"
            ],
            "same_case_group_id": "same_case:iii_ca_1707_18",
        },
        {
            "doc_uid": "saos_pl:171957",
            "source_system": "saos_pl",
            "title": "REASONS II Ca 886/14 (COMMON)",
            "source_urls": ["https://www.saos.org.pl/judgments/171957"],
        },
    ]

    groups = group_same_case_candidates(documents)

    assert len(groups) == 1
    assert groups[0]["case_signature"] == "III CA 1707/18"
    assert groups[0]["doc_uids"] == [
        "courts_pl:urlsha:74cfe0dfc8b4592a",
        "saos_pl:385394",
    ]
    assert groups[0]["same_case_group_ids"] == [
        "same_case:iii_ca_1707_18",
        "same_case:iii_ca_1707_18",
    ]
    assert groups[0]["all_members_have_same_case_group_id"] is True
    assert groups[0]["group_id_consistent"] is True


def test_find_bad_titles_flags_section7_documents() -> None:
    documents = [
        {
            "doc_uid": "sn_pl:V_CSK_480-18",
            "title": "SN",
            "source_system": "sn_pl",
        },
        {
            "doc_uid": "curia_eu:urlsha:54acc341b17f3a57",
            "title": "RPEX",
            "source_system": "curia_eu",
        },
        {
            "doc_uid": "uokik_pl:urlsha:5efe92f726049194",
            "title": "WYROK W IMIENIU RZECZYPOSPOLITEJ POLSKIEJ",
            "source_system": "uokik_pl",
        },
    ]

    findings = find_bad_titles(documents)

    assert [item["doc_uid"] for item in findings] == [
        "curia_eu:urlsha:54acc341b17f3a57",
        "sn_pl:V_CSK_480-18",
        "uokik_pl:urlsha:5efe92f726049194",
    ]
    assert findings[0]["expected_title"] == (
        "C-488/11 Asbeek Brusse and Katarina de Man Garabito"
    )
    assert findings[2]["issue_type"] == "excluded_candidate"


def test_find_bad_titles_ignores_normalized_excluded_candidate() -> None:
    documents = [
        {
            "doc_uid": "uokik_pl:urlsha:5efe92f726049194",
            "title": "AmC 86/2003",
            "canonical_title": "AmC 86/2003",
            "status": "excluded",
            "exclusion_reason": "Inventory-only excluded record.",
            "source_system": "uokik_pl",
        }
    ]

    findings = find_bad_titles(documents)

    assert findings == []


def test_find_canonical_invariant_violations_flags_null_doc_uid() -> None:
    documents = [
        {
            "doc_uid": "sn_pl:III_CZP_58-02",
            "status": "canonical",
            "canonical_doc_uid": None,
            "title": "Uchwala SN III CZP 58/02",
        },
        {
            "doc_uid": "saos_pl:171957",
            "status": "canonical",
            "canonical_doc_uid": "saos_pl:171957",
            "title": "Wyrok II Ca 886/14",
        },
        {
            "doc_uid": "courts_pl:urlsha:20c9c82554a6e7f2",
            "status": "alias",
            "canonical_doc_uid": "saos_pl:360096",
            "title": "Wyrok I Ca 56/18",
        },
    ]

    violations = find_canonical_invariant_violations(documents)

    assert violations == [
        {
            "doc_uid": "sn_pl:III_CZP_58-02",
            "title": "Uchwala SN III CZP 58/02",
            "status": "canonical",
        }
    ]


def test_baseline_validity_rejects_error_checksum() -> None:
    documents = [
        {
            "doc_uid": "eurlex_eu:urlsha:broken",
            "status": "active",
            "document_kind": "CASELAW",
            "legal_role": "OPTIONAL_EU",
            "source_tier": "official",
            "canonical_title": "EUR-Lex document celex:62011CJ0415",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415",
            "normalized_source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415",
            "external_id": "celex:62011CJ0415",
            "checksum_sha256": "ERROR",
            "storage_uri": "docs/eurlex_eu:urlsha:broken/raw/ERROR/original.bin",
        }
    ]

    validity = compute_baseline_metadata_validity(documents)
    integrity = compute_artifact_integrity(documents)

    assert validity["valid_documents"] == 0
    assert validity["field_invalid_counts"]["checksum_sha256"] == 1
    assert integrity["total_invalid_checksum"] == 1


def test_artifact_integrity_rejects_synthetic_and_nonexistent_storage_uri() -> None:
    documents = [
        {
            "doc_uid": "eurlex_eu:urlsha:synthetic",
            "status": "active",
            "document_kind": "GUIDANCE",
            "legal_role": "GUIDANCE",
            "source_tier": "official",
            "canonical_title": "Synthetic storage",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019H1128(01)",
            "normalized_source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019H1128(01)",
            "external_id": "celex:32019H1128(01)",
            "checksum_sha256": "a" * 64,
            "storage_uri": "document_sources:eurlex_eu:urlsha:synthetic:ERROR",
        },
        {
            "doc_uid": "eurlex_eu:urlsha:missing-path",
            "status": "active",
            "document_kind": "GUIDANCE",
            "legal_role": "GUIDANCE",
            "source_tier": "official",
            "canonical_title": "Missing path",
            "source_url": "https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng",
            "normalized_source_url": "https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng",
            "external_id": "eli:dir/1993/13/oj/eng",
            "checksum_sha256": "b" * 64,
            "storage_uri": "/definitely/missing/artifact.bin",
        },
    ]

    validity = compute_baseline_metadata_validity(documents)
    integrity = compute_artifact_integrity(documents)

    assert validity["valid_documents"] == 0
    assert validity["field_invalid_counts"]["storage_uri"] == 2
    assert integrity["total_invalid_storage_uri"] == 2
    assert integrity["affected_doc_uids"] == [
        "eurlex_eu:urlsha:missing-path",
        "eurlex_eu:urlsha:synthetic",
    ]


def test_broken_inventory_record_is_invalid_in_all_docs_but_exempt_operationally() -> (
    None
):
    documents = [
        {
            "doc_uid": "curia_eu:urlsha:broken",
            "status": "excluded",
            "document_kind": "GUIDANCE",
            "legal_role": "INVENTORY_ONLY",
            "source_tier": "official",
            "canonical_title": "Curia fact sheet on unfair terms",
            "source_url": "https://curia.europa.eu/jcms/jcms/p1_4220451/en/",
            "normalized_source_url": "https://curia.europa.eu/jcms/jcms/p1_4220451/en/",
            "external_id": "curia:jcms:p1_4220451",
            "checksum_sha256": "ERROR",
            "storage_uri": "docs/curia_eu:urlsha:broken/raw/ERROR/original.bin",
            "exclusion_reason": (
                f"{BROKEN_ARTIFACT_EXCLUSION_REASON} Reasons: invalid checksum sentinel."
            ),
        }
    ]

    all_docs_validity = compute_baseline_metadata_validity(
        documents,
        include_broken_inventory=True,
    )
    operational_validity = compute_baseline_metadata_validity(
        documents,
        include_broken_inventory=False,
    )
    all_docs_integrity = compute_artifact_integrity(
        documents,
        include_broken_inventory=True,
    )
    operational_integrity = compute_artifact_integrity(
        documents,
        include_broken_inventory=False,
    )
    exemptions = collect_broken_inventory_exemptions(documents)

    assert all_docs_validity["valid_documents"] == 0
    assert all_docs_validity["invalid_documents"] == 1
    assert operational_validity["valid_documents"] == 0
    assert operational_validity["total_documents"] == 0
    assert all_docs_integrity["invalid_documents"] == 1
    assert operational_integrity["invalid_documents"] == 0
    assert exemptions["count"] == 1
    assert exemptions["doc_uids"] == ["curia_eu:urlsha:broken"]
    assert exemptions["reasons"]["curia_eu:urlsha:broken"] == [
        "broken imported artifact path",
        "invalid checksum sentinel",
        "nonexistent storage path",
    ]


def test_operational_metrics_exclude_broken_inventory_from_denominator() -> None:
    documents = [
        {
            "doc_uid": "saos_pl:10138",
            "status": "active",
            "document_kind": "CASELAW",
            "legal_role": "GENERAL_CASELAW",
            "source_tier": "saos",
            "canonical_title": "SENTENCE II Ca 34/13 (COMMON)",
            "source_url": "https://www.saos.org.pl/",
            "normalized_source_url": "https://www.saos.org.pl/",
            "external_id": "saos:10138",
            "checksum_sha256": "a" * 64,
            "storage_uri": "artifacts/corpus/legal/saos_pl:10138/source.json",
        },
        {
            "doc_uid": "curia_eu:urlsha:broken",
            "status": "excluded",
            "document_kind": "GUIDANCE",
            "legal_role": "INVENTORY_ONLY",
            "source_tier": "official",
            "canonical_title": "Curia fact sheet on unfair terms",
            "source_url": "https://curia.europa.eu/jcms/jcms/p1_4220451/en/",
            "normalized_source_url": "https://curia.europa.eu/jcms/jcms/p1_4220451/en/",
            "external_id": "curia:jcms:p1_4220451",
            "checksum_sha256": "ERROR",
            "storage_uri": "docs/curia_eu:urlsha:broken/raw/ERROR/original.bin",
            "exclusion_reason": (
                f"{BROKEN_ARTIFACT_EXCLUSION_REASON} Reasons: invalid checksum sentinel."
            ),
        },
    ]

    all_docs_validity = compute_baseline_metadata_validity(
        documents,
        include_broken_inventory=True,
    )
    operational_validity = compute_baseline_metadata_validity(
        documents,
        include_broken_inventory=False,
    )

    assert all_docs_validity["valid_documents"] == 1
    assert all_docs_validity["total_documents"] == 2
    assert operational_validity["valid_documents"] == 1
    assert operational_validity["total_documents"] == 1


def test_section5_enrichment_coverage_counts_all_and_caselaw_fields() -> None:
    documents = [
        {
            "doc_uid": "eli_pl:DU/1964/296",
            "title_short": "Kodeks postepowania cywilnego",
            "summary_1line": "Normative corpus record: Kodeks postepowania cywilnego.",
            "issue_tags": ["act", "civil_procedure"],
            "relevance_score": 100,
            "search_terms_positive": ["Kodeks postepowania cywilnego"],
            "search_terms_negative": ["error"],
            "query_templates": ["Kodeks postepowania cywilnego"],
            "last_verified_at": "2026-03-07T00:00:00+00:00",
            "document_kind": "STATUTE",
        },
        {
            "doc_uid": "saos_pl:10138",
            "title_short": "II CA 34/13",
            "summary_1line": "Caselaw corpus record: II CA 34/13.",
            "issue_tags": ["caselaw"],
            "relevance_score": 80,
            "search_terms_positive": ["II CA 34/13"],
            "search_terms_negative": ["error"],
            "query_templates": ["II CA 34/13"],
            "last_verified_at": "2026-03-07T00:00:00+00:00",
            "document_kind": "CASELAW",
            "doc_type": "CASELAW",
            "case_signature": "II CA 34/13",
            "judgment_date": "2013-03-19",
            "court_name": "Sad powszechny (SAOS)",
            "court_level": "common_court",
            "artifact_type": "judgment",
            "holding_1line": "Rule-based placeholder for II CA 34/13.",
            "facts_tags": ["facts_not_extracted"],
            "related_provisions": ["not_determined"],
        },
    ]

    coverage = compute_section5_enrichment_coverage(documents)

    assert coverage["all_documents"]["covered_documents"] == 2
    assert coverage["caselaw_documents"]["covered_documents"] == 1


def test_section5_placeholder_metrics_distinguish_raw_and_avoidable_unknown_dates() -> (
    None
):
    documents = [
        {
            "doc_uid": "saos_pl:171957",
            "document_kind": "CASELAW",
            "holding_1line": "Rule-based placeholder for II CA 886/14.",
            "facts_tags": ["facts_not_extracted"],
            "related_provisions": ["not_determined"],
            "judgment_date": "unknown",
            "court_name": "Court not identified from source",
            "title": "Wyrok II Ca 886/14",
            "source_urls": ["https://www.saos.org.pl/judgments/171957"],
            "_source_text_blob": (
                "Sygn. akt II Ca 886/14 Dnia 13 maja 2015 r. Sad Okregowy w Siedlcach"
            ),
        },
        {
            "doc_uid": "curia_eu:urlsha:54acc341b17f3a57",
            "document_kind": "CASELAW",
            "holding_1line": "Holding from tracked legal notes.",
            "facts_tags": ["consumer_unfair_terms"],
            "related_provisions": ["Directive 93/13/EEC art. 6"],
            "judgment_date": "unknown",
            "court_name": "Court of Justice of the European Union",
            "title": "C-488/11 Asbeek Brusse and Katarina de Man Garabito",
            "source_urls": [
                "https://curia.europa.eu/juris/document/document.jsf?docid=137830&doclang=EN"
            ],
            "_source_text_blob": "RPEX",
        },
    ]

    metrics = compute_section5_placeholder_metrics(documents)

    assert metrics["total_documents"] == 2
    assert metrics["caselaw_documents"] == 2
    assert metrics["placeholder_holding_1line"]["doc_uids"] == ["saos_pl:171957"]
    assert metrics["fallback_facts_tags"]["doc_uids"] == ["saos_pl:171957"]
    assert metrics["fallback_related_provisions"]["doc_uids"] == ["saos_pl:171957"]
    assert metrics["judgment_date_unknown_total"]["doc_uids"] == [
        "curia_eu:urlsha:54acc341b17f3a57",
        "saos_pl:171957",
    ]
    assert metrics["judgment_date_unknown_avoidable"]["doc_uids"] == ["saos_pl:171957"]
    assert metrics["judgment_date_unknown_unavoidable"]["doc_uids"] == [
        "curia_eu:urlsha:54acc341b17f3a57"
    ]
    assert metrics["unresolved_court_name"]["doc_uids"] == ["saos_pl:171957"]


def test_required_runtime_placeholder_metrics_track_required_caselaw_slice() -> None:
    documents = [
        {
            "doc_uid": "saos_pl:171957",
            "document_kind": "CASELAW",
            "holding_1line": "Concrete holding.",
            "facts_tags": ["deposit_return_deadline"],
            "related_provisions": ["art. 6 ust. 4 ustawy o ochronie praw lokatorow"],
            "judgment_date": "2015-05-13",
            "court_name": "Sad Okregowy w Siedlcach",
        },
        {
            "doc_uid": "curia_eu:urlsha:54acc341b17f3a57",
            "document_kind": "CASELAW",
            "holding_1line": "Directive 93/13 applies to residential tenancy.",
            "facts_tags": ["consumer_unfair_terms"],
            "related_provisions": ["Directive 93/13/EEC art. 6"],
            "judgment_date": "unknown",
            "court_name": "Court of Justice of the European Union",
            "_source_text_blob": "RPEX",
        },
    ]
    required_entries = [
        {
            "entry_id": "position-12",
            "document_kind": "CASELAW",
            "canonical_doc_uid": "saos_pl:171957",
        },
        {
            "entry_id": "position-31",
            "document_kind": "CASELAW",
            "canonical_doc_uid": "curia_eu:urlsha:54acc341b17f3a57",
        },
    ]

    metrics = compute_required_runtime_section5_placeholder_metrics(
        documents,
        required_entries,
    )

    assert metrics["expected_doc_uids"] == [
        "curia_eu:urlsha:54acc341b17f3a57",
        "saos_pl:171957",
    ]
    assert metrics["missing_doc_uids"] == []
    assert metrics["placeholder_holding_1line"]["count"] == 0
    assert metrics["fallback_facts_tags"]["count"] == 0
    assert metrics["fallback_related_provisions"]["count"] == 0
    assert metrics["judgment_date_unknown_total"]["count"] == 1
    assert metrics["judgment_date_unknown_avoidable"]["count"] == 0
    assert metrics["unresolved_court_name"]["count"] == 0
