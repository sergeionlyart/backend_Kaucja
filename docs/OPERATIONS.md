# Operations Guide

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m app.ui.gradio_app
```

Optional quality gate before commit:

```bash
ruff format .
ruff check .
pytest -q
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```

## Artifacts and Logs

Runtime artifacts are stored under:

- `data/sessions/<session_id>/runs/<run_id>/run.json`
- `data/sessions/<session_id>/runs/<run_id>/logs/run.log`
- `data/sessions/<session_id>/runs/<run_id>/documents/<doc_id>/...`
- `data/sessions/<session_id>/runs/<run_id>/llm/...`

SQLite metadata default path:

- `data/kaucja.sqlite3` (or value from environment/config)

## Sensitive Data Policy

Uploaded files and OCR/LLM artifacts may include sensitive identifiers (for example PESEL, IBAN, IDs).

Policy:

- keep `data/` local for MVP;
- do not commit artifacts, DB files, `.env`, or real user documents;
- share ZIP exports only with authorized recipients;
- remove old runs manually when no longer needed.

## Export Run Bundle (ZIP)

From UI History:

1. Select/load a `run_id` in History section.
2. Click `Export run bundle (zip)`.
3. UI shows export status, generated path, and downloadable file.

Current behavior:

- ZIP source is selected run `artifacts_root_path`.
- Output path: sibling of run folder, `<run_id>_bundle.zip`.
- ZIP keeps relative structure from run root (e.g. `run.json`, `logs/`, `documents/`, `llm/`).
- Export uses deterministic file ordering and fixed ZIP timestamps.

## Export Limitations

- Export fails when artifacts root is missing or empty.
- Export rejects symlinked paths inside run artifacts (path traversal protection).
- ZIP generation is local filesystem operation; large runs may take noticeable time.
