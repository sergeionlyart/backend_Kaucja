# Iteration 4 Full E2E Pipeline Report

## Summary
Implemented full E2E pipeline for MVP flow:
`OCR -> pack_documents -> LLM structured output -> validate_output -> persist -> UI`.

Completed:
- Added ExecPlan for Iteration 4 in `PLANS.md`.
- Added run-level LLM artifacts:
  - `llm/request.txt`
  - `llm/response_raw.txt`
  - `llm/response_parsed.json`
  - `llm/validation.json`
- Extended `StorageRepo`:
  - `upsert_llm_output`, `get_llm_output`
  - `update_run_metrics` (`timings_json`, `usage_json`, `usage_normalized_json`, `cost_json`)
  - persisted error fields via run status updates.
- Integrated full orchestrator flow:
  - OCR stage
  - document packing (`<BEGIN_DOCUMENTS> ... <END_DOCUMENTS>`)
  - LLM call by provider (openai/google)
  - validation (schema + invariants)
  - artifact and DB persistence
  - run status mapping (`completed` or `failed` with `LLM_API_ERROR`, `LLM_INVALID_JSON`, `LLM_SCHEMA_INVALID`, etc.)
- Updated Gradio Analyze callback to full pipeline outputs:
  - OCR table
  - human summary (`critical_gaps_summary`, `next_questions_to_user`)
  - raw JSON
  - validation state/errors
  - metrics (tokens/cost/timings)
- Added runtime preflight checks (SDK + API keys) with user-readable UI error messages.
- Added unit/integration tests for repo, orchestrator branches, full integration, schema-invalid scenario, and UI smoke.

## Git pre-steps
- Iteration 3 committed separately on branch `codex/iteration-3-llm`:
  - `fab31f8 feat: implement iteration 3 llm clients and validation`
- Working branch for this task:
  - `codex/iteration-4-e2e`

## Commands Run
```bash
ruff format .
ruff check .
pytest -q
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```

Outputs:
- `ruff format .` -> `41 files left unchanged`
- `ruff check .` -> `All checks passed!`
- `pytest -q` -> `42 passed in 2.74s`
- build check -> `gradio_app_started`

## Demo artifacts (mocked E2E run)
- Session: `2d698018-6d42-4067-a2dc-c2e2b9aa5e1f`
- Run: `bf32f8a3-161c-45b4-88ec-3e561172a26f`
- Run root:
  - `data/sessions/2d698018-6d42-4067-a2dc-c2e2b9aa5e1f/runs/bf32f8a3-161c-45b4-88ec-3e561172a26f`
- LLM artifacts:
  - `.../llm/request.txt`
  - `.../llm/response_raw.txt`
  - `.../llm/response_parsed.json`
  - `.../llm/validation.json`
- OCR artifacts example:
  - `.../documents/0000001/ocr/combined.md`
  - `.../documents/0000001/ocr/raw_response.json`

## Files changed
- `PLANS.md`
- `app/storage/artifacts.py`
- `app/storage/models.py`
- `app/storage/repo.py`
- `app/pipeline/orchestrator.py`
- `app/ui/gradio_app.py`
- `tests/test_artifacts_manager.py`
- `tests/test_storage_repo.py`
- `tests/test_gradio_smoke.py`
- `tests/test_orchestrator_full_pipeline.py`

## Risks / follow-ups
- Current orchestrator persists and reports failures by stage; next step is wiring a persistent run history UI view from DB snapshots.
- Provider-side API shape drift remains a runtime risk; payload/branch tests are in place to catch local regressions.
