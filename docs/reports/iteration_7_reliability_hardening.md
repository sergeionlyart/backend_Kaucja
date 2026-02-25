# Iteration 7 Reliability Hardening Report

## Scope
Finalized reliability hardening for TechSpec alignment (sections 5.1.3, 9.3, runtime error taxonomy):
- real PDF bad-pages rendering,
- retry policy hardening for OCR/LLM,
- full runtime error taxonomy mapping with storage/unknown branches,
- deterministic failure persistence for context-too-large and storage-error scenarios.

## Changes
1. OCR bad pages render:
   - `app/ocr_client/mistral_ocr.py` now renders real PNG pages for PDF `quality.bad_pages` into `documents/<doc_id>/ocr/page_renders/<page>.png` via `pymupdf` (`fitz`).
   - non-PDF inputs keep safe skip behavior and add explicit warning to `quality.json`.
   - placeholder render approach removed.

2. Retry policy:
   - Added reusable retry helper in `app/utils/retry.py`.
   - OCR retry: exactly 1 retry on transient network/timeout/429/5xx (`is_retryable_ocr_exception`).
   - LLM retry: exactly 1 retry on 429/5xx (`is_retryable_llm_exception`).
   - no retry for `LLM_INVALID_JSON`, `LLM_SCHEMA_INVALID`, `CONTEXT_TOO_LARGE`.

3. Error taxonomy and runtime mapping:
   - Added `app/utils/error_taxonomy.py` with canonical codes:
     - `FILE_UNSUPPORTED`, `OCR_API_ERROR`, `OCR_PARSE_ERROR`,
     - `LLM_API_ERROR`, `LLM_INVALID_JSON`, `LLM_SCHEMA_INVALID`,
     - `CONTEXT_TOO_LARGE`, `STORAGE_ERROR`, `UNKNOWN_ERROR`.
   - Added shared user-friendly messages map used by UI.
   - `app/pipeline/orchestrator.py` now classifies storage exceptions into `STORAGE_ERROR` and unknown ones into `UNKNOWN_ERROR`, while preserving technical details in `run.log` and raw artifacts.

4. Persistence hardening:
   - Added guarded persistence helpers in orchestrator for metrics/status/manifest updates in failure paths.
   - Prevented secondary crashes when persistence fails during error handling; storage details are appended to logs.

5. Dependencies:
   - `pyproject.toml`: added `pymupdf>=1.24.0`.

## Tests
Added/updated tests:
- `tests/test_mistral_ocr_client.py`
  - PDF bad-page render path,
  - non-PDF skip warning path,
  - contract safety for artifacts.
- `tests/test_error_taxonomy_retry.py`
  - retry classifiers,
  - taxonomy mapping (including STORAGE/UNKNOWN),
  - status-code extraction.
- `tests/test_reliability_hardening.py`
  - OCR retry success after first failure,
  - LLM retry on 5xx,
  - no-retry branches for invalid JSON/schema,
  - context-too-large failure branch,
  - STORAGE/UNKNOWN mapping branches.

Validation commands executed:
```bash
ruff format .
ruff check .
pytest -q
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```

Outputs:
- `ruff format .` -> `53 files left unchanged`
- `ruff check .` -> `All checks passed!`
- `pytest -q` -> `64 passed in 2.91s`
- build check -> `gradio_app_started`

## Known Limits
1. PDF bad-page render depends on `pymupdf`; when unavailable, OCR continues and records warning in `quality.json`.
2. Retry policy is intentionally strict (single retry) per TechSpec and may still fail under prolonged provider outages.
3. Context guard is char-length based (`context_char_limit`) and conservative; it does not estimate provider-specific tokenization.
