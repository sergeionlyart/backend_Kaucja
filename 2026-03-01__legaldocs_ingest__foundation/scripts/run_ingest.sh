#!/usr/bin/env bash
# Canonical ingest run script.
# Usage: bash scripts/run_ingest.sh [run_id] [artifact_dir] [config]
#
# Examples:
#   bash scripts/run_ingest.sh                    # defaults
#   bash scripts/run_ingest.sh my_run_001         # custom run_id
#   bash scripts/run_ingest.sh my_run ./artifacts_custom configs/config.caslaw_v22.full.yml
set -euo pipefail

RUN_ID="${1:-}"
ARTIFACT_DIR="${2:-}"
CONFIG="${3:-configs/config.caslaw_v22.full.yml}"

OVERRIDE_ARGS=""
if [ -n "$RUN_ID" ]; then
    OVERRIDE_ARGS="$OVERRIDE_ARGS --run-id $RUN_ID"
fi
if [ -n "$ARTIFACT_DIR" ]; then
    OVERRIDE_ARGS="$OVERRIDE_ARGS --artifact-dir $ARTIFACT_DIR"
fi

echo "=== Legal Ingest: Canonical Run ==="
echo "Config: $CONFIG"
echo "Run ID: ${RUN_ID:-<from config>}"
echo "Artifact dir: ${ARTIFACT_DIR:-<from config>}"
echo ""

python -m legal_ingest.cli --env-file .env validate-config --config "$CONFIG"
python -m legal_ingest.cli --env-file .env ensure-indexes --config "$CONFIG"
python -m legal_ingest.cli --env-file .env ingest --config "$CONFIG" $OVERRIDE_ARGS
