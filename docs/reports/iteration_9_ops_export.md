# Iteration 9: Post-MVP Operations (CI + Export Run Bundle)

## Scope
- ZIP export for run artifacts from History.
- History UI integration for export status/path/download.
- GitHub Actions CI for lint + tests + Gradio smoke.
- Operations documentation for local runtime and data handling.

## Changes
1. Added deterministic ZIP exporter with safety guards:
   - `app/storage/zip_export.py`
   - validates artifacts root existence and directory type,
   - deterministic archive ordering,
   - fixed ZIP timestamps,
   - rejects symlinked paths (traversal protection),
   - returns clear errors for missing/invalid roots.

2. Integrated export in History UI:
   - `app/ui/gradio_app.py`
   - callback `export_history_run_bundle(...)`,
   - button `Export run bundle (zip)`,
   - status textbox, ZIP path textbox, download file output.

3. Added CI pipeline:
   - `.github/workflows/ci.yml`
   - runs `ruff check .`, `pytest -q`, and Gradio startup smoke.

4. Added operations guide:
   - `docs/OPERATIONS.md`

5. Added tests:
   - `tests/test_zip_export.py` (success, missing root, traversal/symlink guard),
   - `tests/test_gradio_smoke.py` export callback coverage.

## Verification
Commands executed:

```bash
ruff format .
ruff check .
pytest -q
python -c "from app.ui.gradio_app import build_app; build_app(); print('gradio_app_started')"
```

Outputs:
- `ruff format .` -> `57 files left unchanged`
- `ruff check .` -> `All checks passed!`
- `pytest -q` -> `76 passed in 2.76s`
- Gradio smoke -> `gradio_app_started`

## Known Limits
1. Export file is created on local filesystem and not auto-cleaned.
2. Very large run artifacts can make ZIP export slower.
3. CI installs full dependencies (including UI libs), so run time depends on package download speed.
