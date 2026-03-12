# TechSpec 3.1 Delivery Sync

Date: 2026-03-07

## Accepted snapshot

- Accepted audit snapshot: `artifacts/legal_ingest/audits/20260307T121218Z/audit_report.json`
- Snapshot result used for delivery sync:
  - `required_present_canonical=18`
  - `required_present_noncanonical=0`
  - `required_missing=0`
  - `section7_findings=0`
  - `same_case_groups_with_full_id=3/3`
  - `artifact_integrity_operational.invalid_documents=0`

## Current external deliverable

- Rebuilt corpus reference: `KORPUS_DOKUMENTOW_KAUCJA_PL.md`
- Source of truth for the rebuild: current `legal_rag_runtime.documents`
- Deduplication rule for the file: one entry per `doc_uid`; current `status` is preserved as `canonical` / `alias` / `excluded` / other runtime status.
- Operational note: the file includes the whole corpus for traceability, but the 6 intentionally broken inventory records remain outside the operational slice.

## Intentionally broken / excluded records

- `curia_eu:urlsha:556c3aa0fb85f92e`
- `eurlex_eu:urlsha:27e3506c61c42585`
- `eurlex_eu:urlsha:3cc91aee0436279b`
- `eurlex_eu:urlsha:51fd4eed44abc101`
- `eurlex_eu:urlsha:86a3a115b4b0e267`
- `eurlex_eu:urlsha:8f4d90b5081ec765`

These records stay `excluded` / `INVENTORY_ONLY` because their stored checksum and/or artifact path is still broken. They are listed in the external KORPUS file for traceability only.

## Revalidation commands

```bash
python -m legal_ingest metadata-migrate --dry-run --scope full
python -m legal_ingest audit
python scripts/build_korpus_reference.py
ruff check .
pytest -q
```
