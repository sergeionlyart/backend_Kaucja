# Iteration 6 Final Acceptance

Date: 2026-03-07

Scope: final TechSpec 3.1 closeout inside `legal_ingest` without destructive cleanup and without changing the ingest/fetch pipeline.

## Acceptance Table

| TechSpec area | Status | Evidence | Residual risks |
| --- | --- | --- | --- |
| Foundation CLI, migration-map invariants, idempotent migration flow | closed | `python -m legal_ingest metadata-migrate --dry-run --scope full` -> `manual_review_count=0`, `non_noop=0`; `canonical_invariants.null_canonical_doc_uid_count=0` in `artifacts/legal_ingest/audits/20260307T121218Z/audit_report.json` | None in this slice. |
| Baseline metadata coverage and operational validity semantics | closed | `baseline_metadata_coverage=931/931`; `baseline_metadata_validity_all_docs=925/931`; `baseline_metadata_validity_operational=925/925`; `artifact_integrity_all_docs.invalid_documents=6`; `artifact_integrity_operational.invalid_documents=0` | All-doc validity remains below full coverage by design because 6 broken inventory records stay explicitly invalid. |
| Required runtime top-level corpus | closed | `required_total=18`; `present_canonical=18`; `present_noncanonical=0`; `missing=0` in the same audit report | None in this slice. |
| same-case grouping and duplicate resolution | closed | `same_case_candidates.groups_with_full_same_case_group_id=3/3`; `duplicate_final_url_groups.unresolved_multi_doc_duplicates=0` | Physical duplicates are still retained intentionally as metadata-resolved records. |
| Section 5 enrichment coverage | closed | `section5_enrichment_coverage.all_documents=931/931`; `section5_enrichment_coverage.caselaw_documents=906/906` | Outside the curated slice, many CASELAW records still use rule-based fallback facts/provisions; this is visible in placeholder metrics and was not normalized semantically in this iteration. |
| `court_name` normalization for portal/pageindex cases | closed | `court_name` ISO-date suffix count = `0`; portal mirrors now resolve to normalized values without `z YYYY-MM-DD` tails | None in this slice. |
| Curated required runtime caselaw semantic minimum | closed | `section5_placeholder_metrics_required_runtime.placeholder_holding_1line.count=0`; `fallback_facts_tags.count=0`; `fallback_related_provisions.count=0`; `judgment_date_unknown_avoidable.count=0`; `unresolved_court_name.count=0` | Two CURIA records still have `judgment_date='unknown'`, but the audit now classifies them as unavoidable because the stored artifact is only an RPEX shell page. |
| Broken imported artifact handling | partially closed | `broken_inventory_exemptions.count=6`; all 6 remain visible in `artifact_integrity_all_docs` and excluded from operational validity only via explicit exemption reporting | Restoration was not safe without a new authoritative re-fetch. |

## What Changed In Iteration 6

- `court_name` normalization now strips portal suffixes like `z 2018-05-08` and keeps the court institution only.
- `metadata-migrate --scope full` now uses existing `pages` text as a deterministic source for `judgment_date` and `court_name` when the document record itself is incomplete.
- The 9 required runtime caselaw authorities now have curated, source-derived `holding_1line`, `facts_tags`, and `related_provisions` instead of generic placeholders.
- `audit` now publishes explicit placeholder metrics for all docs and for the required runtime caselaw slice, including raw and avoidable `judgment_date='unknown'`.

## Placeholder Metrics Snapshot

- All docs placeholder holding: `885`
- All docs fallback `facts_tags`: `882`
- All docs fallback `related_provisions`: `893`
- All docs `judgment_date='unknown'`: `4`
- All docs avoidable `judgment_date='unknown'`: `0`
- All docs unresolved `court_name`: `0`
- Required runtime `judgment_date='unknown'`: `2`
- Required runtime avoidable `judgment_date='unknown'`: `0`

## Broken Inventory Records

All 6 previously confirmed broken records were retained as explicit excluded inventory, not restored:

- `curia_eu:urlsha:556c3aa0fb85f92e`
- `eurlex_eu:urlsha:27e3506c61c42585`
- `eurlex_eu:urlsha:3cc91aee0436279b`
- `eurlex_eu:urlsha:51fd4eed44abc101`
- `eurlex_eu:urlsha:86a3a115b4b0e267`
- `eurlex_eu:urlsha:8f4d90b5081ec765`

Reason: their stored checksum and/or artifact path is still broken, and no safe restoration path was introduced in this iteration. They therefore remain invalid in `all_docs` metrics and exempt only in `operational` metrics.

## Commands

```bash
python -m legal_ingest metadata-migrate --apply --scope full
python -m legal_ingest metadata-migrate --dry-run --scope full
python -m legal_ingest audit
ruff check .
pytest -q
```

## Residual Risks For Post-TechSpec Work

- Three CURIA shell artifacts and one SAOS search seed still have `judgment_date='unknown'`, but the audit now shows that none of them are avoidable with the currently stored source material.
- The corpus still contains large counts of template-derived `facts_tags` and `related_provisions` outside the curated required runtime slice.
- `KORPUS_DOKUMENTOW_KAUCJA_PL.md` was not regenerated in this iteration to keep the diff scoped to `legal_ingest`, tests, and final reporting.
