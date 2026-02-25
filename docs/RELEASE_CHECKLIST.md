# Release Preflight Checklist

## One-command preflight gate

```bash
./scripts/release/run_preflight.sh
```

## Reproducible install

- Runtime dependencies lock: `requirements/runtime.lock.txt`
- Dev/test dependencies lock: `requirements/dev.lock.txt`

Install from lock:

```bash
./scripts/deps/install_from_lock.sh --group dev
```

Regenerate locks (when dependencies are intentionally changed):

```bash
./scripts/deps/regenerate_locks.sh
```

## Main CI gate (blocking)

Primary CI (`.github/workflows/ci.yml`) now includes mandatory `browser-p0-gate`
for every `push` and `pull_request`.

- Gate command in CI: `./scripts/browser/run_regression.sh --suite p0 --run-id ci-p0-gate`
- On failure diagnostics are always uploaded from `artifacts/browser/ci/p0/**`.

Preflight runs stages in this exact order:

1. `ruff check .`
2. `pytest -q` (core profile)
3. `./scripts/browser/run_regression.sh --suite p0`
4. `./scripts/browser/run_regression.sh --suite full`
5. optional `python -m app.ops.live_smoke` (runs only when at least one provider API key is configured, otherwise `skipped`)

## GO / NO-GO rule

- `GO`: preflight `overall_status=pass`.
  - `skipped` is acceptable only for optional live-smoke stage.
  - optional `live_smoke=fail` is reported, but does not block browser-release gate.
- `NO-GO`: any mandatory stage is `fail` (`ruff_check`, `pytest_core`, `browser_p0`, `browser_full`).

## Artifacts and logs

Each run stores deterministic artifacts under:

- `artifacts/release_preflight/<timestamp>/report.json`
- `artifacts/release_preflight/<timestamp>/report.md`
- `artifacts/release_preflight/<timestamp>/<stage>.log`

Additional browser artifacts from preflight:

- `artifacts/release_preflight/<timestamp>/browser_p0/`
- `artifacts/release_preflight/<timestamp>/browser_full/`

Minimal triage bundle from each browser suite:

- `junit.xml`
- `runner.stdout.log`
- `runner.stderr.log`
- suite app log (`browser_p0_app.log` / `browser_full_app.log`)
- Playwright failure diagnostics (`trace.zip`, screenshots, video when present)

## How to interpret report

`report.json` contains:

- global: `overall_status`, `go_no_go`, `started_at`, `finished_at`, `total_duration_seconds`
- environment: `commit_sha`, `python_version`, `playwright_version`, `browser_suites`
- per-stage: `name`, `status`, `duration_seconds`, `exit_code`, `log_path`, `command`
- summary counters: `pass`, `fail`, `skipped`, `total`

If `overall_status=fail`, open failing stage `log_path` first, then inspect related browser artifacts (junit/trace/app logs).
