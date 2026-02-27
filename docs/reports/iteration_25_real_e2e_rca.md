# Iteration 25 - Real E2E RCA (Mistral Blocked)

## Issue
During the "Real E2E" execution via the Gradio Browser UI using actual documents from `fixtures/1/`, both the **OpenAI** and **Google Gemini** executions failed immediately upon clicking "Analyze".

## Stage & Error Message
*   **Stage**: Pipeline Preflight Verification (Before OCR)
*   **Status Box Message**: `Runtime preflight failed: MISTRAL_API_KEY is not configured.`
*   **Run Artifacts generated**: None (Execution was halted before a `run_id` directory was fully populated).

## Root Cause
The `backend_Kaucja` application's OCR pipeline strictly depends on the Mistral API to transcribe uploaded binary PDFs/images into Markdown context required by the LLM prompts. 

When the local environment `.env` lacks a valid `MISTRAL_API_KEY`, the application orchestrator's environment health check (`app/ui/gradio_app.py: _run_startup_checks` and backend validations) intentionally prevents the system from blindly pushing empty or corrupt context to the LLM. 

## Minimum Patch Plan
This is **not a code bug** but an expected architectural invariant (Fail-fast on missing critical secrets). 
The patch requires no code modifications, only operator action:

1. Obtain a `MISTRAL_API_KEY` from Mistral AI.
2. Insert it into the `.env` file at the root of the project.
3. Restart the UI (`./scripts/start.sh`) and re-run the real E2E Playwright wrapper (`python scripts/browser/real_e2e.py`).

No further code masking or changes are required, as the application behaved safely exactly as designed.
