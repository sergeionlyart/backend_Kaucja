# Iteration 4.2: Final Consistency Report

**Run ID**: `iter4_caslaw_v22_full_final`
**Config**: `configs/config.caslaw_v22.full.yml` (38 sources)
**Pipeline metrics** (from `run_report.json`): `sources_total=37, docs_ok=25, docs_restricted=10, docs_error=2`
**Primary source breakdown**: **OK=26, RESTRICTED=10, ERROR=2** (total=38)

> [!NOTE]
> `sources_total=37` in run_report excludes the `saos_search` meta-source which becomes expansions.
> `docs_ok=25` in run_report doesn't count `s11_saos_search` (meta-source with OK status in source_status).
> Primary OK=26 includes `s11_saos_search` as OK.

## Consistency verification

| Metric | source_status.json | run_report.json | Match |
|--------|-------------------|-----------------|-------|
| RESTRICTED | 10 | docs_restricted=10 | ✅ |
| ERROR | 2 | docs_error=2 | ✅ |
| not_loaded count | 12 | restricted+error=12 | ✅ |

## Not Loaded (12 of 38 primary sources)

### RESTRICTED (10) — SAOS API maintenance

| # | source_id | Reason |
|---|-----------|--------|
| 12 | s12_saos_171957 | SAOS API returning maintenance HTML (1230 bytes) |
| 13 | s13_saos_205996 | SAOS API returning maintenance HTML (1230 bytes) |
| 14 | s14_saos_279345 | SAOS API returning maintenance HTML (1230 bytes) |
| 15 | s15_saos_330695 | SAOS API returning maintenance HTML (1230 bytes) |
| 16 | s16_saos_346698 | SAOS API returning maintenance HTML (1230 bytes) |
| 17 | s17_saos_472812 | SAOS API returning maintenance HTML (1230 bytes) |
| 18 | s18_saos_486542 | SAOS API returning maintenance HTML (1230 bytes) |
| 19 | s19_saos_487012 | SAOS API returning maintenance HTML (1230 bytes) |
| 20 | s20_saos_505310 | SAOS API returning maintenance HTML (1230 bytes) |
| 21 | s21_saos_521555 | SAOS API returning maintenance HTML (1230 bytes) |

### ERROR (2)

| # | source_id | Error | Evidence |
|---|-----------|-------|----------|
| 24 | s24_orzeczenia_katowice | Server disconnected without sending a response | Persistent: `orzeczenia.katowice.sa.gov.pl` |
| 35 | s35_uokik_dec | [Errno 60] Operation timed out | Persistent: `decyzje.uokik.gov.pl` SSL timeout |

## OK sources confirmed (26 of 38)

All non-SAOS-individual sources loaded successfully, including all Iteration 4 recovery targets:

| # | source_id | Recovery action |
|---|-----------|-----------------|
| 5 | s05_lex_art118 | `min_chars_override: 200` (per-source, global=500) |
| 31 | s31_curia_137830 | EUR-Lex `CELEX:62011CJ0415` (C-415/11 Aziz) |
| 32 | s32_curia_237043 | EUR-Lex `CELEX:62019CJ0725` (C-725/19 Impuls Leasing) |
| 33 | s33_curia_74812 | EUR-Lex `CELEX:62008CJ0243` (C-243/08 Pannon) |
| 34 | s34_curia_guide | EUR-Lex `OJ:C:2019:380:FULL` (76KB, 2 pages) |

## Code changes (Iteration 4.2)

1. **`scripts/build_iter4_reports.py`** (NEW): Robust status generator with sticky RESTRICTED flag, run_id filter, and triple consistency check.
2. **`configs/config.caslaw_v22.full.yml`**: `run_id` → `iter4_caslaw_v22_full_final`.

## Canonical run path

```bash
cd 2026-03-01__legaldocs_ingest__foundation && source venv/bin/activate
python -m legal_ingest.cli --env-file .env validate-config --config configs/config.caslaw_v22.full.yml
python -m legal_ingest.cli --env-file .env ensure-indexes --config configs/config.caslaw_v22.full.yml
python -m legal_ingest.cli --env-file .env ingest --config configs/config.caslaw_v22.full.yml
python scripts/build_iter4_reports.py iter4_caslaw_v22_full_final
```

## Absolute paths

- **Config**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/configs/config.caslaw_v22.full.yml`
- **Run Report**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter4/runs/iter4_caslaw_v22_full_final/run_report.json`
- **Logs**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter4/runs/iter4_caslaw_v22_full_final/logs.jsonl`
- **Source Status**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter4_source_status.json`
- **Not Loaded**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter4_not_loaded.json`
- **This Report**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter4_recovery_report.md`
