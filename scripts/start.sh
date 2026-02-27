#!/usr/bin/env bash
# Usage: ./scripts/start.sh
# Activates the virtual environment and boots the UI application

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
    echo "[!] Virtual environment not found. Please run ./scripts/bootstrap.sh first."
    exit 1
fi

source .venv/bin/activate

# Execute the entry point, this includes environment checks and port fallback bindings.
python -m app.ui.gradio_app
