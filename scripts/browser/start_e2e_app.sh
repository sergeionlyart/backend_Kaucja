#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

export KAUCJA_E2E_MODE="${KAUCJA_E2E_MODE:-true}"
export KAUCJA_DATA_DIR="${KAUCJA_DATA_DIR:-data/e2e}"
export KAUCJA_SQLITE_PATH="${KAUCJA_SQLITE_PATH:-$KAUCJA_DATA_DIR/kaucja_e2e.sqlite3}"
export KAUCJA_GRADIO_SERVER_NAME="${KAUCJA_GRADIO_SERVER_NAME:-127.0.0.1}"
export KAUCJA_GRADIO_SERVER_PORT="${KAUCJA_GRADIO_SERVER_PORT:-7861}"

python -m app.ui.gradio_app
