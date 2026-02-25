# Iteration 13: Restore Integrity + Anti-ZipBomb + Rollback Safety

## Scope
- Add backup bundle integrity control (`bundle_manifest.json`) on export and verify it on restore.
- Add anti-zip-bomb limits in restore path.
- Add rollback semantics when file restore succeeds but metadata restore fails.
- Surface restore verification and rollback details in History UI.
- Extend tests for integrity, limits, rollback, and UI restore behaviors.

## Changes

### 1) ZIP export integrity manifest
- Updated `app/storage/zip_export.py`.
- Export now includes deterministic `bundle_manifest.json` at ZIP root with:
  - `version`, `run_id`, `session_id`
  - `files[]` entries: `relative_path`, `size_bytes`, `sha256`
- ZIP entries remain deterministic:
  - sorted paths
  - fixed timestamp `(1980, 1, 1, 0, 0, 0)`

### 2) Restore integrity + anti-zip-bomb + rollback
- Updated `app/storage/restore.py`.
- Added `RestoreSafetyLimits` constants and validation for:
  - `max_entries`
  - `max_total_uncompressed_bytes`
  - `max_single_file_bytes`
  - `max_compression_ratio`
- Added archive hardening:
  - duplicate path detection
  - path traversal/symlink checks retained
- Added manifest verification flow:
  - if `bundle_manifest.json` exists: verify each listed file checksum/size before extraction
  - checksum/size/path mismatch => `RESTORE_INVALID_ARCHIVE`
  - if manifest missing (legacy zip): restore allowed with warning
- Added identity check: `bundle_manifest.json` `run_id/session_id` must match `run.json`.
- Added rollback on metadata failure (default `True`):
  - if metadata restore fails after files were copied, restore attempts to remove restored run tree
- Added CLI flag:
  - `--no-rollback-on-metadata-failure`

### 3) Restore result contract + UI details
- Updated `app/storage/models.py` (`RestoreRunResult`) with:
  - `manifest_verification_status`
  - `files_checked`
  - `rollback_attempted`
  - `rollback_succeeded`
- Updated `app/ui/gradio_app.py` restore callback details to include:
  - manifest verification status
  - files checked
  - rollback status
  - error code/message

### 4) Tests
- Updated `tests/test_zip_export.py`:
  - verifies `bundle_manifest.json` presence and structure.
- Updated `tests/test_restore_run.py`:
  - checksum mismatch failure
  - legacy ZIP restore warning without manifest
  - anti-zip-bomb limit checks (`max_entries`, `max_compression_ratio`)
  - metadata failure rollback `True/False` behavior
- Updated `tests/test_gradio_smoke.py`:
  - restore success includes verification details
  - restore integrity failure shown in UI details
  - rollback/verification details surfaced in failure details

## Validation runs
Executed on branch `codex/iteration-13-restore-integrity` at `2026-02-25T17:46:00Z`.

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
Result: `106 passed in 2.81s`

```bash
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```
Result: `gradio_app_started`

## Known limits
- Manifest verification checks archive payload integrity only; it does not provide cryptographic signing/authentication.
- Legacy bundles without `bundle_manifest.json` are allowed for backward compatibility and marked with warning.
- Default zip-bomb limits are static constants in code; they are not yet runtime-configurable via env/settings.
