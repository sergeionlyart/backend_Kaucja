# Iteration 28 - Go-Live Hardening

## Overview

Iteration 28 focused on preparing the Legal Copilot UN / Kaucja extraction backend for real-world user operations. The overarching objective was to eliminate any "lab environment" quirks and create a stable, reliable pipeline that can seamlessly ingest, process, and output real document extractions using real APIs without brittle configurations.

## Achievements

### 1. Hardened Live Smoke Probes (`app/ops/live_smoke.py`)
- Removed simple sequential execution inside LLM and OCR probes.
- Added `@retry` robust handling via `tenacity` library to automatically retry on transient network errors (Connection errors, HTTP 429, HTTP 500-504, Timeout).
- Modified the JSON report output to now track execution `attempts` to allow operational visibility into provider degradation.
- Raised default `LIVE_SMOKE_PROVIDER_TIMEOUT_SECONDS` from 30 seconds to 60 seconds to ensure high-latency, un-cached cold boot requests from Gemini/Mistral don't automatically trigger false-positive outages.

### 2. Parameterized the Real E2E tool (`scripts/browser/real_e2e.py`)
- Replaced hard-coded file paths and Gradio ports.
- Switched to an `argparse` driven CLI tool capable of passing standard Playwright test runs dynamically.
- Migrated terminal stdout prints to output a deterministic JSON block recording the latency, final `status`, and `run_id` for inspection.

### 3. Master GO-LIVE CI Target (`scripts/run_go_live_check.sh`)
- Authored a fully encompassing bash verification script `run_go_live_check.sh`.
- Programmed it to automatically spin up a headless internal `gradio_app` via background processing, verify API key presence without leaking secrets, and invoke both `live_smoke` and `real_e2e`.
- Further enhanced the E2E verification to explicitly ensure the generation of expected system artifacts (`run.json`, `run.log`, `combined.md`, `validation.json`) on the file system tied to the specific Playwright `run_id` output.

### 4. Fully Covered Unit & Integration Testing
- Wrote proper tests isolating the `_AttemptTracker` logic and validating that the expected exceptions (`LLMAPIError`, `TimeoutError`) are flagged as transient correctly.
- Added a dry-run integrity test for `run_go_live_check.sh` ensuring it successfully halts when dependencies are unfulfilled.

### 5. Perfect Quality Gates execution
- Formatted gracefully (`ruff format .` / `ruff check . --fix`) and eliminated duplicate `LLMAPIError` dependencies.
- Passed 134 `pytest` units natively.
- Clean execution of `./scripts/run_preflight.sh` which encapsulates Browser UI Smoke/Execution tests for both `p0` and `full`.

## Verdict
**GO 🟢**

The codebase now seamlessly supports automated environment deployment, reliable recovery from network hiccups, and an end-to-end mechanism to confirm infrastructure viability locally without developer friction.
