from legal_ingest.config import load_config
import os


TECHSPEC_MAPPING = {
    "pl_eli_du_2001_733": "https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf",
    "pl_isap_wdu19640160093": "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf",
    "pl_lex_ochrona_praw_lokatorow": "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658",
    "pl_lex_art_19a": "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658/art-19-a",
    "pl_lex_kc_art_118": "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/kodeks-cywilny-16785996/art-118",
    "pl_sn_III_CZP_58-02": "https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf",
    "pl_sn_II_CSK_862-14": "https://www.sn.pl/sites/orzecznictwo/orzeczenia3/ii%20csk%20862-14-1.pdf",
    "pl_sn_I_CSK_292-12": "https://www.sn.pl/sites/orzecznictwo/Orzeczenia2/I%20CSK%20292-12-1.pdf",
    "pl_sn_V_CSK_480-18_html": "https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/v%20csk%20480-18-1.docx.html",
    "pl_sn_I_CNP_31-13_html": "https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/I%20CNP%2031-13.docx.html",
    "pl_saos_search_kaucja_mieszkaniowa": "https://www.saos.org.pl/search?courtCriteria.courtType=COMMON&keywords=kaucja+mieszkaniowa",
    "pl_saos_171957": "https://www.saos.org.pl/judgments/171957",
    "pl_courts_wloclawek_I_Ca_56_2018": "https://orzeczenia.wloclawek.so.gov.pl/content/$N/151030000000503_I_Ca_000056_2018_Uz_2018-05-08_001",
    "eu_eurlex_dir_1993_13": "https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng",
    "pl_uokik_RKR_37_2013": "https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/43104c28a7a1be23c1257eac006d8dd4/6168c41ed23328e8c1257ec6007ba3ca/$FILE/RKR-37-2013%20Novis%20MSK.pdf",
}


def test_full_config_techspec_mapping():
    # Target the primary full template located natively
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "configs", "config.full.template.yml"
    )
    cfg = load_config(config_path)

    # Generate actual mapping logic
    cfg_map = {src.source_id: str(src.url) for src in cfg.sources}

    # 1. Assert exactly 15 records to match parity
    assert len(cfg_map) == 15, (
        f"Expected 15 sources in config.full.template.yml. Found {len(cfg_map)}"
    )

    # 2. Iterate and ensure strict structural equivalence
    for ts_id, ts_url in TECHSPEC_MAPPING.items():
        assert ts_id in cfg_map, f"Missing TechSpec source_id in config: {ts_id}"
        assert cfg_map[ts_id] == ts_url, (
            f"TechSpec mismatch on {ts_id}: Expected {ts_url} but got {cfg_map[ts_id]}"
        )
