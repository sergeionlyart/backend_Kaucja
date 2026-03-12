from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceCatalogEntry:
    position: int
    category: str
    source_url: str
    source_id: str
    source_doc_uid: str


@dataclass(frozen=True, slots=True)
class RequiredCurrentSource:
    entry_id: str
    doc_uid: str
    source_system: str
    source_id: str
    source_url: str
    canonical_title: str
    title_short: str
    document_kind: str
    legal_role: str
    external_id: str
    external_ids: dict[str, str]
    language: str = "pl"
    jurisdiction: str = "PL"
    license_tag: str = "OFFICIAL"


TECHSPEC_SOURCE_CATALOG: tuple[SourceCatalogEntry, ...] = (
    SourceCatalogEntry(
        position=1,
        category="PL_ACTS",
        source_url="https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf",
        source_id="pl_eli_du_2001_733_original",
        source_doc_uid="eli_pl:DU/2001/733",
    ),
    SourceCatalogEntry(
        position=2,
        category="PL_ACTS",
        source_url="https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf",
        source_id="pl_isap_wdu19640160093_current",
        source_doc_uid="isap_pl:WDU19640160093",
    ),
    SourceCatalogEntry(
        position=3,
        category="PL_ACTS",
        source_url="https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658",
        source_id="pl_lex_ochrona_praw_lokatorow",
        source_doc_uid="lex_pl:16903658",
    ),
    SourceCatalogEntry(
        position=4,
        category="PL_ACTS",
        source_url="https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658/art-19-a",
        source_id="pl_lex_art_19a",
        source_doc_uid="lex_pl:16903658:art-19-a",
    ),
    SourceCatalogEntry(
        position=5,
        category="PL_ACTS",
        source_url="https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/kodeks-cywilny-16785996/art-118",
        source_id="pl_lex_kc_art_118",
        source_doc_uid="lex_pl:118",
    ),
    SourceCatalogEntry(
        position=6,
        category="PL_SN",
        source_url="https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf",
        source_id="pl_sn_iii_czp_58_02",
        source_doc_uid="sn_pl:III_CZP_58-02",
    ),
    SourceCatalogEntry(
        position=7,
        category="PL_SN",
        source_url="https://www.sn.pl/sites/orzecznictwo/orzeczenia3/ii%20csk%20862-14-1.pdf",
        source_id="pl_sn_ii_csk_862_14",
        source_doc_uid="sn_pl:II_CSK_862-14",
    ),
    SourceCatalogEntry(
        position=8,
        category="PL_SN",
        source_url="https://www.sn.pl/sites/orzecznictwo/Orzeczenia2/I%20CSK%20292-12-1.pdf",
        source_id="pl_sn_i_csk_292_12",
        source_doc_uid="sn_pl:I_CSK_292-12",
    ),
    SourceCatalogEntry(
        position=9,
        category="PL_SN",
        source_url="https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/v%20csk%20480-18-1.docx.html",
        source_id="pl_sn_v_csk_480_18_html",
        source_doc_uid="sn_pl:V_CSK_480-18",
    ),
    SourceCatalogEntry(
        position=10,
        category="PL_SN",
        source_url="https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/I%20CNP%2031-13.docx.html",
        source_id="pl_sn_i_cnp_31_13_html",
        source_doc_uid="sn_pl:I_CNP_31-13",
    ),
    SourceCatalogEntry(
        position=11,
        category="PL_SAOS",
        source_url="https://www.saos.org.pl/search?courtCriteria.courtType=COMMON&keywords=kaucja+mieszkaniowa",
        source_id="pl_saos_search_kaucja_mieszkaniowa",
        source_doc_uid="saos_pl:search:kaucja_mieszkaniowa",
    ),
    SourceCatalogEntry(
        position=12,
        category="PL_SAOS",
        source_url="https://www.saos.org.pl/judgments/171957",
        source_id="pl_saos_171957",
        source_doc_uid="saos_pl:171957",
    ),
    SourceCatalogEntry(
        position=13,
        category="PL_SAOS",
        source_url="https://www.saos.org.pl/judgments/205996",
        source_id="pl_saos_205996",
        source_doc_uid="saos_pl:205996",
    ),
    SourceCatalogEntry(
        position=14,
        category="PL_SAOS",
        source_url="https://www.saos.org.pl/judgments/279345",
        source_id="pl_saos_279345",
        source_doc_uid="saos_pl:279345",
    ),
    SourceCatalogEntry(
        position=15,
        category="PL_SAOS",
        source_url="https://www.saos.org.pl/judgments/330695",
        source_id="pl_saos_330695",
        source_doc_uid="saos_pl:330695",
    ),
    SourceCatalogEntry(
        position=16,
        category="PL_SAOS",
        source_url="https://www.saos.org.pl/judgments/346698",
        source_id="pl_saos_346698",
        source_doc_uid="saos_pl:346698",
    ),
    SourceCatalogEntry(
        position=17,
        category="PL_SAOS",
        source_url="https://www.saos.org.pl/judgments/472812",
        source_id="pl_saos_472812",
        source_doc_uid="saos_pl:472812",
    ),
    SourceCatalogEntry(
        position=18,
        category="PL_SAOS",
        source_url="https://www.saos.org.pl/judgments/486542",
        source_id="pl_saos_486542",
        source_doc_uid="saos_pl:486542",
    ),
    SourceCatalogEntry(
        position=19,
        category="PL_SAOS",
        source_url="https://www.saos.org.pl/judgments/487012",
        source_id="pl_saos_487012",
        source_doc_uid="saos_pl:487012",
    ),
    SourceCatalogEntry(
        position=20,
        category="PL_SAOS",
        source_url="https://www.saos.org.pl/judgments/505310",
        source_id="pl_saos_505310",
        source_doc_uid="saos_pl:505310",
    ),
    SourceCatalogEntry(
        position=21,
        category="PL_SAOS",
        source_url="https://www.saos.org.pl/judgments/521555",
        source_id="pl_saos_521555",
        source_doc_uid="saos_pl:521555",
    ),
    SourceCatalogEntry(
        position=22,
        category="PL_COURTS",
        source_url="https://orzeczenia.wloclawek.so.gov.pl/content/$N/151030000000503_I_Ca_000056_2018_Uz_2018-05-08_001",
        source_id="pl_courts_i_ca_56_18_portal",
        source_doc_uid="courts_pl:urlsha:20c9c82554a6e7f2",
    ),
    SourceCatalogEntry(
        position=23,
        category="PL_COURTS",
        source_url="https://orzeczenia.ms.gov.pl/content/$N/152510000001503_III_Ca_001707_2018_Uz_2019-02-28_001",
        source_id="pl_courts_iii_ca_1707_18_portal",
        source_doc_uid="courts_pl:urlsha:74cfe0dfc8b4592a",
    ),
    SourceCatalogEntry(
        position=24,
        category="PL_COURTS",
        source_url="https://orzeczenia.katowice.sa.gov.pl/content/$N/151500000002503_V_ACa_000599_2014_Uz_2015-02-18_001",
        source_id="pl_courts_v_aca_599_14_portal",
        source_doc_uid="courts_pl:urlsha:9ea678728691b52e",
    ),
    SourceCatalogEntry(
        position=25,
        category="EU_ACTS",
        source_url="https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng",
        source_id="eu_eurlex_dir_93_13",
        source_doc_uid="eurlex_eu:dir/1993/13/oj/eng",
    ),
    SourceCatalogEntry(
        position=26,
        category="EU_ACTS",
        source_url="https://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=CELEX:31993L0013:en:HTML",
        source_id="eu_eurlex_lexuriserv_93_13",
        source_doc_uid="eurlex_eu:celex:31993L0013",
    ),
    SourceCatalogEntry(
        position=27,
        category="EU_ACTS",
        source_url="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?from=FR&uri=CELEX:52019XC0927(01)",
        source_id="eu_eurlex_commission_notice_2019_c_323_04",
        source_doc_uid="eurlex_eu:urlsha:252f802534879b95",
    ),
    SourceCatalogEntry(
        position=28,
        category="EU_ACTS",
        source_url="https://eur-lex.europa.eu/eli/reg/2007/861/oj/eng",
        source_id="eu_eurlex_reg_861_2007",
        source_doc_uid="eurlex_eu:eli:reg/2007/861/oj/eng",
    ),
    SourceCatalogEntry(
        position=29,
        category="EU_ACTS",
        source_url="https://eur-lex.europa.eu/eli/reg/2006/1896/oj/eng",
        source_id="eu_eurlex_reg_1896_2006",
        source_doc_uid="eurlex_eu:eli:reg/2006/1896/oj/eng",
    ),
    SourceCatalogEntry(
        position=30,
        category="EU_ACTS",
        source_url="https://eur-lex.europa.eu/eli/reg/2004/805/oj/eng",
        source_id="eu_eurlex_reg_805_2004",
        source_doc_uid="eurlex_eu:eli:reg/2004/805/oj/eng",
    ),
    SourceCatalogEntry(
        position=31,
        category="EU_CASELAW",
        source_url="https://curia.europa.eu/juris/document/document.jsf?docid=137830&doclang=EN",
        source_id="eu_curia_c_488_11_asbeek_brusse",
        source_doc_uid="curia_eu:urlsha:54acc341b17f3a57",
    ),
    SourceCatalogEntry(
        position=32,
        category="EU_CASELAW",
        source_url="https://curia.europa.eu/juris/document/document.jsf?docid=237043&doclang=en",
        source_id="eu_curia_c_229_19_dexia",
        source_doc_uid="curia_eu:docid:237043",
    ),
    SourceCatalogEntry(
        position=33,
        category="EU_CASELAW",
        source_url="https://curia.europa.eu/juris/document/document.jsf?docid=74812&doclang=EN",
        source_id="eu_curia_c_243_08_pannon_gsm",
        source_doc_uid="curia_eu:urlsha:ef65918198e5ffee",
    ),
    SourceCatalogEntry(
        position=34,
        category="EU_CASELAW",
        source_url="https://curia.europa.eu/jcms/jcms/p1_4220451/en/",
        source_id="eu_curia_unfair_terms_factsheet",
        source_doc_uid="curia_eu:jcms:p1_4220451",
    ),
    SourceCatalogEntry(
        position=35,
        category="PL_UOKIK",
        source_url="https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/43104c28a7a1be23c1257eac006d8dd4/6168c41ed23328e8c1257ec6007ba3ca/$FILE/RKR-37-2013%20Novis%20MSK.pdf",
        source_id="pl_uokik_rkr_37_2013_novis_msk",
        source_doc_uid="uokik_pl:urlsha:c506ff470f4740ad",
    ),
    SourceCatalogEntry(
        position=36,
        category="PL_UOKIK",
        source_url="https://uokik.gov.pl/niedozwolone-klauzule",
        source_id="pl_uokik_niedozwolone_klauzule",
        source_doc_uid="uokik_pl:urlsha:054662ca9a699d16",
    ),
    SourceCatalogEntry(
        position=37,
        category="PL_UOKIK",
        source_url="https://rejestr.uokik.gov.pl/uzasadnienia/891/AmC%20_86_2003.pdf",
        source_id="pl_uokik_amc_86_2003",
        source_doc_uid="uokik_pl:urlsha:5efe92f726049194",
    ),
    SourceCatalogEntry(
        position=38,
        category="PL_COMMENTARY",
        source_url="https://www.prawo.pl/student/niedozwolone-klauzule-w-umowach-najmu-skutki-ochrona-lokatora%2C510151.html",
        source_id="pl_prawo_niedozwolone_klauzule_najem",
        source_doc_uid="prawo_pl:urlsha:7315b25566b744a4",
    ),
)

SOURCE_BY_POSITION = {entry.position: entry for entry in TECHSPEC_SOURCE_CATALOG}

REQUIRED_CURRENT_SOURCES: tuple[RequiredCurrentSource, ...] = (
    RequiredCurrentSource(
        entry_id="runtime-current-lokatorzy-act",
        doc_uid="eli_pl:DU/2001/733",
        source_system="eli_pl",
        source_id="required_current_lokatorzy_act",
        source_url="https://eli.gov.pl/api/acts/DU/2001/733/text/U/D20010733Lj.pdf",
        canonical_title="Ustawa z dnia 21 czerwca 2001 r. o ochronie praw lokatorow, mieszkaniowym zasobie gminy i o zmianie Kodeksu cywilnego",
        title_short="Ustawa o ochronie praw lokatorow",
        document_kind="STATUTE",
        legal_role="DIRECT_NORM",
        external_id="eli:DU/2001/733",
        external_ids={"eli": "DU/2001/733"},
    ),
    RequiredCurrentSource(
        entry_id="runtime-current-kc",
        doc_uid="isap_pl:WDU19640160093",
        source_system="isap_pl",
        source_id="required_current_kc",
        source_url="https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf",
        canonical_title="Kodeks cywilny",
        title_short="Kodeks cywilny",
        document_kind="STATUTE",
        legal_role="DIRECT_NORM",
        external_id="isap:WDU19640160093",
        external_ids={"isap_wdu": "WDU19640160093"},
    ),
    RequiredCurrentSource(
        entry_id="required-addition-kpc",
        doc_uid="eli_pl:DU/1964/296",
        source_system="eli_pl",
        source_id="required_kpc_current",
        source_url="https://eli.gov.pl/api/acts/DU/1964/296/text/U/D19640296Lj.pdf",
        canonical_title="Kodeks postepowania cywilnego",
        title_short="Kodeks postepowania cywilnego",
        document_kind="STATUTE",
        legal_role="PROCESS_NORM",
        external_id="eli:DU/1964/296",
        external_ids={"eli": "DU/1964/296"},
    ),
    RequiredCurrentSource(
        entry_id="required-addition-costs-act",
        doc_uid="eli_pl:DU/2005/1398",
        source_system="eli_pl",
        source_id="required_costs_act_current",
        source_url="https://eli.gov.pl/api/acts/DU/2005/1398/text/U/D20051398Lj.pdf",
        canonical_title="Ustawa o kosztach sadowych w sprawach cywilnych",
        title_short="Ustawa o kosztach sadowych",
        document_kind="STATUTE",
        legal_role="PROCESS_NORM",
        external_id="eli:DU/2005/1398",
        external_ids={"eli": "DU/2005/1398"},
    ),
    RequiredCurrentSource(
        entry_id="required-addition-uokk",
        doc_uid="eli_pl:DU/2007/331",
        source_system="eli_pl",
        source_id="required_uokk_current",
        source_url="https://eli.gov.pl/api/acts/DU/2007/331/text/U/D20070331Lj.pdf",
        canonical_title="Ustawa o ochronie konkurencji i konsumentow",
        title_short="Ustawa o ochronie konkurencji i konsumentow",
        document_kind="STATUTE",
        legal_role="EU_CONSUMER_LAYER",
        external_id="eli:DU/2007/331",
        external_ids={"eli": "DU/2007/331"},
    ),
)

REQUIRED_SOURCE_BY_ENTRY_ID = {
    entry.entry_id: entry for entry in REQUIRED_CURRENT_SOURCES
}


def get_source_entry(position: int) -> SourceCatalogEntry:
    try:
        return SOURCE_BY_POSITION[position]
    except KeyError as exc:
        raise ValueError(f"Unknown TechSpec source position: {position}") from exc
