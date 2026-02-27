# Iteration 31.3 - Release Handoff

## Summary
- TechSpec drift resolved completely in code and `TECH_SPEC_MVP.md`.
- Strict OpenAI JSON Schema compatibility enforced inside `canonical_schema.json` removing mapped dynamic keys.
- Adjusted Playwright logic to wait `180` seconds to securely process OpenAI structured outputs on larger docs, resolving go-live timeouts.

## Quality Gates
- `ruff format --check .`: PASS
- `ruff check .`: PASS
- `pytest -q`: PASS (146 tests)
- `run_preflight.sh`: PASS
- `run_go_live_check.sh`: GO (OpenAI + Google + Mistral OCR passed locally on live smoke & playwright ui tests)

## Artifacts
- **Commit Hash:** `3911937`
- **Preflight Run:** `artifacts/release_preflight/20260227T215243Z`
- **Go-Live Run:** `artifacts/go_live/1772229196`

## PR Opening Command
To create the PR, run:
```bash
gh pr create --title "Release Iteration 31.3: Stabilize TechSpec Lock and Strict OpenAI Schema Compliance" --body "\
## Summary
- Reverted mapping objects to strictly typed array-of-objects schemas in canonical configurations and test mocks.
- Ensured strict JSON schema enforcement through complete compliance of \`fact.value\` typing with string/number/boolean/null declarations to bypass OpenAI 400 Bad Requests.
- Enlarged Playwright timeout tolerance to 180s to prevent generation teardowns during large schemas.

## Why
OpenAI's Structured Outputs enforces a zero-ambiguity policy that rejected typeless \`{}\` values and \`additionalProperties\` maps, leading to systematic gate failure. Additionally, the complex schema exceeded the default 120s playwright wait policy on full real-world docs.
 
## Changes
1. **Schema Refactoring:** \`canonical_schema.json\` and \`TECH_SPEC_MVP.md\` refactored to eliminate un-typed values and dynamic maps.
2. **Timeouts:** E2E threshold jumped to 180s in \`run_go_live_check.sh\`.
3. **Tests Sync:** Mocks updated in all unit/integration boundary tests.

## How to Test
Execute \`./scripts/release/run_go_live_check.sh\`

## Risk / Rollback
Low code-logic risk but modifies API communication structure (array vs dict arrays for \`parties\`, \`money\`). The application UI parsing logic remains impervious to these structural API drifts thanks to dynamic checklist rendering.
"
```
