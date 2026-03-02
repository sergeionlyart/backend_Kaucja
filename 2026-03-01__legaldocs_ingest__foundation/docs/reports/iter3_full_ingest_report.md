# Iteration 3.1: Full Source Coverage Report (Production)

**Run ID**: `iter3_caslaw_v22_full_fix1`  
**Config**: `configs/config.caslaw_v22.full.yml` (38 sources, 1:1 from `cas_law_V_2.2 2.md`)  
**CLI commands**:
```bash
python -m legal_ingest.cli --env-file .env validate-config --config configs/config.caslaw_v22.full.yml
python -m legal_ingest.cli --env-file .env ensure-indexes --config configs/config.caslaw_v22.full.yml
python -m legal_ingest.cli --env-file .env ingest --config configs/config.caslaw_v22.full.yml
```
**Pipeline metrics**: `sources_total=920, docs_ok=913, docs_restricted=4, docs_error=3, pages_written=1401, nodes_written=3355, citations_written=3677`

## Successfully Loaded (31 of 38 primary sources)

| # | source_id | URL | Strategy |
|---|-----------|-----|----------|
| 1 | s01_eli_pdf | https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf | direct |
| 2 | s02_isap_pdf | https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf | direct |
| 3 | s03_lex_lokator | https://sip.lex.pl/.../ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658 | direct |
| 4 | s04_lex_art19a | https://sip.lex.pl/.../art-19-a | direct |
| 6 | s06_sn_czp58 | https://www.sn.pl/.../III%20CZP%2058-02.pdf | direct |
| 7 | s07_sn_csk862 | https://www.sn.pl/.../ii%20csk%20862-14-1.pdf | direct |
| 8 | s08_sn_csk292 | https://www.sn.pl/.../I%20CSK%20292-12-1.pdf | direct |
| 9 | s09_sn_csk480 | https://www.sn.pl/.../v%20csk%20480-18-1.docx.html | direct |
| 10 | s10_sn_cnp31 | https://www.sn.pl/.../I%20CNP%2031-13.docx.html | direct |
| 11 | s11_saos_search | SAOS API search (`all`+`courtType`) | saos_search → **883 expanded judgments** |
| 12 | s12_saos_171957 | https://www.saos.org.pl/judgments/171957 | saos_judgment |
| 13 | s13_saos_205996 | https://www.saos.org.pl/judgments/205996 | saos_judgment |
| 14 | s14_saos_279345 | https://www.saos.org.pl/judgments/279345 | saos_judgment |
| 15 | s15_saos_330695 | https://www.saos.org.pl/judgments/330695 | saos_judgment |
| 16 | s16_saos_346698 | https://www.saos.org.pl/judgments/346698 | saos_judgment |
| 17 | s17_saos_472812 | https://www.saos.org.pl/judgments/472812 | saos_judgment |
| 18 | s18_saos_486542 | https://www.saos.org.pl/judgments/486542 | saos_judgment |
| 19 | s19_saos_487012 | https://www.saos.org.pl/judgments/487012 | saos_judgment |
| 20 | s20_saos_505310 | https://www.saos.org.pl/judgments/505310 | saos_judgment |
| 21 | s21_saos_521555 | https://www.saos.org.pl/judgments/521555 | saos_judgment |
| 22 | s22_orzeczenia_wloclawek | https://orzeczenia.wloclawek.so.gov.pl/content/... | direct |
| 23 | s23_orzeczenia_ms | https://orzeczenia.ms.gov.pl/content/... | direct |
| 25 | s25_eurlex_dir13 | https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng | direct |
| 26 | s26_eurlex_celex13 | https://eur-lex.europa.eu/LexUriServ/LexUriServ.do?... | direct |
| 27 | s27_eurlex_guide | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?... | direct |
| 28 | s28_eurlex_reg861 | https://eur-lex.europa.eu/eli/reg/2007/861/oj/eng | direct |
| 29 | s29_eurlex_reg1896 | https://eur-lex.europa.eu/eli/reg/2006/1896/oj/eng | direct |
| 30 | s30_eurlex_reg805 | https://eur-lex.europa.eu/eli/reg/2004/805/oj/eng | direct |
| 36 | s36_uokik_clauses | https://uokik.gov.pl/niedozwolone-klauzule | direct |
| 37 | s37_uokik_amc86 | https://rejestr.uokik.gov.pl/uzasadnienia/891/AmC%20_86_2003.pdf | direct |
| 38 | s38_prawo_klauzule | https://www.prawo.pl/student/niedozwolone-klauzule-w-umowach-najmu-... | direct |

## Not Loaded (7 of 38 primary sources)

| # | source_id | Status | Reason |
|---|-----------|--------|--------|
| 5 | s05_lex_art118 | RESTRICTED | LEX paywall — low char count after fetch |
| 24 | s24_orzeczenia_katowice | ERROR | Server disconnected without sending a response |
| 31 | s31_curia_137830 | RESTRICTED | Curia .jsf — JS-rendered shell, static fetch yields low char count |
| 32 | s32_curia_237043 | RESTRICTED | Curia .jsf — same as #31 |
| 33 | s33_curia_74812 | RESTRICTED | Curia .jsf — same as #31 |
| 34 | s34_curia_guide | ERROR | HTTP 404 — page not found on Curia portal |
| 35 | s35_uokik_dec | ERROR | Timed out — `decyzje.uokik.gov.pl` unreachable |

## Абсолютные пути к артефактам

- **Config**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/configs/config.caslaw_v22.full.yml`
- **Run Report**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter3/runs/iter3_caslaw_v22_full_fix1/run_report.json`
- **Logs**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter3/runs/iter3_caslaw_v22_full_fix1/logs.jsonl`
- **Source Status**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter3_source_status.json`
- **Not Loaded**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter3_not_loaded.json`
- **This Report**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter3_full_ingest_report.md`
