# Iteration 2 OCR Stage Report

## Summary
Implemented Iteration 2 (Mistral OCR + OCR artifacts + OCR stage pipeline) according to TechSpec sections 5.1, 6.1, 12.1/12.2.

Done:
- Added OCR client modules:
  - `app/ocr_client/types.py`
  - `app/ocr_client/quality.py`
  - `app/ocr_client/mistral_ocr.py`
- Extended artifacts layout to include:
  - `documents/<doc_id>/original/`
  - `documents/<doc_id>/ocr/{raw_response.json,combined.md,pages,tables,images,page_renders,quality.json}`
  - `logs/run.log`
- Extended storage repo with `documents` CRUD:
  - create document row with `pending`
  - update OCR status (`pending|ok|failed`) with pages/path/error
  - read/list documents by run
- Implemented OCR-only pipeline stage in `app/pipeline/orchestrator.py`:
  - deterministic `doc_id` sequence (`0000001...`)
  - save original files into run artifacts
  - run OCR per document and persist artifacts + DB updates
  - finalize run status to `completed`/`failed`
- Updated Gradio UI for Iteration 2:
  - multi-file upload
  - OCR settings (model, table format, include images)
  - Analyze triggers OCR stage and renders table: `doc_id`, `ocr_status`, `pages_count`, `combined_md_path`
- Added test coverage:
  - OCR client parsing and artifact save with mocked Mistral response
  - integration test for OCR pipeline (DB + filesystem)
  - updated UI smoke callback test
  - updated artifacts/storage tests for new document-level behavior

## Branch / Git
- Baseline commit created before Iteration 2:
  - `feat: complete iteration 1 storage artifacts baseline`
- Working branch:
  - `codex/iteration-2-ocr`

## Commands Run
```bash
python -m pip install -e '.[dev]'
ruff format .
ruff check .
pytest -q
python -m app.ui.gradio_app
```

Key outputs:
- `ruff format .` -> `28 files left unchanged`
- `ruff check .` -> `All checks passed!`
- `pytest -q` -> `15 passed in 3.45s`
- `python -m app.ui.gradio_app` -> `gradio_app_started`

## Demo OCR Artifacts (created via mocked OCR service)
- Session: `c8d46583-e1ee-47e4-817a-b8300b8c883f`
- Run: `469dd336-c644-49c2-ae80-042aa5f653eb`
- Run root:
  - `data/sessions/c8d46583-e1ee-47e4-817a-b8300b8c883f/runs/469dd336-c644-49c2-ae80-042aa5f653eb`
- Document artifacts examples:
  - `data/sessions/c8d46583-e1ee-47e4-817a-b8300b8c883f/runs/469dd336-c644-49c2-ae80-042aa5f653eb/documents/0000001/ocr/combined.md`
  - `data/sessions/c8d46583-e1ee-47e4-817a-b8300b8c883f/runs/469dd336-c644-49c2-ae80-042aa5f653eb/documents/0000001/ocr/raw_response.json`
  - `data/sessions/c8d46583-e1ee-47e4-817a-b8300b8c883f/runs/469dd336-c644-49c2-ae80-042aa5f653eb/logs/run.log`

## Risks / Notes
- `pip` reported global-environment conflicts (`huggingface-hub` with existing `transformers/tokenizers`).
- Recommended execution path remains isolated virtualenv from `docs/SETUP.md`.
