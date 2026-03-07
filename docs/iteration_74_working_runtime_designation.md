# Iteration 74: Working Runtime Designation

**Date**: 2026-03-07

## Designation

As of **2026-03-07**, the primary working runtime for local launch is:

- branch target: `main`
- frozen tag: `kaucja-working-main-20260307`

This designation refers to the runtime that includes:

- OpenAI model `gpt-5.4` in the UI and backend provider config
- prompt selection in the UI
- additional plain-text prompt `canonical_prompt_v3_1`
- resizable `Raw LLM Response` output area in Gradio

## Launch Rule

From this date forward, the default launch target for operators and reviewers is `origin/main`
after pulling the merge that contains tag `kaucja-working-main-20260307`.

Preferred launch flow:

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
./scripts/bootstrap.sh
./scripts/start.sh
```

## Verification Baseline

Minimum local verification for this designated runtime:

```bash
ruff check .
pytest -q
curl -I http://127.0.0.1:7400
```

Expected result:

- `ruff check .` passes
- `pytest -q` passes
- Gradio responds on `http://127.0.0.1:7400`
