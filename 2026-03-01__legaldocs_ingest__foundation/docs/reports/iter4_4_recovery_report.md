# Iteration 4.4: Recovery Report

**Run ID**: `iter4_4_caslaw_v22_full`
**Config**: `configs/config.caslaw_v22.full.yml` (38 sources → 920 with SAOS expansion)
**Pipeline metrics**: `sources_total=920, docs_ok=910, docs_restricted=0, docs_error=10`
**Primary sources**: **OK=28, RESTRICTED=0, ERROR=10** (total=38)

## Evidence source of truth

| File | Role | Authority |
|------|------|-----------|
| `artifacts_iter4/runs/iter4_4_caslaw_v22_full/run_report.json` | Pipeline metrics | Canonical — final pipeline counts |
| `artifacts_iter4/runs/iter4_4_caslaw_v22_full/logs.jsonl` | Per-source logs | Canonical — raw evidence |
| `docs/reports/iter4_4_source_status.json` | Per-source status | Derived from logs.jsonl |
| `docs/reports/iter4_4_not_loaded.json` | Not-OK sources | Derived from source_status |
| `docs/reports/iter4_4_recovery_probes.json` | Probe-only results | Supplementary — stateless probes, no retries |
| `docs/reports/iter4_4_recovery_report.md` | This report | Derived — must match JSON artifacts |

> [!IMPORTANT]
> Recovery probes do NOT use tenacity retries — they are single-attempt per-round. Pipeline uses
> exponential backoff with 6 retries. Therefore pipeline outcome may differ from probe outcome
> (e.g., #24 Katowice: pipeline=OK via retry, probe=ERROR on malformed headers).

## Consistency verification

| Metric | source_status.json | run_report.json | Match |
|--------|-------------------|-----------------|-------|
| RESTRICTED | 0 | docs_restricted=0 | ✅ |
| ERROR | 10 | docs_error=10 | ✅ |
| not_loaded | 10 | restricted+error=10 | ✅ |

## Recovery progress (iter4.2 → iter4.3 → iter4.4)

| Source group | iter4.2 | iter4.3 | iter4.4 | Change |
|-------------|---------|---------|---------|--------|
| SAOS #12-21 | RESTRICTED (10) | OK (10) | OK (10) | ✅ API back |
| Katowice #24 | ERROR | OK | OK | ✅ Pipeline retry |
| UOKiK #35 | ERROR | ERROR | **OK** | ✅ Server recovered |
| EUR-Lex #25-34 | OK | RESTRICTED | **ERROR** | ❌ WAF challenge |

## Not Loaded (10 of 38 primary sources)

### EURLEX_WAF_CHALLENGE (10)

All EUR-Lex sources return HTTP 202 with 0 bytes (AWS WAF challenge).

| # | source_id | URL | Evidence |
|---|-----------|-----|----------|
| 25 | s25_eurlex_dir13 | `CELEX:32011L0083` | HTTP 202, 0 bytes, AWSALB cookie |
| 26 | s26_eurlex_celex13 | `CELEX:32013R0524` | HTTP 202, 0 bytes |
| 27 | s27_eurlex_guide | `CELEX:32013H0396` | HTTP 202, 0 bytes |
| 28 | s28_eurlex_reg861 | `CELEX:32007R0861` | HTTP 202, 0 bytes |
| 29 | s29_eurlex_reg1896 | `CELEX:32006R1896` | HTTP 202, 0 bytes |
| 30 | s30_eurlex_reg805 | `CELEX:32004R0805` | HTTP 202, 0 bytes |
| 31 | s31_curia_137830 | `CELEX:62011CJ0415` | HTTP 202, 0 bytes |
| 32 | s32_curia_237043 | `CELEX:62019CJ0725` | HTTP 202, 0 bytes |
| 33 | s33_curia_74812 | `CELEX:62008CJ0243` | HTTP 202, 0 bytes |
| 34 | s34_curia_guide | `OJ:C:2019:380:FULL` | HTTP 202, 0 bytes |

> **Root cause**: EUR-Lex eur-lex.europa.eu is behind AWS WAF which serves HTTP 202 with empty body
> to programmatic clients. All 10 sources were OK in iter4.2 (76KB-4.2MB). This is a transient
> WAF block — requires either browser-based fetch (Playwright) or waiting for WAF policy change.
> Playwright is not installed in the current venv.

## Recovery probe results (3 rounds)

| Target | Round 1 | Evidence |
|--------|---------|----------|
| SAOS #12-21 (×10) | **OK** | 18-96KB real JSON |
| #24 Katowice | EXTERNAL_MALFORMED_HEADERS | `illegal header line` (null byte in Connection header) |
| #25 EUR-Lex | EURLEX_WAF_CHALLENGE | 0 bytes, 3/3 rounds |
| #31 EUR-Lex | EURLEX_WAF_CHALLENGE | 0 bytes, 3/3 rounds |
| #35 UOKiK | **OK** | 264KB PDF |

> #24 Katowice: probe fails on malformed headers, but **pipeline succeeds** via tenacity retries.
> Pipeline evidence: `Fetched source bytes=26617, Document saved successfully pages=5`.

## Code changes (Iteration 4.4)

1. **`legal_ingest/fetch.py`**: Added `EurlexWafChallengeError`, `is_eurlex_waf_challenge()`, `EURLEX_DOMAINS`. `fetch_direct()` raises on WAF challenge.
2. **`scripts/build_iter4_reports.py`**: Machine-readable error classification: `EURLEX_WAF_CHALLENGE`, `EXTERNAL_MALFORMED_HEADERS`, `EXTERNAL_TIMEOUT`, `EXTERNAL_DISCONNECT`.
3. **`scripts/recover_iter4_sources.py`**: Added EUR-Lex probe targets with WAF detection, writes to `iter4_4_recovery_probes.json`.
4. **`tests/unit/test_eurlex_waf.py`** (NEW): 8 unit tests for WAF detection.

## Quality gates

```
ruff check .  → All checks passed!
pytest -q     → 56 passed
```

## Canonical run path

```bash
cd 2026-03-01__legaldocs_ingest__foundation && source venv/bin/activate
python -m legal_ingest.cli --env-file .env validate-config --config configs/config.caslaw_v22.full.yml
python -m legal_ingest.cli --env-file .env ensure-indexes --config configs/config.caslaw_v22.full.yml
python -m legal_ingest.cli --env-file .env ingest --config configs/config.caslaw_v22.full.yml
python scripts/build_iter4_reports.py iter4_4_caslaw_v22_full iter4_4
python scripts/recover_iter4_sources.py
```
