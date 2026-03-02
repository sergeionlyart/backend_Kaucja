"""Iteration 3: Full ingest of all 38 sources from cas_law_V_2.2 2.md"""
import os
import json
from legal_ingest.config import PipelineConfig, SourceConfig, HttpConfig, RunConfig, MongoConfig, ParsersConfig
from legal_ingest.pipeline import run_pipeline

# All 38 sources mapped 1:1 from cas_law_V_2.2 2.md
SOURCES = [
    # --- Польша — нормативка / LEX / ISAP / ELI ---
    SourceConfig(source_id="s01_eli_pdf", url="https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf", fetch_strategy="direct", doc_type_hint="STATUTE", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s02_isap_pdf", url="https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf", fetch_strategy="direct", doc_type_hint="STATUTE", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s03_lex_lokator", url="https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658", fetch_strategy="direct", doc_type_hint="STATUTE", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s04_lex_art19a", url="https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658/art-19-a", fetch_strategy="direct", doc_type_hint="STATUTE_REF", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s05_lex_art118", url="https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/kodeks-cywilny-16785996/art-118", fetch_strategy="direct", doc_type_hint="STATUTE_REF", jurisdiction="PL", language="pl"),

    # --- Польша — SN (Верховный суд) ---
    SourceConfig(source_id="s06_sn_czp58", url="https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s07_sn_csk862", url="https://www.sn.pl/sites/orzecznictwo/orzeczenia3/ii%20csk%20862-14-1.pdf", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s08_sn_csk292", url="https://www.sn.pl/sites/orzecznictwo/Orzeczenia2/I%20CSK%20292-12-1.pdf", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s09_sn_csk480", url="https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/v%20csk%20480-18-1.docx.html", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s10_sn_cnp31", url="https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/I%20CNP%2031-13.docx.html", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),

    # --- Польша — SAOS ---
    SourceConfig(source_id="s11_saos_search", url="https://www.saos.org.pl/search?courtCriteria.courtType=COMMON&keywords=kaucja+mieszkaniowa", fetch_strategy="saos_search", saos_search_params={"courtCriteria.courtType": "COMMON", "keywords": "kaucja mieszkaniowa"}, doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s12_saos_171957", url="https://www.saos.org.pl/judgments/171957", fetch_strategy="saos_judgment", external_ids={"saos_id": "171957"}, doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s13_saos_205996", url="https://www.saos.org.pl/judgments/205996", fetch_strategy="saos_judgment", external_ids={"saos_id": "205996"}, doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s14_saos_279345", url="https://www.saos.org.pl/judgments/279345", fetch_strategy="saos_judgment", external_ids={"saos_id": "279345"}, doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s15_saos_330695", url="https://www.saos.org.pl/judgments/330695", fetch_strategy="saos_judgment", external_ids={"saos_id": "330695"}, doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s16_saos_346698", url="https://www.saos.org.pl/judgments/346698", fetch_strategy="saos_judgment", external_ids={"saos_id": "346698"}, doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s17_saos_472812", url="https://www.saos.org.pl/judgments/472812", fetch_strategy="saos_judgment", external_ids={"saos_id": "472812"}, doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s18_saos_486542", url="https://www.saos.org.pl/judgments/486542", fetch_strategy="saos_judgment", external_ids={"saos_id": "486542"}, doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s19_saos_487012", url="https://www.saos.org.pl/judgments/487012", fetch_strategy="saos_judgment", external_ids={"saos_id": "487012"}, doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s20_saos_505310", url="https://www.saos.org.pl/judgments/505310", fetch_strategy="saos_judgment", external_ids={"saos_id": "505310"}, doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s21_saos_521555", url="https://www.saos.org.pl/judgments/521555", fetch_strategy="saos_judgment", external_ids={"saos_id": "521555"}, doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),

    # --- Польша — порталы решений судов ---
    SourceConfig(source_id="s22_orzeczenia_wloclawek", url="https://orzeczenia.wloclawek.so.gov.pl/content/$N/151030000000503_I_Ca_000056_2018_Uz_2018-05-08_001", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s23_orzeczenia_ms", url="https://orzeczenia.ms.gov.pl/content/$N/152510000001503_III_Ca_001707_2018_Uz_2019-02-28_001", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s24_orzeczenia_katowice", url="https://orzeczenia.katowice.sa.gov.pl/content/$N/151500000002503_V_ACa_000599_2014_Uz_2015-02-18_001", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),

    # --- ЕС — EUR-Lex ---
    SourceConfig(source_id="s25_eurlex_dir13", url="https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng", fetch_strategy="direct", doc_type_hint="EU_ACT", jurisdiction="EU", language="en"),
    SourceConfig(source_id="s26_eurlex_celex13", url="https://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=CELEX:31993L0013:en:HTML", fetch_strategy="direct", doc_type_hint="EU_ACT", jurisdiction="EU", language="en"),
    SourceConfig(source_id="s27_eurlex_guide", url="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?from=FR&uri=CELEX:52019XC0927(01)", fetch_strategy="direct", doc_type_hint="GUIDANCE", jurisdiction="EU", language="en"),
    SourceConfig(source_id="s28_eurlex_reg861", url="https://eur-lex.europa.eu/eli/reg/2007/861/oj/eng", fetch_strategy="direct", doc_type_hint="EU_ACT", jurisdiction="EU", language="en"),
    SourceConfig(source_id="s29_eurlex_reg1896", url="https://eur-lex.europa.eu/eli/reg/2006/1896/oj/eng", fetch_strategy="direct", doc_type_hint="EU_ACT", jurisdiction="EU", language="en"),
    SourceConfig(source_id="s30_eurlex_reg805", url="https://eur-lex.europa.eu/eli/reg/2004/805/oj/eng", fetch_strategy="direct", doc_type_hint="EU_ACT", jurisdiction="EU", language="en"),

    # --- ЕС — CJEU / Curia ---
    SourceConfig(source_id="s31_curia_137830", url="https://curia.europa.eu/juris/document/document.jsf?docid=137830&doclang=EN", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="EU", language="en"),
    SourceConfig(source_id="s32_curia_237043", url="https://curia.europa.eu/juris/document/document.jsf?docid=237043&doclang=en", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="EU", language="en"),
    SourceConfig(source_id="s33_curia_74812", url="https://curia.europa.eu/juris/document/document.jsf?docid=74812&doclang=EN", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="EU", language="en"),
    SourceConfig(source_id="s34_curia_guide", url="https://curia.europa.eu/jcms/jcms/p1_4220451/en/", fetch_strategy="direct", doc_type_hint="GUIDANCE", jurisdiction="EU", language="en"),

    # --- Польша — UOKiK ---
    SourceConfig(source_id="s35_uokik_dec", url="https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/43104c28a7a1be23c1257eac006d8dd4/6168c41ed23328e8c1257ec6007ba3ca/$FILE/RKR-37-2013%20Novis%20MSK.pdf", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s36_uokik_clauses", url="https://uokik.gov.pl/niedozwolone-klauzule", fetch_strategy="direct", doc_type_hint="GUIDANCE", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s37_uokik_amc86", url="https://rejestr.uokik.gov.pl/uzasadnienia/891/AmC%20_86_2003.pdf", fetch_strategy="direct", doc_type_hint="CASELAW", jurisdiction="PL", language="pl"),
    SourceConfig(source_id="s38_prawo_klauzule", url="https://www.prawo.pl/student/niedozwolone-klauzule-w-umowach-najmu-skutki-ochrona-lokatora%2C510151.html", fetch_strategy="direct", doc_type_hint="COMMENTARY", jurisdiction="PL", language="pl"),
]

assert len(SOURCES) == 38, f"Expected 38 sources, got {len(SOURCES)}"

rc = RunConfig(run_id="iter3_caslaw_v22_full", artifact_dir="./artifacts_iter3", dry_run=True, http=HttpConfig(timeout_seconds=60))
config = PipelineConfig(
    run=rc,
    sources=SOURCES,
    mongo=MongoConfig(uri="mongodb://localhost:27017", db="test"),
    parsers=ParsersConfig()
)

stats = run_pipeline(config)

# Parse logs to build source status
logs_path = "./artifacts_iter3/runs/iter3_caslaw_v22_full/logs.jsonl"
statuses = {}
url_map = {s.source_id: str(s.url) for s in SOURCES}
expanded_saos_ids = []

with open(logs_path, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        sid = data.get("source_id")
        if not sid:
            # Check for saos_search expand info
            if "saos_search yielded" in data.get("msg", ""):
                pass
            continue

        if sid not in url_map and "s11_saos_search_" in sid:
            saos_id_part = sid.split("_")[-1]
            url_map[sid] = f"https://www.saos.org.pl/judgments/{saos_id_part}"
            expanded_saos_ids.append(saos_id_part)

        stage = data.get("stage")
        msg = data.get("msg", "")
        http_status = data.get("metrics", {}).get("http_status")

        if sid not in statuses:
            statuses[sid] = {"status": "UNKNOWN", "reason": "Processing started", "http_status": None, "final_url": None}

        if stage == "fetch" and "Fetched source" in msg:
            statuses[sid]["http_status"] = 200
            statuses[sid]["final_url"] = data.get("final_url")
        if stage == "parse" and "Restricted content" in msg:
            statuses[sid] = {**statuses[sid], "status": "RESTRICTED", "reason": msg}
        elif stage == "save" and "Document saved successfully" in msg:
            if statuses[sid]["status"] not in ["ERROR", "RESTRICTED"]:
                statuses[sid] = {**statuses[sid], "status": "OK", "reason": "Document fetched, parsed, and saved without errors."}
        elif "Error" in msg or "error" in msg.lower():
            if statuses[sid]["status"] not in ["OK"]:
                statuses[sid] = {**statuses[sid], "status": "ERROR", "reason": msg.strip()[:200]}

# Also check for sources that never appeared in logs (pipeline-level errors)
for line in open(logs_path, "r", encoding="utf-8"):
    data = json.loads(line)
    msg = data.get("msg", "")
    if "Error processing source" in msg:
        sid = data.get("source_id")
        if sid and sid in statuses and statuses[sid]["status"] == "UNKNOWN":
            statuses[sid] = {**statuses[sid], "status": "ERROR", "reason": msg.strip()[:200]}

# Build output arrays
all_statuses = []
not_loaded = []
idx = 1
primary_ids = [s.source_id for s in SOURCES]

# First write primary sources
for s in SOURCES:
    sid = s.source_id
    info = statuses.get(sid, {"status": "MISSING", "reason": "Source not processed by pipeline", "http_status": None, "final_url": None})
    entry = {
        "index": idx,
        "source_id": sid,
        "url": str(s.url),
        "fetch_strategy": s.fetch_strategy,
        "status": info["status"],
        "reason": info["reason"],
        "http_status": info.get("http_status"),
        "final_url": info.get("final_url"),
        "run_id": "iter3_caslaw_v22_full"
    }
    if sid == "s11_saos_search":
        entry["expanded_count"] = len(expanded_saos_ids)
        entry["expanded_judgment_ids"] = sorted(expanded_saos_ids)
    all_statuses.append(entry)
    if info["status"] not in ["OK"]:
        not_loaded.append(entry)
    idx += 1

# Also add expanded SAOS sources
for sid, info in statuses.items():
    if sid not in primary_ids and "s11_saos_search_" in sid:
        entry = {
            "index": None,
            "source_id": sid,
            "url": url_map.get(sid, ""),
            "fetch_strategy": "saos_judgment",
            "status": info["status"],
            "reason": info["reason"],
            "http_status": info.get("http_status"),
            "final_url": info.get("final_url"),
            "run_id": "iter3_caslaw_v22_full"
        }
        all_statuses.append(entry)
        if info["status"] not in ["OK"]:
            not_loaded.append(entry)

# Write JSON artifacts
os.makedirs("docs/reports", exist_ok=True)
with open("docs/reports/iter3_source_status.json", "w", encoding="utf-8") as f:
    json.dump(all_statuses, f, indent=2, ensure_ascii=False)
with open("docs/reports/iter3_not_loaded.json", "w", encoding="utf-8") as f:
    json.dump(not_loaded, f, indent=2, ensure_ascii=False)

print("\n=== Iteration 3 Summary ===")
print("Total primary sources: 38")
print(f"Total processed (incl expanded): {len(statuses)}")
print(f"OK: {sum(1 for v in statuses.values() if v['status'] == 'OK')}")
print(f"RESTRICTED: {sum(1 for v in statuses.values() if v['status'] == 'RESTRICTED')}")
print(f"ERROR: {sum(1 for v in statuses.values() if v['status'] == 'ERROR')}")
print(f"MISSING: {sum(1 for v in statuses.values() if v['status'] in ('UNKNOWN', 'MISSING'))}")
print(f"Expanded SAOS IDs: {len(expanded_saos_ids)}")
