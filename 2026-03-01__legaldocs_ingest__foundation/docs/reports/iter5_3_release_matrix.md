# Iteration 5.3: Release Matrix

**Branch**: `exp/iter1-lex-saos-fixes`
**Date**: 2026-03-03

## Release Decision: ✅ MERGE RECOMMENDED

All quality gates pass. 38/38 primary sources loaded in Mode A, deterministic degradation in Mode B, full telemetry coverage, CI pipeline in place.

## Mode A vs Mode B Matrix

| Metric | Mode A (browser ON) | Mode B (browser OFF) |
|--------|---------------------|---------------------|
| **config** | `config.caslaw_v22.full.yml` | `config.caslaw_v22.mode_b.yml` |
| **run_id** | `iter5_3_mode_a` | `iter5_3_mode_b` |
| **sources_total** | 920 | 920 |
| **docs_ok** | 920 | 910 |
| **docs_error** | 0 | 10 |
| **primary OK** | 38/38 | 28/38 |
| **browser_attempts** | 10 | 0 |
| **browser_success** | 10 | 0 |
| **fallback triggers** | EURLEX_WAF_CHALLENGE × 10 | — |
| **telemetry coverage** | 38/38 ✅ | 38/38 ✅ |
| **reason completeness** | 0 null ✅ | 0 null ✅ |
| **pipeline crash** | No ✅ | No ✅ |

## Mode B Error Profile (deterministic)

All 10 errors are EUR-Lex/Curia sources blocked by AWS WAF challenge:

| # | source_id | reason_code | transport |
|---|-----------|-------------|-----------|
| 25 | s25_eurlex_dir13 | EURLEX_WAF_CHALLENGE | direct_httpx |
| 26 | s26_eurlex_celex13 | EURLEX_WAF_CHALLENGE | direct_httpx |
| 27 | s27_eurlex_guide | EURLEX_WAF_CHALLENGE | direct_httpx |
| 28 | s28_eurlex_reg861 | EURLEX_WAF_CHALLENGE | direct_httpx |
| 29 | s29_eurlex_reg1896 | EURLEX_WAF_CHALLENGE | direct_httpx |
| 30 | s30_eurlex_reg805 | EURLEX_WAF_CHALLENGE | direct_httpx |
| 31 | s31_curia_137830 | EURLEX_WAF_CHALLENGE | direct_httpx |
| 32 | s32_curia_237043 | EURLEX_WAF_CHALLENGE | direct_httpx |
| 33 | s33_curia_74812 | EURLEX_WAF_CHALLENGE | direct_httpx |
| 34 | s34_curia_guide | EURLEX_WAF_CHALLENGE | direct_httpx |

## CI Pipeline

Workflow: `.github/workflows/ci.yml`

| Job | Description |
|-----|-------------|
| `lint-test` | ruff check + pytest (68 tests) |
| `smoke-mode-a` | validate-config, doctor, ingest (full), assert docs_error=0 |
| `smoke-mode-b` | validate-config, ingest (browser disabled), assert browser_attempts=0 |

## Stability Summary (iter5.2)

| Run | docs_ok | docs_error | browser_ok |
|-----|---------|------------|------------|
| r1 | 920 | 0 | 10/10 |
| r2 | 920 | 0 | 10/10 |
| r3 | 920 | 0 | 10/10 |

3/3 = 100% success rate.

## Quality Gates

| Gate | Status |
|------|--------|
| `ruff check .` | ✅ All checks passed |
| `pytest -q` | ✅ 68 passed |
| `validate-config` (Mode A) | ✅ Config is valid |
| `validate-config` (Mode B) | ✅ Config is valid |
| Telemetry 38/38 (Mode A) | ✅ PASS |
| Telemetry 38/38 (Mode B) | ✅ PASS |
| Reason completeness | ✅ 0 null in both modes |
| No `commit --amend` / `force-push` | ✅ |

## Known Limitations

1. **EUR-Lex WAF**: Bypassed via headless Chromium. Future anti-bot measures may require stealth-mode or API fallback.
2. **Playwright CI**: Requires `python -m playwright install chromium` in CI setup step. ~150MB download.
3. **SAOS expansion**: `s11_saos_search` expands to ~883 sub-judgments. Synthetic telemetry record covers the meta-source.
4. **Court disconnects**: `orzeczenia.ms.gov.pl` / `orzeczenia.katowice.sa.gov.pl` now in `allowed_domains` with `RemoteProtocolError` browser fallback. Stable across 3+ consecutive runs.
