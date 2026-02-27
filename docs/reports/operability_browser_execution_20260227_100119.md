# Operability Browser Execution Report

**Date of Execution:** 2026-02-27T10:01:19+01:00
**Environment:**
- Baseline Commit SHA: 47c57cbec8cc0f4ad7b962df21fe7945f7a97a7b
- Browser Mode: Playwright Chromium (Headless)

## Executive Summary
**Final GO/NO-GO:** **WORKABLE**
The backend_Kaucja Gradio application has passed all P0 and P1 browser requirements. The core scenarios for the document analysis sandbox (processing, history, comparison, and exporting) behave as expected. 

## Coverage by Cases

| Case ID | Title | Status | Notes | Artifacts / Logs |
|---------|-------|--------|-------|-----------|
| TC-P0-01 | App start & render core sections | **PASS** | App started correctly. | [P0 Logs](file:///Users/sergejavdejcik/Library/Mobile%20Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/browser/p0) |
| TC-P0-02 | History load run | **PASS** | Seeded deterministic data (e2e-run-a/b) loaded. | [P0 Logs](file:///Users/sergejavdejcik/Library/Mobile%20Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/browser/p0) |
| TC-P0-03 | Compare runs | **PASS** | Diff views and metrics generated accurately. | [P0 Logs](file:///Users/sergejavdejcik/Library/Mobile%20Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/browser/p0) |
| TC-P0-04 | Export bundle | **PASS** | Run bundle `zip` exported. | [P0 Logs](file:///Users/sergejavdejcik/Library/Mobile%20Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/browser/p0) |
| TC-P0-05 | Restore verify-only | **PASS** | Verified integrity of restored data successfully. | [P0 Logs](file:///Users/sergejavdejcik/Library/Mobile%20Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/browser/p0) |
| TC-P0-06 | Browser P0 CI-gate | **PASS** | CI script executed successfully without skips. | [Preflight Logs](file:///Users/sergejavdejcik/Library/Mobile%20Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/release_preflight) |
| TC-P1-01 | Restore strict unsigned -> Expected fail | **PASS** | Test framework confirmed validation failure. | [Full Suite Logs](file:///Users/sergejavdejcik/Library/Mobile%20Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/browser/full) |
| TC-P1-02 | Delete run confirm mismatch -> validation error | **PASS** | Validation errors trigger securely. | [Full Suite Logs](file:///Users/sergejavdejcik/Library/Mobile%20Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/browser/full) |
| TC-P1-03 | Errors for preflight/empty inputs | **PASS** | Prevented actions without configurations. | [Full Suite Logs](file:///Users/sergejavdejcik/Library/Mobile%20Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/browser/full) |
| TC-P1-04 | Campaign stability | **PASS** | 5 iterations of loop passed identically (0 flakes). | [Campaign Logs](file:///Users/sergejavdejcik/Library/Mobile%20Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/browser/campaign) |

*Note on Live Smoke*: `live_smoke` script found a networking closure API error dynamically on the `google` provider, marked fail but is optional per CI gate rules.

## What to Fix First (Top-5)
1. **Google GenAI Client Re-Use Issue**: The Google Client throws `RuntimeError: Cannot send a request, as the client has been closed` unexpectedly during `live_smoke` execution. This might indicate poor teardown handling in the backend `gemini_client.py`. (See RCA).
2. **Setup script documentation (`prepare_env.sh`)**: State explicitly that the script requires the active pip/venv (`source .venv/bin/activate`) context from Python 3.11 when downloading strict lock dependencies containing `numpy>=3.11`.
3. **Graceful App Start Failure Protection**: Ensure orphaned local Gradio processes (`7861`) do not silently crash nested e2e operations down the line. Add `lsof -ti:7861` port-clearers dynamically in pipeline setups to avoid flakes.
