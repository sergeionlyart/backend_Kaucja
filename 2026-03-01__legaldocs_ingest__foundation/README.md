# LegalDocs Ingest Iteration 1

This is the foundation for the `legal_ingest` pipeline.

## Features Supported
- **Sources**: HTTP direct fetch, SAOS judgment by ID.
- **Parsing**: PyMuPDF for PDF, BeautifulSoup4 for HTML, SAOS JSON flattening.
- **Normalize**: Virt pages and tree nodes mapping according to `TechSpec_LegalDocs_Ingest_Pipeline.md`.
- **Database**: MongoDB idempotent storage with strict schema tracking (Pydantic).

## How to run
1. Ensure Docker is running and start the MongoDB test DB:
   ```bash
   docker compose up -d
   ```
2. Create and populate the environment configuration (`.env`):
   ```bash
   cp .env.example .env
   # Add your MISTRAL_API_KEY and adjust MONGO_* values inside .env
   ```
3. Execute the full pipeline orchestrator script:
   ```bash
   # Executes configs mapping automatically 
   ./scripts/run_ingest.sh configs/config.runtime.yml
   ```
   **Alternative (Production / Strict Mode):**
   ```bash
   python -m legal_ingest.cli --env-file .env ingest --config configs/config.full.runtime.yml --strict-ok
   ```
   `--strict-ok` exits with code `1` if at least one document is `RESTRICTED` or `ERROR`.

## Troubleshooting
- **Missing Env Variable**: Pydantic validations will actively reject pipelines executing without mapped strings (e.g. `MONGO_URI` missing throws ValueError).
- **RESTRICTED Output**: Pages with paywall markers/login prompts or low extracted content are marked as `RESTRICTED` (including commercial sources). If `--strict-ok` is enabled, the command will fail.
- **Commercial Sources**: If LEX session cookie is unavailable/invalid, commercial pages may remain `RESTRICTED`. Configure `LEX_SESSION_ID` in `.env` only with a valid session.
