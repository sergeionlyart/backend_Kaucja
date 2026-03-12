#!/usr/bin/env bash
# CI-safe wrapper for optional mistral tests.
# Exit codes: 0 (pass/skip), 5 (no tests collected) → 0, others → fail.
set -euo pipefail
cd "$(dirname "$0")/.."
echo "=== Optional: mistral tests ==="
EXIT_CODE=0
python3.11 -m pytest -q -m optional_mistral 2>&1 || EXIT_CODE=$?
if [ "$EXIT_CODE" -eq 0 ]; then
    echo "=== PASS ==="
elif [ "$EXIT_CODE" -eq 5 ]; then
    echo "=== NO TESTS COLLECTED (exit 5 → normalized to 0) ==="
    EXIT_CODE=0
else
    echo "=== FAIL (exit $EXIT_CODE) ==="
fi
exit "$EXIT_CODE"
