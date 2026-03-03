#!/usr/bin/env bash
# Setup browser runtime for legal-ingest pipeline.
# Usage: bash scripts/setup_browser_runtime.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Legal Ingest: Browser Runtime Setup ==="

# 1. Install Python dependencies
echo "[1/3] Installing Python dependencies..."
pip install -r "$PROJECT_DIR/requirements.txt"

# 2. Install Playwright Chromium
echo "[2/3] Installing Playwright Chromium browser..."
python -m playwright install chromium

# 3. Verify
echo "[3/3] Verifying..."
python -c "from playwright.sync_api import sync_playwright; print('  Playwright: OK')"
python -c "import httpx; print('  httpx: OK')"
python -c "import pymongo; print('  pymongo: OK')"

echo ""
echo "=== Setup complete. Run 'python -m legal_ingest.cli doctor' to verify full runtime. ==="
