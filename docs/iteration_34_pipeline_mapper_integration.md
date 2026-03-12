# Iteration 34 — Pipeline Mapper Integration

**Branch:** `codex/shared-v2-pipeline-adapter`
**Date:** 2026-03-03
**Risk:** high (end-to-end backend flow, multipart, mapping)

## Summary

Connected real `OCRPipelineOrchestrator.run_full_pipeline` to `/api/v2/case/documents/analyze` endpoint via a strict mapper that converts canonical schema checklist items into UI v2 contract.

## TODO Results

| # | TODO | Status |
|---|---|---|
| 1 | RequestValidationError/HTTPException → unified error format | ✅ |
| 2 | Intake response `case_status="parsed"` | ✅ |
| 3 | Real pipeline path (`PIPELINE_STUB=false`) | ✅ |
| 4 | Mapper: canonical → UI v2 contract | ✅ |
| 5 | Tests: coverage, snapshot, unified format, pipeline integration | ✅ |
| 6 | Docs iteration report | ✅ |

## Files Changed

| File | Status | Key Changes |
|---|---|---|
| `app/api/errors.py` | MOD | +RequestValidationError handler, +HTTPException handler |
| `app/api/models.py` | MOD | +`case_status` in IntakeResponse, +`analysis_run_id`/`warnings` in DocumentAnalyzeResponse |
| `app/api/service.py` | MOD | Split stub/real paths, +`save_upload`, +`handle_documents_analyze_real` |
| `app/api/router.py` | MOD | Save files, route stub vs real, catch pipeline exceptions |
| `app/api/mapper.py` | **NEW** | 22 item_id → UI v2 mapping, canonical → summary_fields/fields_meta/questions/missing_docs |
| `tests/test_api_validation.py` | MOD | +2 framework unified format tests (17 total) |
| `tests/test_api_intake_contract.py` | MOD | +`case_status` test (12 total) |
| `tests/test_api_analyze_contract.py` | — | Unchanged (10 tests) |
| `tests/test_mapper_coverage.py` | **NEW** | 4 tests: all 22 item_ids matched, valid fields/doc_types |
| `tests/test_mapper_snapshot.py` | **NEW** | 8 tests: fixture parsed_json → UI contract |
| `tests/test_api_pipeline_integration.py` | **NEW** | 4 tests: stub/real routing, failure handling, analysis_run_id |

## Commands & Results

```
ruff check .       → All checks passed
ruff format --check → All files formatted
pytest (targeted)  → 55 passed in 0.38s
pytest -q (full)   → 205 passed in 2.96s
```

## Risks / Next Steps

1. `handle_documents_analyze_real` imports Settings/OCRClient lazily — needs env vars for real pipeline
2. CORS still `*` for dev
3. Frontend integration: consume `case_status`, `analysis_run_id`, `warnings`
4. FS storage still MVP — Supabase migration planned
