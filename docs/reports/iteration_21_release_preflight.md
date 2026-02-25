# Iteration 21 — Release Preflight Gate

## Scope
- Added a single reproducible release preflight command for core + browser readiness.
- Added deterministic preflight artifacts (`report.json`, `report.md`, per-stage logs).
- Reduced baseline pytest noise with targeted filtering of known third-party warnings.
- Added manual CI workflow for preflight gate and documentation for GO/NO-GO.

## Implemented changes

1. Preflight runner
- Added `scripts/release/run_preflight.sh`.
- Sequential stages:
  1) `ruff check .`
  2) `pytest -q` (core profile)
  3) `./scripts/browser/run_regression.sh --suite p0`
  4) `./scripts/browser/run_regression.sh --suite full`
  5) optional live-smoke (`python -m app.ops.live_smoke ...`) if provider keys are present.
- Deterministic outputs:
  - `artifacts/release_preflight/<timestamp>/report.json`
  - `artifacts/release_preflight/<timestamp>/report.md`
  - stage logs: `artifacts/release_preflight/<timestamp>/<stage>.log`
- GO/NO-GO logic:
  - mandatory failures (`ruff_check`, `pytest_core`, `browser_p0`, `browser_full`) => `NO-GO`
  - `live_smoke` is optional and tracked separately (`optional_failures`).

2. Warning noise reduction
- Updated `pyproject.toml` (`[tool.pytest.ini_options].filterwarnings`) with 3 narrow message-level ignores for known external `swig` deprecation warnings:
  - `SwigPyPacked has no __module__ attribute`
  - `SwigPyObject has no __module__ attribute`
  - `swigvarlink has no __module__ attribute`

3. CI
- Added `.github/workflows/release-preflight.yml` (`workflow_dispatch`) to run preflight and upload `artifacts/release_preflight/**`.
- Main CI workflows unchanged.

4. Docs
- Added `docs/RELEASE_CHECKLIST.md` with one-command gate, GO/NO-GO policy, and artifact interpretation.
- Updated `docs/BROWSER_TESTS.md` with preflight gate reference.

## Verification (factual)

1. `ruff format .`
- `72 files left unchanged`
- `real 0.12s`

2. `ruff check .`
- `All checks passed!`
- `real 0.12s`

3. `pytest -q`
- `131 passed in 3.19s`
- `real 4.05s`
- warnings in base output: `0`

4. `python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"`
- `gradio_app_started`
- `real 2.42s`

5. `./scripts/release/run_preflight.sh`
- report root: `artifacts/release_preflight/20260225T203643Z`
- aggregate status: `overall_status=pass`, `go_no_go=GO`
- total duration: `24.193194s` (`real 24.66s`)
- stage summary:
  - `ruff_check`: pass (`0.160367s`)
  - `pytest_core`: pass (`3.768771s`)
  - `browser_p0`: pass (`7.665959s`)
  - `browser_full`: pass (`7.543373s`)
  - `live_smoke`: fail (`3.458658s`) — counted as optional

## GO/NO-GO result
- Final decision for browser release gate: **GO**.
- Rationale: all mandatory preflight stages passed; optional live-smoke failure is reported and non-blocking.

## Known limits
- Optional live-smoke currently failed in this environment due provider runtime issue (`google` probe: `LLM_API_ERROR`), captured in preflight artifact log.
