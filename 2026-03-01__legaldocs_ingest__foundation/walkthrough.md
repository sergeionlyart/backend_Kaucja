# LegalDocs Ingest Pipeline: Iteration 1 Report

## Summary
Successfully implemented the Iteration 1 foundation for the `legal_ingest` pipeline. The CLI is fully operational with commands to validate configuration, ensure MongoDB indexes, perform dry-runs, and ingest documents. We built an idempotent pipeline mapping HTTP `direct` and SAOS API sources to a common `Document`, `Page`, and `Node` database schema via `pymongo` bulk operations. Parsing covers PDF text extraction, virtual HTML chunks, and SAOS JSON flattening. 

## Files Changed
- `2026-03-01__legaldocs_ingest__foundation/README.md`
- `2026-03-01__legaldocs_ingest__foundation/docker-compose.yml`
- `2026-03-01__legaldocs_ingest__foundation/requirements.txt`
- `2026-03-01__legaldocs_ingest__foundation/pyproject.toml`
- `2026-03-01__legaldocs_ingest__foundation/.gitignore`
- `2026-03-01__legaldocs_ingest__foundation/configs/config.sample.yml`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/__main__.py`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/cli.py`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/config.py`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/ids.py`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/logging.py`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/fetch.py`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/pipeline.py`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/store/mongo.py`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/store/models.py`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/parsers/pdf.py`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/parsers/html.py`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/parsers/saos.py`
- `2026-03-01__legaldocs_ingest__foundation/legal_ingest/parsers/tree.py`
- `2026-03-01__legaldocs_ingest__foundation/tests/unit/test_config.py`
- `2026-03-01__legaldocs_ingest__foundation/tests/unit/test_ids.py`
- `2026-03-01__legaldocs_ingest__foundation/tests/unit/test_parsers.py`
- `2026-03-01__legaldocs_ingest__foundation/tests/integration/test_mongo_upsert.py`
- `2026-03-01__legaldocs_ingest__foundation/tests/integration/test_idempotency.py`

## Commands Run & Key Outputs

1. **Format and Linting**
   ```bash
   ruff format . && ruff check .
   ```
   *Result: All clear after minor fixes.*

2. **Integration Tests**
   ```bash
   pytest -q
   ```
   *Result: `tests/integration/test_idempotency.py` ensures doc/page/node counts do not grow upon idempotent upserts of the identical payloads.*

3. **Ingest Verification Commands**
   ```bash
   python -m legal_ingest validate-config --config configs/config.sample.yml
   python -m legal_ingest ensure-indexes --config configs/config.sample.yml
   python -m legal_ingest dry-run --config configs/config.sample.yml --limit 2
   python -m legal_ingest ingest --config configs/config.sample.yml
   ```
   *Result: Configuration parsed properly. Pipeline executed perfectly yielding 4 `OK` documents and 1 `RESTRICTED` (commercial proxy).*

## MongoDB Verification

Current counts on the local `mongo` database after two passes (proving idempotency on docs/pages/nodes via UPSERT logic):
- **`documents`**: 5
- **`document_sources`**: 8 (Multiple fetch executions on same documents stored as history)
- **`pages`**: 24
- **`nodes`**: 76
- **`ingest_runs`**: 2

**Sample Document:**
```json
{
  "doc_uid": "eli_pl:DU/2001/733",
  "current_source_hash": "01bfc26482f1b6b69fdc177a8c9c023d729ff1964053e45d29949bef94e2e76c",
  "page_count": 9
}
```

## Artifacts Paths

Run Level Artifacts (from Run ID `3aa27c4d41304481abf1b0be66b279dd`):
- **Run Report**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts/runs/3aa27c4d41304481abf1b0be66b279dd/run_report.json`
- **Logs JSONL**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts/runs/3aa27c4d41304481abf1b0be66b279dd/logs.jsonl`

Source Document Level Artifacts (Sample: `pl_lex_kc_art_118`):
- **Raw Document**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts/docs/lex_pl:urlsha:c31ee8071848130d/raw/4f9c170bb8362fb53828d0382fd1db653e9f5dcc82a27d0ef5b375460e1be64f/original.bin`
- **Normalized Pages**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts/docs/lex_pl:urlsha:c31ee8071848130d/normalized/4f9c170bb8362fb53828d0382fd1db653e9f5dcc82a27d0ef5b375460e1be64f/pages.jsonl`

## Deferred Items for Iteration 2
The following items were expressly deferred:
1. Mistral OCR pipeline fallback capabilities via `mistral-ocr-2512`.
2. SAOS `saos_search` fetch strategy (paginating over judgment lists).
3. The `citations` metadata extraction matching models for document relationships.

## Git Info
- **Commit Hash(es)**: (To be added once committed)
- **PR Link**: (To be added once PR is open)
