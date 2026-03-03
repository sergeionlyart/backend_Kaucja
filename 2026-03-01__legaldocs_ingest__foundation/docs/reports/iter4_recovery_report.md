# Iteration 4.1: Recovery Report (Closure)

**Run ID**: `iter4_caslaw_v22_full_recovery_rerun`
**Config**: `configs/config.caslaw_v22.full.yml` (38 sources)
**Pipeline metrics**: `sources_total=920, docs_ok=919, docs_restricted=0, docs_error=1, pages_written=1421, nodes_written=3360, citations_written=3677`
**Primary sources**: **36/38 OK, 0 RESTRICTED, 2 ERROR**

## Delta table

| # | source_id | Iter 3.1 (initial) | Iter 4 (first run) | Iter 4.1 (rerun) | Recovery action |
|---|-----------|---------------------|---------------------|-------------------|-----------------|
| 5 | s05_lex_art118 | RESTRICTED | OK | **OK** ✅ | Per-source `min_chars_override: 200` (art-118 = ~300 text chars, legitimately short) |
| 22 | s22_orzeczenia_wloclawek | OK | OK | **ERROR** ❌ | Regression: `orzeczenia.wloclawek.so.gov.pl` server disconnect (transient) |
| 23 | s23_orzeczenia_ms | OK | ERROR | **OK** ✅ | Transient recovery — server responded on this run |
| 24 | s24_orzeczenia_katowice | ERROR | ERROR | **OK** ✅ | Transient recovery — server responded on this run |
| 31 | s31_curia_137830 | RESTRICTED | OK | **OK** ✅ | Curia JSF → EUR-Lex `CELEX:62011CJ0415` (C-415/11 Aziz) |
| 32 | s32_curia_237043 | RESTRICTED | OK | **OK** ✅ | Curia JSF → EUR-Lex `CELEX:62019CJ0725` (C-725/19 Impuls Leasing) |
| 33 | s33_curia_74812 | RESTRICTED | OK | **OK** ✅ | Curia JSF → EUR-Lex `CELEX:62008CJ0243` (C-243/08 Pannon) |
| 34 | s34_curia_guide | ERROR (404) | ERROR (wrong CELEX) | **OK** ✅ | `OJ:C:2019:380:FULL` (76KB, 2 pages) |
| 35 | s35_uokik_dec | ERROR | ERROR | **ERROR** ❌ | `decyzje.uokik.gov.pl` SSL handshake timeout — persistent, server unreachable |

## Not Loaded (2 of 38 primary sources)

| # | source_id | Status | Reason | Evidence |
|---|-----------|--------|--------|----------|
| 22 | s22_orzeczenia_wloclawek | ERROR | Server disconnected without sending a response | Transient — worked in iter3.1 and iter4, failed in iter4.1 rerun |
| 35 | s35_uokik_dec | ERROR | SSL handshake timeout after 120s × 6 retries | Persistent — failed in all runs (iter3.1, iter4, iter4.1) |

## Code changes (Iteration 4.1)

1. **`legal_ingest/config.py`**: Added `min_chars_override: Optional[int] = None` to `SourceConfig`.
2. **`legal_ingest/pipeline.py`**:
   - Restored global threshold to **500** chars.
   - Added per-source override: `source.min_chars_override if not None else 500`.
   - Wrapped error-handler Mongo save in nested try/except to prevent chain-crash.
3. **`configs/config.caslaw_v22.full.yml`**: Added `min_chars_override: 200` for `s05_lex_art118`.
4. **`tests/unit/test_threshold_override.py`**: 5 unit tests for default=500, override logic, override=0.
5. **`.gitignore`**: Added `artifacts_iter4/`.

## Canonical run path

```bash
cd 2026-03-01__legaldocs_ingest__foundation
source venv/bin/activate
python -m legal_ingest.cli --env-file .env validate-config --config configs/config.caslaw_v22.full.yml
python -m legal_ingest.cli --env-file .env ensure-indexes --config configs/config.caslaw_v22.full.yml
python -m legal_ingest.cli --env-file .env ingest --config configs/config.caslaw_v22.full.yml
```

## Absolute paths to artifacts

- **Config**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/configs/config.caslaw_v22.full.yml`
- **Run Report**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter4/runs/iter4_caslaw_v22_full_recovery_rerun/run_report.json`
- **Logs**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter4/runs/iter4_caslaw_v22_full_recovery_rerun/logs.jsonl`
- **Source Status**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter4_source_status.json`
- **Not Loaded**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter4_not_loaded.json`
- **This Report**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter4_recovery_report.md`
