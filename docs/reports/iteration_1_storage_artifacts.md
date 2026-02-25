# Iteration 1 Storage + Artifacts Report

## Summary
Closed Iteration 0 gaps and implemented Iteration 1 baseline from `docs/TECH_SPEC_MVP.md`.

Completed:
- Added reproducible dependency management via `pyproject.toml`.
- Added bootstrap doc with install/check/run commands.
- Updated prompt schema `v001` to full TechSpec 12.3 contract.
- Implemented `app/storage/artifacts.py` with deterministic run paths and `logs/run.log` creation.
- Integrated artifacts creation into `StorageRepo.create_run` and Analyze callback flow.
- Added tests for schema contract and artifacts behavior.
- Removed false-green smoke skip (`importorskip`) for Gradio UI tests.

## Bootstrap
See `docs/SETUP.md`.

## Commands Run
```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
ruff format .
ruff check .
pytest -q
python -m app.ui.gradio_app
```

Outputs (key lines):
- `ruff format .` -> `22 files left unchanged`
- `ruff check .` -> `All checks passed!`
- `pytest -q` -> `11 passed in 1.75s`
- `python -m app.ui.gradio_app` -> module started successfully (process stayed alive until terminated by check script).

## Files Changed
- `pyproject.toml`
- `docs/SETUP.md`
- `app/prompts/kaucja_gap_analysis/v001/schema.json`
- `app/storage/artifacts.py`
- `app/storage/repo.py`
- `tests/test_prompt_schema_v001.py`
- `tests/test_artifacts_manager.py`
- `tests/test_gradio_smoke.py`
- `tests/test_storage_repo.py`
- `docs/reports/iteration_1_storage_artifacts.md`

## Risks / Follow-ups
- During dependency install, `pip` reported global-environment conflicts (`huggingface-hub` vs existing `transformers/tokenizers`).
- For strict isolation, run via project virtualenv as documented in `docs/SETUP.md`.
