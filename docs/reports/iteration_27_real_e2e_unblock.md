# Iteration 27 - Real E2E Unblock & Final Operations Report

**Date:** 2026-02-27T13:45:00+01:00  
**Branch:** `codex/iteration-27-real-e2e-unblock`  
**Status / Verdict:** **WORKABLE** (Pipeline verified end-to-end against multiple Real LLM inference engines and Real Mistral OCR algorithms).

## 1. Executive Summary
The primary goal of Iteration 27 was to unblock the external capability constraints identified in Iteration 26 (Missing OCR key) and to achieve an undeniably verifiable End-to-End run of the intelligence pipeline using actual user-provided PDF files from `fixtures/1/Faktura PGE.pdf`.  
This objective was accomplished successfully. The backend systems cleanly orchestrated physical uploads through the browser UI to the inference APIs, generated valid factual outputs under zero-shot deterministic modes, passed rigorous quality gates securely, and archived everything on local disks.

## 2. Environments and Technical Modifications
**Key Resolutions Implemented:**
1.  **Environment Determinism:** Modified `app.config.settings.py` forcing the framework to load `.env` from the project's root node dynamically, irrespective of entry execution context. Additionally registered `OCR_API_KEY` as a valid validation alias mapping for the Mistral configurations.
2.  **OpenAI Schema Normalization:** Upgraded the `schema.json` format definitions. Converted dynamic key dictionaries `parties`, `key_dates`, and `money` into arrays with `name`/`role` string schemas as OpenAI's Strict Structure Output explicitly prohibits dynamic dictionary keys map resolutions.
3.  **Google Payload Normalization:** Registered actual production models (`gemini-2.5-flash`) inside the application architectures (`providers.yaml` and `pricing.yaml`) to replace future structural mock names (`gemini-3.1-flash-preview`), avoiding persistent `404 NOT FOUND` errors when calling inference endpoints.

## 3. Real E2E Operations Run Proofs
Test scripts ran via the automated Playwright Browser Engine executing headless simulated user inputs to process `Faktura PGE.pdf`.

| Provider | Playwright Result | UI Status Box | Run ID Generated | Wait Duration |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAI** (`gpt-5.1` fallback mapped) | Completed | `Run finished. status=completed` | `c760257f-1518-4541-ad03-8417deb64259` | ~25s |
| **Google Gemini** (`gemini-2.5-flash`) | Completed | `Run finished. status=completed` | `d6a27161-7f65-48e1-b86d-8028ef0e4ba7` | ~23s |

## 4. Quality Engineering Gates
*   **[PASS]** `ruff format .`
*   **[PASS]** `ruff check .`
*   **[PASS]** `pytest -q` (131 tests passed post-schema-update refactor)
*   **[PASS]** `run_regression.sh --suite p0`
*   **[PASS]** `run_regression.sh --suite full`
*   **[PASS]** `run_preflight.sh`

## 5. Artifact Index Generation
*   `docs/reports/iteration_27_real_e2e_rca.md` (Analyzed why API calls failed downstream initially after applying the OCR key patch).
*   Mock Data fixtures in Python tests correctly re-written to target new OpenAI structural demands safely securing zero test regressions.
