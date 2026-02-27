# Iteration 24 - Bug Fix RCA: Live Smoke & Port Conflicts

## 1. Google GenAI `live_smoke` Connection Closure

**Problem:** 
During the execution of `./scripts/release/run_preflight.sh` (specifically the `live_smoke` stage), the Google Gemini provider consistently failed with `RuntimeError: Cannot send a request, as the client has been closed.`

**Root Cause:**
In `app/llm_client/gemini_client.py`, the `_resolve_service` method instantiated the `google.genai.Client` locally within the function and promptly returned only the `client.models` property:  
```python
client = genai.Client(api_key=self._api_key)
self._generate_service = client.models
return self._generate_service
```
As soon as the function returned, the local `client` object went out of scope and was garbage collected. The `google.genai.Client` manages an underlying async networking pool, which automatically closes active connections upon garbage collection. Consequently, any subsequent calls via `self._generate_service.generate_content(...)` attempted to push data through a destroyed socket, raising the `RuntimeError`.

**Resolution:**
The fix involves maintaining a persistent reference to the `genai.Client` within the `GeminiLLMClient` instance.
```python
client = getattr(self, "_genai_client", None)
if client is None:
    client = genai.Client(api_key=self._api_key)
    self._genai_client = client

self._generate_service = client.models
return self._generate_service
```
This ensures the client (and its underlying HTTP connection pool) remains active for the lifespan of the `GeminiLLMClient`.

---

## 2. Gradio App Port 7861 Conflicts

**Problem:**
When running the automated E2E test suites (or when a user aborts the app ungracefully), the Gradio web server occupying port `7861` could be left orphaned in the background. Subsequent attempts to run `python -m app.ui.gradio_app` or scripts like `./scripts/start.sh` would instantly crash with `OSError: Cannot find empty port in range: 7861-7861` or `Address already in use`.

**Root Cause:**
By default, the `gradio_server_port` setting strictly bound the app to exactly `7861`. If the port was occupied, the `app.launch()` method threw a fatal exception without attempting to find another open port, halting the entire startup process.

**Resolution:**
In `app/ui/gradio_app.py`, the `main()` function was refactored to implement a graceful fallback loop testing ports sequentially from `target_port` up to `target_port + 5`.
```python
target_port = settings.gradio_server_port
max_port = target_port + 5

for port in range(target_port, max_port + 1):
    try:
        app.launch(server_name=settings.gradio_server_name, server_port=port)
        return
    except OSError as e:
        if "Cannot find empty port" in str(e) or "Address already in use" in str(e):
            print(f"[!] Port {port} is occupied. Trying next...")
        else:
            raise
```
Additionally, an `_run_startup_checks()` function was added to explicitly check for missing API keys (`.env`) and warn the user pre-launch, fulfilling UX and stability criteria.
