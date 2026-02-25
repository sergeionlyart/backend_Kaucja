#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

export KAUCJA_E2E_MODE="${KAUCJA_E2E_MODE:-true}"
export KAUCJA_DATA_DIR="${KAUCJA_DATA_DIR:-data/e2e}"
export KAUCJA_SQLITE_PATH="${KAUCJA_SQLITE_PATH:-$KAUCJA_DATA_DIR/kaucja_e2e.sqlite3}"

python -m app.ops.seed_e2e_data \
  --db-path "$KAUCJA_SQLITE_PATH" \
  --data-dir "$KAUCJA_DATA_DIR"
