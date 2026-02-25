# Iteration 22 — Browser P0 Gate in Main CI

## Scope
- Add mandatory browser P0 gate to main CI (`push` / `pull_request`).
- Ensure deterministic diagnostics artifact upload for browser failures.
- Update release/browser docs to reflect blocking CI gate.

## Changes

1. Main CI workflow update
- Updated `.github/workflows/ci.yml`.
- Kept existing `lint-test-smoke` job unchanged.
- Added new blocking job `browser-p0-gate`:
  - `needs: lint-test-smoke`
  - installs project deps and Playwright Chromium
  - runs `./scripts/browser/run_regression.sh --suite p0 --run-id ci-p0-gate`
  - deterministic env paths:
    - `KAUCJA_BROWSER_ARTIFACTS_DIR=artifacts/browser/ci/p0`
    - `KAUCJA_BROWSER_APP_LOG_PATH=artifacts/browser/ci/p0/app.log`

2. Failure diagnostics in CI
- In `browser-p0-gate` added `upload-artifact` step with `if: always()`.
- Uploaded path: `artifacts/browser/ci/p0/**`.
- Includes app log, junit, traces/screenshots/videos under deterministic layout.

3. Docs update
- Updated `docs/RELEASE_CHECKLIST.md`:
  - main CI now has mandatory `browser-p0-gate`
  - diagnostic artifact location for failures.
- Updated `docs/BROWSER_TESTS.md`:
  - added section about blocking P0 gate in main CI.

## Verification (factual)

1. `ruff format .`
- result: `72 files left unchanged`
- duration: `real 0.13s`

2. `ruff check .`
- result: `All checks passed!`
- duration: `real 0.13s`

3. `pytest -q`
- result: `131 passed in 3.48s`
- duration: `real 4.51s`

4. `python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"`
- result: `gradio_app_started`
- duration: `real 2.61s`

5. `./scripts/browser/run_regression.sh --suite p0`
- result: `5 passed, 3 deselected in 4.77s`
- duration: `real 8.04s`

6. CI workflow structural validation
- command: Python YAML parse + assertions for `browser-p0-gate`, playwright install step, P0 command, and upload-artifact step.
- result: `ci_yml_validated`

## Risks and notes
- Main CI runtime increases due separate browser job (expected tradeoff for blocking UI safety gate).
- Browser gate relies on Playwright/browser install availability in GitHub runners.

## Outcome
- Browser P0 is now an explicit blocking gate in primary CI.
- Failure diagnostics are always captured with deterministic artifact paths.
