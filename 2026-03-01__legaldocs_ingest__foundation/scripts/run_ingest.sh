#!/usr/bin/env bash

set -e

CONFIG_TARGET=${1:-"configs/config.runtime.yml"}
ENV_TARGET=${2:-".env"}

echo "--- LegalDocs Ingest Pipeline ---"
echo "Target Config: $CONFIG_TARGET"
echo "Target ENV: $ENV_TARGET"

# Step 1: Install runtime requirements locally if script runs 
# Or verify environments
if [ ! -f "$ENV_TARGET" ]; then
    echo "ERROR: Environment file $ENV_TARGET missing. Aborting."
    exit 1
fi

echo "[1/4] Validating Configuration Map..."
python -m legal_ingest.cli --env-file "$ENV_TARGET" validate-config --config "$CONFIG_TARGET"

echo "[2/4] Ensuring MongoDB Target Indexes..."
python -m legal_ingest.cli --env-file "$ENV_TARGET" ensure-indexes --config "$CONFIG_TARGET"

echo "[3/4] Running Main Ingestion Sequence..."
python -m legal_ingest.cli --env-file "$ENV_TARGET" ingest --config "$CONFIG_TARGET"

echo "[4/4] Complete."
echo "Execution artifacts and logs created locally referencing Config directives."
