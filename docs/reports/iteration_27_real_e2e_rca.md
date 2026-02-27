# Iteration 27 - Real E2E RCA (LLM API Blocks)

## Issue
During Iteration 27, after successfully applying the `MISTRAL_API_KEY` to the runtime (unblocking OCR), the E2E verification still failed for both targeted LLM providers with `LLM_API_ERROR`.

## Analysis

### 1. OpenAI (Strict Mode JSON Schema parsing rejected)
OpenAI's Structured Outputs mechanism enforces a subset of JSON schema (Strict Mode). The API returned:
`Invalid schema for response_format [...] Extra required key 'parties' supplied.`

**Root Cause:**
*   Our original schema used dynamic mapped objects bounded using `additionalProperties: { "$ref": "#/$defs/fact" }` for `parties`, `key_dates`, and `money`. 
*   OpenAI's Schema Strict Mode rejects arbitrary Maps dynamically and enforces `additionalProperties: false` algorithmically. As a result, the properties did not register cleanly, failing the `required` array definition check.

**Resolution:**
The definitions for `parties`, `key_dates`, and `money` inside `app/prompts/kaucja_gap_analysis/v001/schema.json` were refactored from "Map of Facts" `{ "tenant": Fact }` to "Array of named facts" `[{ "role": "tenant", "fact": Fact }]`. The mock objects in `tests/` were identically aligned, returning 100% test pass rates downstream.

### 2. Google Gemini (Model Parameter 404 Error)
Google's API generated a 404 Error:
`models/gemini-3.1-flash-preview is not found for API version v1beta`

**Root Cause:**
*   The system configs (`app/config/providers.yaml` and `pricing.yaml`) contained placeholder strings for future generative model versions (`gemini-3.1-flash-preview`). Given that `real_e2e.py` specifically selected this dropdown, the backend sent a mocked non-existent model to the production endpoint, which 404'd securely.

**Resolution:**
Introduced and integrated `gemini-2.5-flash` natively into the backend configuration specs, and configured the E2E framework to specifically request this valid semantic model variant.
