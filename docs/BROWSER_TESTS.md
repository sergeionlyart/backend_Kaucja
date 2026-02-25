# Browser Tests Guide

## Prerequisites

```bash
python -m venv .venv
source .venv/bin/activate
```

Install project + browser dependencies:

```bash
./scripts/browser/prepare_env.sh
```

`run_regression.sh` no longer reinstalls dependencies by default.
Use explicit prepare when needed:

```bash
./scripts/browser/run_regression.sh --prepare-only
```

## Test Profiles

- core profile (default): excludes browser tests
  - command: `pytest -q`
  - result: no browser skips in base run
- browser profile:
  - `browser_p0` for deterministic P0 baseline
  - `browser_p1` for negative/protection scenarios

Marker expressions:

- P0 only: `-m browser_p0`
- Full browser regression: `-m "browser_p0 or browser_p1"`

## E2E Mode (No External API Keys)

Browser smoke uses deterministic local mode:

- `KAUCJA_E2E_MODE=true`
- seeded SQLite + artifacts under `data/e2e/`
- no network/API calls required for history/load/compare flows

## Seed Deterministic Data

```bash
./scripts/browser/seed_data.sh
```

This creates deterministic history fixtures:

- session: `e2e-session-001`
- runs: `e2e-run-a`, `e2e-run-b`
- full artifacts for run manifest, logs, OCR, and LLM payloads

## Start App for Browser E2E

```bash
./scripts/browser/start_e2e_app.sh
```

Default URL:

- `http://127.0.0.1:7861`

## Run Browser Regression

Single command (seed + start app + wait + run tests):

```bash
./scripts/browser/run_regression.sh --suite p0
```

This command runs P0 browser regression baseline (5 cases):

1. app start + key sections
2. history load seeded run
3. compare seeded runs
4. export run bundle
5. restore verify-only

Run full browser regression (P0 + P1):

```bash
./scripts/browser/run_regression.sh --suite full
```

Explicit prepare + execute:

```bash
./scripts/browser/run_regression.sh --prepare --suite p0
```

Run with explicit run-id (isolated artifacts/log paths):

```bash
./scripts/browser/run_regression.sh --suite p0 --run-id local-check-001
```

Run campaign loops with aggregation:

```bash
./scripts/browser/run_campaign.sh --suite p0 --iterations 10
./scripts/browser/run_campaign.sh --suite full --iterations 5
```

Legacy alias:

```bash
./scripts/browser/run_smoke.sh
```

Direct pytest mode (if app already running):

```bash
export KAUCJA_RUN_BROWSER_TESTS=1
export KAUCJA_BROWSER_BASE_URL=http://127.0.0.1:7861
pytest -q -o addopts= tests/browser -m "browser_p0 or browser_p1" --junitxml artifacts/browser/junit.xml
```

## Results and Logs

- Pytest output: terminal.
- App log (regression runner): `data/browser_regression_<suite>_<run_id>_app.log`.
- Browser diagnostics: `artifacts/browser/`:
  - `junit.xml`
  - per-test Playwright traces/screenshots/videos on failure
- Seeded artifacts root: `data/e2e/sessions/e2e-session-001/runs/`.
- Campaign outputs: `artifacts/browser/campaign/<suite>_<timestamp>/`:
  - per-iteration artifacts/logs,
  - `report.json`,
  - `report.md`.

## CI Execution

Browser regression workflow:

- file: `.github/workflows/browser-smoke.yml`
- triggers:
  - `workflow_dispatch`
  - weekly `schedule`

Workflow steps:

1. install project dependencies
2. install Playwright Chromium
3. run `./scripts/browser/run_regression.sh --suite <p0|full>`
4. upload diagnostics artifacts

Browser campaign workflow:

- file: `.github/workflows/browser-campaign.yml`
- trigger: `workflow_dispatch`
- inputs:
  - `suite` (`p0|full`)
  - `iterations`
- output artifacts:
  - `artifacts/browser/campaign/**`

## Troubleshooting Flakes

- Symptom: app not reachable in browser tests
  - check `data/browser_regression_*_app.log`
  - verify `KAUCJA_GRADIO_SERVER_PORT` is free
- Symptom: selectors fail after UI change
  - keep/update `elem_id` in `app/ui/gradio_app.py`
  - avoid text-only selectors in tests
- Symptom: restore/export case fails intermittently
  - ensure seed step succeeded (`status=ok`)
  - verify exported path exists in `export_path_box`
- Symptom: browser tests not discovered in direct pytest run
  - core profile ignores `tests/browser` by default
  - use `-o addopts=` for explicit browser execution
- Symptom: repeated runs are slow due repeated installs
  - avoid `--prepare` for every run
  - run `prepare_env.sh` once, then execute regression/campaign
