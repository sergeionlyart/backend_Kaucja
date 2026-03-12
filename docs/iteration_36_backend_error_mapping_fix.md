# Iteration 36 — Backend Error Mapping Fix (Task 5A)

**Branch:** `codex/shared-v2-error-mapping-fix`
**Date:** 2026-03-03

## TODO Results

| # | TODO | Status |
|---|---|---|
| 1 | Normalize `result.error_code` (UPPER_SNAKE + lowercase) | ✅ |
| 2 | Fail-closed behavior (error_code → always API error, never 200) | ✅ |
| 3 | Rewrite prompt_name test to verify orchestrator call | ✅ |
| 4 | Tests for UPPER_SNAKE codes | ✅ |
| 5 | Ruff/tests green | ✅ |

## Files Changed

| File | Changes |
|---|---|
| `app/api/service.py` | Normalize error_code to lowercase, extended code sets (OCR_API_ERROR, LLM_API_ERROR, LLM_INVALID_JSON, CONTEXT_TOO_LARGE), fail-closed fallback for unknown codes + no-parsed_json |
| `tests/test_api_pipeline_integration.py` | Full rewrite: 24 tests, shared helpers `_run_with_orchestrator_result`/`_make_settings_mock`, patches at source modules |

## Error Code Mapping

| Pipeline Code | Normalized | API Code | HTTP |
|---|---|---|---|
| ocr_failed, OCR_FAILED, ocr_all_failed, ocr_timeout, OCR_API_ERROR | ocr_* | OCR_FAILED | 502 |
| llm_failed, LLM_FAILED, llm_refused, LLM_API_ERROR, LLM_INVALID_JSON, context_too_large, CONTEXT_TOO_LARGE | llm_* | LLM_FAILED | 502 |
| validation_failed, json_parse_failed, PIPELINE_VALIDATION_FAILED | validation_* | PIPELINE_VALIDATION_FAILED | 422 |
| (unknown) | — | INTERNAL_ERROR | 500 |
| (no error_code + no parsed_json) | — | INTERNAL_ERROR | 500 |

## Commands & Results

```
ruff format + check → All passed
pytest (targeted)   → 24 passed in 0.45s
pytest -q (full)    → 227 passed in 3.33s
```
