# Iteration 5: Recovery Report

**Run ID**: `iter5_caslaw_v22_full_browser`
**Config**: `configs/config.caslaw_v22.full.yml` (38 sources → 920 with SAOS expansion)
**Pipeline metrics**: `sources_total=920, docs_ok=920, docs_restricted=0, docs_error=0`
**Primary sources**: **OK=38, RESTRICTED=0, ERROR=0** (total=38)

## 🎯 KPI: 38/38 OK — ACHIEVED

## Evidence source of truth

| File | Role |
|------|------|
| `artifacts_iter5/runs/iter5_caslaw_v22_full_browser/run_report.json` | Pipeline metrics (canonical) |
| `artifacts_iter5/runs/iter5_caslaw_v22_full_browser/logs.jsonl` | Per-source logs (canonical) |
| `artifacts_iter5/runs/iter5_caslaw_v22_full_browser/fetch_attempts.jsonl` | Transport ladder telemetry (canonical) |
| `docs/reports/iter5_source_status.json` | Per-source status (derived) |
| `docs/reports/iter5_not_loaded.json` | Not-OK sources (derived — empty) |
| `docs/reports/iter5_recovery_report.md` | This report (derived) |

## Consistency verification

| Metric | source_status | run_report | Match |
|--------|--------------|------------|-------|
| OK | 38 | docs_ok=920 (incl SAOS expanded) | ✅ |
| RESTRICTED | 0 | docs_restricted=0 | ✅ |
| ERROR | 0 | docs_error=0 | ✅ |
| not_loaded | 0 | restricted+error=0 | ✅ |

## Recovery progress (iter4.2 → iter5)

| Source group | iter4.2 | iter4.3 | iter4.4 | iter5 |
|-------------|---------|---------|---------|-------|
| SAOS #12-21 (×10) | RESTRICTED | OK | OK | **OK** |
| Katowice #24 | ERROR | OK | OK | **OK** |
| UOKiK #35 | ERROR | ERROR | OK | **OK** |
| EUR-Lex #25-34 (×10) | OK | RESTRICTED | ERROR (WAF) | **OK** ← browser fallback |

## Transport ladder summary

| Method | Attempts | OK | Fallback |
|--------|----------|----|-----------| 
| direct_httpx | 920 | 910 | 10 → browser |
| browser_playwright | 10 | 10 | — |

All 10 browser fallbacks triggered by `EURLEX_WAF_CHALLENGE`:
EUR-Lex returns HTTP 202 with 0 bytes (AWS WAF challenge) for direct httpx requests.
Playwright renders the page through the WAF challenge and returns full HTML content (76KB-4.2MB).

## Code changes (Iteration 5)

1. **`legal_ingest/reason_codes.py`** (NEW): Canonical reason code constants + `classify_error()`.
2. **`legal_ingest/fetch_browser.py`** (NEW): Playwright-based browser fetcher with lazy Chromium init, rendered HTML extraction, same `FetchResult` contract.
3. **`legal_ingest/fetch.py`** (MODIFY): Transport ladder in `fetch_source()` — `direct_httpx` → `browser_playwright` on `EurlexWafChallengeError` / `RemoteProtocolError`. `_make_attempt()` for structured telemetry. `BROWSER_FALLBACK_ERRORS` tuple.
4. **`legal_ingest/pipeline.py`** (MODIFY): Unpacks `(FetchResult, attempt_log)` tuple. Writes `fetch_attempts.jsonl`. Browser cleanup at finalize.
5. **`scripts/build_iter5_reports.py`** (NEW): Report builder using `fetch_attempts.jsonl` for reason codes and transport methods.
6. **`tests/unit/test_transport_ladder.py`** (NEW): 10 unit tests for reason codes, transport ladder, fallback policy.
7. **`tests/integration/test_pipeline_artifacts.py`** (MODIFY): Fixed mocks for `(FetchResult, [])` tuple return.

## Quality gates

```
ruff check .  → All checks passed!
pytest -q     → 68 passed
```

## Canonical run path

```bash
cd 2026-03-01__legaldocs_ingest__foundation && source venv/bin/activate
python -m legal_ingest.cli --env-file .env validate-config --config configs/config.caslaw_v22.full.yml
python -m legal_ingest.cli --env-file .env ensure-indexes --config configs/config.caslaw_v22.full.yml
python -m legal_ingest.cli --env-file .env ingest --config configs/config.caslaw_v22.full.yml
python scripts/build_iter5_reports.py iter5_caslaw_v22_full_browser iter5
```
