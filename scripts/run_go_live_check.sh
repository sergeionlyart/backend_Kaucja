#!/bin/bash
set -eo pipefail

echo "=========================================================="
echo "          Iteration 28 - GO-LIVE VERIFICATION CHECK       "
echo "=========================================================="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$REPO_ROOT"
cd "$REPO_ROOT"

RUN_TIMESTAMP=$(date +%s)
REPORT_DIR="artifacts/go_live/${RUN_TIMESTAMP}"
mkdir -p "$REPORT_DIR"
FINAL_REPORT_JSON="$REPORT_DIR/report.json"
FINAL_REPORT_MD="$REPORT_DIR/report.md"

echo "1. Checking Core Environment API Boundaries..."

MISSING_KEYS=0
if [ -z "$OPENAI_API_KEY" ]; then echo "[-] OPENAI_API_KEY is missing"; MISSING_KEYS=1; else echo "[+] OPENAI_API_KEY is present"; fi
if [ -z "$GOOGLE_API_KEY" ]; then echo "[-] GOOGLE_API_KEY is missing"; MISSING_KEYS=1; else echo "[+] GOOGLE_API_KEY is present"; fi
if [ -z "$MISTRAL_API_KEY" ] && [ -z "$KAUCJA_MISTRAL_API_KEY" ] && [ -z "$OCR_API_KEY" ]; then 
    echo "[-] MISTRAL_API_KEY (or KAUCJA_MISTRAL_API_KEY or OCR_API_KEY) is missing"
    MISSING_KEYS=1
else 
    echo "[+] MISTRAL_API_KEY (OCR) is present"
fi

if [ $MISSING_KEYS -eq 1 ]; then
    echo "ERROR: Missing required keys for Go-Live check. Aborting."
    exit 1
fi

echo "2. Booting Application Server..."
kill -9 $(lsof -ti:7860-7865) 2>/dev/null || true
nohup ./scripts/start.sh > "$REPORT_DIR/server.log" 2>&1 &
SERVER_PID=$!

echo "Waiting 5 seconds for Gradio to bind..."
sleep 5

if ! kill -0 $SERVER_PID 2>/dev/null; then
  echo "ERROR: Server failed to start. View $REPORT_DIR/server.log"
  exit 1
fi

echo "3. Executing Strict Policy Live Smoke Probes..."
source .venv/bin/activate
if ! python app/ops/live_smoke.py --strict --required-providers openai,google,mistral_ocr --output "$REPORT_DIR/smoke_report.json"; then
    echo "ERROR: Live smoke probes failed or timed out!"
    cat "$REPORT_DIR/smoke_report.json"
    kill -9 $(lsof -ti:7860-7865) 2>/dev/null || true
    exit 2
fi
echo "[+] Live Smoke Validation Passed."

echo "4. Executing Full Real E2E Playwright Automation..."
E2E_JSON="$REPORT_DIR/e2e_report.json"
if ! python scripts/browser/real_e2e.py \
    --base-url "http://127.0.0.1:7860" \
    --file-path "$REPO_ROOT/fixtures/1/Faktura PGE.pdf" \
    --providers "openai,google" \
    --timeout-seconds 120 \
    --output-report "$E2E_JSON"; then
    echo "ERROR: E2E Playwright execution crashed!"
    kill -9 $(lsof -ti:7860-7865) 2>/dev/null || true
    exit 3
fi

echo "5. Validating Application Artifacts Output Correctness..."

E2E_OVERALL=$(cat "$E2E_JSON" | python -c "import sys, json; print(json.load(sys.stdin)['overall_status'])")
if [ "$E2E_OVERALL" != "pass" ]; then
    echo "ERROR: E2E Playwright recorded logic failures!"
    cat "$E2E_JSON"
    kill -9 $(lsof -ti:7860-7865) 2>/dev/null || true
    exit 4
fi

validate_run() {
    local provider=$1
    local run_id=$2
    if [ "$run_id" == "null" ] || [ -z "$run_id" ]; then
        echo "ERROR: Provider $provider failed to generate a Run ID!"
        kill -9 $(lsof -ti:7860-7865) 2>/dev/null || true
        exit 5
    fi

    # Find the session directory that contains this run_id
    SESSION_DIR=$(find "$REPO_ROOT/data/sessions" -type d -name "$run_id" | head -n 1)
    
    if [ -z "$SESSION_DIR" ]; then
        echo "ERROR: Run ID $run_id for $provider not found in local disk!"
        kill -9 $(lsof -ti:7860-7865) 2>/dev/null || true
        exit 5
    fi

    echo "  - Checking $provider artifacts at $SESSION_DIR..."
    for f in "run.json" "logs/run.log" "llm/response_parsed.json" "llm/validation.json"; do
        if [ ! -f "$SESSION_DIR/$f" ]; then
            echo "ERROR: Missing Required Artifact $f for Provider $provider"
            kill -9 $(lsof -ti:7860-7865) 2>/dev/null || true
            exit 6
        fi
    done
    
    # Check for combined MD which is nested dynamically under documents/<id>/ocr/combined.md
    if ! find "$SESSION_DIR/documents" -type f -name "combined.md" | read; then
        echo "ERROR: Missing Required Artifact combined.md for Provider $provider"
        kill -9 $(lsof -ti:7860-7865) 2>/dev/null || true
        exit 6
    fi
    echo "  [+] $provider artifacts confirmed present and valid."
}

OPENAI_RUN_ID=$(cat "$E2E_JSON" | python -c "import sys, json; d=json.load(sys.stdin); print(next((p['run_id'] for p in d['providers'] if p['provider'] == 'openai'), 'null'))")
validate_run "openai" "$OPENAI_RUN_ID"

GOOGLE_RUN_ID=$(cat "$E2E_JSON" | python -c "import sys, json; d=json.load(sys.stdin); print(next((p['run_id'] for p in d['providers'] if p['provider'] == 'google'), 'null'))")
validate_run "google" "$GOOGLE_RUN_ID"

echo "6. Saving Final Consolidated Reports..."
cat <<EOF > "$FINAL_REPORT_JSON"
{
  "timestamp": "$RUN_TIMESTAMP",
  "go_no_go": "GO",
  "smoke_report": "$REPORT_DIR/smoke_report.json",
  "e2e_report": "$REPORT_DIR/e2e_report.json"
}
EOF

cat <<EOF > "$FINAL_REPORT_MD"
# Go-Live Verification Check

**Status:** GO 🟢
**Timestamp:** $RUN_TIMESTAMP

All backend integrations and physical browser E2E workflows executed correctly against real APIs.

- **Smoke Report:** \`$REPORT_DIR/smoke_report.json\`
- **E2E Playwright Run:** \`$REPORT_DIR/e2e_report.json\`
EOF

echo ""
echo "=========================================================="
echo "                  FINAL VERDICT: GO                       "
echo "=========================================================="
echo "Report JSON: $FINAL_REPORT_JSON"
echo "Report MD: $FINAL_REPORT_MD"

# Teardown
kill -9 $(lsof -ti:7860-7865) 2>/dev/null || true
exit 0
