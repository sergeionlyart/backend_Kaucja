#!/usr/bin/env bash
# Usage: ./scripts/smoke.sh [--strict]
# Runs live provider diagnostics to verify API connections

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
    echo "[!] Virtual environment not found. Please run ./scripts/bootstrap.sh first."
    exit 1
fi

source .venv/bin/activate

python -m app.ops.live_smoke "$@"
