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

## Browser E2E Smoke (No External APIs)

Prepare local browser test environment:

```bash
./scripts/browser/prepare_env.sh
```

Seed deterministic local history/artifacts:

```bash
./scripts/browser/seed_data.sh
```

Start app in browser e2e mode:

```bash
./scripts/browser/start_e2e_app.sh
```

Run browser smoke (seed + start + test in one command):

```bash
./scripts/browser/run_smoke.sh
```

Reference guide: `docs/BROWSER_TESTS.md`.

## Live E2E Verification (Requires External APIs)

To execute a real browser-driven End-to-End test that uploads a fixture document and runs the full OCR + LLM pipeline against both OpenAI and Google Gemini providers:

1. Ensure `MISTRAL_API_KEY`, `OPENAI_API_KEY`, and `GOOGLE_API_KEY` are valid in `.env`.
2. Start the Gradio app in the background (`./scripts/start.sh`).
3. Run the automated Playwright verifier:

```bash
source .venv/bin/activate
python scripts/browser/real_e2e.py \
    --base-url "http://127.0.0.1:7860" \
    --file-path "fixtures/1/Faktura PGE.pdf" \
    --providers "openai,google" \
    --timeout-seconds 120 \
    --output-report "artifacts/e2e_report.json"
```

## Live Provider Smoke

Run local operational diagnostics for provider contracts:

```bash
python -m app.ops.live_smoke --output data/live_smoke_report.json
```

Run with explicit readiness policy and timeout:

```bash
python -m app.ops.live_smoke \
  --required-providers openai,google,mistral_ocr \
  --provider-timeout-seconds 30 \
  --strict \
  --output data/live_smoke_report.json
```

Report format is machine-readable JSON with:

- `started_at`, `finished_at`, `overall_status`
- `required_providers`, `required_failures`, `required_skipped`
- `providers[]` entries:
  - `name`
  - `status` (`pass|fail|skipped`)
  - `latency_ms`
  - `error_code`
  - `error_message`

Status interpretation:

- `pass`: provider call succeeded under project contract.
- `fail`: provider call failed (taxonomy-aligned `error_code` where applicable).
- `skipped`: diagnostic intentionally not executed (for example missing API key/SDK).

Operational live-smoke codes:

- `LIVE_SMOKE_TIMEOUT`
- `LIVE_SMOKE_MISSING_API_KEY`
- `LIVE_SMOKE_SDK_NOT_INSTALLED`

Operational actions:

- `overall_status=pass`:
  - all required providers passed;
  - non-required providers may be skipped in non-strict mode.
- `overall_status=fail`:
  - inspect `providers[].error_code/error_message`;
  - inspect `required_failures/required_skipped` policy fields;
  - check API key configuration and provider status;
  - re-run smoke with explicit required providers and timeout after remediation.

CI live-smoke workflow:

- Workflow file: `.github/workflows/live-smoke.yml`
- Triggers:
  - `workflow_dispatch` (strict + required providers + timeout inputs),
  - weekly schedule.
- Report artifact: `live-smoke-report` (`artifacts/live_smoke_report.json`).
- Main PR CI remains unchanged (`.github/workflows/ci.yml`).

Restore limits and signing are configurable via `.env`:

- `RESTORE_MAX_ENTRIES`
- `RESTORE_MAX_TOTAL_UNCOMPRESSED_BYTES`
- `RESTORE_MAX_SINGLE_FILE_BYTES`
- `RESTORE_MAX_COMPRESSION_RATIO`
- `RESTORE_REQUIRE_SIGNATURE`
- `BUNDLE_SIGNING_KEY`
- `LIVE_SMOKE_REQUIRED_PROVIDERS`
- `LIVE_SMOKE_PROVIDER_TIMEOUT_SECONDS`
- `KAUCJA_E2E_MODE`

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
- Export writes deterministic `bundle_manifest.json` with file checksums/sizes.
- If `BUNDLE_SIGNING_KEY` is configured, manifest includes HMAC-SHA256 signature.

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

Verification-only mode (no writes to filesystem/SQLite):

```bash
python -m app.storage.restore \
  --zip-path data/sessions/<session_id>/runs/<run_id>_bundle.zip \
  --db-path data/kaucja.sqlite3 \
  --data-dir data \
  --verify-only
```

Enable strict signature requirement:

```bash
python -m app.storage.restore \
  --zip-path data/sessions/<session_id>/runs/<run_id>_bundle.zip \
  --db-path data/kaucja.sqlite3 \
  --data-dir data \
  --require-signature
```

Output:

- JSON report with `status`, `run_id`, `session_id`, `restored_paths`, `warnings`, `errors`, `error_code`, `error_message`, `manifest_verification_status`, `files_checked`, `signature_verification_status`, `archive_signed`, `signature_required`, `verify_only`, `rollback_attempted`, `rollback_succeeded`.

Safety checks:

- archive entry names must be relative (no absolute paths, no `..`);
- symlink entries in ZIP are rejected;
- archive must include `run.json` and at least one layout root (`logs/`, `documents/`, `llm/`).
- if `bundle_manifest.json` exists, restore validates `size_bytes` and `sha256` for each listed file before extracting;
- if manifest signature exists and `BUNDLE_SIGNING_KEY` is configured, restore verifies HMAC-SHA256 signature;
- strict mode (`RESTORE_REQUIRE_SIGNATURE=true` or `--require-signature`) rejects unsigned/unverifiable bundles;
- if `bundle_manifest.json` is missing (legacy archive), restore continues with warning;
- anti-zip-bomb limits are enforced (`max_entries`, `max_total_uncompressed_bytes`, `max_single_file_bytes`, `max_compression_ratio`);
- by default, when file copy succeeds but metadata restore fails, restore attempts rollback (delete restored run tree).

Error codes:

- `RESTORE_INVALID_ARCHIVE`
- `RESTORE_INVALID_SIGNATURE`
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
- technical details (manifest verification, signature verification, signed/unsigned state, strict mode, verify-only state, rollback status, error code/message),
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
