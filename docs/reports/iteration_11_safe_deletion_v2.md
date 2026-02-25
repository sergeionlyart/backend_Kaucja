# Iteration 11: Safe Deletion v2 (dry-run + backup-first + audit trail)

## Scope
- Strengthen retention utility with dry-run, backup-before-delete, and deterministic per-run audit.
- Persist retention report JSON files for later analysis.
- Harden History UI delete flow with backup-first option.
- Cover success/failure paths with tests.

## Changes
1. Retention utility enhancements:
   - `app/storage/retention.py`
   - added CLI flags: `--dry-run`, `--export-before-delete`, `--export-dir`, `--report-dir`, `--report-path`.
   - backup-first logic: if backup fails, delete for that run is skipped.
   - deterministic candidate ordering and per-run audit entries.

2. Retention report persistence:
   - reports saved as JSON in `data/retention_reports/<timestamp>.json` by default,
   - custom report location supported via CLI args,
   - report payload structured for post-analysis.

3. UI delete hardening:
   - `app/ui/gradio_app.py`
   - added `Create backup ZIP before delete` checkbox,
   - delete flow now supports backup-first behavior,
   - UI shows delete status + backup path + technical details,
   - history table and compare dropdowns refreshed after delete attempts.

4. Models:
   - `app/storage/models.py`
   - expanded `RetentionCleanupResult` to include dry-run/export/report/audit fields.

5. Tests:
   - `tests/test_delete_run_retention.py`
     - dry-run no deletion,
     - export-before-delete success,
     - export failure skips delete,
     - report file persistence,
     - existing delete safety cases retained.
   - `tests/test_gradio_smoke.py`
     - delete with backup success,
     - delete with backup failure path.

6. Operations docs:
   - `docs/OPERATIONS.md` updated for dry-run, backup-first delete, and retention report paths.

## Verification
Commands executed:

```bash
ruff format .
ruff check .
pytest -q
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```

Outputs:
- `ruff format .` -> `59 files left unchanged`
- `ruff check .` -> `All checks passed!`
- `pytest -q` -> `91 passed in 3.06s`
- Gradio smoke -> `gradio_app_started`

## Known Limits
1. Backup-before-delete doubles I/O for selected runs (ZIP + delete).
2. Retention reports contain technical error details and should be treated as operational logs.
3. Cleanup remains manual (no scheduler/background worker in MVP).
