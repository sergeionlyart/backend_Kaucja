# ExecPlan: TechSpec 3.1 Iteration 5

## Scope
Refine `legal_ingest` semantics for audit/manual-review and complete deterministic TechSpec 3.1 section-5 enrichment across the normalized corpus without changing ingest/fetch flow.

## Dependencies
1. Iteration 4 corpus-wide metadata normalization and duplicate resolution.
2. Existing `legal_ingest metadata-migrate --scope full` command and audit artifacts.
3. Existing Mongo runtime corpus (`documents/pages/nodes/document_sources`) with no destructive cleanup.

## Steps
1. Split audit validity and artifact integrity into:
   - all-doc metrics
   - operational metrics
   - explicit broken-inventory exemptions.
2. Resolve `unknown:urlsha:4307a0f3b0cab777` deterministically as an official secondary mirror or leave one explicit reason in report if not safely resolvable.
3. Extend metadata migration with rule-based section-5 enrichment for all documents:
   - baseline fields for all docs
   - caselaw-specific fields for all `CASELAW`
   - `is_search_page` and `superseded_by` for excluded/search-like records.
4. Update audit/report wording so operational cleanliness is not presented as whole-corpus validity.
5. Add tests for:
   - all-doc vs operational metrics
   - broken-inventory exemptions
   - unknown mirror manual-review closure
   - section-5 enrichment across representative document classes.
6. Run `ruff check .`, `pytest -q`, then publish iteration report.

## Risks
1. Over-aggressive heuristics can fabricate legal semantics for sparse records.
2. Manual-review suppression can hide unresolved data-quality issues.
3. Full-corpus enrichment can break idempotency if template values are not stable.

## Risk Mitigation
1. Prefer source-derived values; otherwise use conservative template strings, empty lists, or zero scores.
2. Keep broken inventory visible in dedicated audit exemptions and all-doc integrity metrics.
3. Reuse existing normalization helpers and compute deterministic values from current document state only.

## Definition of Done
1. Audit exposes both all-doc and operational validity/integrity metrics.
2. Broken inventory remains visible in all-doc metrics and explicit exemption blocks.
3. `manual_review_count` is `0` or `1` with explicit report justification.
4. Section-5 field coverage reaches:
   - `931/931` for baseline enrichment fields
   - `906/906` for caselaw enrichment fields.
5. `ruff check .` and `pytest -q` pass.

## Rollback Plan
1. Keep changes scoped to `legal_ingest/*`, tests, and docs/report artifacts.
2. If enrichment semantics regress, revert Iteration 5 commits and return to Iteration 4 metadata baseline.
