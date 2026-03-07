# ExecPlan: Iteration 74 Prompt Modes (Structured JSON + Plain Text)

## Scope
Add explicit prompt-mode support so the UI can switch between:
- the existing structured JSON prompt-set;
- a new plain-text prompt sourced from `canonical_prompt_V3_1.md`.

The selected prompt must flow end-to-end into backend execution and UI rendering.

## Constraints
1. Existing JSON flow must stay backward-compatible.
2. Prompt selection must remain deterministic and persisted in run artifacts.
3. Plain-text prompts must not be forced through JSON parsing/schema validation.
4. Prompt metadata must declare response mode explicitly.

## Steps
1. Extend prompt metadata loading to expose `response_mode` and external prompt source paths.
2. Register a second prompt-set for the V3.1 canonical brief prompt.
3. Add `generate_text()` support to OpenAI/Gemini clients while keeping `generate_json()` intact.
4. Refactor orchestrator prompt loading:
   - keep canonical lock for the current structured JSON prompt;
   - branch LLM execution by prompt response mode.
5. Update Gradio UI rendering:
   - prompt choice remains user-selectable;
   - plain-text runs render the text brief in human-readable output and skip JSON validation UI.
6. Add tests for prompt manager, orchestrator plain-text mode, and UI plain-text rendering.
7. Run `ruff` and `pytest`, then restart the local app.

## Risks
1. Existing TechSpec lock can reject any non-canonical prompt unless explicitly scoped.
2. History/UI paths assume parsed JSON exists.
3. Saving a new version of a plain-text prompt can silently lose its mode if metadata is not preserved.

## Mitigation
1. Scope TechSpec lock to the canonical structured prompt only.
2. Persist plain-text response in raw artifacts and store an empty parsed artifact placeholder.
3. Preserve `response_mode` metadata when saving new prompt versions.

## Definition of Done
1. UI exposes both prompt options.
2. Backend uses the actually selected prompt.
3. Structured JSON prompt still validates as before.
4. Plain-text prompt completes successfully and renders readable output in UI/history.
5. `ruff check .` and `pytest -q` pass.
