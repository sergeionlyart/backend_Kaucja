# Iteration 5.6: Merge Readiness Report

**Branch**: `exp/iter1-lex-saos-fixes`
**PR**: [#6](https://github.com/sergeionlyart/backend_Kaucja/pull/6)
**Date**: 2026-03-03

## Summary

Legal document ingestion pipeline — production-ready with 38/38 primary sources, browser fallback for EUR-Lex WAF, self-contained CI, deterministic telemetry.

## CI Gate Status

### Required Checks (self-contained, no secrets)

| Check | Role | Evidence |
|-------|------|----------|
| `lint-test` | ruff + pytest (68 tests incl. integration) | MongoDB service container |
| `smoke-mode-a` | 4-source ingest, browser ON | Asserts: `docs_ok>=3`, Playwright tested |
| `smoke-mode-b` | 4-source ingest, browser OFF | Asserts: `browser_attempts==0`, `docs_error>=1` |

### Optional (workflow_dispatch)

| Check | Role |
|-------|------|
| `full-ingest` | 38 sources, needs MONGO_URI/MONGO_DB secrets |

### Evidence Freshness

| Commit | Push Run | PR Run | Timestamp |
|--------|----------|--------|-----------|
| `2af60e1` | [#22624985107](https://github.com/sergeionlyart/backend_Kaucja/actions/runs/22624985107) ✅ | [#22624986643](https://github.com/sergeionlyart/backend_Kaucja/actions/runs/22624986643) ✅ | 2026-03-03T13:32Z |
| `ffddeca` | [#22624358324](https://github.com/sergeionlyart/backend_Kaucja/actions/runs/22624358324) ✅ | [#22624360206](https://github.com/sergeionlyart/backend_Kaucja/actions/runs/22624360206) ✅ | 2026-03-03T13:12Z |

> [!NOTE]
> After this commit is pushed, a new CI run will be triggered. Verify with `scripts/verify_release_gate.py`.

## Artifact Locations

### GitHub Actions (per run)
- `smoke-mode-a-artifacts/`: run_report.json, logs.jsonl, fetch_attempts.jsonl (30-day retention)
- `smoke-mode-b-artifacts/`: same structure

### Local (full 38-source runs from iter5.3)
- `artifacts_iter5_3/runs/iter5_3_mode_a/` — 920/920 OK
- `artifacts_iter5_3/runs/iter5_3_mode_b/` — 910/920 OK

### Reports (committed)
- `docs/reports/iter5_3_release_matrix.md` — full matrix (Mode A/B, stability 3×)
- `docs/reports/iter5_5_release_matrix.md` — CI authority hardening evidence
- `docs/reports/iter5_6_merge_readiness.md` — this document

## Risk / Rollback

| Risk | Mitigation |
|------|------------|
| EUR-Lex WAF evolves | Browser fallback config-gated; disable via `browser_fallback.enabled: false` |
| Playwright CI overhead | ~30s install; chromium cached in self-hosted runners |
| Court server outages | Retry + browser fallback; transient errors don't block pipeline |
| DB schema changes | None — pipeline uses upsert only |

**Rollback**: Revert merge commit. No DB schema changes, no external state mutations.

## Merge Command Sequence

```bash
# 1. Verify release gate
cd 2026-03-01__legaldocs_ingest__foundation
python scripts/verify_release_gate.py

# 2. Merge (squash recommended for clean history)
gh pr merge 6 --squash --subject "feat: Legal docs ingest pipeline — 38/38 production-ready"

# 3. Tag release
git fetch origin main
git checkout main
git pull
git tag -a v0.5.0 -m "Legal ingest pipeline: 38/38 sources, browser fallback, CI"
git push origin v0.5.0

# 4. Post-merge verification
ruff check .
pytest -q
python -m legal_ingest.cli doctor --config configs/config.caslaw_v22.full.yml
```
