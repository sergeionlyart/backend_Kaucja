# Iteration 35 — Backend Hardening (Task 4A)

**Branch:** `codex/shared-v2-backend-hardening`
**Date:** 2026-03-03

## TODO Results

| # | TODO | Status |
|---|---|---|
| 1 | Configurable prompt_name/version from Settings | ✅ |
| 2 | HTTPException mapping (404→NOT_FOUND, 405→METHOD_NOT_ALLOWED, etc.) | ✅ |
| 3 | Pipeline error codes (OCR_FAILED, LLM_FAILED, PIPELINE_VALIDATION_FAILED) | ✅ |
| 4 | Tests (HTTP mapping, prompt config, pipeline error codes) | ✅ |
| 5 | Iteration report | ✅ |

## Files Changed

| File | Changes |
|---|---|
| `app/api/errors.py` | +HTTP status→code mapping dict, +`ocr_failed`/`llm_failed`/`pipeline_validation_failed` helpers |
| `app/api/service.py` | Use `settings.default_prompt_name`/`default_prompt_version`, classify `error_code` into specific ApiErrors |
| `app/api/router.py` | Re-raise ApiError from pipeline, import ApiError |
| `tests/test_api_validation.py` | +2 tests (HTTP 404, 405 mapping) |
| `tests/test_api_pipeline_integration.py` | +4 tests (prompt config, OCR_FAILED/LLM_FAILED/PIPELINE_VALIDATION_FAILED) |

## Commands & Results

```
ruff format + check → All passed
pytest (targeted)   → 31 passed in 0.35s
pytest -q (full)    → 211 passed in 3.32s
```
