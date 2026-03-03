# Iteration 5.2: Release Readiness Report

**Branch**: `exp/iter1-lex-saos-fixes`
**Date**: 2026-03-03

## Merge-Ready Checklist

| Gate | Status | Evidence |
|------|--------|----------|
| Mode A: 38/38 OK | ✅ PASS | R1/R2/R3 = 920/920 each |
| Mode B: graceful degradation | ✅ PASS | 910/920 OK, 10 EUR-Lex WAF, no crash |
| Stability: 3 consecutive runs | ✅ PASS | 100% success rate (3/3) |
| Telemetry: 37 primaries in fetch_attempts | ✅ PASS | Invariant check PASS |
| reason_code/reason_text completeness | ✅ PASS | No null in not_loaded |
| Consistency: status ↔ run_report | ✅ PASS | restricted/error match |
| `ruff check .` | ✅ PASS | All checks passed |
| `pytest -q` | ✅ PASS | 68 passed |
| Canonical config unchanged per run | ✅ PASS | CLI `--run-id`/`--artifact-dir` overrides |
| README up to date | ✅ PASS | Architecture, setup, CLI, limitations |
| `doctor` preflight | ✅ PASS | JSON output, exit code |

## Stability Table (3× Mode A)

| Run | docs_ok | docs_error | browser_ok | browser_fail | #23 MS | #24 Katowice | Duration |
|-----|---------|------------|------------|-------------|--------|-------------|----------|
| r1 | 920 | 0 | 10 | 0 | OK | OK | ~6min |
| r2 | 920 | 0 | 10 | 0 | OK | OK | ~6min |
| r3 | 920 | 0 | 10 | 0 | OK | OK | ~6min |

**Success rate**: 100% (3/3). #23/#24 court sources: 3/3 OK each (formerly transient disconnects, now handled).

**Court source mitigation**: Added `orzeczenia.ms.gov.pl` and `orzeczenia.katowice.sa.gov.pl` to `browser_fallback.allowed_domains` + `httpx.RemoteProtocolError` in `BROWSER_FALLBACK_ERRORS`. If direct httpx disconnect → browser fallback. Result: 3/3 stable.

## Mode B Error Profile (browser disabled)

| Source | reason_code | Expected |
|--------|------------|----------|
| s25_eurlex_dir13 | EURLEX_WAF_CHALLENGE | ✅ |
| s26_eurlex_celex13 | EURLEX_WAF_CHALLENGE | ✅ |
| s27_eurlex_guide | EURLEX_WAF_CHALLENGE | ✅ |
| s28_eurlex_reg861 | EURLEX_WAF_CHALLENGE | ✅ |
| s29_eurlex_reg1896 | EURLEX_WAF_CHALLENGE | ✅ |
| s30_eurlex_reg805 | EURLEX_WAF_CHALLENGE | ✅ |
| s31_curia_137830 | EURLEX_WAF_CHALLENGE | ✅ |
| s32_curia_237043 | EURLEX_WAF_CHALLENGE | ✅ |
| s33_curia_74812 | EURLEX_WAF_CHALLENGE | ✅ |
| s34_curia_guide | EURLEX_WAF_CHALLENGE | ✅ |

`transport_metrics: {direct_attempts: 920, browser_attempts: 0}` — no browser attempted, pipeline completed normally.

## Code Changes (iter5.2)

1. **`legal_ingest/fetch.py`**: `.attempt_log` attached to ALL exceptions (fallback-skipped, non-fallback, browser ImportError, browser generic). `httpx.RemoteProtocolError` added to `BROWSER_FALLBACK_ERRORS`.
2. **`legal_ingest/pipeline.py`**: Error handler extracts `attempt_log` from exceptions via `getattr(e, "attempt_log", None)`.
3. **`configs/config.caslaw_v22.full.yml`**: Court domains in `allowed_domains`, circuit breaker bumped to 25.
4. **`configs/config.caslaw_v22.mode_b.yml`**: NEW — full 38-source config with `browser_fallback.enabled=false`.
5. **`scripts/build_iter5_reports.py`**: Rewritten with invariant checks (telemetry coverage, reason completeness, consistency), `reason_text` + `last_exception_class` in not_loaded.

## Known Limitations

- **Playwright CI**: Requires `python -m playwright install chromium`.
- **EUR-Lex WAF**: Bypass via headless Chromium; may need upgrade if anti-bot strengthens.
- **SAOS**: `s11_saos_search` expands to ~883 judgments; no telemetry for search source itself (by design).
