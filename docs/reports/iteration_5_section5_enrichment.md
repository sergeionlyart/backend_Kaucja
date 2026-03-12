# Iteration 5: Audit Semantics and Section-5 Enrichment

## Scope

- Split audit semantics into whole-corpus (`all_docs`) and operational runtime metrics.
- Moved broken inventory handling out of `manual_review` into explicit `broken_inventory_exemptions`.
- Added deterministic TechSpec 3.1 section-5 enrichment over the full corpus.
- Closed the remaining manual-review tail for `unknown:urlsha:4307a0f3b0cab777`.

## What Was Added

- New audit blocks:
  - `baseline_metadata_validity_all_docs`
  - `baseline_metadata_validity_operational`
  - `artifact_integrity_all_docs`
  - `artifact_integrity_operational`
  - `broken_inventory_exemptions`
  - `section5_enrichment_coverage`
- Rule-based section-5 fields now populate for all `931/931` documents:
  - `title_short`
  - `summary_1line`
  - `issue_tags`
  - `relevance_score`
  - `search_terms_positive`
  - `search_terms_negative`
  - `query_templates`
  - `last_verified_at`
- Rule-based case layer now populates for `906/906` `CASELAW` documents:
  - `case_signature`
  - `judgment_date`
  - `court_name`
  - `court_level`
  - `holding_1line`
  - `facts_tags`
  - `related_provisions`
  - `artifact_type`
- Supersession/search metadata now populates deterministically for alias/excluded/search-like records:
  - `is_search_page`
  - `superseded_by`

## Final Metrics

- Baseline coverage: `931/931`
- Baseline validity, all docs: `925/931`
- Baseline validity, operational docs: `925/925`
- Artifact integrity, all docs: `6` invalid documents
- Artifact integrity, operational docs: `0` invalid documents
- Broken inventory exemptions: `6`
- Section-5 baseline enrichment coverage: `931/931`
- Section-5 caselaw enrichment coverage: `906/906`
- Required runtime docs: `18/18 present_canonical`, `present_noncanonical=0`, `missing=0`
- Manual review: `0`
- Same-case consistency: `3/3`

## Source-Derived vs Template-Derived

- Source-derived or source-system-derived:
  - `last_verified_at` from existing runtime timestamps
  - `case_signature` from existing title/external id/source URL heuristics where available
  - `judgment_date` from source fields or parsed headings in `887/906` case records
  - `court_name`/`court_level` from source system, pageindex headings, host patterns, or explicit conservative fallback
  - `title_short`, `issue_tags`, `search_terms_positive`, `query_templates` from canonical title, act ids, signatures, and external ids
- Template-derived:
  - `summary_1line` for `931/931`
  - `holding_1line` for `906/906`
  - generic negative search terms for all docs
  - fallback `facts_tags=['facts_not_extracted']` in `889/906`
  - fallback `related_provisions=['not_determined']` in `900/906`
  - fallback `judgment_date='unknown'` in `19/906`
  - singleton `same_case_group_id` placeholders for `900` non-confirmed case records

## Unknown Mirror Resolution

- `unknown:urlsha:4307a0f3b0cab777` is now treated as an official secondary mirror to `eli_pl:DU/2001/733`.
- Final metadata:
  - `status=alias`
  - `legal_role=SECONDARY_SOURCE`
  - `source_tier=official`
  - `superseded_by=eli_pl:DU/2001/733`
- It no longer appears in `manual_review`.

## Remaining for Iteration 6

- Replace the remaining conservative placeholders where worthwhile:
  - `19` unknown `judgment_date` values
  - `1` unresolved `court_name`
  - `889` fallback `facts_tags`
  - `900` fallback `related_provisions`
- Decide whether any of the six broken inventory records should be restored from reproducible official artifacts instead of remaining exempt inventory.
- If needed, refine singleton `same_case_group_id` placeholders into broader cross-source group identities beyond the three confirmed groups.
