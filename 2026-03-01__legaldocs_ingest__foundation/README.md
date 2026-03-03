# Legal Ingest — Case Law Ingestion Pipeline

Document ingestion pipeline for Polish and EU legal sources (38 primary sources from `cas_law_V_2.2`).

## Architecture

```
                          ┌─────────────┐
                          │   CLI       │ --run-id, --artifact-dir, doctor
                          └──────┬──────┘
                                 │
                          ┌──────▼──────┐
                          │  Pipeline   │ config + overrides
                          └──────┬──────┘
                                 │
                    ┌────────────▼────────────┐
                    │     Transport Ladder     │
                    │   ┌─────────────────┐   │
                    │   │ 1. direct_httpx  │──── OK → done
                    │   └────────┬────────┘   │
                    │            │ WAF/headers │
                    │   ┌────────▼────────┐   │
                    │   │ 2. browser_pw   │──── OK → done
                    │   │   (Playwright)  │   │
                    │   └─────────────────┘   │
                    └─────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Parse → Normalize     │
                    │   → Save (Mongo + FS)   │
                    └─────────────────────────┘
```

### Transport Ladder

Browser fallback is **policy-driven** via config:
- **`browser_fallback.enabled`** — master switch (default: `true`)
- **`browser_fallback.allowed_domains`** — only these domains get browser fallback
- **`browser_fallback.max_browser_fallbacks_per_run`** — circuit breaker
- Triggers: `EURLEX_WAF_CHALLENGE`, `EXTERNAL_MALFORMED_HEADERS`
- If Playwright is not installed, reason code = `BROWSER_RUNTIME_MISSING`

### Reason Codes

All errors use canonical codes from `legal_ingest/reason_codes.py`:
`EURLEX_WAF_CHALLENGE`, `SAOS_MAINTENANCE`, `EXTERNAL_TIMEOUT`,
`EXTERNAL_MALFORMED_HEADERS`, `BROWSER_RUNTIME_MISSING`, etc.

## Setup

```bash
python -m venv venv && source venv/bin/activate
bash scripts/setup_browser_runtime.sh   # pip install + playwright chromium
cp .env.example .env                     # fill MONGO_URI, MONGO_DB
```

### Preflight Check

```bash
python -m legal_ingest.cli --env-file .env doctor --config configs/config.caslaw_v22.full.yml
```

Outputs machine-readable JSON with checks for: MongoDB, Playwright, env vars, browser_fallback config.

## Run

```bash
# Canonical with CLI overrides (config stays stable):
python -m legal_ingest.cli --env-file .env ingest \
  --config configs/config.caslaw_v22.full.yml \
  --run-id my_run_001 \
  --artifact-dir ./artifacts_my_run

# Or use the helper script:
bash scripts/run_ingest.sh my_run_001 ./artifacts_my_run
```

### CLI Subcommands

| Command | Purpose |
|---------|---------|
| `validate-config` | Validate YAML config |
| `ensure-indexes` | Create MongoDB indexes |
| `ingest` | Run full pipeline (accepts `--run-id`, `--artifact-dir`, `--strict-ok`) |
| `dry-run` | Test with `--limit N` sources |
| `doctor` | Preflight runtime checks |

## Artifacts

Each run produces in `<artifact_dir>/runs/<run_id>/`:
- `run_report.json` — metrics + `transport_metrics`
- `logs.jsonl` — per-source structured logs
- `fetch_attempts.jsonl` — transport ladder telemetry

Report scripts:
```bash
python scripts/build_iter5_reports.py <run_id> <prefix>
```

## Testing

```bash
ruff check .    # linting
pytest -q       # unit + integration tests
```

## CI Prerequisites

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Known Limitations

- **EUR-Lex WAF**: Requires Playwright Chromium for browser fallback (AWS WAF challenge).
- **Katowice**: Server sends malformed `Connection: close\x00` header; works via tenacity retries.
- **SAOS**: Intermittent maintenance pages; explicit `SAOS_MAINTENANCE` detection.
