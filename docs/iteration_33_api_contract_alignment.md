# Iteration 33 — API Contract Alignment (TechSpec)

**Branch:** `codex/shared-v2-api-foundation`
**Date:** 2026-03-03
**Risk:** medium-high (breaking API contract changes)

## What Was Done

### 1. Response keys aligned to TechSpec
- `questions` replaces `open_questions` (intake + analyze)
- `analyzed_documents` (array) replaces `documents_by_id` (dict)
- `case_status` replaces `status` (submit)

### 2. Document model aligned with UI v2
- `id` (was `doc_id`)
- `categoryId` camelCase (was `category_id`)
- `sizeMb` camelCase (was `size_mb`)
- `status`: `done|error` (was `analyzed|pending|error`)
- `progress`: int 0..100 (was float 0..1)
- `extracted_fields`, `analyzed_at` retained

### 3. Error format aligned to TechSpec
- All error codes in UPPER_SNAKE_CASE
- Codes: `VALIDATION_ERROR`, `FILES_VALIDATION_ERROR`, `UNSUPPORTED_MEDIA_TYPE`, `PAYLOAD_TOO_LARGE`, `NOT_FOUND`, `INTERNAL_ERROR`
- All errors include `request_id` (uuid hex)
- Optional `details` dict in error body

### 4. Documents/analyze endpoint enhanced
- Added optional `intake_text` Form parameter
- Added `MAX_TOTAL_SIZE_BYTES` (50 MB) aggregate check
- Removed `other` from valid categories (strict TechSpec enum)
- Added `FILES_VALIDATION_ERROR` for file-related 422s

### 5. Tests updated
- `test_api_validation.py`: 15 tests (was 13) — added `other` category rejection + error body structure
- `test_api_intake_contract.py`: 11 tests — `questions` key assertions
- **NEW** `test_api_analyze_contract.py`: 10 tests — document shape, keys, status/progress, questions key, extracted fields, multiple files, missing docs reduction, intake_text param

### 6. AGENTS.md not touched (separate scope)

## Files Changed

| File | Status | Changes |
|---|---|---|
| `app/api/errors.py` | MODIFIED | UPPER_SNAKE codes, `details`+`request_id`, +FILES_VALIDATION_ERROR, +INTERNAL_ERROR |
| `app/api/models.py` | MODIFIED | `questions`, `analyzed_documents`, `case_status`, doc model camelCase |
| `app/api/service.py` | MODIFIED | `questions` key, `analyzed_documents` list, `case_status`, MAX_TOTAL_SIZE, VALID_CATEGORIES |
| `app/api/router.py` | MODIFIED | +intake_text param, MAX_TOTAL_SIZE check, FILES_VALIDATION_ERROR, no `other` |
| `tests/test_api_validation.py` | MODIFIED | TechSpec key assertions, UPPER_SNAKE error codes |
| `tests/test_api_intake_contract.py` | MODIFIED | `questions` key assertions |
| `tests/test_api_analyze_contract.py` | NEW | 10 tests for analyze contract |
| `docs/iteration_33_api_contract_alignment.md` | NEW | This file |

## Commands and Results

```
ruff check .           -> All checks passed
ruff format --check .  -> 9 files already formatted
pytest (API tests)     -> 36 passed in 0.37s
pytest -q (full suite) -> see below
```

## Risks / Next Steps

1. **Frontend V2 must update** `open_questions` -> `questions`, `documents_by_id` -> loop over `analyzed_documents`, `status` -> `case_status`
2. **Pipeline adapter** needed — `handle_documents_analyze` currently returns stub; real pipeline integration is next task
3. **camelCase doc fields** (`categoryId`, `sizeMb`) — intentional UI compat; backend-internal may differ
