# Iteration 3: Corpus-Wide Normalization

## Scope

- Expanded `metadata-migrate` from required slice to corpus-wide normalization with `--scope full`.
- Kept cleanup metadata-only and idempotent. No document deletes and no new ingest flow.
- Extended `audit` with baseline coverage, act-layer coverage, and resolved vs unresolved duplicate metrics.

## What Changed

- Baseline metadata fields are now deterministically populated for all `931` documents:
  - `status`
  - `document_kind`
  - `legal_role`
  - `source_tier`
  - `canonical_title`
  - `source_url`
  - `normalized_source_url`
  - `external_id`
  - `checksum_sha256`
  - `storage_uri`
- Act-layer fields are now populated for all `16` `STATUTE` / `EU_ACT` documents:
  - `act_id`
  - `act_short_name`
  - `article_nodes`
  - `current_status`
  - `current_text_ref`
  - `is_consolidated_text`
  - `key_provisions`
- Exact duplicate inventory is metadata-resolved for all `8` current multi-doc duplicate groups:
  - owner record marked with `duplicate_role=owner`
  - retained mirrors marked with `status=alias` or `status=excluded`
  - all members receive `duplicate_group_id` and `duplicate_owner_doc_uid`
- Section 7 tail is closed:
  - `uokik_pl:urlsha:5efe92f726049194` is now an excluded inventory-only record with normalized title metadata

## Acceptance Snapshot

- Baseline metadata coverage: `931 / 931`
- Act-layer coverage: `16 / 16`
- Required runtime docs: `18 / 18 present_canonical`
- Required runtime docs: `present_noncanonical=0`
- Required runtime docs: `missing=0`
- Same-case groups with consistent `same_case_group_id`: `3 / 3`
- Section 7 findings: `0`
- Resolved multi-doc duplicate groups: `8`
- Unresolved multi-doc duplicate groups: `0`
- Repeatability check:
  - `python -m legal_ingest metadata-migrate --dry-run --scope full` -> `document_updates=0`

## Manual Review

- `eurlex_eu:urlsha:27e3506c61c42585`
  - missing current `document_source`
- `unknown:urlsha:4307a0f3b0cab777`
  - unknown `source_system`
  - act owner inferred from non-official mirror

## Artifacts

- Final metadata migration report:
  - `artifacts/legal_ingest/metadata-migrate/20260307T104928Z/metadata_migration_report.json`
- Final audit:
  - `artifacts/legal_ingest/audits/20260307T104928Z/audit_report.json`
  - `artifacts/legal_ingest/audits/20260307T104928Z/audit_report.md`
- Latest safety backup before mutation:
  - `artifacts/legal_ingest/backups/20260307T104919Z/backup_manifest.json`

## Next Steps

1. Use the manual-review list to decide whether the remaining unknown / missing-source documents should stay as inventory-only or be re-fetched.
2. Move from deterministic baseline into semantic enrichment for Section 5 fields still intentionally left empty (`summary_1line`, `holding_1line`, `issue_tags`, `query_templates`, `relevance_score`).
3. Revisit semantic, non-exact duplicate families after the exact duplicate inventory is stable.
