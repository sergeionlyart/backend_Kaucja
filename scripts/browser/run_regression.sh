#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

SUITE="p0"
RUN_ID="${KAUCJA_BROWSER_RUN_ID:-latest}"
RUN_PREPARE=0
PREPARE_ONLY=0

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/browser/run_regression.sh [--suite p0|full] [--run-id ID] [--prepare] [--prepare-only]

Options:
  --suite p0|full     Select marker set (default: p0).
  --run-id ID         Artifact/log run identifier (default: latest).
  --prepare           Explicitly run environment preparation before execute.
  --prepare-only      Run only preparation and exit.
  --help              Show this message.
USAGE
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
RUN_STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
COMMIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

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
export KAUCJA_GRADIO_SERVER_PORT="${KAUCJA_GRADIO_SERVER_PORT:-7401}"
export KAUCJA_GRADIO_SERVER_PORT_MAX="${KAUCJA_GRADIO_SERVER_PORT_MAX:-7450}"
export KAUCJA_BROWSER_BASE_URL="${KAUCJA_BROWSER_BASE_URL:-http://127.0.0.1:${KAUCJA_GRADIO_SERVER_PORT}}"
export KAUCJA_BROWSER_ARTIFACTS_DIR="${KAUCJA_BROWSER_ARTIFACTS_DIR:-$ROOT_DIR/artifacts/browser/$SUITE/$RUN_ID_SAFE}"
export KAUCJA_BROWSER_APP_LOG_PATH="${KAUCJA_BROWSER_APP_LOG_PATH:-$ROOT_DIR/data/browser_regression_${SUITE}_${RUN_ID_SAFE}_app.log}"
export KAUCJA_BROWSER_RUNNER_STDOUT_LOG="${KAUCJA_BROWSER_RUNNER_STDOUT_LOG:-$KAUCJA_BROWSER_ARTIFACTS_DIR/runner.stdout.log}"
export KAUCJA_BROWSER_RUNNER_STDERR_LOG="${KAUCJA_BROWSER_RUNNER_STDERR_LOG:-$KAUCJA_BROWSER_ARTIFACTS_DIR/runner.stderr.log}"
export KAUCJA_RUN_BROWSER_TESTS=1

mkdir -p "$KAUCJA_BROWSER_ARTIFACTS_DIR"
mkdir -p "$(dirname "$KAUCJA_BROWSER_APP_LOG_PATH")"
mkdir -p "$(dirname "$KAUCJA_BROWSER_RUNNER_STDOUT_LOG")"
mkdir -p "$(dirname "$KAUCJA_BROWSER_RUNNER_STDERR_LOG")"

: >"$KAUCJA_BROWSER_RUNNER_STDOUT_LOG"
: >"$KAUCJA_BROWSER_RUNNER_STDERR_LOG"

log_info() {
  local message="$1"
  printf '%s\n' "$message"
  printf '%s\n' "$message" >>"$KAUCJA_BROWSER_RUNNER_STDOUT_LOG"
}

log_error() {
  local message="$1"
  printf '%s\n' "$message" >&2
  printf '%s\n' "$message" >>"$KAUCJA_BROWSER_RUNNER_STDERR_LOG"
}

require_non_empty_file() {
  local file_path="$1"
  local label="$2"

  if [[ ! -f "$file_path" ]]; then
    log_error "[runner] diagnostics_missing label=${label} path=${file_path}"
    return 1
  fi

  if [[ ! -s "$file_path" ]]; then
    log_error "[runner] diagnostics_empty label=${label} path=${file_path}"
    return 1
  fi

  return 0
}

log_info "[runner] started_at=${RUN_STARTED_AT} suite=${SUITE} run_id=${RUN_ID_SAFE} commit_sha=${COMMIT_SHA}"
log_info "[runner] env data_dir=${KAUCJA_DATA_DIR} sqlite_path=${KAUCJA_SQLITE_PATH} base_url=${KAUCJA_BROWSER_BASE_URL} artifacts_dir=${KAUCJA_BROWSER_ARTIFACTS_DIR}"
printf '[runner] stderr_initialized suite=%s run_id=%s\n' "$SUITE" "$RUN_ID_SAFE" >>"$KAUCJA_BROWSER_RUNNER_STDERR_LOG"

cat >"$KAUCJA_BROWSER_APP_LOG_PATH" <<APP_BANNER
[browser-runner] started_at=${RUN_STARTED_AT}
[browser-runner] suite=${SUITE}
[browser-runner] run_id=${RUN_ID_SAFE}
[browser-runner] commit_sha=${COMMIT_SHA}
[browser-runner] base_url=${KAUCJA_BROWSER_BASE_URL}
[browser-runner] data_dir=${KAUCJA_DATA_DIR}
[browser-runner] sqlite_path=${KAUCJA_SQLITE_PATH}
[browser-runner] artifacts_dir=${KAUCJA_BROWSER_ARTIFACTS_DIR}
APP_BANNER

RUNNER_FAILURE=0
PYTEST_EXIT=0
DIAGNOSTICS_FAILURE=0

log_info "[runner] seed_data_start"
if ! "$ROOT_DIR/scripts/browser/seed_data.sh" >>"$KAUCJA_BROWSER_RUNNER_STDOUT_LOG" 2>>"$KAUCJA_BROWSER_RUNNER_STDERR_LOG"; then
  RUNNER_FAILURE=1
  log_error "[runner] seed_data_failed"
fi

"$ROOT_DIR/scripts/browser/start_e2e_app.sh" >>"$KAUCJA_BROWSER_APP_LOG_PATH" 2>&1 &
APP_PID=$!

cleanup() {
  if kill -0 "$APP_PID" >/dev/null 2>&1; then
    kill "$APP_PID" >/dev/null 2>&1 || true
    wait "$APP_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

set +e
python - <<'PY' >>"$KAUCJA_BROWSER_RUNNER_STDOUT_LOG" 2>>"$KAUCJA_BROWSER_RUNNER_STDERR_LOG"
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
APP_READY_EXIT=$?
set -e
if [[ "$APP_READY_EXIT" -ne 0 ]]; then
  RUNNER_FAILURE=1
  log_error "[runner] app_ready_check_failed base_url=${KAUCJA_BROWSER_BASE_URL}"
else
  log_info "[runner] app_ready_check_passed base_url=${KAUCJA_BROWSER_BASE_URL}"
fi

MARK_EXPR="browser_p0"
if [[ "$SUITE" == "full" ]]; then
  MARK_EXPR="browser_p0 or browser_p1"
fi

set +e
pytest -q \
  -o addopts= \
  tests/browser \
  -m "$MARK_EXPR" \
  --junitxml "$KAUCJA_BROWSER_ARTIFACTS_DIR/junit.xml" \
  > >(tee -a "$KAUCJA_BROWSER_RUNNER_STDOUT_LOG") \
  2> >(tee -a "$KAUCJA_BROWSER_RUNNER_STDERR_LOG" >&2)
PYTEST_EXIT=$?
set -e
if [[ "$PYTEST_EXIT" -ne 0 ]]; then
  log_error "[runner] pytest_failed suite=${SUITE} exit_code=${PYTEST_EXIT}"
else
  log_info "[runner] pytest_passed suite=${SUITE}"
fi

if [[ ! -s "$KAUCJA_BROWSER_RUNNER_STDERR_LOG" ]]; then
  printf '[runner] stderr_empty_placeholder\n' >>"$KAUCJA_BROWSER_RUNNER_STDERR_LOG"
fi

if ! require_non_empty_file "$KAUCJA_BROWSER_APP_LOG_PATH" "app_log"; then
  DIAGNOSTICS_FAILURE=1
fi
if ! require_non_empty_file "$KAUCJA_BROWSER_ARTIFACTS_DIR/junit.xml" "junit"; then
  DIAGNOSTICS_FAILURE=1
fi
if ! require_non_empty_file "$KAUCJA_BROWSER_RUNNER_STDOUT_LOG" "runner_stdout"; then
  DIAGNOSTICS_FAILURE=1
fi
if ! require_non_empty_file "$KAUCJA_BROWSER_RUNNER_STDERR_LOG" "runner_stderr"; then
  DIAGNOSTICS_FAILURE=1
fi

if [[ "$PYTEST_EXIT" -ne 0 ]]; then
  if ! find "$KAUCJA_BROWSER_ARTIFACTS_DIR" \
    -type f \
    \( -name 'trace.zip' -o -name '*.png' -o -name '*.webm' \) \
    | grep -q .; then
    DIAGNOSTICS_FAILURE=1
    log_error "[runner] diagnostics_missing_failure_artifacts path=${KAUCJA_BROWSER_ARTIFACTS_DIR}"
  fi
fi

FINAL_EXIT=0
if [[ "$PYTEST_EXIT" -ne 0 ]]; then
  FINAL_EXIT="$PYTEST_EXIT"
fi
if [[ "$RUNNER_FAILURE" -ne 0 || "$DIAGNOSTICS_FAILURE" -ne 0 ]]; then
  if [[ "$FINAL_EXIT" -eq 0 ]]; then
    FINAL_EXIT=1
  fi
fi

log_info "[runner] finished suite=${SUITE} run_id=${RUN_ID_SAFE} final_exit=${FINAL_EXIT}"
exit "$FINAL_EXIT"
