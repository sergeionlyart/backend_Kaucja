# Iteration 18: Browser Regression Baseline + CI

## Scope
- Added stable `elem_id` identifiers for key UI controls (Run/History/Compare/Export/Restore).
- Hardened browser tests with reusable id-based helpers and ready-state checks.
- Expanded browser baseline to 5 deterministic P0 regression cases.
- Added separate GitHub Actions workflow for browser smoke regression with diagnostics artifacts.
- Updated browser testing documentation for local and CI usage.

## Pre-flight
- Baseline before iteration: `8963361a9f2f03dd395bf618c75e70dfee6af03f`.
- Working branch: `codex/iteration-18-browser-regression`.
- `git status` was clean before changes.

## Changes

### 1) Stable selectors + anti-flake helpers
- Updated `app/ui/gradio_app.py` with stable `elem_id` for:
  - run status/summary/raw/validation outputs,
  - history filters/table/actions,
  - export/restore controls and status fields,
  - compare controls and outputs.
- Added browser helper layer:
  - `tests/browser/helpers.py`
  - id-based actions/readers (`click_button`, `fill_textbox`, `upload_file`, checkbox setter, deterministic assertions).

### 2) Browser P0 regression suite (5 cases)
- `tests/browser/test_browser_smoke.py` now includes:
  1. app startup + key sections render,
  2. history load for `e2e-run-a` + summary/raw/validation visibility,
  3. compare flow for seeded runs + diff/metrics checks,
  4. export run bundle from history + ZIP path existence,
  5. restore verify-only for exported ZIP + verification details.

### 3) Browser CI workflow
- Added `.github/workflows/browser-smoke.yml`:
  - triggers: `workflow_dispatch` + weekly `schedule`,
  - installs Playwright browser,
  - runs deterministic browser regression script,
  - uploads diagnostics artifacts on failure/always:
    - `data/browser_smoke_app.log`,
    - `artifacts/browser/**` (junit + traces/screenshots/videos).

### 4) Script/runtime hardening for browser runs
- Updated `scripts/browser/run_smoke.sh`:
  - sets `KAUCJA_BROWSER_ARTIFACTS_DIR`,
  - writes junit report for browser tests,
  - remains one-shot seed + app start + browser suite.

### 5) Docs
- Updated `docs/BROWSER_TESTS.md`:
  - one-shot local run,
  - CI run model,
  - artifact locations,
  - flake troubleshooting guidance.

## Verification (actual runs)
Executed at `2026-02-25T19:30:55Z`.

```bash
ruff format .
```
Result: `72 files left unchanged`

```bash
ruff check .
```
Result: `All checks passed!`

```bash
pytest -q
```
Result: `131 passed, 5 skipped, 5 warnings in 3.69s`

```bash
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```
Result: `gradio_app_started`

```bash
./scripts/browser/run_smoke.sh
```
Result:
- seed: `status=ok`, runs `e2e-run-a`, `e2e-run-b`
- app readiness: `app_ready url=http://127.0.0.1:7861 status=200`
- browser baseline: `5 passed in 5.10s`

## Known limits
- Baseline focuses on P0 deterministic flows only; deeper scenario coverage is planned for next QA expansion.
- CI diagnostics artifacts are richest on failure (trace/screenshot/video); on full pass only junit may be present.
