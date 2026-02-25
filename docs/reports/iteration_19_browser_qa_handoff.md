# Iteration 19: Browser QA Handoff

## Scope
- Separated test profiles into core and browser suites to remove browser skips from default pytest run.
- Extended browser regression with P1 negative/protection scenarios.
- Added unified QA runner script with `--suite p0|full`.
- Updated browser CI workflow and handoff documentation.
- Produced go/no-go assessment for QA browser campaign.

## Pre-flight
- Baseline before iteration: `1dae10ae43a9cf903f43abde624cbcd8ae1fd9e5`.
- Working branch: `codex/iteration-19-browser-qa-handoff`.
- `git status` was clean before changes.

## Changes

### 1) Test profiles split (core vs browser)
- `pyproject.toml` updated:
  - `addopts = "--ignore=tests/browser"` (core `pytest -q` excludes browser tests by default),
  - registered markers:
    - `browser_p0`
    - `browser_p1`
- Result: base run has no browser skips.

### 2) Browser regression expanded to P1
- Browser tests now include markers and 8 deterministic cases:
  - P0 (5): app render, history load, compare, export, restore verify-only.
  - P1 (3):
    - delete confirmation mismatch -> expected UI error,
    - restore strict mode on unsigned bundle -> expected `RESTORE_INVALID_SIGNATURE`,
    - compare with empty selection -> graceful message, no callback crash.

### 3) Unified QA runner
- Added `scripts/browser/run_regression.sh` with:
  - `--suite p0`
  - `--suite full`
- Runner behavior:
  - prepares env (default),
  - seeds deterministic data,
  - starts app,
  - runs selected browser suite with marker expression,
  - stores artifacts:
    - junit,
    - Playwright diagnostics (trace/screenshot/video on failure),
    - app log.
- `scripts/browser/run_smoke.sh` kept as compatibility alias to `--suite p0`.

### 4) CI browser workflow and docs
- Updated `.github/workflows/browser-smoke.yml`:
  - `workflow_dispatch` suite input (`p0|full`),
  - weekly schedule retained,
  - uploads diagnostics artifacts.
- Updated `docs/BROWSER_TESTS.md`:
  - profile model,
  - local/CI commands,
  - troubleshooting and artifact paths.

## Verification (actual runs)
Executed at `2026-02-25T19:37:52Z`.

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
Result (core profile): `131 passed, 5 warnings in 3.84s`

```bash
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```
Result: `gradio_app_started`

```bash
./scripts/browser/run_regression.sh --suite p0
```
Result: `5 passed, 3 deselected in 4.95s`

```bash
./scripts/browser/run_regression.sh --suite full
```
Result: `8 passed in 7.65s`

## Go/No-Go for browser campaign
- **Decision: GO**
- Rationale:
  - core test profile is clean and deterministic (no browser skips),
  - browser P0 + P1 suites pass locally on deterministic seed,
  - unified QA command exists for both quick and full regression,
  - CI workflow preserves diagnostics artifacts for failure triage.

## Known limits
- `run_regression.sh` prepares environment on each run by default; for CI optimization use `KAUCJA_BROWSER_SKIP_PREPARE=1`.
- Baseline remains deterministic/local-only and intentionally does not call external providers.
