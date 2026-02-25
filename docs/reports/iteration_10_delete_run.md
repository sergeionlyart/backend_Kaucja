# Iteration 10: Data Lifecycle Controls (Delete Run + Retention Safety)

## Scope
- Safe run deletion (SQLite metadata + filesystem artifacts).
- History UI integration with explicit delete confirmation.
- Manual retention utility for deleting runs older than N days.
- Tests for delete edge-cases and retention best-effort behavior.

## Changes
1. Storage delete operation:
   - `app/storage/repo.py`
   - added `delete_run(run_id)` returning structured result,
   - handles scenarios: run not found, invalid artifacts path, filesystem delete failure, DB delete failure,
   - enforces path safety (`data/` root + expected `sessions/<session>/runs/<run>` layout),
   - rejects symlinked paths while deleting artifacts.

2. Data lifecycle models:
   - `app/storage/models.py`
   - added `DeleteRunResult` and `RetentionCleanupResult`.

3. Retention utility:
   - `app/storage/retention.py`
   - added `purge_runs_older_than_days(...)` (best-effort),
   - added CLI entrypoint:
     `python -m app.storage.retention --days N --db-path ... --data-dir ...`.

4. UI history delete flow:
   - `app/ui/gradio_app.py`
   - added `Delete run` button,
   - added explicit confirmation field (`Confirm Run ID for Delete`),
   - added delete status/technical details fields,
   - refreshes history table + compare dropdowns after delete attempt.

5. Tests:
   - `tests/test_delete_run_retention.py`
     - delete success/not-found/path-guard/fs/db/symlink cases,
     - retention success + best-effort failure report.
   - `tests/test_gradio_smoke.py`
     - UI delete callback success + confirmation mismatch.

6. Operations docs:
   - `docs/OPERATIONS.md`
   - added sections: UI delete flow, safety controls, retention command.

## Verification
Commands executed:

```bash
ruff format .
ruff check .
pytest -q
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```

Outputs:
- `ruff format .` -> `2 files reformatted, 57 files left unchanged`
- `ruff check .` -> `All checks passed!`
- `pytest -q` -> `86 passed in 3.10s`
- Gradio smoke -> `gradio_app_started`

## Known Limits
1. Deletion is synchronous; large artifact trees can take noticeable time.
2. If artifacts deletion succeeds but DB delete fails, operation reports failure and requires retry.
3. Retention utility uses manual invocation only (no scheduler in MVP).
