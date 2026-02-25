# Iteration 16: Live-Smoke Policy Hardening (required providers + timeouts)

## Scope
- Added required-providers policy for live-smoke readiness.
- Added per-provider timeout guard to prevent infinite hangs.
- Normalized operational live-smoke error codes.
- Updated live-smoke workflow with explicit policy parameters.
- Extended tests, docs, and acceptance verification.

## Pre-flight
- Baseline before iteration: `78c7001d733004781ff2316b9d9621ef91aaa4fb`.
- Working branch: `codex/iteration-16-live-smoke-policy`.
- `git status` was clean before changes.

## Changes

### 1) Required providers policy
- Added CLI flag: `--required-providers` (CSV, e.g. `openai,google,mistral_ocr`).
- Added settings/env defaults:
  - `LIVE_SMOKE_REQUIRED_PROVIDERS`
  - `KAUCJA_LIVE_SMOKE_REQUIRED_PROVIDERS`
- Policy behavior:
  - any `fail` on required provider => overall `fail`
  - any `skipped` on required provider => overall `fail` (even non-strict)
  - skipped non-required provider is allowed in non-strict mode
- Added report fields:
  - `required_providers`
  - `required_failures`
  - `required_skipped`

### 2) Provider timeout hardening
- Added CLI flag: `--provider-timeout-seconds`.
- Added settings/env defaults:
  - `LIVE_SMOKE_PROVIDER_TIMEOUT_SECONDS`
  - `KAUCJA_LIVE_SMOKE_PROVIDER_TIMEOUT_SECONDS`
- Provider probes now run with per-provider timeout protection.
- Timeout result is deterministic failure:
  - `status=fail`
  - `error_code=LIVE_SMOKE_TIMEOUT`
- Hanging provider no longer blocks smoke indefinitely.

### 3) Operational taxonomy normalization
- Added normalized live-smoke operational codes:
  - `LIVE_SMOKE_TIMEOUT`
  - `LIVE_SMOKE_MISSING_API_KEY`
  - `LIVE_SMOKE_SDK_NOT_INSTALLED`
- Runtime API errors still use existing taxonomy (`LLM_API_ERROR`, `OCR_API_ERROR`, etc.).

### 4) Workflow policy hardening
- Updated `.github/workflows/live-smoke.yml`:
  - `workflow_dispatch` inputs now include:
    - `strict`
    - `required_providers`
    - `provider_timeout_seconds`
  - weekly schedule uses explicit policy params and explicit strict mode.
- Main PR CI workflow unchanged.

### 5) Tests
- Updated/extended tests for:
  - required providers pass/fail/skipped policy
  - timeout path with `LIVE_SMOKE_TIMEOUT`
  - report policy fields presence/shape
  - CLI exit codes under new policy behavior
  - settings env override for new live-smoke defaults

## Verification (actual runs)
Executed at `2026-02-25T18:44:52Z`.

```bash
ruff format .
```
Result: `64 files left unchanged`

```bash
ruff check .
```
Result: `All checks passed!`

```bash
pytest -q
```
Result: `125 passed in 3.53s`

```bash
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```
Result: `gradio_app_started`

## Notes
- Readiness is now policy-driven (`required_providers`) and not only strict/non-strict skipped handling.
- Timeout guard is per provider and deterministic in report/exit behavior.
