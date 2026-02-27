#!/usr/bin/env bash
# Usage: ./scripts/bootstrap.sh
# Initializes the virtual environment and installs deterministic dependencies

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== Kaucja E2E Bootstrap ==="

if [[ ! -d ".venv" ]]; then
    echo "[+] Creating virtual environment '.venv' with python3..."
    python3 -m venv .venv
else
    echo "[*] Virtual environment '.venv' already exists."
fi

echo "[+] Activating virtual environment..."
source .venv/bin/activate

echo "[+] Installing deterministic dependencies via install_from_lock.sh..."
./scripts/deps/install_from_lock.sh --group dev

echo "[+] Bootstrap complete! You can now start the app with: ./scripts/start.sh"
