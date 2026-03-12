# Iteration 2: Legal Ingest Metadata Migration

## Scope

- Fixed Iteration 1 self-containment defects in `legal_ingest migration-plan`.
- Added tracked source catalog under `legal_ingest/source_catalog.py`.
- Enforced migration-map invariant: `status=canonical => canonical_doc_uid != null`.
- Added idempotent CLI commands:
  - `python -m legal_ingest required-fetch --dry-run|--apply`
  - `python -m legal_ingest metadata-migrate --dry-run|--apply`
- Fetched only official current sources for 5 required Polish acts.
- Canonicalized required runtime docs in place and populated TechSpec 3.1 metadata.

## What Changed

- `legal_ingest/data/migration_map_v3_1.json` is now generated from tracked data only.
- `position-35` now resolves canonically to `uokik_pl:urlsha:c506ff470f4740ad`.
- New required docs fetched into Mongo:
  - `eli_pl:DU/1964/296`
  - `eli_pl:DU/2005/1398`
  - `eli_pl:DU/2007/331`
- Existing runtime canonicals updated in place:
  - `eli_pl:DU/2001/733`
  - `isap_pl:WDU19640160093`
  - `eurlex_eu:urlsha:252f802534879b95`
  - `curia_eu:urlsha:54acc341b17f3a57`
  - `curia_eu:urlsha:ef65918198e5ffee`
  - `uokik_pl:urlsha:c506ff470f4740ad`
  - `uokik_pl:urlsha:054662ca9a699d16`
- Confirmed same-case groups now carry `same_case_group_id` on all members:
  - `same_case:i_ca_56_18`
  - `same_case:iii_ca_1707_18`
  - `same_case:v_aca_599_14`

## Acceptance Snapshot

- Final audit: `required_total=18`
- `present_canonical=18`
- `present_noncanonical=0`
- `missing=0`
- `status=canonical` with null `canonical_doc_uid`: `0`
- Same-case groups with consistent `same_case_group_id`: `3 / 3`
- Remaining Section 7 finding: `uokik_pl:urlsha:5efe92f726049194` as excluded candidate only
- Repeatability check:
  - `required-fetch --dry-run` after apply -> `noop=5`
  - `metadata-migrate --dry-run` after apply -> `document_updates=0`

## Mongo Delta

- `documents`: `928 -> 931`
- `pages`: `3167 -> 3951`
- `nodes`: `6725 -> 9188`
- `citations`: unchanged at `3647`
- `document_sources`: `1172 -> 1176`
- `ingest_runs`: unchanged at `25`

## Artifacts

- Backup before required fetch:
  - `artifacts/legal_ingest/backups/20260307T101023Z/backup_manifest.json`
- Backup before metadata migration:
  - `artifacts/legal_ingest/backups/20260307T101043Z/backup_manifest.json`
- Final audit:
  - `artifacts/legal_ingest/audits/20260307T101341Z/audit_report.json`
  - `artifacts/legal_ingest/audits/20260307T101341Z/audit_report.md`

## Missing / Deferred To Iteration 3

- No global rebuild of `pages`, `nodes`, or `citations` for legacy documents.
- No canonical cleanup yet for duplicate archive aliases such as `eli_pl:urlsha:*` and `isap_pl:urlsha:*`.
- No full Section 5 metadata enrichment for the broader corpus beyond required, alias, and excluded slices.
- No citation refresh for newly fetched acts.

## Exact Next Steps

1. Add alias/archive entries for duplicate act mirrors that still coexist beside canonical runtime docs.
2. Expand metadata migration from required slice to the wider TechSpec 3.1 corpus.
3. Rebuild or backfill `article_node` coverage and cross-document citations where current fetch added new acts.
4. Move `uokik_pl:urlsha:5efe92f726049194` out of the core runtime slice as excluded-only inventory.
