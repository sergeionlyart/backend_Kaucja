# RCA: Google GenAI Client Closed Connection Error (Live Smoke)

## 1. Problem Description
**Feature/Action:** `google` provider ping in `live_smoke`
**Reproduction Step:** Running `./scripts/release/run_preflight.sh` which delegates to `python -m app.ops.live_smoke` calling Google LLM API.
**Actual UI/Log error:** `RuntimeError: Cannot send a request, as the client has been closed.`
**Severity:** Medium (Only impacts live smoke gate and concurrent generation checks, does not fail the browser application state or schema verifications).

## 2. Technical Causes
**Probable Cause:** The `google-genai` Python library's asynchronous networking context (likely `httpx.AsyncClient`) was instantiated inside a singleton or dynamically reused async loop that closed at the end of a previous task snippet. When the `live_smoke` script pings it subsequently or concurrently, it tries to invoke `generate_content` over the already closed `AsyncClient` socket object. 

## 3. Minimal Fix Plan
1. Refactor `app/llm_client/gemini_client.py`: Wrap the API client instantiation in a dependency injection context or instantiate a fresh `google.genai.Client` per generator call rather than maintaining a global singleton.
2. In `app.ops.live_smoke`, ensure asyncio context managers properly await completions without terminating shared underlying event loops during fan-out tasks.
3. Add a retry wrapper around `google` smoke triggers mapping to closed connections to re-instantiate the client natively.
