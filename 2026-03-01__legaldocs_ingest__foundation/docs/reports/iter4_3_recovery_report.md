# Iteration 4.3: Recovery Report

**Run ID**: `iter4_3_caslaw_v22_full`
**Config**: `configs/config.caslaw_v22.full.yml` (38 sources → 920 with SAOS expansion)
**Pipeline metrics**: `sources_total=920, docs_ok=909, docs_restricted=10, docs_error=1`
**Primary sources**: **OK=27, RESTRICTED=10, ERROR=1** (total=38)

## Consistency verification

| Metric | source_status | run_report | Match |
|--------|--------------|------------|-------|
| RESTRICTED | 10 | docs_restricted=10 | ✅ |
| ERROR | 1 | docs_error=1 | ✅ |
| not_loaded | 11 | restricted+error=11 | ✅ |

## Recovery probe (3 rounds with backoff)

| Target | Probe result | Evidence |
|--------|-------------|----------|
| #12-21 SAOS judgments (×10) | **ALL OK** ✅ | API back online, 18-96KB real JSON |
| #24 orzeczenia Katowice | **OK** ✅ | 26617 bytes, 5 pages |
| #35 UOKiK | **ERROR** ❌ | SSL handshake timeout (3/3 rounds) |

## Not Loaded (11 of 38 primary sources)

### RESTRICTED (10) — EUR-Lex transient empty response

| # | source_id | Bytes | Reason |
|---|-----------|-------|--------|
| 25 | s25_eurlex_dir13 | 0 | EUR-Lex returned empty body (rate-limiting/maintenance) |
| 26 | s26_eurlex_celex13 | 0 | EUR-Lex returned empty body |
| 27 | s27_eurlex_guide | 0 | EUR-Lex returned empty body |
| 28 | s28_eurlex_reg861 | 0 | EUR-Lex returned empty body |
| 29 | s29_eurlex_reg1896 | 0 | EUR-Lex returned empty body |
| 30 | s30_eurlex_reg805 | 0 | EUR-Lex returned empty body |
| 31 | s31_curia_137830 | 0 | EUR-Lex CELEX returned empty body |
| 32 | s32_curia_237043 | 0 | EUR-Lex CELEX returned empty body |
| 33 | s33_curia_74812 | 0 | EUR-Lex CELEX returned empty body |
| 34 | s34_curia_guide | 0 | EUR-Lex OJ URI returned empty body |

> **All 10 EUR-Lex sources returned 76-4231KB in previous runs** (iter4.2, iter4.1). This is a **transient EUR-Lex issue** — the server returned HTTP 200 with 0 bytes. Re-run when EUR-Lex normalizes.

### ERROR (1) — persistent external failure

| # | source_id | Error | Evidence |
|---|-----------|-------|----------|
| 35 | s35_uokik_dec | SSL handshake timeout | `decyzje.uokik.gov.pl` unreachable (all iterations, 3/3 probe rounds) |

## Code changes (Iteration 4.3)

1. **`legal_ingest/fetch.py`**: Added `SaosMaintenanceError`, `is_saos_maintenance()`, `SAOS_MAINTENANCE_SIGNATURES`. Updated `fetch_saos_judgment()` to detect maintenance on both API and HTML endpoints.
2. **`legal_ingest/pipeline.py`**: Explicit SAOS maintenance check in HTML path (before generic char threshold).
3. **`scripts/recover_iter4_sources.py`** (NEW): 3-round retry probe with backoff for 12 targets.
4. **`scripts/build_iter4_reports.py`**: SAOS maintenance reason detection, configurable report prefix.
5. **`tests/unit/test_saos_maintenance.py`** (NEW): 6 unit tests for maintenance detection.

## Canonical run path

```bash
cd 2026-03-01__legaldocs_ingest__foundation && source venv/bin/activate
python -m legal_ingest.cli --env-file .env validate-config --config configs/config.caslaw_v22.full.yml
python -m legal_ingest.cli --env-file .env ensure-indexes --config configs/config.caslaw_v22.full.yml
python -m legal_ingest.cli --env-file .env ingest --config configs/config.caslaw_v22.full.yml
python scripts/build_iter4_reports.py iter4_3_caslaw_v22_full iter4_3
python scripts/recover_iter4_sources.py  # targeted probe
```
