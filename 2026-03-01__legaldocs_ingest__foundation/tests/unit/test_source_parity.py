"""Test that the source-set in run_iter3.py matches the 38 URLs in cas_law_V_2.2 2.md"""
import re
import os

MARKDOWN_PATH = os.path.join(
    os.path.dirname(__file__), 
    "..", "..", "..", "..", "backend_Kaucja", "docs", "legal", "cas_law_V_2.2 2.md"
)

# Canonical list of 38 URLs extracted from the markdown (order and content must match)
EXPECTED_URLS = [
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


def test_source_count_is_38():
    assert len(EXPECTED_URLS) == 38


def test_source_urls_match_run_iter3():
    # Read run_iter3.py and extract URLs via regex
    run_iter3_path = os.path.join(os.path.dirname(__file__), "..", "..", "run_iter3.py")
    with open(run_iter3_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract all url="..." values
    urls_in_script = re.findall(r'url="([^"]+)"', content)
    
    assert len(urls_in_script) == 38, f"Expected 38 URLs in run_iter3.py, got {len(urls_in_script)}"
    
    for i, (expected, actual) in enumerate(zip(EXPECTED_URLS, urls_in_script)):
        assert expected == actual, f"URL mismatch at index {i}: expected {expected}, got {actual}"
