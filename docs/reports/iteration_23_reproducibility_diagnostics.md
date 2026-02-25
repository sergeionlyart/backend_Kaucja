# Iteration 23 — Reproducibility + Diagnostics Hardening

## Scope
- Introduce pinned lock-based dependency installation for reproducible local/CI runs.
- Harden browser runner diagnostics so key artifacts are always present and validated.
- Extend release preflight report with deterministic environment snapshot.
- Update operational docs for reproducible install and minimal triage bundle.

## Baseline
- Baseline branch state: `codex/iteration-22-ci-browser-gate`
- Baseline commit: `7545c96dda7259a87abcf8bb35eed333b645d01d`
- `git status` before changes: clean

## Changes

1. Lock-based reproducible dependencies
- Added lock files:
  - `requirements/runtime.lock.txt`
  - `requirements/dev.lock.txt`
- Added lock scripts:
  - `scripts/deps/install_from_lock.sh`
  - `scripts/deps/regenerate_locks.sh`
- Updated installation flows to use lock files:
  - `scripts/browser/prepare_env.sh`
  - `.github/workflows/ci.yml`
  - `.github/workflows/browser-smoke.yml`
  - `.github/workflows/browser-campaign.yml`
  - `.github/workflows/release-preflight.yml`
  - `.github/workflows/live-smoke.yml`

2. Browser runner diagnostics hardening
- Updated `scripts/browser/run_regression.sh`:
  - adds guaranteed startup banner in app log with run context (`suite`, `run_id`, `commit_sha`, env summary),
  - emits deterministic runner logs:
    - `runner.stdout.log`
    - `runner.stderr.log`
  - validates diagnostics at end (fail-fast):
    - non-empty app log,
    - non-empty junit,
    - non-empty runner stdout/stderr,
    - when pytest fails: ensures Playwright failure artifacts exist (`trace.zip`/`*.png`/`*.webm`).

3. Preflight report environment snapshot
- Updated `scripts/release/run_preflight.sh` report payload:
  - new `environment` block in `report.json`/`report.md`:
    - `commit_sha`
    - `python_version`
    - `playwright_version`
    - `browser_suites`
- Format remains deterministic (`sort_keys=True` for JSON output).

4. Documentation
- Updated `docs/BROWSER_TESTS.md`:
  - added "Reproducible Install",
  - added lock regeneration command,
  - added "Minimal Triage Bundle" section.
- Updated `docs/RELEASE_CHECKLIST.md`:
  - lock-based install/regeneration,
  - triage bundle expectations,
  - preflight environment block fields.

## Verification (factual)

1. `ruff format .`
- result: `72 files left unchanged`
- duration: `real 0.13s`

2. `ruff check .`
- result: `All checks passed!`
- duration: `real 0.13s`

3. `pytest -q`
- result: `131 passed in 3.30s`
- duration: `real 4.27s`

4. `python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"`
- result: `gradio_app_started`
- duration: `real 2.62s`

5. `./scripts/browser/run_regression.sh --suite p0`
- result: `5 passed, 3 deselected in 4.90s`
- duration: `real 8.44s`
- diagnostics produced and non-empty:
  - `artifacts/browser/p0/latest_/junit.xml` (`871 bytes`)
  - `artifacts/browser/p0/latest_/runner.stdout.log` (`2136 bytes`)
  - `artifacts/browser/p0/latest_/runner.stderr.log` (`52 bytes`)
  - `data/browser_regression_p0_latest__app.log` (`432 bytes`)

6. `./scripts/release/run_preflight.sh`
- result: `overall_status=pass`, `go_no_go=GO`
- duration: `real 23.65s`
- report root: `artifacts/release_preflight/20260225T210231Z`
- environment snapshot in report:
  - `commit_sha=7545c96dda7259a87abcf8bb35eed333b645d01d`
  - `python_version=3.10.10`
  - `playwright_version=1.58.0`
  - `browser_suites=[p0, full]`

## Risks / notes
- Lock files are platform-specific snapshots from current environment and should be regenerated intentionally when dependency graph changes.
- Optional live-smoke remains non-blocking for preflight gate and may fail independently from browser readiness.
