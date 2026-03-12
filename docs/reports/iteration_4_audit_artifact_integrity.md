# Iteration 4: Audit Artifact Integrity

## Scope

- Tightened `legal_ingest audit` so baseline coverage and strict validity are reported separately.
- Added `artifact_integrity` gate for `checksum_sha256` and `storage_uri`.
- Expanded `metadata-migrate --scope full` manual-review coverage for broken artifact records.
- Resolved six confirmed broken-artifact documents without destructive deletes.

## Findings

- Previous audit defect: `checksum_sha256='ERROR'` and synthetic or broken `storage_uri` values counted as covered metadata.
- Confirmed broken-artifact docs:
  - `eurlex_eu:urlsha:8f4d90b5081ec765`
  - `curia_eu:urlsha:556c3aa0fb85f92e`
  - `eurlex_eu:urlsha:3cc91aee0436279b`
  - `eurlex_eu:urlsha:51fd4eed44abc101`
  - `eurlex_eu:urlsha:86a3a115b4b0e267`
  - `eurlex_eu:urlsha:27e3506c61c42585`
- Historical `document_sources` rows for several of these docs pointed to legacy artifact locations that are not present in the current checkout, so safe local restoration was not reproducible.

## Resolution

- Added strict checksum validation: `ERROR` and non-hex values are invalid.
- Added strict storage validation for:
  - synthetic `document_sources:*`
  - broken `/ERROR/` paths
  - nonexistent current-style filesystem paths
- Downgraded all six confirmed docs to explicit `status=excluded`, `legal_role=INVENTORY_ONLY` with `Broken imported artifact retained for inventory only.` in `exclusion_reason`.
- Kept the records in MongoDB for inventory traceability and duplicate resolution.
- Manual-review output now lists all six broken-artifact docs plus the pre-existing unknown-source review item.

## Final State

- `baseline_metadata_coverage = 931/931`
- `baseline_metadata_validity = 931/931`
- `artifact_integrity.invalid_documents = 0`
- `same_case_group_id` remains consistent for `3/3` groups
- `section7_findings.total_findings = 0`
- `unresolved_multi_doc_duplicates = 0`

## Iteration 5 Input

- Decide whether any excluded broken EU optional docs should be re-fetched from official sources and re-activated.
- Review the remaining non-artifact manual-review tail (`unknown:urlsha:4307a0f3b0cab777`) before broader corpus curation.
