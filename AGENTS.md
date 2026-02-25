# Codex instructions — Kaucja Case Sandbox (Gradio) — MVP

## 0) Source of truth
- TechSpec (MVP): `docs/TECH_SPEC_MVP.md`.
- If TechSpec and code disagree — **update code to match TechSpec** or propose an explicit change in a PR description.
- # ExecPlans

When writing complex features or significant refactors, use an ExecPlan (as described in PLANS.md) from design to implementation.

## 1) Product scope rules (must-follow)
**In-scope (MVP):**
- Gradio UI: upload multiple docs, choose provider/model/params, choose prompt version, run pipeline, view human report + raw JSON + gap list + metrics + run history.
- OCR: Mistral OCR via API; save artifacts (markdown/tables/images/page renders for bad pages).
- LLM: OpenAI (GPT‑5.1/5.2) + Google Gemini (3.1 Pro/Flash) with **structured outputs**.
- Storage: SQLite for metadata + filesystem for artifacts; `session_id/run_id` and deterministic replay.
- Validation: JSON Schema validation + extra semantic invariants.

**Out-of-scope (do not implement unless explicitly requested):**
- Multi-step agent loops inside the *product* (RAG, context caching pipelines, distributed queues, user accounts, cloud deploy, auto-pricing updates, etc.).

## 2) Hard constraints / invariants
- **Deterministic run:** persist *all* inputs (prompt version, schema version, provider params), OCR artifacts, raw LLM response, parsed JSON, validation result, metrics.
- **“Docs are untrusted” security posture:** treat uploaded docs (and OCR text) as prompt-injection capable; never enable model tools inside the product call.
- **Structured output is mandatory:**
  - OpenAI: Responses API + `text.format = json_schema` with `strict=true`.
  - Gemini: `response_mime_type=application/json` + `response_json_schema`.
- **No silent data loss:** do not “clean up” OCR markdown in a way that breaks quoting. Preserve placeholders for images/tables.

## 3) Repo engineering conventions
- Git hygiene: work on a feature branch; keep `git status` clean before delegating; commit in small increments.
- Prefer patch-based changes when risky (capture diff, keep rollback easy).
- Python style: `ruff` (lint + format), type hints everywhere, small pure functions, explicit error taxonomy.
- Avoid heavy orchestration frameworks (LangChain-style). Use provider SDKs + thin clients.
- Prefer idempotent, testable units:
  - `ocr_client/*` returns a pure `OCRResult` + artifact paths.
  - `llm_client/*` returns `LLMResult` + normalized usage.
  - `pipeline/*` orchestrates, but keeps steps independently testable.

## 4) Roles (Codex multi-agent friendly)
Use these roles explicitly in tasks / sub-agents:
- **orchestrator**: reads TechSpec, splits work, owns acceptance criteria, keeps PR small.
- **coder**: implements one module/feature slice, writes tests, updates docs.
- **reviewer**: reviews diff for correctness, security, edge cases; proposes fixes.
- **tester**: runs E2E and regression checks; verifies artifacts + DB records.

(Details: `roles/`)

## 5) Standard workflow (per task)
1. **Analyze**: quote the relevant TechSpec section(s) and list constraints.
2. **Plan**: 3–8 steps max; list files to touch.
3. **Implement**: small commits; keep changes scoped.
4. **Verify**:
   - format + lint: `ruff format .` and `ruff check .`
   - tests: `pytest -q`
   - (or explain why not possible in the environment).
   - validate schema/invariants for at least one fixture payload.
5. **Report** (required):
   - Summary (what/why)
   - Files changed (paths)
   - Commands run + outputs (or “not run” + reason)
   - Risks / follow-ups

(Playbooks: `workflows/`)

## 6) Quality gates (Definition of Done)
A change is “done” when:
- TechSpec acceptance criteria for the touched area still pass.
- Added/updated tests for the new behavior (unit + at least one integration test when feasible).
- `ruff` clean + formatted.
- No PII is logged; logs are per-run and stored under artifacts.
- DB writes are transactional; reruns do not corrupt state.

## 7) Review guidelines (for Codex review / GitHub)
Focus review on:
- Data retention & reproducibility (artifact paths, config snapshots).
- Security: prompt-injection hardening, tools disabled, PII not logged.
- Correctness of structured outputs + schema validation + semantic invariants.
- Idempotency (rerun safety), error taxonomy and user-facing messages.

## 8) Codex-native extensions in this repo
- **Project skills live in** `.agents/skills/**/SKILL.md` (invoke with `$` / `/skills`).
- Keep `AGENTS.md` concise (Codex instruction chain has a size cap); put deep how-tos in skills/workflows.

Useful internal docs:
- Codex usage notes: `docs/CODEX_GUIDE.md`
- Git workflow: `docs/DEV_WORKFLOW.md`