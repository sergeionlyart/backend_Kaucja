#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LOCK_ROOT="${KAUCJA_BROWSER_PREPARE_LOCK_DIR:-$ROOT_DIR/.tmp/browser_prepare.lock}"
LOCK_WAIT_SECONDS="${KAUCJA_BROWSER_PREPARE_LOCK_WAIT_SECONDS:-120}"

mkdir -p "$ROOT_DIR/.tmp"
deadline=$((SECONDS + LOCK_WAIT_SECONDS))

while ! mkdir "$LOCK_ROOT" >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    echo "Timeout waiting for browser prepare lock: $LOCK_ROOT"
    exit 1
  fi
  sleep 1
done

cleanup_lock() {
  rmdir "$LOCK_ROOT" >/dev/null 2>&1 || true
}
trap cleanup_lock EXIT INT TERM

python -m pip install -e ".[dev]"
python -m playwright install chromium
