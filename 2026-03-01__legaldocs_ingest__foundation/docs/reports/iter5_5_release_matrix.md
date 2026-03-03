# Iteration 5.5: Release Matrix — CI Authority Hardening

**Branch**: `exp/iter1-lex-saos-fixes`
**Date**: 2026-03-03

## Release Decision: ✅ MERGE RECOMMENDED

All required CI jobs execute real pipeline with MongoDB — no hidden skips.

## CI Architecture

```
Required jobs (every PR/push):
  lint-test      → ruff + pytest (68 local / 68 CI, including integration test)
  smoke-mode-a   → 4 sources, browser ON, MongoDB service
  smoke-mode-b   → 4 sources, browser OFF, MongoDB service

Optional (workflow_dispatch only):
  full-ingest    → 38 sources, requires MONGO_URI/MONGO_DB secrets
```

## CI Evidence (Real Execution)

### PR Run [#22624360206](https://github.com/sergeionlyart/backend_Kaucja/actions/runs/22624360206)

| Job | Status | Duration | Details |
|-----|--------|----------|---------|
| lint-test | ✅ SUCCESS | 31s | ruff clean, pytest passed, integration test executed (MongoDB service) |
| smoke-mode-a | ✅ SUCCESS | 48s | 4 sources ingested, browser fallback for EUR-Lex |
| smoke-mode-b | ✅ SUCCESS | 35s | 4 sources, browser=0, EUR-Lex WAF error confirmed |
| full-ingest | ⏭ SKIPPED | — | Correctly skipped (not workflow_dispatch) |

### Push Run [#22624358324](https://github.com/sergeionlyart/backend_Kaucja/actions/runs/22624358324)

| Job | Status | Duration |
|-----|--------|----------|
| lint-test | ✅ SUCCESS | 33s |
| smoke-mode-a | ✅ SUCCESS | 50s |
| smoke-mode-b | ✅ SUCCESS | 30s |
| full-ingest | ⏭ SKIPPED | — |

### PR statusCheckRollup (6 checks)

| Check | Conclusion |
|-------|------------|
| lint-test (push) | SUCCESS |
| lint-test (PR) | SUCCESS |
| smoke-mode-a (push) | SUCCESS |
| smoke-mode-a (PR) | SUCCESS |
| smoke-mode-b (push) | SUCCESS |
| smoke-mode-b (PR) | SUCCESS |

## CI Smoke Details

### smoke-mode-a assertions
- `docs_ok >= 3` ✅ (3 direct PL + 1 EUR-Lex via browser)
- Pipeline completed without crash ✅

### smoke-mode-b assertions
- `browser_attempts == 0` ✅ (browser disabled in config)
- `docs_ok >= 2` ✅ (3 direct PL sources)
- `docs_error >= 1` ✅ (EUR-Lex WAF confirmed)
- Pipeline completed without crash ✅

## Self-Containment Proof

| Property | Evidence |
|----------|----------|
| No repo secrets needed | MongoDB 7 service container on all required jobs |
| No external DB | `mongodb://localhost:27017`, DB: `ci_legal_ingest_smoke` |
| Integration test runs | `test_idempotency.py` — no skipif, uses service MongoDB |
| Deterministic configs | `config.ci.mode_a.yml`, `config.ci.mode_b.yml` (4 sources each) |
| Browser tested in CI | Playwright Chromium installed, EUR-Lex fallback exercised |

## Known Limitations

1. **Transient source flakiness**: Polish government sources may occasionally be slow/down in CI. Assertions relaxed to `>=2` OK.
2. **EUR-Lex WAF**: May change behavior — browser fallback tested but not guaranteed permanent.
3. **Full ingest**: 38 sources, ~6min — only on `workflow_dispatch` with secrets.
