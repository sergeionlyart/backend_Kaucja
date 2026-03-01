from legal_ingest.config import load_config
import os


TECHSPEC_MAPPING = {
    "pl_eli_du_2001_733": {
        "url": "https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf",
        "fetch_strategy": "direct",
        "doc_type_hint": "STATUTE",
        "jurisdiction": "PL",
        "language": "pl",
        "external_ids": {"eli": "DU/2001/733"},
    },
    "pl_isap_wdu19640160093": {
        "url": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf",
        "fetch_strategy": "direct",
        "doc_type_hint": "STATUTE",
        "jurisdiction": "PL",
        "language": "pl",
        "external_ids": {"isap_wdu": "WDU19640160093"},
    },
    "pl_lex_ochrona_praw_lokatorow": {
        "url": "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658",
        "fetch_strategy": "direct",
        "doc_type_hint": "STATUTE_REF",
        "jurisdiction": "PL",
        "language": "pl",
        "license_tag": "COMMERCIAL",
    },
    "pl_lex_art_19a": {
        "url": "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658/art-19-a",
        "fetch_strategy": "direct",
        "doc_type_hint": "STATUTE_REF",
        "jurisdiction": "PL",
        "language": "pl",
        "license_tag": "COMMERCIAL",
    },
    "pl_lex_kc_art_118": {
        "url": "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/kodeks-cywilny-16785996/art-118",
        "fetch_strategy": "direct",
        "doc_type_hint": "STATUTE_REF",
        "jurisdiction": "PL",
        "language": "pl",
        "license_tag": "COMMERCIAL",
        # In TS: no external_ids? TS doesn't show external_ids for kc_art_118, but wait:
        # In the original TS:  it just doesn't show it for pl_lex_kc_art_118.
    },
    "pl_sn_III_CZP_58-02": {
        "url": "https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf",
        "fetch_strategy": "direct",
        "doc_type_hint": "CASELAW",
        "jurisdiction": "PL",
        "language": "pl",
        "external_ids": {"sn_signature": "III CZP 58/02"},
    },
    "pl_sn_II_CSK_862-14": {
        "url": "https://www.sn.pl/sites/orzecznictwo/orzeczenia3/ii%20csk%20862-14-1.pdf",
        "fetch_strategy": "direct",
        "doc_type_hint": "CASELAW",
        "jurisdiction": "PL",
        "language": "pl",
        "external_ids": {"sn_signature": "II CSK 862/14"},
    },
    "pl_sn_I_CSK_292-12": {
        "url": "https://www.sn.pl/sites/orzecznictwo/Orzeczenia2/I%20CSK%20292-12-1.pdf",
        "fetch_strategy": "direct",
        "doc_type_hint": "CASELAW",
        "jurisdiction": "PL",
        "language": "pl",
        "external_ids": {"sn_signature": "I CSK 292/12"},
    },
    "pl_sn_V_CSK_480-18_html": {
        "url": "https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/v%20csk%20480-18-1.docx.html",
        "fetch_strategy": "direct",
        "doc_type_hint": "CASELAW",
        "jurisdiction": "PL",
        "language": "pl",
        "external_ids": {"sn_signature": "V CSK 480/18"},
    },
    "pl_sn_I_CNP_31-13_html": {
        "url": "https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/I%20CNP%2031-13.docx.html",
        "fetch_strategy": "direct",
        "doc_type_hint": "CASELAW",
        "jurisdiction": "PL",
        "language": "pl",
        "external_ids": {"sn_signature": "I CNP 31/13"},
    },
    "pl_saos_search_kaucja_mieszkaniowa": {
        "url": "https://www.saos.org.pl/search?courtCriteria.courtType=COMMON&keywords=kaucja+mieszkaniowa",
        "fetch_strategy": "saos_search",
        "doc_type_hint": "CASELAW",
        "jurisdiction": "PL",
        "language": "pl",
    },
    "pl_saos_171957": {
        "url": "https://www.saos.org.pl/judgments/171957",
        "fetch_strategy": "saos_judgment",
        "doc_type_hint": "CASELAW",
        "jurisdiction": "PL",
        "language": "pl",
        "external_ids": {"saos_id": "171957"},
    },
    "pl_courts_wloclawek_I_Ca_56_2018": {
        "url": "https://orzeczenia.wloclawek.so.gov.pl/content/$N/151030000000503_I_Ca_000056_2018_Uz_2018-05-08_001",
        "fetch_strategy": "direct",
        "doc_type_hint": "CASELAW",
        "jurisdiction": "PL",
        "language": "pl",
    },
    "eu_eurlex_dir_1993_13": {
        "url": "https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng",
        "fetch_strategy": "direct",
        "doc_type_hint": "EU_ACT",
        "jurisdiction": "EU",
        "language": "en",
        "external_ids": {"eli": "dir/1993/13/oj/eng"},
    },
    "pl_uokik_RKR_37_2013": {
        "url": "https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/43104c28a7a1be23c1257eac006d8dd4/6168c41ed23328e8c1257ec6007ba3ca/$FILE/RKR-37-2013%20Novis%20MSK.pdf",
        "fetch_strategy": "direct",
        "doc_type_hint": "GUIDANCE",
        "jurisdiction": "PL",
        "language": "pl",
    },
}


def test_full_config_techspec_mapping():
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "configs", "config.full.template.yml"
    )
    cfg = load_config(config_path)

    cfg_map = {src.source_id: src for src in cfg.sources}

    # 1. Assert exactly 15 records to match parity
    assert len(cfg_map) == 15, (
        f"Expected 15 sources in config.full.template.yml. Found {len(cfg_map)}"
    )

    # 2. Iterate and ensure strict structural equivalence for specified fields
    for ts_id, ts_expected in TECHSPEC_MAPPING.items():
        assert ts_id in cfg_map, f"Missing TechSpec source_id in config: {ts_id}"
        src_model = cfg_map[ts_id]

        assert str(src_model.url) == ts_expected["url"], (
            f"TechSpec URL mismatch on {ts_id}"
        )
        assert src_model.fetch_strategy == ts_expected["fetch_strategy"], (
            f"TechSpec fetch_strategy mismatch on {ts_id}"
        )
        assert src_model.doc_type_hint == ts_expected["doc_type_hint"], (
            f"TechSpec doc_type_hint mismatch on {ts_id}"
        )
        assert src_model.jurisdiction == ts_expected["jurisdiction"], (
            f"TechSpec jurisdiction mismatch on {ts_id}"
        )
        assert src_model.language == ts_expected["language"], (
            f"TechSpec language mismatch on {ts_id}"
        )

        if "license_tag" in ts_expected:
            assert src_model.license_tag == ts_expected["license_tag"], (
                f"TechSpec license_tag mismatch on {ts_id}"
            )

        if "external_ids" in ts_expected:
            assert src_model.external_ids == ts_expected["external_ids"], (
                f"TechSpec external_ids mismatch on {ts_id}"
            )
        else:
            # If TS doesn't specify external_ids, then config might have none or empty
            assert src_model.external_ids is None or len(src_model.external_ids) == 0, (
                f"TechSpec unexpected external_ids on {ts_id}"
            )
