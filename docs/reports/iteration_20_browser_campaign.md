# Iteration 20 — Browser Campaign Stability + Final Go/No-Go

## Scope
- Harden browser regression runner for repeated execution without implicit dependency reinstall.
- Add campaign runner for repeated suites with aggregate flake/stability metrics.
- Add dedicated CI workflow for browser campaign execution.
- Run required verification commands and factual browser campaigns.

## Changes

### 1) Runner hardening (`prepare` vs `execute`)
- Updated `scripts/browser/run_regression.sh`:
  - default mode no longer runs dependency install,
  - added `--prepare` and `--prepare-only`,
  - added `--run-id` for isolated logs/artifacts per execution.
- Updated `scripts/browser/prepare_env.sh`:
  - added lock-based serialization (`.tmp/browser_prepare.lock`) to avoid parallel editable-install conflicts.

### 2) Campaign runner
- Added `scripts/browser/run_campaign.sh`:
  - args: `--suite p0|full`, `--iterations N`, optional `--prepare`,
  - runs suite N times,
  - stores per-iteration outputs (`junit`, app log, runner stdout/stderr, `iteration.json`),
  - writes aggregate `report.json` + `report.md` with pass/fail counts, pass rate, avg duration, flaky tests, and failed iteration details.

### 3) CI
- Added `.github/workflows/browser-campaign.yml` (manual workflow_dispatch):
  - inputs: `suite`, `iterations`,
  - runs campaign script,
  - uploads `artifacts/browser/campaign/**`.
- Updated `.github/workflows/browser-smoke.yml`:
  - removed obsolete `KAUCJA_BROWSER_SKIP_PREPARE` env.

### 4) Docs
- Updated `docs/BROWSER_TESTS.md` with:
  - new prepare/execute split,
  - campaign command examples,
  - artifact paths for per-run and campaign outputs,
  - troubleshooting notes for repeated runs.

## Verification (factual)

### Mandatory checks
1. `ruff format .`
- result: `72 files left unchanged`
- duration: `real 0.12s`

2. `ruff check .`
- result: `All checks passed!`
- duration: `real 0.12s`

3. `pytest -q`
- result: `131 passed, 5 warnings in 3.01s`
- duration: `real 3.88s`

4. `python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"`
- result: `gradio_app_started`
- duration: `real 2.50s`

5. `./scripts/browser/run_regression.sh --suite p0`
- result: `5 passed, 3 deselected in 4.63s`
- duration: `real 7.40s`

6. `./scripts/browser/run_regression.sh --suite full`
- result: `8 passed in 6.55s`
- duration: `real 9.35s`

### Campaign runs
1. `./scripts/browser/run_campaign.sh --suite p0 --iterations 10`
- campaign root: `artifacts/browser/campaign/p0_20260225T195537Z`
- aggregate: `10/10 pass`, `0 fail`, `pass_rate=1.0`, `flaky_tests=0`
- average iteration duration: `5.45582s`
- command duration: `real 56.58s`

2. `./scripts/browser/run_campaign.sh --suite full --iterations 5`
- campaign root: `artifacts/browser/campaign/full_20260225T195636Z`
- aggregate: `5/5 pass`, `0 fail`, `pass_rate=1.0`, `flaky_tests=0`
- average iteration duration: `7.810143s`
- command duration: `real 40.06s`

## Go/No-Go
- Decision: **GO** for starting a broader browser campaign.
- Evidence:
  - all mandatory checks passed,
  - both campaign suites passed with zero failures,
  - flaky count is zero in both aggregate reports,
  - runner now supports repeatable execution without implicit reinstall.

## Known limits
- Campaign currently runs iterations sequentially; no built-in parallel mode.
- Browser campaign workflow is manual (`workflow_dispatch`) only.
