# Iteration 6 Prompt Management + Result UX Report

## Summary
Completed Iteration 6 according to TechSpec sections 2.1/2.2/7.1/7.2/11:

1. Prompt management:
   - Added prompt-set discovery under `app/prompts/<prompt_name>/vNNN`.
   - Added UI for:
     - viewing current `system_prompt.txt` and `schema.json`,
     - editing system prompt,
     - `Save as new version` with automatic next `vNNN`,
     - dynamic prompt version dropdown refresh without restart.
   - New version save writes:
     - `system_prompt.txt`,
     - `schema.json` (copied from base unless explicitly provided),
     - `meta.yaml` (`created_at`, `author`, `note`, `source_version`).
   - Added schema validation on save: JSON parse + root object check.

2. Result UX completion:
   - Added checklist table (`item_id`, `importance`, `status`, `confidence`).
   - Added gap list from `request_from_user.ask`.
   - Added details view by selected `item_id` (findings/quotes/requests).
   - Kept summary/raw JSON/validation/metrics outputs.

3. Progress + runtime log:
   - Added stage progress indicator (`OCR -> LLM -> Validate -> Finalize`).
   - Added runtime log tail view and full log path field.
   - Added user-friendly error message and technical error details (`error_code/error_message`).

4. Tests:
   - Prompt manager discovery/next version/save flow.
   - Result helper rendering (checklist/gap/details).
   - UI smoke/integration for:
     - analyze outputs with progress/log fields,
     - prompt save flow followed by run with new version,
     - history load with persisted run artifacts.

## Commands Run
```bash
ruff format .
ruff check .
pytest -q
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```

Outputs:
- `ruff format .` -> `5 files reformatted, 44 files left unchanged`
- `ruff check .` -> `All checks passed!`
- `pytest -q` -> `52 passed in 2.80s`
- build check -> `gradio_app_started`

## Files Changed
- `app/prompts/manager.py`
- `app/ui/gradio_app.py`
- `app/ui/result_helpers.py`
- `tests/test_prompt_manager.py`
- `tests/test_result_helpers.py`
- `tests/test_gradio_smoke.py`

## Artifacts / Paths
- Prompt versions root: `app/prompts/<prompt_name>/vNNN/`
- Prompt files:
  - `app/prompts/<prompt_name>/vNNN/system_prompt.txt`
  - `app/prompts/<prompt_name>/vNNN/schema.json`
  - `app/prompts/<prompt_name>/vNNN/meta.yaml`
- Run artifacts:
  - `data/sessions/<session_id>/runs/<run_id>/run.json`
  - `data/sessions/<session_id>/runs/<run_id>/logs/run.log`
  - `data/sessions/<session_id>/runs/<run_id>/llm/response_parsed.json`
  - `data/sessions/<session_id>/runs/<run_id>/llm/validation.json`
