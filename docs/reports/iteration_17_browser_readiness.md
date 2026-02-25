# Iteration 17: Browser Test Readiness

## Scope
- Added deterministic local e2e harness that runs without external provider keys/calls.
- Added reproducible seed script for History/Compare browser flows.
- Added browser smoke infrastructure with Playwright.
- Added copy-paste scripts and browser testing docs.

## Pre-flight
- Baseline commit: `482434a74af307c36357a16e25986aaf431cf19e`.
- Working branch: `codex/iteration-17-browser-readiness`.
- `git status` was clean before changes.

## Changes

### 1) E2E mode in app runtime
- Added `KAUCJA_E2E_MODE` / `E2E_MODE` setting in `app/config/settings.py` and `.env.example`.
- In `app/ui/gradio_app.py`, runtime preflight now bypasses API-key/SDK checks when `e2e_mode=true`.

### 2) Deterministic seed for browser runs
- Added `app/ops/seed_e2e_data.py`:
  - seeds deterministic `session_id=e2e-session-001`,
  - seeds deterministic runs `e2e-run-a`, `e2e-run-b`,
  - writes compatible artifacts: `run.json`, `logs/run.log`, `documents/*/ocr/*`, `llm/*`,
  - writes SQLite metadata (`runs`, `documents`, `llm_outputs`),
  - idempotent for seeded run IDs.

### 3) Browser test suite (Playwright)
- Added dev dependency `playwright` in `pyproject.toml`.
- Added `tests/browser/`:
  - app opens and core blocks render,
  - history seed works with load/compare flow.
- Browser tests are gated by `KAUCJA_RUN_BROWSER_TESTS=1`, so default `pytest -q` is not blocked.

### 4) Browser test scripts
- Added:
  - `scripts/browser/prepare_env.sh`
  - `scripts/browser/seed_data.sh`
  - `scripts/browser/start_e2e_app.sh`
  - `scripts/browser/run_smoke.sh`
- `run_smoke.sh` runs seed + app start + readiness wait + browser tests in one command.

### 5) Documentation
- Added `docs/BROWSER_TESTS.md`.
- Updated `docs/OPERATIONS.md` with browser e2e flow and commands.

## Verification (actual runs)
Executed on branch `codex/iteration-17-browser-readiness` at `2026-02-25T19:07:31Z`.

```bash
ruff format .
```
Result: `69 files left unchanged`

```bash
ruff check .
```
Result: `All checks passed!`

```bash
pytest -q
```
Result: `131 passed, 2 skipped, 5 warnings in 4.78s`

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
- browser tests: `2 passed in 2.64s`

## Known limits
- Browser smoke currently validates core UI readiness and one deterministic history flow.
- It is intentionally small (2 tests) and ready for expansion with richer interaction cases.
