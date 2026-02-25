# Iteration 14: Backup Authenticity + Configurable Restore Limits + Verify-Only

## Scope
- Add configurable restore safety limits via ENV/settings.
- Add optional bundle authenticity signature (HMAC-SHA256) for `bundle_manifest.json`.
- Add strict signature mode and new restore error code `RESTORE_INVALID_SIGNATURE`.
- Add restore CLI `--verify-only` mode (no writes to SQLite/filesystem).
- Update History UI restore details for signature/strict/verify-only states.
- Extend tests and operations docs.

## Pre-flight
- Baseline commit before iteration: `59fdd25d9152b71198d35666bdd22161c341e4dc`
- Clean status verified before work.
- Working branch: `codex/iteration-14-restore-auth`.

## Key Changes

### 1) Configurable restore limits (ENV)
- Added in `app/config/settings.py` and `.env.example`:
  - `RESTORE_MAX_ENTRIES`
  - `RESTORE_MAX_TOTAL_UNCOMPRESSED_BYTES`
  - `RESTORE_MAX_SINGLE_FILE_BYTES`
  - `RESTORE_MAX_COMPRESSION_RATIO`
- Defaults preserved (backward compatible with previous hardcoded values).
- UI/CLI restore now consume these values through settings.

### 2) Bundle authenticity (manifest signature)
- Updated `app/storage/zip_export.py`:
  - optional `signing_key` argument;
  - when present, `bundle_manifest.json` includes:
    - `signature.algorithm = hmac-sha256`
    - `signature.hmac_sha256`.
  - signature built from canonical JSON serialization (`sort_keys=True`, compact separators).
- Key source: env/settings (`BUNDLE_SIGNING_KEY` / `KAUCJA_BUNDLE_SIGNING_KEY`), no hardcoded secrets.

### 3) Restore signature verification + strict mode
- Updated `app/storage/restore.py`:
  - restore params: `signing_key`, `require_signature`, `verify_only`;
  - if signed and key configured: verifies HMAC;
  - invalid signature => `RESTORE_INVALID_SIGNATURE`;
  - unsigned bundles in non-strict mode: allowed with warning;
  - strict mode (ENV or CLI): rejects unsigned/unverifiable bundles.
- Added result fields:
  - `signature_verification_status`
  - `archive_signed`
  - `signature_required`
  - `verify_only`

### 4) Verify-only mode
- Added CLI flag: `--verify-only`.
- Behavior:
  - validates archive safety + manifest integrity + signature checks;
  - does not extract files and does not write metadata to SQLite;
  - returns deterministic JSON report.

### 5) UI restore details and taxonomy alignment
- Updated `app/ui/gradio_app.py`:
  - restore controls include:
    - `Verify only (no restore)`;
    - `Require signature (strict)`.
  - technical details now show:
    - manifest verification status,
    - signature verification status,
    - signed/unsigned state,
    - strict mode,
    - verify-only state,
    - rollback status.
- Updated `app/utils/error_taxonomy.py` with restore-related friendly messages and `RESTORE_INVALID_SIGNATURE`.

### 6) Additional wiring
- `app/storage/retention.py` now passes optional signing key into ZIP backup export.

## Tests Updated
- `tests/test_settings.py`
  - ENV override coverage for restore limits and signing/strict settings.
- `tests/test_zip_export.py`
  - signature presence/shape in signed exports.
- `tests/test_restore_run.py`
  - signed bundle success,
  - invalid signature failure,
  - signed bundle without key warning (non-strict),
  - strict reject unsigned (manifest and legacy),
  - verify-only success,
  - verify-only failure,
  - existing integrity/zip-bomb/rollback tests kept green.
- `tests/test_gradio_smoke.py`
  - restore UI details now assert signature/strict/verify-only fields,
  - verify-only UI scenario,
  - strict reject unsigned UI scenario,
  - rollback detail rendering with extended result shape.
- `tests/test_delete_run_retention.py`
  - backup-export monkeypatch updated for `signing_key` argument.

## Required Checks (actual runs)
Executed at `2026-02-25T18:02:24Z` on `codex/iteration-14-restore-auth`.

```bash
ruff format .
```
Result: `61 files left unchanged`

```bash
ruff check .
```
Result: `All checks passed!`

```bash
pytest -q
```
Result: `117 passed in 3.50s`

```bash
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```
Result: `gradio_app_started`

## Backward Compatibility
- Legacy archives without `bundle_manifest.json` restore successfully in non-strict mode with warning.
- Unsigned bundles with manifest also restore in non-strict mode with warning.
- Strict mode can be enabled explicitly via env/CLI/UI.

## Known Limits
- Authenticity uses shared-secret HMAC; no asymmetric signing/public-key trust model.
- Verify-only reports expected restore path but does not reserve/lock it against concurrent operations.
