#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

SUITE="p0"
RUN_ID="${KAUCJA_BROWSER_RUN_ID:-latest}"
RUN_PREPARE=0
PREPARE_ONLY=0

usage() {
  cat <<'EOF'
Usage:
  ./scripts/browser/run_regression.sh [--suite p0|full] [--run-id ID] [--prepare] [--prepare-only]

Options:
  --suite p0|full     Select marker set (default: p0).
  --run-id ID         Artifact/log run identifier (default: latest).
  --prepare           Explicitly run environment preparation before execute.
  --prepare-only      Run only preparation and exit.
  --help              Show this message.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --suite)
      SUITE="${2:-}"
      shift 2
      ;;
    --run-id)
      RUN_ID="${2:-}"
      shift 2
      ;;
    --prepare)
      RUN_PREPARE=1
      shift
      ;;
    --prepare-only)
      RUN_PREPARE=1
      PREPARE_ONLY=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 2
      ;;
  esac
done

if [[ "$SUITE" != "p0" && "$SUITE" != "full" ]]; then
  echo "Unsupported suite: '$SUITE'. Use --suite p0|full"
  exit 2
fi

if [[ -z "$RUN_ID" ]]; then
  echo "Run id must not be empty."
  exit 2
fi

RUN_ID_SAFE="$(echo "$RUN_ID" | tr -c 'A-Za-z0-9_.-' '_')"

if [[ "$RUN_PREPARE" -eq 1 ]]; then
  "$ROOT_DIR/scripts/browser/prepare_env.sh"
fi

if [[ "$PREPARE_ONLY" -eq 1 ]]; then
  echo "prepare_done=true"
  exit 0
fi

export KAUCJA_E2E_MODE="${KAUCJA_E2E_MODE:-true}"
export KAUCJA_DATA_DIR="${KAUCJA_DATA_DIR:-data/e2e}"
export KAUCJA_SQLITE_PATH="${KAUCJA_SQLITE_PATH:-$KAUCJA_DATA_DIR/kaucja_e2e.sqlite3}"
export KAUCJA_GRADIO_SERVER_NAME="${KAUCJA_GRADIO_SERVER_NAME:-127.0.0.1}"
export KAUCJA_GRADIO_SERVER_PORT="${KAUCJA_GRADIO_SERVER_PORT:-7861}"
export KAUCJA_BROWSER_BASE_URL="${KAUCJA_BROWSER_BASE_URL:-http://127.0.0.1:${KAUCJA_GRADIO_SERVER_PORT}}"
export KAUCJA_BROWSER_ARTIFACTS_DIR="${KAUCJA_BROWSER_ARTIFACTS_DIR:-$ROOT_DIR/artifacts/browser/$SUITE/$RUN_ID_SAFE}"
export KAUCJA_BROWSER_APP_LOG_PATH="${KAUCJA_BROWSER_APP_LOG_PATH:-$ROOT_DIR/data/browser_regression_${SUITE}_${RUN_ID_SAFE}_app.log}"
export KAUCJA_RUN_BROWSER_TESTS=1

mkdir -p "$KAUCJA_BROWSER_ARTIFACTS_DIR"
mkdir -p "$(dirname "$KAUCJA_BROWSER_APP_LOG_PATH")"

"$ROOT_DIR/scripts/browser/seed_data.sh"

"$ROOT_DIR/scripts/browser/start_e2e_app.sh" >"$KAUCJA_BROWSER_APP_LOG_PATH" 2>&1 &
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

MARK_EXPR="browser_p0"
if [[ "$SUITE" == "full" ]]; then
  MARK_EXPR="browser_p0 or browser_p1"
fi

pytest -q \
  -o addopts= \
  tests/browser \
  -m "$MARK_EXPR" \
  --junitxml "$KAUCJA_BROWSER_ARTIFACTS_DIR/junit.xml"
