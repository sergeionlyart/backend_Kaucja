from __future__ import annotations

from legal_ingest.normalization import (
    build_curated_entry_indexes,
    build_duplicate_group_report,
    derive_act_id,
    infer_document_kind,
)


def test_build_curated_entry_indexes_prefers_required_canonical_entry() -> None:
    payload = {
        "positions": [
            {
                "entry_id": "position-1",
                "position": 1,
                "source_url": "https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf",
                "source_doc_uid": "eli_pl:DU/2001/733",
                "status": "optional",
                "canonical_title": "Archive title",
                "canonical_doc_uid": None,
                "document_kind": "STATUTE",
                "legal_role": "DIRECT_NORM_ARCHIVE",
                "expected_external_id": "eli:DU/2001/733",
                "required_top_level": False,
                "notes": "archive",
            }
        ],
        "derived_runtime_targets": [
            {
                "entry_id": "runtime-current-lokatorzy-act",
                "position": None,
                "source_url": "https://eli.gov.pl/api/acts/DU/2001/733/text/U/D20010733Lj.pdf",
                "source_doc_uid": "eli_pl:DU/2001/733",
                "status": "canonical",
                "canonical_title": "Current title",
                "canonical_doc_uid": "eli_pl:DU/2001/733",
                "document_kind": "STATUTE",
                "legal_role": "DIRECT_NORM",
                "expected_external_id": "eli:DU/2001/733",
                "required_top_level": True,
                "notes": "runtime",
            }
        ],
        "required_additions": [],
    }

    by_doc_uid, _ = build_curated_entry_indexes(payload)

    assert (
        by_doc_uid["eli_pl:DU/2001/733"]["entry_id"] == "runtime-current-lokatorzy-act"
    )
    assert by_doc_uid["eli_pl:DU/2001/733"]["status"] == "canonical"


def test_build_duplicate_group_report_distinguishes_resolved_and_unresolved() -> None:
    documents = [
        {
            "doc_uid": "sn_pl:III_CZP_58-02",
            "duplicate_role": "owner",
            "duplicate_group_id": "duplicate:sn_pl:III_CZP_58-02",
            "duplicate_owner_doc_uid": "sn_pl:III_CZP_58-02",
            "status": "canonical",
        },
        {
            "doc_uid": "sn_pl:urlsha:c37d660f070b6362",
            "duplicate_role": "alias",
            "duplicate_group_id": "duplicate:sn_pl:III_CZP_58-02",
            "duplicate_owner_doc_uid": "sn_pl:III_CZP_58-02",
            "status": "alias",
        },
        {
            "doc_uid": "eli_pl:DU/2001/733",
            "status": "canonical",
        },
        {
            "doc_uid": "eli_pl:urlsha:8b1bb9b48a8ca9ec",
            "status": "active",
        },
    ]
    document_sources = [
        {
            "doc_uid": "sn_pl:III_CZP_58-02",
            "final_url": "https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf",
            "source_hash": "hash-a",
        },
        {
            "doc_uid": "sn_pl:urlsha:c37d660f070b6362",
            "final_url": "https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf",
            "source_hash": "hash-b",
        },
        {
            "doc_uid": "eli_pl:DU/2001/733",
            "final_url": "https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf",
            "source_hash": "hash-c",
        },
        {
            "doc_uid": "eli_pl:urlsha:8b1bb9b48a8ca9ec",
            "final_url": "https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf",
            "source_hash": "hash-d",
        },
    ]

    groups = build_duplicate_group_report(documents, document_sources)

    assert len(groups) == 2
    assert groups[0]["resolved"] is False
    assert groups[1]["resolved"] is True
    assert groups[1]["owner_doc_uid"] == "sn_pl:III_CZP_58-02"


def test_infer_document_kind_keeps_article_node_docs_out_of_act_layer() -> None:
    document = {
        "doc_uid": "lex_pl:urlsha:4f0332a0f08cee51",
        "doc_type": "STATUTE",
    }
    curated_entry = {
        "status": "article_node",
        "document_kind": "STATUTE",
    }

    assert infer_document_kind(document, curated_entry) == "STATUTE_REF"


def test_derive_act_id_maps_lex_landing_page_to_official_act() -> None:
    document = {
        "doc_uid": "lex_pl:urlsha:2c175d980032d2be",
        "doc_type": "STATUTE",
        "source_urls": [
            "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658"
        ],
    }

    assert derive_act_id(document) == "eli:DU/2001/733"
