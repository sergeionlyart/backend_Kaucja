# Iteration 24 - User Readiness Report

**Date:** 2026-02-27T11:58:00+01:00
**Branch:** `codex/iteration-24-user-readiness`
**Status:** **PARTIALLY_READY** (LLM flow is fully operational, OCR flow is blocked on external dependencies).

## 1. Executive Summary
The backend_Kaucja application has successfully completed Iteration 24: User Readiness. Critical bugs disrupting local developer flow and automated smoke tests have been addressed, and a streamlined mechanism for users to initialize the app without knowing Python module paths has been introduced. However, a full real-world end-to-end execution involving uploaded PDF files cannot be verified due to missing `MISTRAL_API_KEY` configuration.

## 2. Bug Fixes & Stability
*   **Google Live Smoke Closure Fix**: Fixed a `RuntimeError` (`client has been closed`) causing the `google` provider validation test in `./scripts/smoke.sh` to fail by storing a persistent `genai.Client` in the `GeminiLLMClient` instance inside `app/llm_client/gemini_client.py`.
*   **Port Binding Fallback**: Modified `main()` in `app/ui/gradio_app.py` to gracefully capture `OSError` if port `7861` is already in use by a zombie/forgotten process. It now auto-increments up to port `7865` before halting.
*   **Gemini JSON Parsing Fix**: Updated the parameters on Google `live_smoke` call to `max_output_tokens: 256` to prevent the structured output from returning abruptly truncated `{"pong...` payloads causing `JSONDecodeError` while testing.

## 3. Pre-flight UX & Environment
An explicit `_run_startup_checks()` routine now executes prominently upon every Gradio application start (`./scripts/start.sh`). It checks the visibility of `MISTRAL_API_KEY`, `OPENAI_API_KEY`, and `GOOGLE_API_KEY`, logging clear diagnostic warnings if critical dependencies for OCR or configured LLMs are missing, effectively transitioning "cryptic stack traces later" into "immediate configuration feedback now".

## 4. Unified Launch Experience
To eliminate friction for testers, QA, and local researchers, a unified shell toolkit was added:
1.  **`./scripts/bootstrap.sh`**: Safely prepares a `.venv`, activates it, and installs exact dependency constraints via the lockfile.
2.  **`./scripts/start.sh`**: A single command to start the UI, auto-resolving activation paths.
3.  **`./scripts/smoke.sh`**: An instant diagnostic script to verify if local keys possess valid network connectivity.

The `docs/SETUP.md` document has been cleanly rewritten to feature this entrypoint flow.

## 5. Verification Constraints (Real E2E)
*   Seed-driven end-to-end regression testing (`p0`, `full`, `campaign`) passed flawlessly under automated Chromium evaluation (flaky tests: 0).
*   Live smoke execution (`google` and `openai`) passed `HTTP 200` validations in under `9000ms`.
*   A true document execution with new uploads was **BLOCKED** due to `MISTRAL_API_KEY` not being supplied in the local `.env`. See [iteration_24_real_e2e_execution.md](./iteration_24_real_e2e_execution.md) for details.

## 6. Resulting Artifacts
*   `docs/reports/iteration_24_bugfix_rca.md`
*   `docs/reports/iteration_24_real_e2e_execution.md`
*   `docs/reports/iteration_24_user_readiness.md` (This file)
