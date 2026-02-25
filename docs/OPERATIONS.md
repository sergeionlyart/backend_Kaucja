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

## Restore Run from ZIP

### Restore from CLI

Basic command:

```bash
python -m app.storage.restore \
  --zip-path data/sessions/<session_id>/runs/<run_id>_bundle.zip \
  --db-path data/kaucja.sqlite3 \
  --data-dir data
```

Overwrite existing run:

```bash
python -m app.storage.restore \
  --zip-path data/sessions/<session_id>/runs/<run_id>_bundle.zip \
  --db-path data/kaucja.sqlite3 \
  --data-dir data \
  --overwrite-existing
```

Disable rollback on metadata failure:

```bash
python -m app.storage.restore \
  --zip-path data/sessions/<session_id>/runs/<run_id>_bundle.zip \
  --db-path data/kaucja.sqlite3 \
  --data-dir data \
  --no-rollback-on-metadata-failure
```

Output:

- JSON report with `status`, `run_id`, `session_id`, `restored_paths`, `warnings`, `errors`, `error_code`, `error_message`, `manifest_verification_status`, `files_checked`, `rollback_attempted`, `rollback_succeeded`.

Safety checks:

- archive entry names must be relative (no absolute paths, no `..`);
- symlink entries in ZIP are rejected;
- archive must include `run.json` and at least one layout root (`logs/`, `documents/`, `llm/`).
- if `bundle_manifest.json` exists, restore validates `size_bytes` and `sha256` for each listed file before extracting;
- if `bundle_manifest.json` is missing (legacy archive), restore continues with warning;
- anti-zip-bomb limits are enforced (`max_entries`, `max_total_uncompressed_bytes`, `max_single_file_bytes`, `max_compression_ratio`);
- by default, when file copy succeeds but metadata restore fails, restore attempts rollback (delete restored run tree).

Error codes:

- `RESTORE_INVALID_ARCHIVE`
- `RESTORE_RUN_EXISTS`
- `RESTORE_FS_ERROR`
- `RESTORE_DB_ERROR`

### Restore from UI

In History section:

1. Upload ZIP in `Restore ZIP File`.
2. Optional: enable `Overwrite existing run`.
3. Click `Restore run bundle`.

UI shows:

- restore status,
- technical details (manifest verification, files checked, rollback status, error code/message),
- restored `run_id`,
- restored artifacts root path.

After success, history table and compare dropdowns are refreshed automatically.

## Delete Run / Retention

### Delete single run from UI

In History section:

1. Enter target `run_id` in `Run ID to load`.
2. Type the same value in `Confirm Run ID for Delete`.
3. Optional: enable `Create backup ZIP before delete`.
4. Click `Delete run`.

Behavior:

- On success: SQLite metadata is removed and run artifacts folder is deleted.
- If backup option is enabled: backup ZIP is created first; delete starts only after successful backup.
- On failure: UI shows status and technical details (`error_code/error_message/details`).
- UI also shows backup ZIP path when backup is enabled and succeeds.
- History table and compare dropdowns are refreshed after delete attempt.

Safety controls:

- run artifacts path must resolve under configured `data/` root;
- expected layout `sessions/<session_id>/runs/<run_id>` is enforced;
- symlinked paths are rejected during delete traversal.

### Manual retention cleanup (older than N days)

Command:

```bash
python -m app.storage.retention --days 30 --db-path data/kaucja.sqlite3 --data-dir data
```

Dry-run (no deletion, only candidates + report):

```bash
python -m app.storage.retention --days 30 --dry-run --db-path data/kaucja.sqlite3 --data-dir data
```

Backup-before-delete with custom backup and report locations:

```bash
python -m app.storage.retention \
  --days 30 \
  --export-before-delete \
  --export-dir data/backups \
  --report-dir data/retention_reports \
  --db-path data/kaucja.sqlite3 \
  --data-dir data
```

Notes:

- cleanup is best-effort: continues even if some runs fail to delete;
- output is JSON report with per-run audit entries (`run_id`, `action`, `status`, `error`, `backup_zip_path`);
- report is always persisted by default in `data/retention_reports/<timestamp>.json` unless overridden by `--report-path` or `--report-dir`;
- no background scheduler in MVP, only manual invocation.
