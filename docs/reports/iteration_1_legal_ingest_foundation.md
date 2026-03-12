## Iteration 1 - legal_ingest foundation slice

### Scope

Foundation-only slice for TechSpec 3.1:
- new read-only `legal_ingest` CLI package;
- repeatable Mongo backup;
- repeatable audit against section 5 / 6 / 7 of TechSpec 3.1;
- versioned migration map for positions 1-38 plus required section 3 additions;
- no in-place Mongo mutations.

### What Was Added

- `legal_ingest/config.py`
- `legal_ingest/mongo.py`
- `legal_ingest/schema.py`
- `legal_ingest/backup.py`
- `legal_ingest/audit.py`
- `legal_ingest/migration_plan.py`
- `legal_ingest/cli.py`
- `legal_ingest/__main__.py`
- `legal_ingest/data/migration_map_v3_1.json`
- `tests/test_legal_ingest_audit.py`

### Commands Run

```bash
python -m legal_ingest migration-plan
python -m legal_ingest audit
python -m legal_ingest backup
ruff check .
pytest -q
```

Primary artifacts:
- audit JSON: `artifacts/legal_ingest/audits/20260307T092914Z/audit_report.json`
- audit Markdown: `artifacts/legal_ingest/audits/20260307T092914Z/audit_report.md`
- backup manifest: `artifacts/legal_ingest/backups/20260307T092919Z/backup_manifest.json`

### Key Findings

- Mongo counts matched the confirmed runtime baseline:
  - `documents=928`
  - `pages=3167`
  - `nodes=6725`
  - `citations=3647`
  - `document_sources=1172`
  - `ingest_runs=25`
- TechSpec 3.1 section 5 schema gap is wide:
  - all `928` documents miss `canonical_title`, `document_kind`, `legal_role`, `source_tier`, `normalized_source_url`, `relevance_score`, `summary_1line`, `issue_tags`, `storage_uri` and the other new required fields.
- Required runtime documents:
  - present canonical: `8`
  - present but noncanonical / wrong-title / wrong-id: `7`
  - hard missing: `3`
- same-case candidates confirmed:
  - `I Ca 56/18`
  - `III Ca 1707/18`
  - `V ACa 599/14`
- section 7 findings confirmed: `7`
  - `sn_pl:V_CSK_480-18`
  - `sn_pl:I_CNP_31-13`
  - `uokik_pl:urlsha:c506ff470f4740ad`
  - `curia_eu:urlsha:54acc341b17f3a57`
  - `curia_eu:urlsha:ef65918198e5ffee`
  - `eurlex_eu:urlsha:252f802534879b95`
  - `uokik_pl:urlsha:5efe92f726049194`
- duplicate `final_url` groups:
  - total groups: `31`
  - multi-doc groups: `8`
  - highest-noise examples: Directive 93/13, `I CNP 31/13`, `V CSK 480/18`, ELI/ISAP/SN mirror duplicates.

### Hard Missing

- `Kodeks postepowania cywilnego`
- `Ustawa o kosztach sadowych w sprawach cywilnych`
- `Ustawa o ochronie konkurencji i konsumentow`

### Present But Need Canonicalization

- `Commission Notice - Guidance on the interpretation and application of Directive 93/13/EEC`
- `C-488/11 Asbeek Brusse and Katarina de Man Garabito`
- `C-243/08 Pannon GSM`
- `Decyzja Prezesa UOKiK RKR-37/2013 (Novis MSK)`
- current consolidated tenants-rights act target is still represented by archive source only
- current consolidated `Kodeks cywilny` target is still represented by archive source only
- `UOKiK Niedozwolone klauzule` exists only under a noncanonical `urlsha` document

### Exact Next Steps For Iteration 2

1. Add / fetch the 3 hard-missing acts into Mongo with official current sources only.
2. Canonicalize the 7 noncanonical required runtime documents by updating metadata in-place instead of creating new docs.
3. Introduce TechSpec 3.1 fields on existing `documents` and fill them deterministically from current metadata plus migration map.
4. Create `same_case_group_id` for `I Ca 56/18`, `III Ca 1707/18`, `V ACa 599/14` and mark portal entries as alias / group members.
5. Reclassify section 7 excluded candidate `uokik_pl:urlsha:5efe92f726049194` out of core runtime.
6. Add article-node coverage for lokator act and KC minimum articles required by section 5.
7. Rebuild `pages`, `nodes`, `citations` only after canonical metadata and required additions are in place.
