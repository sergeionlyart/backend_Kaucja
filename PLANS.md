# ExecPlan: Iteration 4 Full E2E Pipeline

## Scope
Implement end-to-end pipeline in local sandbox:
`OCR -> pack_documents -> LLM structured output -> validate_output -> persist -> UI`.

## Dependencies
1. Iteration 2 OCR artifacts and documents persistence.
2. Iteration 3 LLM clients + validators.
3. SQLite schema with `runs/documents/llm_outputs`.

## Steps
1. Extend artifacts API for run-level LLM files (`llm/request.txt`, `llm/response_raw.txt`, `llm/response_parsed.json`, `llm/validation.json`).
2. Extend storage repo:
   - upsert/get `llm_outputs`
   - update `runs.timings_json`, `usage_json`, `usage_normalized_json`, `cost_json`
   - preserve `error_code/error_message`.
3. Implement full orchestrator flow:
   - OCR stage
   - pack markdown documents
   - provider-specific LLM call (OpenAI/Gemini)
   - jsonschema + semantic invariant validation
   - persist metrics/artifacts/status.
4. Add runtime preflight checks for required SDK and API key by provider.
5. Upgrade Gradio Analyze callback to full pipeline outputs (OCR table, summary, raw JSON, validation, metrics).
6. Add tests:
   - repo llm_outputs + run metrics
   - orchestrator success/failure branches
   - integration full pipeline and schema-invalid scenario
   - updated UI smoke.
7. Run quality gates (`ruff format`, `ruff check`, `pytest`) and produce report.

## Risks
1. Provider SDK payload mismatch can break structured output calls.
2. Failure branches can leave partial artifacts/DB rows inconsistent.
3. Validation/invariant failures can be conflated with API failures if error mapping is weak.

## Risk Mitigation
1. Keep LLM payload builders unchanged; orchestrator only composes clients.
2. Persist artifacts in deterministic order and update run status with explicit error code.
3. Add dedicated tests per failure code: `LLM_API_ERROR`, `LLM_INVALID_JSON`, `LLM_SCHEMA_INVALID`.

## Definition of Done
1. Analyze executes full flow with mocked or real providers.
2. Run artifacts include OCR + LLM files under deterministic run path.
3. `llm_outputs` and run metrics are persisted.
4. UI shows OCR table, summary, raw JSON, validation status/errors, metrics.
5. `ruff format .`, `ruff check .`, `pytest -q` all pass.

## Rollback Plan
1. Keep changes scoped to `artifacts/repo/orchestrator/ui/tests`.
2. If regression appears, revert this branch commit(s) and return to `fab31f8` baseline.
3. Preserve existing Iteration 2 OCR-only behavior via prior commit history.

---

# ExecPlan: Iteration 5 Run Manifest + History UI

## Scope
Add deterministic `run.json` manifest updates through pipeline lifecycle and expose run history browsing/loading in Gradio UI.

## Dependencies
1. Iteration 4 full E2E flow (`OCR -> pack -> LLM -> validate -> persist`).
2. Existing SQLite entities `runs/documents/llm_outputs`.
3. Existing artifact tree `data/sessions/<session_id>/runs/<run_id>/...`.

## Steps
1. Add manifest module to create/update/read `run.json` under run artifacts root.
2. Integrate manifest updates in orchestrator at key stages:
   - init
   - after OCR
   - after LLM/validation
   - finalize (success/failure).
3. Extend repository APIs:
   - `list_runs(...)` with filters (`session_id/provider/model/prompt_version/date_from/date_to/limit`)
   - `get_run_bundle(run_id)` returning run + documents + llm_output.
4. Add safe artifact readers for:
   - `run.json`
   - `llm/*.json|txt`
   - `documents/*/ocr/combined.md`
   with non-throwing, user-readable errors.
5. Update Gradio UI with History section:
   - filters + table
   - load selected `run_id`
   - hydrate existing summary/raw/validation/metrics/OCR outputs
   - show artifacts root path.
6. Add tests:
   - manifest writer/reader unit
   - repo filter unit
   - orchestrator integration (`run.json` exists + keys)
   - UI history integration.
7. Run quality gates and publish report.

## Risks
1. Missing manifest updates in error branches.
2. Drift between DB values and file artifacts in history hydration.
3. Date filter edge cases (date-only vs datetime values).

## Risk Mitigation
1. Explicit manifest writes in each branch with stage status + error fields.
2. Prefer DB as source for run/doc metadata and artifact readers for payloads.
3. Normalize date-only filters to UTC day boundaries.

## Definition of Done
1. `run.json` exists per run and contains inputs/stages/artifacts/metrics/validation/error.
2. History UI lists runs by filters and loads past run payloads without crashes.
3. Missing artifacts surface readable messages in UI.
4. `ruff format .`, `ruff check .`, `pytest -q`, and `build_app()` startup check pass.

## Rollback Plan
1. Revert Iteration 5 commits touching `storage/pipeline/ui/tests`.
2. Keep Iteration 4 analyze flow intact as rollback baseline.
