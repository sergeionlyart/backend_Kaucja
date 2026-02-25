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

## Run Browser Smoke

Single command (seed + start app + wait + run tests):

```bash
./scripts/browser/run_smoke.sh
```

Direct pytest mode (if app already running):

```bash
export KAUCJA_RUN_BROWSER_TESTS=1
export KAUCJA_BROWSER_BASE_URL=http://127.0.0.1:7861
pytest -q tests/browser
```

## Results and Logs

- Pytest output: terminal.
- App log (for smoke runner): `data/browser_smoke_app.log`.
- Seeded artifacts root: `data/e2e/sessions/e2e-session-001/runs/`.
