# Iteration 5.1: Release Candidate Report

**Branch**: `exp/iter1-lex-saos-fixes`
**Config**: `configs/config.caslaw_v22.full.yml` (canonical, no iteration-specific values)
**Date**: 2026-03-03

## KPI: 36/38 OK (Mode A, browser enabled)

2 transient court server disconnects (#23 Orzeczenia MS, #24 Katowice) — external blockers.
All 10 EUR-Lex browser fallbacks succeeded. Browser: 10 attempts, 10 OK, 0 fail.

## Verification: Two Modes

### Mode A: Browser Enabled (run_id: `iter5_1_mode_a`)

```
CLI: python -m legal_ingest.cli --env-file .env ingest \
     --config configs/config.caslaw_v22.full.yml \
     --run-id iter5_1_mode_a --artifact-dir ./artifacts_iter5_1

Pipeline: sources_total=920, docs_ok=918, docs_restricted=0, docs_error=2
Transport: direct_attempts=918, browser_attempts=10, browser_success=10, browser_fail=0
           fallback_trigger_counts: {EURLEX_WAF_CHALLENGE: 10}
```

| Primary Source | Status | Reason |
|---------------|--------|--------|
| #1-22, #25-38 | OK (36) | All loaded |
| #23 s23_orzeczenia_ms | ERROR | EXTERNAL_DISCONNECT (transient) |
| #24 s24_orzeczenia_katowice | ERROR | EXTERNAL_DISCONNECT (transient) |

### Mode B: Browser Disabled

```
CLI: python -m legal_ingest.cli dry-run --config /tmp/config_mode_b.yml
     (browser_fallback.enabled: false)

Result: EUR-Lex → "browser fallback skipped: browser_fallback disabled in config"
        → EURLEX_WAF_CHALLENGE error with no crash
        ELI PDF → OK (272KB)
transport_metrics: {direct_attempts: 1, browser_attempts: 0}
```

## Hardening Changes

### 1. Dependency Bootstrap
- `requirements.txt` + `playwright`
- `scripts/setup_browser_runtime.sh` — pip install + playwright install chromium

### 2. CLI Enhancements
- `doctor` subcommand: MongoDB, Playwright, env keys, browser config validation (JSON output, exit code)
- `--run-id` and `--artifact-dir` overrides on `ingest` command
- Canonical config stays stable, no per-iteration modifications

### 3. Transport Policy (Config-Driven)
```yaml
browser_fallback:
  enabled: true
  allowed_domains: ["eur-lex.europa.eu"]
  browser_timeout_ms: 30000
  browser_retries: 1
  max_browser_fallbacks_per_run: 20
```
- Domain check: only allowed_domains get browser fallback
- Circuit breaker: max_browser_fallbacks_per_run
- `BROWSER_RUNTIME_MISSING`: explicit reason code if Playwright not installed

### 4. Reporting
- `transport_metrics` in `run_report.json`:
  `direct_attempts`, `browser_attempts`, `browser_success`, `browser_fail`, `fallback_trigger_counts`
- Reason codes from `fetch_attempts.jsonl` (not log heuristics)

### 5. Documentation
- `README.md` — architecture, transport ladder, setup/doctor/run, known limitations

## Quality Gates

```
ruff check .    → All checks passed!
pytest -q       → 68 passed
validate-config → Config is valid
doctor          → Overall: PASS
```

## Limitations

- **#23/#24**: Court servers intermittently disconnect. Not in `allowed_domains` for browser fallback.
  Adding `orzeczenia.ms.gov.pl` and `orzeczenia.katowice.sa.gov.pl` to allowed_domains could help.
- **Playwright CI**: Requires `python -m playwright install chromium` in CI setup.
- **EUR-Lex WAF**: Currently bypassed via headless Chromium. Future anti-bot measures may require upgrade.
