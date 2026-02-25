# Iteration 5 Run Manifest + Run History Report

## Summary
Implemented Iteration 5 scope from TechSpec (sections 4.2, 6.1 deterministic run, 8 metrics, 2.1D history, 11 DoD):

- Added `run.json` manifest lifecycle in run artifacts root and wired updates across pipeline key stages.
- Added storage history APIs:
  - `list_runs(...)` with filters (`session_id`, `provider`, `model`, `prompt_version`, `date_from`, `date_to`, `limit`)
  - `get_run_bundle(run_id)` returning run + documents + llm_output.
- Added safe artifact readers for history loading:
  - `run.json`
  - `llm/response_raw.txt`, `llm/response_parsed.json`, `llm/validation.json`
  - `documents/*/ocr/combined.md`.
- Updated Gradio UI:
  - kept Analyze flow working,
  - added History filters/table,
  - added run loading by `run_id`,
  - hydrates summary/raw JSON/validation/metrics/OCR table from persisted run data,
  - shows artifacts root path.
- Added tests for manifest contract, repo filters/bundle, orchestrator `run.json` integration, and UI history loading.

## Commands Run
```bash
ruff format .
ruff check .
pytest -q
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```

Outputs:
- `ruff format .` -> `3 files reformatted, 42 files left unchanged`
- `ruff check .` -> `All checks passed!`
- `pytest -q` -> `46 passed in 2.85s`
- build check -> `gradio_app_started`

## Artifacts
Run-level deterministic artifacts now include:
- `data/sessions/<session_id>/runs/<run_id>/run.json`
- `data/sessions/<session_id>/runs/<run_id>/logs/run.log`
- `data/sessions/<session_id>/runs/<run_id>/llm/request.txt`
- `data/sessions/<session_id>/runs/<run_id>/llm/response_raw.txt`
- `data/sessions/<session_id>/runs/<run_id>/llm/response_parsed.json`
- `data/sessions/<session_id>/runs/<run_id>/llm/validation.json`
- `data/sessions/<session_id>/runs/<run_id>/documents/<doc_id>/ocr/combined.md`

## Files Changed
- `PLANS.md`
- `app/pipeline/orchestrator.py`
- `app/storage/models.py`
- `app/storage/repo.py`
- `app/storage/run_manifest.py`
- `app/storage/artifact_reader.py`
- `app/ui/gradio_app.py`
- `tests/test_run_manifest.py`
- `tests/test_storage_repo.py`
- `tests/test_orchestrator_full_pipeline.py`
- `tests/test_gradio_smoke.py`

## Notes
- History loader is resilient to missing artifacts and returns readable messages instead of throwing.
- Manifest updates include input params, stage statuses, artifact paths, metrics, validation summary, and error fields.
