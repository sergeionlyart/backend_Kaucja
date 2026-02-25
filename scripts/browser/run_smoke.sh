#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

export KAUCJA_E2E_MODE="${KAUCJA_E2E_MODE:-true}"
export KAUCJA_DATA_DIR="${KAUCJA_DATA_DIR:-data/e2e}"
export KAUCJA_SQLITE_PATH="${KAUCJA_SQLITE_PATH:-$KAUCJA_DATA_DIR/kaucja_e2e.sqlite3}"
export KAUCJA_GRADIO_SERVER_NAME="${KAUCJA_GRADIO_SERVER_NAME:-127.0.0.1}"
export KAUCJA_GRADIO_SERVER_PORT="${KAUCJA_GRADIO_SERVER_PORT:-7861}"
export KAUCJA_BROWSER_BASE_URL="${KAUCJA_BROWSER_BASE_URL:-http://127.0.0.1:${KAUCJA_GRADIO_SERVER_PORT}}"
export KAUCJA_RUN_BROWSER_TESTS=1

"$ROOT_DIR/scripts/browser/seed_data.sh"

APP_LOG_PATH="${KAUCJA_BROWSER_APP_LOG_PATH:-$ROOT_DIR/data/browser_smoke_app.log}"
mkdir -p "$(dirname "$APP_LOG_PATH")"

"$ROOT_DIR/scripts/browser/start_e2e_app.sh" >"$APP_LOG_PATH" 2>&1 &
APP_PID=$!

cleanup() {
  if kill -0 "$APP_PID" >/dev/null 2>&1; then
    kill "$APP_PID" >/dev/null 2>&1 || true
    wait "$APP_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

python - <<'PY'
import os
import time
from urllib.error import URLError
from urllib.request import urlopen

url = os.environ["KAUCJA_BROWSER_BASE_URL"]
deadline = time.monotonic() + 45

while time.monotonic() < deadline:
    try:
        with urlopen(url, timeout=3) as response:
            status = int(getattr(response, "status", 200))
            if 200 <= status < 500:
                print(f"app_ready url={url} status={status}")
                raise SystemExit(0)
    except URLError:
        time.sleep(0.5)
    except TimeoutError:
        time.sleep(0.5)

print(f"app_not_ready url={url}")
raise SystemExit(1)
PY

pytest -q tests/browser
