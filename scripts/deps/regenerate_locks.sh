#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
RUNTIME_LOCK="$ROOT_DIR/requirements/runtime.lock.txt"
DEV_LOCK="$ROOT_DIR/requirements/dev.lock.txt"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/kaucja-locks.XXXXXX")"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT INT TERM

generate_lock() {
  local profile="$1"
  local install_spec="$2"
  local output_path="$3"
  local venv_dir="$TMP_DIR/${profile}-venv"
  local python_path="$venv_dir/bin/python"
  local pip_path="$venv_dir/bin/pip"

  "$PYTHON_BIN" -m venv "$venv_dir"
  "$python_path" -m pip install --upgrade pip
  "$pip_path" install "$install_spec"

  "$pip_path" freeze --exclude-editable \
    | sed '/^backend-kaucja==/d; /^backend-kaucja @/d' \
    | LC_ALL=C sort > "$output_path"
}

generate_lock "runtime" "." "$RUNTIME_LOCK"
generate_lock "dev" ".[dev]" "$DEV_LOCK"

echo "runtime_lock=$RUNTIME_LOCK"
echo "dev_lock=$DEV_LOCK"
