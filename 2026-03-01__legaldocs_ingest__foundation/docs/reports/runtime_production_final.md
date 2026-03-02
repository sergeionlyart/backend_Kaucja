# Runtime Finalization Report

**Date:** 2026-03-02  
**Branch:** `exp/legaldocs-ingest-runtime-env`  
**Run ID:** `467ac9956f7b465288d4f0426ad23405`

## What was fixed
- Removed incorrect COMMERCIAL bypass that could mark low-quality/paywall HTML as `OK`.
- Added strict tests for `--strict-ok` behavior and COMMERCIAL restriction handling.
- Added `artifacts_dev/` to `.gitignore` and removed tracked runtime artifacts from git index.
- Reworked Mongo verification script to verify a specific run (`--run-id`) and report base source coverage vs expanded sources.
- Updated `.env.example` (`LEX_SESSION_ID` placeholder) and README runtime instructions.

## Commands executed
```bash
ruff format . && ruff check .
pytest -q
python -m legal_ingest.cli --env-file .env validate-config --config configs/config.full.runtime.yml
python -m legal_ingest.cli --env-file .env ensure-indexes --config configs/config.full.runtime.yml
python -m legal_ingest.cli --env-file .env ingest --config configs/config.full.runtime.yml --strict-ok
python scripts/verify_mongo.py --env-file .env --run-id 467ac9956f7b465288d4f0426ad23405 --config configs/config.full.runtime.yml --output docs/reports/mongo_verification_export.json
```

## Runtime result (strict mode)
- Strict ingest returned non-zero as expected because restricted/error documents were detected.
- Final metrics:
  - `sources_total=14`
  - `docs_ok=9`
  - `docs_restricted=3`
  - `docs_error=2`
- Main blockers in this run:
  - `pl_saos_171957`: `ReadTimeout`
  - `pl_courts_wloclawek_I_Ca_56_2018`: `RemoteProtocolError`
  - `pl_saos_search_kaucja_mieszkaniowa`: search expansion timeout
  - 3 LEX sources returned `RESTRICTED`

## Conclusion
Pipeline is now technically correct and strict mode works correctly (fails on non-OK outputs).  
A true `15/15 OK` production run still requires stable external source availability and valid commercial access session/cookies for LEX.
