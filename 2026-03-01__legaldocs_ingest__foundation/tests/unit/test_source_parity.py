"""Test URL parity between cas_law_V_2.2 2.md and config.caslaw_v22.full.yml.

This test MUST NOT silently skip. If the markdown source file is not
reachable, it falls back to a hardcoded snapshot of the 38 expected URLs.
"""
import re
import os
import yaml


FOUNDATION_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MARKDOWN_PATH = os.path.join(
    FOUNDATION_DIR, "..", "..", "backend_Kaucja", "docs", "legal", "cas_law_V_2.2 2.md"
)
YAML_CONFIG_PATH = os.path.join(
    FOUNDATION_DIR, "configs", "config.caslaw_v22.full.yml"
)

# Frozen snapshot — last-resort if markdown file is unavailable (e.g. CI).
# Must be kept in sync with the markdown. The parity test below will catch drift
# whenever the markdown IS available.
SNAPSHOT_URLS = [
    "https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf",
    "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf",
    "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658",
    "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658/art-19-a",
    "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/kodeks-cywilny-16785996/art-118",
    "https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf",
    "https://www.sn.pl/sites/orzecznictwo/orzeczenia3/ii%20csk%20862-14-1.pdf",
    "https://www.sn.pl/sites/orzecznictwo/Orzeczenia2/I%20CSK%20292-12-1.pdf",
    "https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/v%20csk%20480-18-1.docx.html",
    "https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/I%20CNP%2031-13.docx.html",
    "https://www.saos.org.pl/search?courtCriteria.courtType=COMMON&keywords=kaucja+mieszkaniowa",
    "https://www.saos.org.pl/judgments/171957",
    "https://www.saos.org.pl/judgments/205996",
    "https://www.saos.org.pl/judgments/279345",
    "https://www.saos.org.pl/judgments/330695",
    "https://www.saos.org.pl/judgments/346698",
    "https://www.saos.org.pl/judgments/472812",
    "https://www.saos.org.pl/judgments/486542",
    "https://www.saos.org.pl/judgments/487012",
    "https://www.saos.org.pl/judgments/505310",
    "https://www.saos.org.pl/judgments/521555",
    "https://orzeczenia.wloclawek.so.gov.pl/content/$N/151030000000503_I_Ca_000056_2018_Uz_2018-05-08_001",
    "https://orzeczenia.ms.gov.pl/content/$N/152510000001503_III_Ca_001707_2018_Uz_2019-02-28_001",
    "https://orzeczenia.katowice.sa.gov.pl/content/$N/151500000002503_V_ACa_000599_2014_Uz_2015-02-18_001",
    "https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng",
    "https://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=CELEX:31993L0013:en:HTML",
    "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?from=FR&uri=CELEX:52019XC0927(01)",
    "https://eur-lex.europa.eu/eli/reg/2007/861/oj/eng",
    "https://eur-lex.europa.eu/eli/reg/2006/1896/oj/eng",
    "https://eur-lex.europa.eu/eli/reg/2004/805/oj/eng",
    "https://curia.europa.eu/juris/document/document.jsf?docid=137830&doclang=EN",
    "https://curia.europa.eu/juris/document/document.jsf?docid=237043&doclang=en",
    "https://curia.europa.eu/juris/document/document.jsf?docid=74812&doclang=EN",
    "https://curia.europa.eu/jcms/jcms/p1_4220451/en/",
    "https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/43104c28a7a1be23c1257eac006d8dd4/6168c41ed23328e8c1257ec6007ba3ca/$FILE/RKR-37-2013%20Novis%20MSK.pdf",
    "https://uokik.gov.pl/niedozwolone-klauzule",
    "https://rejestr.uokik.gov.pl/uzasadnienia/891/AmC%20_86_2003.pdf",
    "https://www.prawo.pl/student/niedozwolone-klauzule-w-umowach-najmu-skutki-ochrona-lokatora%2C510151.html",
]


def _extract_urls_from_markdown(path: str) -> list[str]:
    """Extract all URLs from the numbered list in the markdown file."""
    urls = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.search(r'(?:^|\t)\d+\.\s*(https?://\S+)', line.strip())
            if m:
                urls.append(m.group(1))
    return urls


def _extract_urls_from_yaml(path: str) -> list[str]:
    """Extract source URLs from the YAML config file in order."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [src["url"] for src in data.get("sources", [])]


def _get_reference_urls() -> list[str]:
    """Return reference URLs from markdown if available; otherwise use snapshot."""
    if os.path.exists(MARKDOWN_PATH):
        return _extract_urls_from_markdown(MARKDOWN_PATH)
    return list(SNAPSHOT_URLS)


# ---------- tests ----------


def test_yaml_has_38_sources():
    yaml_urls = _extract_urls_from_yaml(YAML_CONFIG_PATH)
    assert len(yaml_urls) == 38, f"Expected 38 sources in YAML, got {len(yaml_urls)}"


def test_reference_has_38_urls():
    """Ensure the reference source (markdown or snapshot) has exactly 38 URLs."""
    ref = _get_reference_urls()
    assert len(ref) == 38, f"Expected 38 reference URLs, got {len(ref)}"


def test_url_parity():
    """Verify exact 1:1 order and URL match between reference and YAML config."""
    ref_urls = _get_reference_urls()
    yaml_urls = _extract_urls_from_yaml(YAML_CONFIG_PATH)

    assert len(ref_urls) == len(yaml_urls) == 38, (
        f"Count mismatch: reference={len(ref_urls)}, yaml={len(yaml_urls)}"
    )

    for i, (ref, yml) in enumerate(zip(ref_urls, yaml_urls)):
        assert ref == yml, (
            f"URL mismatch at index {i + 1}: reference={ref} vs yaml={yml}"
        )


def test_snapshot_matches_markdown_when_available():
    """If the markdown file IS available, verify snapshot is in sync with it."""
    if not os.path.exists(MARKDOWN_PATH):
        return  # nothing to cross-check — parity still enforced via snapshot
    md_urls = _extract_urls_from_markdown(MARKDOWN_PATH)
    assert len(md_urls) == len(SNAPSHOT_URLS) == 38
    for i, (md, snap) in enumerate(zip(md_urls, SNAPSHOT_URLS)):
        assert md == snap, (
            f"SNAPSHOT_URLS[{i}] is stale! "
            f"markdown={md} vs snapshot={snap}. "
            "Update SNAPSHOT_URLS in test_source_parity.py."
        )
