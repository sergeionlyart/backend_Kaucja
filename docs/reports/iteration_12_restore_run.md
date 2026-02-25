# Iteration 12: Restore Run from Backup ZIP (CLI + UI)

## Scope
- Safe restore of run artifacts + metadata from ZIP backups.
- CLI interface for restore.
- UI integration in History (upload ZIP + restore button + overwrite option).
- Tests for success/failure/overwrite/cycle scenarios.

## Changes
1. Added restore module:
   - `app/storage/restore.py`
   - validates archive entries (no absolute/`..`, no symlink entries),
   - requires `run.json` + basic layout root,
   - extracts to temp dir, restores files into deterministic target path,
   - restores SQLite metadata for `runs`, `documents`, `llm_outputs` in deterministic best-effort flow,
   - error taxonomy: `RESTORE_INVALID_ARCHIVE`, `RESTORE_RUN_EXISTS`, `RESTORE_FS_ERROR`, `RESTORE_DB_ERROR`.

2. Added restore result model:
   - `app/storage/models.py` (`RestoreRunResult`).

3. CLI restore entrypoint:
   - `python -m app.storage.restore --zip-path ... --db-path ... --data-dir ... [--overwrite-existing]`
   - JSON output report.

4. UI integration:
   - `app/ui/gradio_app.py`
   - added restore controls in History:
     - ZIP upload,
     - overwrite checkbox,
     - restore button,
     - status/details/restored run path outputs,
   - refreshes history table and compare dropdowns after successful restore.

5. Tests:
   - `tests/test_restore_run.py`:
     - restore success,
     - invalid archive/traversal,
     - run exists without overwrite,
     - overwrite flow,
     - fs/db failure branches.
   - `tests/test_gradio_smoke.py`:
     - UI restore success/failure,
     - export -> delete -> restore cycle.

6. Docs:
   - `docs/OPERATIONS.md` updated with restore CLI/UI and safety checks.

## Verification
Commands executed:

```bash
ruff format .
ruff check .
pytest -q
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```

Outputs:
- `ruff format .` -> `61 files left unchanged`
- `ruff check .` -> `All checks passed!`
- `pytest -q` -> `99 passed in 2.74s`
- Gradio smoke -> `gradio_app_started`

## Known Limits
1. Restore uses best-effort metadata reconstruction from `run.json` and artifact files; malformed manifests can produce warnings.
2. If file restore succeeds but metadata restore fails, artifacts may remain restored with `RESTORE_DB_ERROR`.
3. Restore operation is synchronous and may be slow for large ZIP archives.
