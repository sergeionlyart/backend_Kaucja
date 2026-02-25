# Iteration 0 Foundation Report

## Summary
Implemented Iteration 0 baseline for the Kaucja MVP according to `docs/TECH_SPEC_MVP.md` (Scope MVP, Architecture 3.2, Storage 4.x, Deliverable #3 Iteration 0):
- Created project skeleton under `app/` with required module directories.
- Added runtime settings and provider/pricing configs.
- Added prompt-set `kaucja_gap_analysis/v001` (system prompt, schema, metadata).
- Implemented minimal SQLite storage with tables `sessions`, `runs`, `documents`, `llm_outputs` and CRUD contract:
  - `create_session`
  - `create_run`
  - `update_run_status`
- Implemented minimal Gradio UI where `Analyze` creates a run record in SQLite.
- Added unit/smoke tests for settings, storage, and UI callback behavior.

## Files Changed
- `.env.example`
- `app/__init__.py`
- `app/config/__init__.py`
- `app/config/settings.py`
- `app/config/providers.yaml`
- `app/config/pricing.yaml`
- `app/prompts/__init__.py`
- `app/prompts/kaucja_gap_analysis/v001/system_prompt.txt`
- `app/prompts/kaucja_gap_analysis/v001/schema.json`
- `app/prompts/kaucja_gap_analysis/v001/meta.yaml`
- `app/schemas/__init__.py`
- `app/ocr_client/__init__.py`
- `app/llm_client/__init__.py`
- `app/pipeline/__init__.py`
- `app/storage/__init__.py`
- `app/storage/db.py`
- `app/storage/models.py`
- `app/storage/repo.py`
- `app/ui/__init__.py`
- `app/ui/gradio_app.py`
- `app/utils/__init__.py`
- `tests/conftest.py`
- `tests/test_settings.py`
- `tests/test_storage_repo.py`
- `tests/test_gradio_smoke.py`

## Commands Run
```bash
ruff format .
```
Output:
```text
19 files left unchanged
```

```bash
ruff check .
```
Output:
```text
All checks passed!
```

```bash
pytest -q
```
Output:
```text
....                                                                     [100%]
4 passed, 1 skipped in 0.12s
```

```bash
python -m app.ui.gradio_app
```
Output:
```text
ModuleNotFoundError: No module named 'gradio'
```

## Risks / Follow-ups
- `gradio` is not installed in the current environment, so:
  - runtime start command currently fails with `ModuleNotFoundError`;
  - Gradio smoke test module is skipped via `pytest.importorskip("gradio")`.
- Acceptance command for UI start:
  - `python -m app.ui.gradio_app`
  - requires `gradio` package available in runtime environment.
