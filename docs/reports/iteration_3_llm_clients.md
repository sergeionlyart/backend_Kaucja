# Iteration 3 LLM Clients + Iteration 2 Hardening Report

## Summary
Implemented requested scope in two parts.

### Part A: OCR hardening
- Added uniqueness invariant for documents per run:
  - `UNIQUE(run_id, doc_id)` in table definition.
  - `CREATE UNIQUE INDEX IF NOT EXISTS ux_documents_run_doc_id ON documents (run_id, doc_id)`.
- Fixed `table_format=none` behavior:
  - OCR request does not send `table_format`.
  - no table files are generated.
- Updated Mistral local-file request flow to SDK contract:
  - upload local file with `files.upload(..., purpose="ocr")`
  - pass uploaded id to OCR with `document={"type":"file","file_id":...}`.
- Added tests covering A1/A2/A3.

### Part B: Iteration 3 LLM layer
Implemented:
- `app/llm_client/base.py`
- `app/llm_client/openai_client.py`
- `app/llm_client/gemini_client.py`
- `app/llm_client/normalize_usage.py`
- `app/llm_client/cost.py`
- `app/pipeline/pack_documents.py`
- `app/pipeline/validate_output.py`

Details:
- OpenAI client uses Responses API payload with:
  - `text.format.type=json_schema`
  - `strict=true`
  - `tools=[]` and `tool_choice="none"`
  - `reasoning.effort` sent only for `low|medium|high` (`auto` omitted).
- Gemini client uses payload with:
  - `response_mime_type=application/json`
  - `response_json_schema`
  - `system_instruction`
  - thinking level mapping (`auto` omitted).
- Usage normalization for OpenAI/Gemini into unified UI shape.
- Cost calculation from `app/config/pricing.yaml`.
- Validation layer:
  - JSON Schema validation.
  - semantic invariants (22 checklist items, unique item_id, confirmed/missing rules, max 10 questions).
- Document packer preserves placeholders and strict wrapper format:
  - `<BEGIN_DOCUMENTS> ... <END_DOCUMENTS>`.

## Git pre-steps done
- Iteration 2 committed separately:
  - `f6d9ce3 feat: implement iteration 2 ocr stage`
- Current working branch:
  - `codex/iteration-3-llm`

## Commands Run
```bash
ruff format .
ruff check .
pytest -q
```

Outputs:
- `ruff format .` -> `41 files left unchanged`
- `ruff check .` -> `All checks passed!`
- `pytest -q` -> `35 passed in 2.55s`

## Test Coverage Added
- OCR hardening:
  - uniqueness invariant (`documents(run_id, doc_id)`)
  - `table_format=none` no table-files
  - Mistral SDK local-file contract (`files.upload` + `document.type=file`)
- LLM:
  - OpenAI payload builder + generate flow (mocked)
  - Gemini payload builder + generate flow (mocked)
  - usage normalization + cost
  - pack documents format preservation
  - validate output invariants and failure cases
  - integration: `pack -> llm mock -> validate`

## Risks / Notes
- SDK payload builders are covered by unit tests; runtime API compatibility still depends on provider SDK versions.
- Existing global Python environment may show unrelated dependency conflicts; project checks pass in current environment.
