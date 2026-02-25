#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

GROUP="dev"

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/deps/install_from_lock.sh [--group runtime|dev]

Options:
  --group runtime|dev   Lock group to install (default: dev).
  --help               Show this message.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --group)
      GROUP="${2:-}"
      shift 2
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

if [[ "$GROUP" != "runtime" && "$GROUP" != "dev" ]]; then
  echo "Unsupported group: '$GROUP'. Use runtime|dev."
  exit 2
fi

LOCK_PATH="$ROOT_DIR/requirements/${GROUP}.lock.txt"
if [[ ! -f "$LOCK_PATH" ]]; then
  echo "Lock file not found: $LOCK_PATH"
  echo "Generate locks with ./scripts/deps/regenerate_locks.sh"
  exit 1
fi

python -m pip install --upgrade pip
python -m pip install -r "$LOCK_PATH"
