# Iteration 63: E2E Assertion Truthfulness Reconciliation

**Date**: 2026-03-03
**Repo**: backend_Kaucja
**Branch**: `codex/shared-v2-api-foundation`
**Commit**: see Git section below

## Summary

Strict warnings presence assertions in test_e2e_chain.py. Verified case_status, submitted_at, analysis_run_id, warnings contract, negative error-format scenarios.

## Test Cases (5 in test_e2e_chain.py)

| # | Class | Test | Key Assertions | Status |
|---|-------|------|----------------|--------|
| 1 | TestE2EChain | test_full_chain | analyze: `warnings` strict presence + type, `analysis_run_id`, docs status=done; reanalyze: `warnings` strict presence + type; submit: `case_status`, `submitted_at` | ✅ |
| 2 | TestE2EChain | test_dedup_then_reanalyze_chain | stable doc identity after SHA dedup | ✅ |
| 3 | TestE2ENegative | test_analyze_missing_case_id | 422, `error.code=="VALIDATION_ERROR"` | ✅ |
| 4 | TestE2ENegative | test_submit_missing_email | 422, `error.code=="VALIDATION_ERROR"` | ✅ |
| 5 | TestE2ENegative | test_reanalyze_nonexistent_case | negative scenario | ✅ |

## Raw Gate Outputs

```
$ source .venv/bin/activate && python -m ruff check .
All checks passed!
```

```
$ python -m pytest tests/test_e2e_chain.py -v
platform darwin -- Python 3.11.5, pytest-9.0.2, pluggy-1.6.0
plugins: anyio-4.12.1
collected 5 items

tests/test_e2e_chain.py::TestE2EChain::test_full_chain PASSED              [ 20%]
tests/test_e2e_chain.py::TestE2EChain::test_dedup_then_reanalyze_chain PASSED [ 40%]
tests/test_e2e_chain.py::TestE2ENegative::test_analyze_missing_case_id PASSED [ 60%]
tests/test_e2e_chain.py::TestE2ENegative::test_submit_missing_email PASSED [ 80%]
tests/test_e2e_chain.py::TestE2ENegative::test_reanalyze_nonexistent_case PASSED [100%]

5 passed in 0.33s
```

```
$ python -m pytest -q
277 passed in 3.84s
```

## Why test count differs from previous report

| Metric | Previous (Task 32 report) | Current (Task 33) | Reason |
|--------|---------------------------|--------------------|--------|
| test_e2e_chain.py | 4 tests | 5 tests | +1: `test_reanalyze_nonexistent_case` was added between reports (already existed in repo, not in previous count) |
| Full suite | 276 tests | 277 tests | Same +1 delta |
| Skipped | 0 | 0 | No change |
| Warnings assertions | `.get()` fallback | Strict `assert 'warnings' in data` | Hardened: key must be present, then type-checked via `data[key]` |

## Slice A: READY ✅
All e2e assertions truthful with strict presence checks. 277/277 pass.
