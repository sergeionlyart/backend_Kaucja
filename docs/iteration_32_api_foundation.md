# Iteration 32 — API Foundation (MVP)

**Branch:** `codex/shared-v2-api-foundation`  
**Date:** 2026-03-03  
**Risk:** medium (new public API surface)

## What Was Done

1. ✅ Added FastAPI scaffold and router `/api/v2`
2. ✅ `GET /api/v2/health` → `{"status":"ok"}`
3. ✅ `POST /api/v2/case/intake` — saves case_id + intake_text to FS, returns UI-compatible response shape (summary_fields, fields_meta, open_questions, missing_docs)
4. ✅ `POST /api/v2/case/documents/analyze` — multipart/form-data with validation: files ↔ files_category count match, MIME type check (PDF/JPEG/PNG/WebP/HEIC), file size limit (20 MB), unified error body (422/415/413)
5. ✅ `POST /api/v2/case/submit` — status → `report_sent`
6. ✅ `PIPELINE_STUB=true` branch for analyze (deterministic UI-compatible response without OCR/LLM)
7. ✅ 24 new API tests green, 174 total tests green
8. ✅ Ruff check + format clean

## Files Changed

| File | Status |
|---|---|
| `pyproject.toml` | MODIFIED — added fastapi, uvicorn, python-multipart, httpx |
| `app/api/__init__.py` | NEW |
| `app/api/errors.py` | NEW — unified error handler |
| `app/api/models.py` | NEW — Pydantic v2 request/response models |
| `app/api/service.py` | NEW — FS storage, intake parsing, stub pipeline |
| `app/api/router.py` | NEW — 4 endpoints |
| `app/api/main.py` | NEW — FastAPI app factory |
| `tests/test_api_validation.py` | NEW — 13 tests (health, intake, analyze, submit validation) |
| `tests/test_api_intake_contract.py` | NEW — 11 tests (response shape, parsing, case_id) |
| `docs/iteration_32_api_foundation.md` | NEW — this file |

## Commands Run

```
git checkout -b codex/shared-v2-api-foundation
pip install fastapi uvicorn python-multipart httpx

python3.11 -m ruff check .           → All checks passed
python3.11 -m ruff format --check .  → 8 files already formatted
python3.11 -m pytest -q              → 174 passed in 3.45s

python3.11 -m uvicorn app.api.main:app --host 127.0.0.1 --port 8502
curl -s http://127.0.0.1:8502/api/v2/health → {"status":"ok"}
```

## NOT Done (by design)

- Did NOT connect real `run_full_pipeline`
- Did NOT change `app/pipeline/orchestrator.py`, `app/prompts/canonical_prompt.txt`, `app/schemas/canonical_schema.json`
- Did NOT make UI changes in `UI_UX_Kaucja`

## Risks / Blockers for Next Iteration

1. **CORS `*`** — acceptable for MVP, must restrict for production
2. **FS storage** — adequate for MVP, will need PostgreSQL/Supabase for multi-user
3. **Regex intake parsing** — works for Polish, should be replaced with LLM structured output in next iteration
4. **No auth** — acceptable for local dev, must add before any deployment
