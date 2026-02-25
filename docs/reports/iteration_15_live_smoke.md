# Iteration 15: Live Provider Contract Smoke + Release Readiness

## Scope
- Added operational live-smoke diagnostics for OpenAI, Gemini, and Mistral OCR.
- Added strict/non-strict execution modes and deterministic JSON report output.
- Added separate CI workflow for operational live-smoke.
- Updated operations documentation and test coverage for smoke report/CLI behavior.

## Pre-flight
- Baseline before iteration: `51e0624ef39e6e03e85acb162f0257cd9aeb71dd`.
- New branch: `codex/iteration-15-live-smoke`.
- `git status` was clean at start.

## Implemented

### 1) Live smoke module and CLI
- Added `app/ops/live_smoke.py` and `app/ops/__init__.py`.
- CLI:
  - `python -m app.ops.live_smoke`
  - options:
    - `--strict`
    - `--output <path>`
- Provider checks use existing project clients/contracts (no alternative contract path):
  - OpenAI via `OpenAILLMClient.generate_json(...)` (structured output schema).
  - Gemini via `GeminiLLMClient.generate_json(...)` (structured output schema).
  - Mistral OCR via `MistralOCRClient.process_document(...)` on temporary smoke image.

### 2) Deterministic machine-readable report
- Report fields include:
  - `started_at`, `finished_at`, `overall_status`
  - `providers[]` with `name`, `status(pass|fail|skipped)`, `latency_ms`, `error_code`, `error_message`
- Added summary block (`pass/fail/skipped`, strict skipped violation).
- JSON output is deterministic in key order (`sort_keys=True`, pretty format).

### 3) Status and strict-mode semantics
- Non-strict:
  - `skipped` providers are allowed; overall can remain `pass` if no failures.
- Strict:
  - any `skipped` provider makes overall status `fail`.
- CLI exit code:
  - `0` when overall `pass`
  - `1` when overall `fail`

### 4) Error taxonomy alignment
- For runtime provider failures, smoke maps to existing taxonomy where applicable:
  - LLM failures via `classify_llm_api_error(...)`
  - OCR failures via `classify_ocr_error(...)`
- For operational skip reasons, explicit operational codes are used (`MISSING_API_KEY`, `SDK_NOT_INSTALLED`).

### 5) CI operational workflow
- Added `.github/workflows/live-smoke.yml`.
- Triggers:
  - `workflow_dispatch` (with optional strict input)
  - weekly `schedule`
- Does not modify/replace the main PR CI workflow.
- Stores report as artifact `live-smoke-report`.

### 6) Documentation update
- Updated `docs/OPERATIONS.md` with:
  - local live-smoke commands
  - strict/non-strict meaning
  - report interpretation and remediation actions
  - CI workflow details

## Tests
Added `tests/test_live_smoke.py` covering:
- pass/fail/skipped aggregation,
- strict vs non-strict behavior,
- deterministic JSON report structure,
- CLI exit code behavior.

Adjusted existing tests for updated export signature argument behavior:
- `tests/test_gradio_smoke.py`
- `tests/test_delete_run_retention.py`

## Validation commands (actual)
Executed at `2026-02-25T18:33:40Z`.

```bash
ruff format .
```
Result: `3 files reformatted, 61 files left unchanged`

```bash
ruff check .
```
Result: `All checks passed!`

```bash
pytest -q
```
Result: `123 passed in 3.61s`

```bash
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```
Result: `gradio_app_started`

Local live smoke sample run:

```bash
python -m app.ops.live_smoke --output data/live_smoke_report.json
```
Result summary:
- `overall_status=pass`
- providers:
  - `openai=pass`
  - `google=skipped (SDK_NOT_INSTALLED)`
  - `mistral_ocr=skipped (MISSING_API_KEY)`

## Known limits
- Live-smoke intentionally performs real provider calls when key+SDK are available.
- In non-strict mode, operational readiness may still be partial if providers are skipped.
