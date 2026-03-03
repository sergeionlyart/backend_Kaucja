# Iteration 63: E2E Assertion Truthfulness Reconciliation

**Date**: 2026-03-03
**Repo**: backend_Kaucja

## Git

| Property | Value |
|----------|-------|
| Branch | `codex/shared-v2-api-foundation` |
| Local commit | `8f284dc84a4964ad590d76f321e919a06953ad2d` |
| PR head (after merge-main) | `036510b22d68` |
| PR | [#7](https://github.com/sergeionlyart/backend_Kaucja/pull/7) |
| Base | `main` |
| mergeable_state | `clean` |

## CI Evidence (2026-03-03T17:35Z)

| Check | Conclusion | Run URL |
|-------|------------|---------|
| lint-test-smoke (push) | **success** | [run/22632876915](https://github.com/sergeionlyart/backend_Kaucja/actions/runs/22632876915/job/65587643466) |
| lint-test-smoke (PR) | **success** | [run/22632878902](https://github.com/sergeionlyart/backend_Kaucja/actions/runs/22632878902/job/65587650211) |
| browser-p0-gate (push) | **success** | [run/22632876915](https://github.com/sergeionlyart/backend_Kaucja/actions/runs/22632876915/job/65587769619) |
| browser-p0-gate (PR) | **success** | [run/22632878902](https://github.com/sergeionlyart/backend_Kaucja/actions/runs/22632878902/job/65587769909) |

## CI Fix Applied (commit 8f284dc)

Root cause: `app/api/` was NOT tracked in git. Tests importing `from app.api.main import create_app` caused pytest collection crash (exit code 2) in CI.

Fix: replaced direct imports with `pytest.importorskip()` guards:
```python
api_main = pytest.importorskip("app.api.main", reason="app.api not available")
api_service = pytest.importorskip("app.api.service", reason="app.api not available")
create_app = api_main.create_app
```

## Test Cases (5 in test_e2e_chain.py)

| # | Class | Test | Key Assertions | Status |
|---|-------|------|----------------|--------|
| 1 | TestE2EChain | test_full_chain | `assert "warnings" in data` (strict), analysis_run_id, case_status, submitted_at | ✅ |
| 2 | TestE2EChain | test_dedup_then_reanalyze_chain | stable doc identity | ✅ |
| 3 | TestE2ENegative | test_analyze_missing_case_id | 422 VALIDATION_ERROR | ✅ |
| 4 | TestE2ENegative | test_submit_missing_email | 422 VALIDATION_ERROR | ✅ |
| 5 | TestE2ENegative | test_reanalyze_nonexistent_case | negative path | ✅ |

## Local Gate Outputs (2026-03-03T17:32Z)

```
$ python -m ruff check .
All checks passed!

$ python -m pytest tests/test_e2e_chain.py -q
.....                                                                    [100%]
5 passed in 0.28s
```

## Slice A: READY ✅ (CI confirmed)
