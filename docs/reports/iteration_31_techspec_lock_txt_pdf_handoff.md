# Iteration 31: TechSpec Lock & TXT -> PDF OCR Handoff

## Overview
This iteration closes the two remaining operational risks identified during pre-release validation:
1.  **Strict TechSpec Governance**: A runtime lock that guarantees the system prompt and extraction schemas strictly match the canonical formats defined in `TECH_SPEC_Prompt.md` and `TECH_SPEC_MVP.md`.
2.  **TXT Processing via OCR**: Fixed the `FILE_UNSUPPORTED` error when processing plain text files using the Mistral OCR model by automatically converting to PDF before passing to the AI engine.

## Changes Implemented

### 1. `TXT` to `PDF` OCR Interception
- The OCR processing pipeline in `MistralOCRClient` now includes an interception step. If a `.txt` file is received, it triggers `convert_txt_to_pdf` seamlessly.
- Metrics logging in the orchestrator captures this execution explicitly as `TXT pre-processed to PDF (size: X -> Y)`.
- Introduced a specific exception `TXTPDFConversionError` so that conversion failures correctly abort the document generation without silently ignoring bad states.

### 2. Runtime TechSpec Lock
- Updated the pipeline orchestrator schema loader to validate that any `prompt_version` requested executes byte-for-byte against the system canonical schema source.
- This creates an irreversible assurance that the orchestrator is never allowed to execute instructions or map output keys differently than governed by the Technical Specs.
- If a drift is identified or the requested version differs from the accepted canonical baseline, the engine throws a fatal `ValueError` blocking the run immediately.
- Refactored `test_techspec_drift.py` so the tests extract schema content securely without brittle regex heuristics, instead doing block slicing directly.

### 3. Comprehensive Automation Checks
- Integration tests (`tests/integration/test_txt_regression_pipeline.py`) added simulating end-to-end OCR processing with `.txt` payload constraints successfully.
- Code formatted with `ruff format .` & `ruff check .` with all linting debt resolved.
- Pytest full suite is 100% green (`140 passed in 3.17s`).

## Commit Checklists
- [x] Codebase formatting cleanup complete
- [x] Tests are passing
- [x] Integration Regression is active
- [x] TechSpec prompt lock active 

### Next Steps 
The codebase is technically ready to merge PR. No missing steps or regressions found.
