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
2. Create environment variables (Optional, for mistral OCR later):
   ```bash
   export MISTRAL_API_KEY="test"
   ```
3. Initialize the database indexes:
   ```bash
   python -m legal_ingest ensure-indexes --config configs/config.sample.yml
   ```
4. Run sample ingest:
   ```bash
   python -m legal_ingest ingest --config configs/config.sample.yml
   ```
