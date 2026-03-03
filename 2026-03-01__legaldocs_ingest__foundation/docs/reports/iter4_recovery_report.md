# Iteration 4: Recovery Report

**Run ID**: `iter4_caslaw_v22_full_recovery`
**Config**: `configs/config.caslaw_v22.full.yml`
**Pipeline metrics**: `sources_total=920, docs_ok=916, docs_restricted=0, docs_error=4`

## Delta: Iteration 3.1 → Iteration 4

| # | source_id | Iter 3.1 | Iter 4 | Recovery action |
|---|-----------|----------|--------|----------------|
| 5 | s05_lex_art118 | RESTRICTED | **OK** | Lowered `total_chars` threshold 500→200 (art-118 content = 583 chars HTML, actual text ~300 chars — legitimately short single-article reference) |
| 23 | s23_orzeczenia_ms | OK | **ERROR** | Regression: `orzeczenia.ms.gov.pl` disconnected without response (server-side, transient) |
| 24 | s24_orzeczenia_katowice | ERROR | **ERROR** | Still failing: `orzeczenia.katowice.sa.gov.pl` disconnects without response despite 120s timeout × 6 retries |
| 31 | s31_curia_137830 | RESTRICTED | **OK** | Replaced Curia JSF URL with EUR-Lex CELEX: `62011CJ0415` (C-415/11 Aziz) |
| 32 | s32_curia_237043 | RESTRICTED | **OK** | Replaced Curia JSF URL with EUR-Lex CELEX: `62019CJ0725` (C-725/19 Impuls Leasing) |
| 33 | s33_curia_74812 | RESTRICTED | **OK** | Replaced Curia JSF URL with EUR-Lex CELEX: `62008CJ0243` (C-243/08 Pannon) |
| 34 | s34_curia_guide | ERROR | **ERROR** | Original Curia URL: 404. Initial CELEX replacement also 404. Corrected to `OJ:C:2019:380:FULL` (verified 200) — **will resolve on next run** |
| 35 | s35_uokik_dec | ERROR | **ERROR** | `decyzje.uokik.gov.pl` SSL handshake timeout — server unreachable despite 120s timeout × 6 retries |

**Summary**: 31→34 OK (+3), 4→0 RESTRICTED (-4), 3→4 ERROR (+1, #23 regression)

## Detailed analysis of remaining failures

### #23 s23_orzeczenia_ms — ERROR (regression)
- **URL**: `https://orzeczenia.ms.gov.pl/content/$N/152510000001503_III_Ca_001707_2018_Uz_2019-02-28_001`
- **Error**: `Server disconnected without sending a response`
- **Root cause**: Polish court portal (`orzeczenia.ms.gov.pl`) intermittently drops connections. This worked in iter3.1 — pure transient failure.
- **Mitigation**: Retry on next run; server uptime is outside our control.

### #24 s24_orzeczenia_katowice — ERROR (persistent)
- **URL**: `https://orzeczenia.katowice.sa.gov.pl/content/$N/151500000002503_V_ACa_000599_2014_Uz_2015-02-18_001`
- **Error**: `Server disconnected without sending a response`
- **Root cause**: Katowice court portal consistently drops connections. Tested with `curl --max-time 15` — also hangs.
- **Evidence**: Failed in both iter3.1 and iter4.

### #34 s34_curia_guide — ERROR (corrected, pending rerun)
- **Original URL**: `https://curia.europa.eu/jcms/jcms/p1_4220451/en/` → HTTP 404
- **1st recovery**: `CELEX:32019H1128(01)` → HTTP 404 (wrong CELEX identifier)
- **2nd recovery**: `OJ:C:2019:380:FULL` → **HTTP 200** (verified via curl)
- **Config updated**: URL now set to `https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:C:2019:380:FULL`
- **Status**: Will resolve on next pipeline run.

### #35 s35_uokik_dec — ERROR (persistent)
- **URL**: `https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/.../RKR-37-2013%20Novis%20MSK.pdf`
- **Error**: `_ssl.c:989: The handshake operation timed out`
- **Root cause**: `decyzje.uokik.gov.pl` server does not respond to TLS handshake. Tested with `curl --max-time 15` — hangs.
- **Evidence**: Failed in both iter3.1 (60s timeout) and iter4 (120s timeout × 6 retries).

## Code changes for recovery

1. **`pipeline.py`**: `total_chars` threshold lowered from 500 to 200 chars — prevents false positives on legitimately short legal article references (like art. 118 KC).
2. **`config.caslaw_v22.full.yml`**:
   - `timeout_seconds`: 60 → 120
   - `max_retries`: 4 → 6
   - #31: `curia.europa.eu/juris/document/document.jsf?docid=137830` → `eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415`
   - #32: `curia.europa.eu...docid=237043` → `eur-lex.europa.eu...CELEX:62019CJ0725`
   - #33: `curia.europa.eu...docid=74812` → `eur-lex.europa.eu...CELEX:62008CJ0243`
   - #34: `curia.europa.eu/jcms/jcms/p1_4220451/en/` → `eur-lex.europa.eu...OJ:C:2019:380:FULL`

## Absolute paths to artifacts

- **Config**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/configs/config.caslaw_v22.full.yml`
- **Run Report**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter4/runs/iter4_caslaw_v22_full_recovery/run_report.json`
- **Logs**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter4/runs/iter4_caslaw_v22_full_recovery/logs.jsonl`
- **Source Status**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter4_source_status.json`
- **Not Loaded**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter4_not_loaded.json`
- **This Report**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter4_recovery_report.md`
