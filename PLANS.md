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

---

# ExecPlan: Iteration 7 Reliability Hardening

## Scope
Finalize reliability hardening to align runtime behavior with TechSpec:
- OCR bad-page PDF renders
- bounded retry policies (OCR/LLM)
- full error taxonomy mapping
- deterministic persistence for context-too-large and failure branches

## Dependencies
1. Iteration 6 prompt/result UX baseline on `codex/iteration-7-reliability`.
2. Existing deterministic artifacts (`run.json`, `run.log`, `llm/*`, `documents/*`).
3. Existing orchestrator and storage repo contracts.

## Steps
1. Replace OCR bad-page placeholder with real PDF rendering in `page_renders/` using `pymupdf`.
2. Preserve safe non-PDF behavior with explicit warning in `quality.json`.
3. Enforce retry contracts:
   - OCR: one retry for transient network/timeout/429/5xx.
   - LLM: one retry for 429/5xx.
   - no retry for invalid JSON/schema/context-too-large.
4. Complete runtime taxonomy mapping:
   - `FILE_UNSUPPORTED`, `OCR_API_ERROR`, `OCR_PARSE_ERROR`
   - `LLM_API_ERROR`, `LLM_INVALID_JSON`, `LLM_SCHEMA_INVALID`
   - `CONTEXT_TOO_LARGE`, `STORAGE_ERROR`, `UNKNOWN_ERROR`.
5. Add best-effort persistence guards for failure paths to avoid cascading crashes when storage writes fail.
6. Update/extend tests:
   - OCR page renders (PDF render, non-PDF skip)
   - retry classifiers and retry attempts
   - storage/unknown error mapping branches
   - context-too-large deterministic failure branch.
7. Run quality gates and publish report.

## Risks
1. PDF renderer dependency mismatch (`pymupdf`) across local environments.
2. Retry logic accidentally triggering on non-retryable branches.
3. Storage failure during error handling causing secondary crashes.

## Risk Mitigation
1. Add dependency in `pyproject.toml` and cover with unit tests.
2. Keep retry classifiers explicit and test retry counts.
3. Use guarded best-effort persistence helpers and keep stack/details in log/artifacts.

## Definition of Done
1. Bad OCR pages from PDF produce real `page_renders/<page>.png`.
2. Non-PDF render path safely skips with warning.
3. Retry behavior matches TechSpec 9.3 exactly.
4. Error codes map consistently into run state + manifest + UI.
5. `ruff format .`, `ruff check .`, `pytest -q`, and `build_app` check pass.

## Rollback Plan
1. Revert Iteration 7 changes in `ocr_client/orchestrator/utils/tests`.
2. Keep Iteration 6 commit (`0e845ce`) as stable fallback.

# ExecPlan: Iteration 1 Scenario 2 Foundation

## Scope
Add a scenario router and foundation backend path for `Scenario 2` that shares OCR pipeline with Scenario 1 and ends in a controlled placeholder response.

## Dependencies
1. Existing Scenario 1 full pipeline (`OCR -> LLM -> validate -> persist`) unchanged.
2. Existing run manifest structure in `app/storage/run_manifest.py`.
3. Existing Gradio run callback and history/result rendering contract.

## Steps
1. Add explicit scenario constants/config in `app/pipeline/scenario_router.py` (`scenario_1`, `scenario_2`).
2. Add UI scenario selector and route selected value into `run_full_pipeline` callback.
3. Extend `run_full_pipeline` orchestrator signature to accept `scenario_id`.
4. In orchestrator:
   - resolve scenario config before run,
   - run OCR stage for both scenarios,
   - keep existing full path for Scenario 1,
   - for Scenario 2 skip LLM/tooling and write deterministic placeholder output and manifest metadata.
5. Add tests for:
   - orchestrator path routing,
   - UI run path routing,
   - manifest persistence of `scenario_id`.
6. Run `ruff format .`, `ruff check .`, `pytest -q`.

## Risks
1. Any change to Scenario 1 branch could introduce behavior drift.
2. Scenario 2 config hardens to fixed model/provider; accidental prompt manager coupling should be avoided this iteration.
3. Manifest-only scenario metadata means DB search/filter by scenario remains unavailable without optional DB migration.

## Definition of Done
1. Scenario 1 behavior unchanged.
2. Scenario 2 executes OCR and returns placeholder completion text.
3. `run.json` includes `inputs.scenario_id` for Scenario 2 runs.
4. `ruff` and `pytest -q` pass for changed surfaces.

# ExecPlan: Iteration 2 Scenario 2 UX + preflight + history hardening

## Scope
Harden foundation UX for `Scenario 2`:
1. run config should show fixed provider/model/prompt source for Scenario 2 and be non-editable;
2. OCR-only preflight path should not require OpenAI runtime and keys/tools;
3. history loading should render Scenario 2 runs as placeholder/flat JSON payload without checklist parsing;
4. validation/progress metadata should mark `not_applicable`/`skipped` for scenario foundation path.

## Steps
1. Update scenario-aware preflight in `app/ui/gradio_app.py` so Scenario 2 uses OCR-only checks.
2. Add/adjust Scenario 2 callback behavior in run config controls (`provider`, `model`, `prompt_name`, `prompt_version`) to fixed read-only values and explicit prompt-source hint.
3. Normalize history rendering:
   - load scenario metadata from manifest,
   - branch summary/raw for Scenario 2 placeholder,
   - render validation/progress as `not_applicable`/`skipped`.
4. Extend `app/pipeline/orchestrator.py` manifest/validation artifact writes for Scenario 2 (`validation.status` and message).
5. Add/update tests for:
   - UI preflight tolerance,
   - scenario-aware run-config controls,
   - history Scenario 2 load + progress/validation text,
   - foundation manifest status.
6. Run `ruff check .` and `python -m pytest -q`.

## Risks
1. Scenario 1 UX regression from shared model/prompt controls and prompt-version interactions.
2. Manifest backward compatibility for historical Scenario 1 runs without `inputs.scenario_id`.
3. Incomplete distinction between skipped validation and failed validation in UI parsing.

## Definition of Done
1. Scenario 2 can be run without OpenAI preflight/runtime dependence in this foundation path.
2. Scenario 2 UI run-config is explicitly fixed and non-editable.
3. History loading of Scenario 2 displays placeholder summary/raw and `not_applicable` validation/progress text.
4. Quality gates (`ruff check .`, `python -m pytest -q`) pass.

# ExecPlan: Iteration 3 Scenario 2 Switch Recovery + Contract Scaffold

## Scope
Harden Scenario 2 UX state recovery and prepare runtime contracts for the next step:
1. restore last valid Scenario 1 controls after Scenario 2 round-trip;
2. keep Scenario 1 controls untouched by Scenario 2 presentation.
3. add explicit contract types for legal corpus adapters and Scenario 2 runner.

## Dependencies
1. Iteration 1 and Iteration 2 changes (`scenario_router`, `gradio_app`, manifest/validation branches).
2. Existing deterministic manifest + storage layout.
3. Existing orchestrator extension point for Scenario 2 runner.

## Steps
1. Add UI state memory for last Scenario 1 config (`provider`, `model`, `prompt_name`, `prompt_version`).
2. Update Scenario 2 switch callback wiring to persist/restore that state and avoid invalid prompt-set injections.
3. Add regression test for full Scenario 1 → Scenario 2 → Scenario 1 value round-trip.
4. Add contract module `app/agentic/legal_corpus_contract.py` (TypedDict + Protocol).
5. Add Scenario 2 runner contract and default stub (`app/agentic/scenario2_runner.py`) usage in orchestrator via dependency injection.
6. Add/update tests verifying runner call path and contract artifacts.

## Risks
1. State restoration can regress when model/prompt dropdown choices change between switches.
2. Over-exposing scenario state could leak invalid values into LLM path.
3. Contract-only additions can be unused and untested.

## Risk Mitigation
1. Restore values only from captured Scenario 1 state; fallback to current Scenario 1 selections.
2. Keep Scenario 2 controls read-only and do not switch underlying prompt model selection.
3. Add explicit tests for round-trip behavior and `run_full_pipeline` runner usage.

## Definition of Done
1. Scenario 1 values round-trip correctly after Scenario 2 round-trip.
2. Scenario 2 UI controls never force non-existent prompt sets into Scenario 1 state.
3. `legal_corpus` and Scenario 2 runner contracts are added with stub path for foundation.
4. `ruff format .`, `ruff check .`, `python -m pytest -q` pass.

# ExecPlan: Iteration 4 Contract Fidelity + Trace Artifacts

## Scope
Finalize Scenario 2 contract/runtime fidelity before enabling real tool-based execution:
1) align `legal_corpus` request/response contracts to TechSpec fields and method names;
2) deterministic scenario prompt-source resolution to an existing file path;
3) persist Scenario 2 runner trace (`steps`, `tool_trace`, `diagnostics`) as a file artifact.

## Dependencies
1. Iteration 1-3 Scenario 2 scaffold.
2. Existing manifest and artifact pipeline.

## Steps
1. Update `app/agentic/legal_corpus_contract.py` to spec-aligned `TypedDict + Protocol` (`search`, `fetch_fragments`, `expand_related`, `get_provenance`).
2. Add scenario prompt resolver helper in `app/pipeline/scenario_router.py` that verifies file existence.
3. Make `StubScenario2Runner` read and fingerprint prompt source or raise deterministic failure if missing.
4. Persist Scenario 2 trace in `llm/scenario2_trace.json` and add `artifacts.llm.trace_path` to `run.json`.
5. Update orchestrator to pass resolved prompt path into runner and consume the trace artifact metadata.
6. Add/adjust tests:
   - exact request-shape checks for `legal_corpus_contract`;
   - resolved prompt path existence;
   - runner receives existing prompt path;
   - manifest points to Scenario 2 trace artifact.
7. Run `ruff check .` and `python -m pytest -q`.

## Risks
1. Incorrect prompt path resolution order may pass in local tests and fail in CI.
2. Trace persistence may be skipped in failure branches and reduce observability.

## Risk Mitigation
1. Keep resolver candidate order explicit and test with non-default `prompt_root`.
2. Store trace path in manifest via deterministic update after trace write.

## Definition of Done
1. `legal_corpus_contract.py` and runner contracts match TechSpec nomenclature.
2. Scenario 2 uses `resolve_scenario_prompt_source_path` with guaranteed existing path before runner execution.
3. `run.json` includes `artifacts.llm.trace_path` and referenced `scenario2_trace.json` exists.
4. `ruff check .` and `python -m pytest -q` pass.

# ExecPlan: Iteration 5 Scenario 2 Failure Hardening

## Scope
Make Scenario 2 failure handling deterministic so any post-OCR failure marks run as failed with explicit taxonomy and persisted state.

## Dependencies
1. Iteration 4 Scenario 2 contract and trace persistence scaffold.
2. Existing manifest + SQLite pipeline persistence.

## Steps
1. Add hardened failure handling in Scenario 2 branch:
   - prompt resolve errors -> `SCENARIO2_CONFIG_ERROR`
   - runner errors -> `SCENARIO2_RUNTIME_ERROR`
   - trace write errors -> `SCENARIO2_TRACE_PERSIST_ERROR`
2. Ensure `run.status` and `run.json` are always driven to failed in these branches and `stages.finalize.status` is failed.
3. Persist best-effort Scenario 2 failure trace payload with `response_mode`, `error_code`, `error_message`, and `error_stage`.
4. Add/extend tests:
   - scenario_id routing stays unchanged for success path;
   - prompt resolution failure;
   - runner failure;
   - trace persistence failure.
5. Keep `ruff check .` and `python -m pytest -q` passing.

## Definition of Done
1. Scenario 2 does not remain in running state after OCR-stage failures.
2. Failure errors are persisted to DB and manifest with deterministic error codes/messages.
3. Success path for Scenario 2 and Scenario 1 remains unchanged.
4. Validation/progress text remains not applicable/skipped in successful Scenario 2 flow.

# ExecPlan: Iteration 6b Scenario 2 Real Runner Wiring

## Scope
Wire the existing `OpenAIScenario2Runner` into orchestrator execution path via dependency injection, keeping stub path as default.

## Dependencies
1. Iteration 4-5 Scenario 2 contract/scaffold + failure hardening.
2. Existing `OCRPipelineOrchestrator` and scenario router.

## Steps
1. Add optional `legal_corpus_tool` dependency to `OCRPipelineOrchestrator`.
2. Pass injected `legal_corpus_tool` into `scenario2_runner.run(...)`.
3. Keep default runtime unchanged (`StubScenario2Runner` when runner is not injected).
4. Add orchestrator integration tests for:
   - successful real runner + injected fake legal tool,
   - injected real runner with missing `legal_corpus_tool` -> deterministic runtime failure.
5. Verify Scenario 2 real-runner trace artifact includes `model`, `tool_round_count`, `tool_trace`, and `diagnostics`.
6. Run `ruff check .` and `pytest -q`.

## Definition of Done
1. Orchestrator can execute Scenario 2 with injected `OpenAIScenario2Runner`.
2. Default Scenario 2 behavior remains stub-based.
3. Existing Scenario 1 behavior unchanged.

# ExecPlan: Iteration 8 Controlled Real Scenario 2 Bootstrap

## Scope
Make `Scenario 2` real mode (`openai_tool_loop`) bootstrappable without test-only manual injection while preserving the safe default stub path.

## Steps
1. Add a read-only local legal corpus adapter over the existing local collection layout.
2. Add a runtime factory that builds:
   - `StubScenario2Runner` in stub mode;
   - `OpenAIScenario2Runner + LocalLegalCorpusTool` in controlled real mode.
3. Extend settings with legal corpus backend and local root path.
4. Wire the factory into `gradio_app.py` and `service.py`.
5. Make Scenario 2 readiness/preflight report local corpus bootstrap errors deterministically.
6. Add tests for:
   - local adapter methods,
   - runtime factory success/failure,
   - build/service wiring,
   - real-mode Scenario 2 completion with fake OpenAI responses.
7. Run `ruff check .` and `python -m pytest -q`.

## Definition of Done
1. Default app path remains stub-based.
2. `openai_tool_loop` can be assembled from app settings without manual DI into orchestrator.
3. Local legal corpus adapter satisfies the contract and is covered by tests.
4. Invalid local corpus config fails closed without changing Scenario 1 behavior.

# ExecPlan: Iteration 9 Local Legal Corpus Retrieval Fidelity

## Scope
Increase local/dev `legal_corpus` retrieval truthfulness so Scenario 2 real mode has a more honest and citation-friendly dev backend.

## Steps
1. Enrich `LocalLegalCorpusTool.search(...)` with richer result metadata (`source_label`, `document_kind`, `doc_uid`, `source_hash`, locator fields, deep link where available).
2. Make `search()` explicitly report `applied_filters`, `ignored_filters`, and `unsupported_filters` for unsupported local capabilities (`as_of_date`, history, citation expansion, non-indexed filters).
3. Make `fetch_fragments()` return citation-ready payload plus diagnostics that it is using raw-text fallback and lacks page-level truth.
4. Extend `get_provenance()` with `provenance_status`, `integrity_status`, artifact hints, and current-snapshot-only version semantics.
5. Keep `expand_related()` deterministic but return structured explanation payload for unsupported local graph expansion.
6. Add focused adapter tests and rerun `ruff check .` and `python -m pytest -q`.

## Definition of Done
1. Local adapter no longer silently ignores unsupported retrieval options.
2. Search/fragment/provenance payloads are richer and explicitly mark local backend limitations.
3. Existing Scenario 2 controlled bootstrap remains green and Scenario 1 remains unchanged.

# ExecPlan: Iteration 10 Scenario 2 Source-Grounding Guard

## Scope
Harden `Scenario 2` real runner so a final answer cannot be accepted after retrieval-tool usage unless exact fragments were fetched through `fetch_fragments`.

## Steps
1. Track Scenario 2 tool usage counts for `search`, `fetch_fragments`, `expand_related`, and `get_provenance` inside `OpenAIScenario2Runner`.
2. Add a fragment-grounding guard: if retrieval tools were used without any successful `fetch_fragments`, do not accept the first final answer.
3. Use one repair turn with an explicit grounding reminder, then fail closed if the model still does not fetch fragments.
4. Persist grounding diagnostics (`tool_usage_counts`, `fragment_grounding_status`, `successful_fetch_fragments`, `repair_turn_used`) in the runner result and trace artifact.
5. Add/update runner and integration tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 no longer silently accepts ungrounded final text after retrieval-step usage.
2. Trace and diagnostics show whether the final answer was fragment-grounded.
3. Existing Scenario 2 openai bootstrap and Scenario 1 behavior remain unchanged.

# ExecPlan: Iteration 11 Scenario 2 Citation Binding

## Scope
Persist fetched fragment provenance in `Scenario 2` real-runner diagnostics so trace data distinguishes missing fragments from a concrete fetched-fragment ledger.

## Steps
1. Add fetched fragment ledger tracking in `OpenAIScenario2Runner` for successful `fetch_fragments` calls.
2. Persist flattened provenance fields (`fetched_fragment_refs`, `fetched_fragment_doc_uids`, `fetched_fragment_source_hashes`) plus `citation_binding_status`.
3. Keep `missing_fragments` fail-closed behavior for retrieval-without-fetch unchanged.
4. Mark successful fetch-based runs as `fragments_fetched` unless a stronger binding proof exists; do not pretend `fragments_bound`.
5. Add/update runner and persisted-trace tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 trace stores concrete fetched fragment provenance.
2. Diagnostics distinguish `missing_fragments` from `fragments_fetched`.
3. Existing Scenario 2 openai bootstrap and Scenario 1 behavior remain unchanged.

# ExecPlan: Iteration 12 Scenario 2 Strict fetch_fragments success semantics

## Scope
Tighten Scenario 2 grounding so `fetch_fragments` only counts as successful when it returns at least one usable fragment with a stable provenance handle.

## Steps
1. Split `fetch_fragments` attempt tracking from usable-fragment success tracking inside `OpenAIScenario2Runner`.
2. Add a helper that treats fetched fragments as usable only when they carry a non-empty `machine_ref` or another stable provenance handle such as `doc_uid` / `source_hash`.
3. Keep the existing repair/fail-closed path, but require usable fetched fragments before final text is accepted.
4. Persist stricter diagnostics in the runner result and trace artifact, including `fetch_fragments_called`, `fetch_fragments_returned_usable_fragments`, and the new `empty_fragments` status.
5. Add/update unit and integration tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Empty or unusable `fetch_fragments` responses no longer remove the grounding guard.
2. `fragment_grounding_status` / `citation_binding_status` stay below `fragments_fetched` until at least one usable fragment exists.
3. Existing Scenario 2 happy path and Scenario 1 behavior remain unchanged.

# ExecPlan: Iteration 13 Preserve partial Scenario 2 failure diagnostics

## Scope
Preserve partial Scenario 2 runtime context on `openai_tool_loop` failures so `scenario2_trace.json` remains informative even when the runner exits with an error.

## Steps
1. Add a `Scenario2RunnerError` type that carries partial `steps`, `tool_trace`, `diagnostics`, `model`, `tool_round_count`, and optional `final_text`.
2. Raise `Scenario2RunnerError` from `OpenAIScenario2Runner` when meaningful partial state already exists, including tool-loop failures, grounding fail-closed errors, and post-step runtime anomalies.
3. Teach the orchestrator to catch `Scenario2RunnerError` separately and pass its partial result into the existing failure trace persistence path.
4. Add/update runner and orchestrator tests that verify failure trace persistence for `missing_fragments`, `empty_fragments`, and repair-turn state.
5. Rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 runner failures no longer discard partial `steps`, `tool_trace`, or grounding diagnostics.
2. `scenario2_trace.json` on failure contains the accumulated trail plus `error_code` / `error_message`.
3. Existing Scenario 2 success path and Scenario 1 behavior remain unchanged.

# ExecPlan: Iteration 14 Scenario 2 diagnostics in Gradio UI and history

## Scope
Expose Scenario 2 grounding, provenance, and failure-trace diagnostics in Gradio for both live runs and history loads without changing Scenario 1 behavior or backend retrieval logic.

## Steps
1. Add read-only Scenario 2 diagnostics and fetched-fragments UI blocks in `gradio_app.py` without changing the overall page layout.
2. Load `scenario2_trace.json` from the manifest when available and render runner mode, grounding status, fetch flags, repair status, tool round count, and tool-trace summary.
3. Render fetched fragment citations / doc_uids / source hashes in a separate summary block, with explicit `none` markers when absent.
4. Make history load Scenario 2-aware so failed runs surface partial diagnostics instead of only the generic error text.
5. Add/update Gradio smoke tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 diagnostics are visible in live-run UI and history load.
2. Failed Scenario 2 runs show partial trace summary and grounding diagnostics.
3. Scenario 1 behavior and default Scenario 2 stub path remain unchanged.

# ExecPlan: Iteration 15 Scenario 2-aware run comparison

## Scope
Extend run comparison so Scenario 2 runs are compared using grounding, provenance, and fetched-fragment diagnostics, while mixed Scenario 1 / Scenario 2 comparisons stay explicitly non-structural and honest.

## Steps
1. Extend `run_comparison.py` snapshots to load `scenario2_trace.json` through manifest `trace_path` when a run belongs to Scenario 2.
2. Persist Scenario 2 comparison fields in the snapshot: runner mode, LLM execution flag, grounding/citation statuses, fetch flags, repair flag, tool rounds, and fetched fragment provenance lists.
3. Add scenario-aware diff logic so Scenario 2 vs Scenario 2 compares diagnostics and fetched fragments set-wise, while mixed-scenario comparison suppresses checklist diff with an explicit compatibility summary.
4. Update Gradio compare rendering to show Scenario 2-specific summary text and fetched-fragment changes without redesigning the page.
5. Add/update comparison and Gradio tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Compare flow meaningfully compares two Scenario 2 runs using diagnostics and fetched fragments.
2. Mixed Scenario 1 / Scenario 2 comparison clearly states that checklist comparison is not applicable.
3. Existing Scenario 1 comparison behavior remains unchanged.

# ExecPlan: Iteration 16 Persist and render fetched fragment excerpts

## Scope
Make Scenario 2 more audit-friendly by persisting citation-ready fetched fragment excerpts plus locator metadata in trace diagnostics, then surfacing that data in live-run UI, history load, and Scenario 2 comparison.

## Steps
1. Extend the fetched fragment ledger in `OpenAIScenario2Runner` with deterministic excerpt and locator fields from `fetch_fragments` output: `text_excerpt`, `locator`, `locator_precision`, `page_truth_status`, and `quote_checksum`.
2. Keep backward compatibility for existing flattened provenance fields and add a stable flattened checksum list for comparison.
3. Update the Gradio Scenario 2 fetched-fragments block to render excerpt, locator, truth-status, and checksum fields when present, with explicit `none` markers otherwise.
4. Extend Scenario 2 comparison snapshot/diff so fetched fragments can be compared set-wise by stable quote checksum in addition to citations and provenance IDs.
5. Add/update runner, Gradio, compare, and persisted-trace tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 trace stores citation-ready fetched fragment excerpts and locator metadata.
2. Gradio shows fetched fragment excerpts in live-run and history when Scenario 2 trace contains them.
3. Scenario 2 comparison can detect fetched fragment changes by stable checksum without changing Scenario 1 behavior.

# ExecPlan: Iteration 17 Deterministic Scenario 2 verifier pass

## Scope
Add a lightweight deterministic verifier for Scenario 2 final text so the runner, trace, UI, and compare flow expose whether the response follows the required prompt structure and explicitly references fetched sources when retrieval was used.

## Steps
1. Add a pure `scenario2_verifier.py` module with deterministic section checks for the required Russian headings and conservative source-reference checks against fetched fragment surface.
2. Integrate verifier diagnostics into `OpenAIScenario2Runner` without changing success/failure semantics of the existing tool loop.
3. Persist verifier diagnostics in `scenario2_trace.json`: `verifier_status`, `missing_sections`, `sources_section_present`, `fetched_sources_referenced`, and `verifier_warnings`.
4. Extend Gradio Scenario 2 diagnostics rendering and Scenario 2 compare snapshot/diff to surface verifier outcomes without redesigning the UI.
5. Add/update runner, Gradio, compare, and integration tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 trace contains deterministic verifier diagnostics.
2. Gradio shows verifier status and missing sections for Scenario 2 live/history views.
3. Scenario 2 comparison can compare verifier outcomes while Scenario 1 behavior remains unchanged.

# ExecPlan: Iteration 18 Deterministic citation-format verifier

## Scope
Strengthen the Scenario 2 deterministic verifier with citation-discipline checks so trace, UI, and compare flow expose whether the final answer uses prompt-compliant inline citations and keeps legal citations inside analytical sections when retrieval was used.

## Steps
1. Extend `scenario2_verifier.py` with regex-based checks for `[Документ пользователя: ...]`, `[Норма: ...]`, and `[Практика: ...]` citation formats.
2. Persist citation-format diagnostics from `OpenAIScenario2Runner`: `citation_format_status`, legal/user citation counts, `citations_in_analysis_sections`, and `malformed_citation_warnings`.
3. Update Gradio Scenario 2 diagnostics rendering to show citation-format status and citation counts without changing page layout.
4. Extend Scenario 2 comparison snapshot/diff to compare citation-format outcomes in addition to existing verifier and grounding fields.
5. Add/update runner, Gradio, compare, and integration tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 trace contains deterministic citation-format verifier diagnostics.
2. Gradio shows citation-format status and citation counts for Scenario 2 live/history views.
3. Scenario 2 comparison can compare citation-format outcomes while Scenario 1 behavior remains unchanged.

# ExecPlan: Iteration 19 Promote Scenario 2 verifier to run-level review status

## Scope
Expose Scenario 2 verifier outcomes as a run-level review signal so history, manifest, live/history UI, and compare flow can quickly show which runs need manual review without changing `run.status`.

## Steps
1. Derive Scenario 2 `review_status` from verifier outcomes with deterministic mapping: `warning -> needs_review`, `passed -> passed`, otherwise `not_applicable`.
2. Persist review payload in `run.json` for Scenario 2 success/failure manifests without adding a SQLite migration.
3. Extend Gradio history rows and filters with scenario-aware `review_status`, keeping Scenario 1 as `not_applicable`.
4. Surface `review_status` in Scenario 2 live/history diagnostics and Scenario 2 or mixed compare summaries.
5. Add/update orchestrator, Gradio, and comparison tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 manifests persist a run-level review payload without changing `run.status`.
2. History rows and filters show `review_status`, and Scenario 1 remains `not_applicable`.
3. Scenario 2 compare flow can compare `review_status` while mixed comparisons stay honest.

# ExecPlan: Iteration 20 Configurable Scenario 2 verifier gate

## Scope
Add a configurable verifier-policy layer for Scenario 2 so the default path stays informational, while optional strict mode makes verifier warnings gate-relevant without turning the run itself into a failed run.

## Steps
1. Add `scenario2_verifier_policy` to settings and propagate it through Gradio and API bootstrap into `OCRPipelineOrchestrator`.
2. Derive deterministic `verifier_gate_status` from `(policy, verifier_status, llm_executed)` and persist it manifest-first plus in Scenario 2 trace diagnostics.
3. Keep `run.status` unchanged and expose strict-mode outcome through explicit gate fields instead of a terminal run failure.
4. Extend Scenario 2 diagnostics UI and Scenario 2 compare flow to show `verifier_policy` and `verifier_gate_status`.
5. Add/update orchestrator, Gradio, settings, API, and comparison tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 supports `informational` and `strict` verifier policies with default behavior unchanged.
2. Strict mode persists explicit gate outcomes in manifest/trace without changing `run.status`.
3. Gradio and Scenario 2 compare flow surface verifier policy and gate status while Scenario 1 remains unchanged.

# ExecPlan: Iteration 21 Final production completion for Scenario 2

## Scope
Close the remaining P0/P1 items from `Tech_spec_agents.md` by adding a production-capable Mongo-first legal corpus backend, a materialized retrieval layer, citation resolution, version-aware retrieval, provenance normalization, and a separate case workspace path for Scenario 2, while keeping Scenario 1 and the default stub path unchanged.

## Steps
1. Add a Mongo-backed Scenario 2 legal corpus adapter plus a materializer for `retrieval_units`, `citation_resolutions`, and retrieval index freshness metadata using the existing `legal_ingest` Mongo schema as the source of truth.
2. Implement production retrieval behaviors on top of the materialized layer: operational/indexable filtering, current-only and `as_of_date` version selection, dedup by canonical/duplicate/same-case groups, real citation-resolution expansion, and stable provenance payloads.
3. Add a separate Mongo-backed case workspace store for `case_workspaces`, `case_documents`, `case_facts`, and `analysis_runs`, and wire it into Scenario 2 orchestrator flow without touching Scenario 1.
4. Extend settings and runtime factory so `scenario2_legal_corpus_backend=mongo` bootstraps a fully working production path through app/UI/API wiring, while keeping `local` as a dev fallback.
5. Add/update unit and integration tests for the materializer, Mongo adapter, runtime factory, case workspace persistence, and an end-to-end Scenario 2 production path, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 can bootstrap a production-capable Mongo-backed `legal_corpus` through settings/bootstrap, not only through manual test DI.
2. Retrieval is driven by materialized `retrieval_units` plus citation resolution, respects operational/indexable and version-aware constraints, and returns stable provenance payloads.
3. User case documents and analysis runs are stored in separate case-workspace collections, leaving the authoritative legal corpus isolated.

# ExecPlan: Iteration 22 Close final spec gaps for case workspace and retrieval audit trail

## Scope
Close the last remaining spec-level gaps for the production Scenario 2 path without changing Scenario 1 or the already-green runner/verifier/UI flow: finish the minimal `case_workspace` contract, add deterministic tool-level audit fields to `legal_corpus` responses, and harden the materialized Mongo rebuild path so partial failures never clear the last valid retrieval index.

## Steps
1. Ensure `case_workspaces` explicitly persists the minimal contract fields from `Tech_spec_agents.md`, even when values are currently unknown, and keep `case_facts` truthfully marked as pending instead of implying extracted facts exist.
2. Add deterministic audit payloads to Mongo-backed `search`, `fetch_fragments`, `expand_related`, and `get_provenance`: request/tool identifiers, request hashes, latency, returned refs, and warnings.
3. Preserve those tool-level audit fields in `Scenario 2` runner trace so `scenario2_trace.json` remains replayable without UI redesign.
4. Replace destructive materialized rebuild semantics with a safe build-then-promote strategy that keeps the previous completed index active when a new rebuild fails.
5. Add/update focused tests for the case-workspace contract, Mongo tool audit fields, safe rebuild fallback, and trace persistence, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. `case_workspaces` and `case_facts` satisfy the minimal truthful contract from `Tech_spec_agents.md`.
2. All Mongo-backed legal-corpus tool responses carry deterministic audit payloads, and Scenario 2 trace preserves them.
3. A rebuild failure no longer creates an empty/partially promoted retrieval index; the last completed build stays readable.

# ExecPlan: Iteration 23 Wire real case metadata into Scenario 2 case workspace

## Scope
Make the Scenario 2 case workspace use real runtime metadata instead of only storing a schema-shaped empty shell: introduce an explicit typed case-metadata payload, pass already-known API signals through orchestrator startup, and keep Gradio honest by leaving missing values as explicit `None`.

## Steps
1. Add a typed `Scenario2CaseMetadata` payload for `claim_amount`, `currency`, `lease_start`, `lease_end`, `move_out_date`, and `deposit_return_due_date`.
2. Extend `OCRPipelineOrchestrator.run_full_pipeline(...)` and Scenario 2 workspace bootstrap so known metadata is written via `store.ensure_workspace(...)` while absent fields remain explicit `None`.
3. In the API path, derive the minimal safe payload from already-extracted signals only: `deposit_amount -> (claim_amount, currency)` and `move_out_date`, with no new heuristics for other fields.
4. Keep Gradio unchanged: it does not currently collect case metadata, so Scenario 2 continues to persist `None` there by design.
5. Add/update API and orchestrator tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Known case-level metadata from the API path reaches Scenario 2 workspace persistence.
2. Missing metadata remains explicit `None` instead of being omitted or invented.
3. Scenario 1 and existing Scenario 2 retrieval/verifier flows remain unchanged.

# ExecPlan: Iteration 24 Explicit Scenario 2 case workspace in Gradio

## Scope
Bring the main Gradio Scenario 2 path to the same case-awareness level as the backend/runtime path: allow an explicit `case_id`, allow direct entry of minimal case metadata, pass both into the existing Scenario 2 workspace flow, and keep a safe fallback to `session_id` when no case id is provided.

## Steps
1. Add a compact Scenario 2 case-workspace block to Gradio with `Scenario 2 Case ID` plus optional `claim_amount`, `currency`, `lease_start`, `lease_end`, `move_out_date`, and `deposit_return_due_date` fields.
2. Keep the block hidden for Scenario 1 and visible for Scenario 2 without changing the existing Scenario 1 config controls or round-trip state behavior.
3. Extend `OCRPipelineOrchestrator.run_full_pipeline(...)` to accept an explicit `scenario2_case_workspace_id`, persist it in manifest inputs, and fall back to `session_id` only when the UI leaves it blank.
4. Pass Gradio-entered case metadata into the existing `Scenario2CaseMetadata` payload and propagate it through the existing Scenario 2 workspace bootstrap path.
5. Add/update Gradio smoke/integration tests plus orchestrator coverage, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Gradio Scenario 2 supports explicit `case_id` and minimal case metadata inputs.
2. Explicit Gradio case metadata is persisted into `case_workspaces`, while blank case id safely falls back to `session_id`.
3. Scenario 1 behavior and Scenario 2 retrieval/verifier semantics remain unchanged.

# ExecPlan: Iteration 25 Persist effective Scenario 2 case workspace identity

## Scope
Close the last Scenario 2 reproducibility gap around case workspace identity: persist the effective `case_workspace_id` that was actually used at runtime, including the fallback-to-`session_id` path, and make live/history UI read that persisted value instead of relying only on transient UI state.

## Steps
1. Compute the effective Scenario 2 `case_workspace_id` before `run.json` is initialized so manifest inputs always contain the real runtime value.
2. Keep explicit Scenario 2 case ids unchanged, but persist fallback `session_id` when the request leaves case id blank.
3. Make the live Gradio status line prefer the persisted manifest `case_workspace_id`, matching history-load behavior.
4. Update focused orchestrator and Gradio tests for explicit-id persistence, fallback-id persistence, and history/status rendering.
5. Rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 `run.json` always contains the effective `case_workspace_id` that runtime actually used.
2. Blank Scenario 2 case id no longer disappears from manifest inputs after fallback to `session_id`.
3. Live and history Gradio summaries show the persisted Scenario 2 case workspace identity.

# ExecPlan: Iteration 26 Complete Mongo search filter contract

## Scope
Finish the remaining Mongo `legal_corpus.search(...)` contract work without touching Scenario 1 or Scenario 2 runtime/UI flow: support the required metadata filters from `Tech_spec_agents.md`, make `status` a truthful alias to `current_status`, and replace the old hidden `include_history` no-op with deterministic behavior plus explicit diagnostics.

## Steps
1. Extend `app/agentic/legal_corpus_mongo.py` to support `issue_tags`, `facts_tags`, `related_provisions`, `judgment_date`, and `status -> current_status` alias semantics while keeping existing filters intact.
2. Make list-like filters use deterministic exact-token/intersection matching and document those rules in search diagnostics.
3. Implement honest `include_history` behavior for the materialized layer: return multiple source versions when possible, and persist explicit status/diagnostics instead of silently ignoring the option.
4. Ensure `unsupported_filters`, `applied_filters`, and `ignored_filters` only report truly unsupported or truly ignored inputs.
5. Add/update focused Mongo backend tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Mongo search supports the required metadata filters from `Tech_spec_agents.md`.
2. `unsupported_filters` no longer includes filters that the backend really handles.
3. `include_history` is no longer a hidden no-op and is surfaced via deterministic diagnostics.

# ExecPlan: Iteration 27 Implement real return_level semantics in Mongo search

## Scope
Finish the remaining Mongo search contract gap by making `SearchRequest.return_level` real instead of fragment-only: add truthful `document`, preserve `fragment`, and implement deterministic `mixed` results without changing Scenario 1 or the Scenario 2 runner/verifier/UI flow.

## Steps
1. Keep the existing fragment scoring and authority dedupe as the baseline, then layer `document` and `mixed` result-building on top of the same candidate set.
2. Add a distinct document-level payload shape with stable machine refs that remain usable for subsequent `fetch_fragments(...)`.
3. Implement deterministic `mixed` ordering so the payload can contain both document- and fragment-level candidates without duplicate authorities.
4. Update `effective_return_level` and search diagnostics so they reflect the actual returned mode instead of always saying `fragment`.
5. Add focused Mongo backend tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Mongo `search(...)` truthfully supports `return_level=document`, `fragment`, and `mixed`.
2. `effective_return_level` and per-result metadata/diagnostics match the actual returned level.
3. Existing fragment/filter/include-history behavior remains green.

# ExecPlan: Iteration 28 Fix Scenario 2 OpenAI tool-output payload and Gradio item_id=None crash

## Scope
Fix two narrow regressions without touching Scenario 1 or the Scenario 2 retrieval/verifier flow: make second-round OpenAI Responses payloads use the correct `function_call_output` shape, and make Gradio checklist-details rendering safe when `item_id` is `None` or no checklist exists.

## Steps
1. Remove unsupported fields from Scenario 2 second-round `function_call_output` items in `app/agentic/openai_scenario2_runner.py`, keeping tool trace and ledger behavior unchanged.
2. Add runner regression coverage that inspects the serialized second-round request payload and verifies `tool_name` is no longer sent.
3. Add an orchestrator-level regression that exercises the fake OpenAI/tool loop path and confirms second-round payload compatibility.
4. Harden `app/ui/result_helpers.py` and `app/ui/gradio_app.py` so empty or `None` checklist selection returns a safe details string instead of raising.
5. Add UI/helper regression tests, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 second OpenAI round no longer sends unsupported `input[*].tool_name`.
2. The fake OpenAI orchestration path proceeds past second-round payload assembly without request-shape failure.
3. Gradio details rendering no longer crashes when `item_id` is `None` or no checklist is available.

# ExecPlan: Iteration 29 Fix call_id / second-round threading for OpenAI Responses API in Scenario 2

## Scope
Fix the remaining OpenAI Responses API continuation bug in Scenario 2 without touching Scenario 1, retrieval, verifier, or UI flow: preserve the real `call_id`, pass `previous_response_id` for continuation, and keep regression coverage at both runner and orchestrator level.

## Steps
1. Update `app/agentic/openai_scenario2_runner.py` so continuation requests prefer OpenAI `call_id` over tool-item `id` and carry `previous_response_id` whenever the prior response exposes it.
2. Keep a safe fallback for fake/no-id responses so existing tests and deterministic local harnesses still work without rewriting unrelated code.
3. Strengthen runner tests to snapshot second- and third-round request payloads, including `previous_response_id` and exact `function_call_output.call_id`.
4. Add orchestration-level regression coverage for the same threading contract through the fake legal-corpus path.
5. Rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 continuation no longer loses or substitutes the real OpenAI `call_id`.
2. Second-round and later requests use `previous_response_id` when the prior response provided one.
3. Fake-service regression tests catch both wrong `call_id` threading and missing `previous_response_id`.

# ExecPlan: Iteration 30 Fix final live OpenAI threading blocker for Scenario 2 end-to-end

## Scope
Keep the diff narrowly focused on the real Responses API continuation contract in `app/agentic/openai_scenario2_runner.py`: preserve real OpenAI `response.id` and `call_id`, persist sanitized threading debug data for live diagnosis, and add a reproducible real smoke path without touching Scenario 1, retrieval, verifier, or UI semantics.

## Steps
1. Extend the Scenario 2 OpenAI runner to persist sanitized threading diagnostics for each request round: `previous_response_id`, parsed tool-call ids, and hashed/sized continuation payload summaries.
2. Preserve those debug fields in `scenario2_trace.json` through existing diagnostics persistence, without adding new artifact classes or redesigning trace structure.
3. Strengthen runner regression tests with SDK-like response objects that expose `response.id` via object attributes rather than plain dict payloads.
4. Extend orchestrator-level regression coverage so persisted Scenario 2 traces prove the same `call_id` / `previous_response_id` chain.
5. Add a manual live smoke script that runs Scenario 2 through OCR + real OpenAI tool continuation using normal settings/bootstrap, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. Scenario 2 no longer fails on real continuation with `No tool call found for function call output with call_id ...`.
2. Persisted diagnostics expose enough sanitized threading state to debug real OpenAI continuation failures.
3. A reproducible local smoke command exists for this exact live-threading bug, separate from fake-service regression tests.

# ExecPlan: Iteration 31 Fix final fetch_fragments.refs blocker in Scenario 2

## Scope
Keep the diff limited to `fetch_fragments` request normalization in the Scenario 2 OpenAI runner: accept the model-side alias `references`, normalize it to backend-facing `refs`, persist that normalization in trace/tool diagnostics, and verify the real smoke path moves beyond the old blocker.

## Steps
1. Add a narrow `fetch_fragments` request normalizer in `app/agentic/openai_scenario2_runner.py` that maps `references -> refs` before validation and dispatch.
2. Persist alias application in Scenario 2 `tool_trace`, including normalized request args and the original raw request when they differ.
3. Add runner-level regression coverage for `references`, keep `refs` happy-path green, and preserve failure on truly empty requests.
4. Add orchestrator-level coverage for the same alias through the fake OpenAI/tool loop path.
5. Re-run the existing real smoke command to confirm Scenario 2 moves past the old `fetch_fragments: refs` blocker, then rerun `ruff check .` and `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`.

## Definition of Done
1. `fetch_fragments` no longer fails when the model sends `references` instead of `refs`.
2. Scenario 2 trace/tool diagnostics show that alias normalization happened.
3. Real smoke reaches at least the post-`fetch_fragments` stage instead of failing on the old contract mismatch.
