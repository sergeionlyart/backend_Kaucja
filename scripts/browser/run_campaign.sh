#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

SUITE="p0"
ITERATIONS=1
RUN_PREPARE=0

usage() {
  cat <<'EOF'
Usage:
  ./scripts/browser/run_campaign.sh --suite p0|full --iterations N [--prepare]

Options:
  --suite p0|full     Browser suite marker group to run.
  --iterations N      Number of repeated runs (N >= 1).
  --prepare           Run explicit environment preparation once before campaign.
  --help              Show this message.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --suite)
      SUITE="${2:-}"
      shift 2
      ;;
    --iterations)
      ITERATIONS="${2:-}"
      shift 2
      ;;
    --prepare)
      RUN_PREPARE=1
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

if ! [[ "$ITERATIONS" =~ ^[0-9]+$ ]] || (( ITERATIONS < 1 )); then
  echo "Iterations must be integer >= 1. Got: '$ITERATIONS'"
  exit 2
fi

if [[ "$RUN_PREPARE" -eq 1 ]]; then
  "$ROOT_DIR/scripts/browser/run_regression.sh" --prepare-only
fi

CAMPAIGN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
CAMPAIGN_ROOT="${KAUCJA_BROWSER_CAMPAIGN_ROOT:-$ROOT_DIR/artifacts/browser/campaign}/${SUITE}_${CAMPAIGN_ID}"
mkdir -p "$CAMPAIGN_ROOT"

for ((i = 1; i <= ITERATIONS; i++)); do
  ITER_ID="$(printf "iter_%03d" "$i")"
  ITER_ROOT="$CAMPAIGN_ROOT/$ITER_ID"
  ITER_ARTIFACTS_DIR="$ITER_ROOT/artifacts"
  ITER_APP_LOG="$ITER_ROOT/app.log"
  ITER_STDOUT_LOG="$ITER_ROOT/runner.stdout.log"
  ITER_STDERR_LOG="$ITER_ROOT/runner.stderr.log"
  ITER_META="$ITER_ROOT/iteration.json"

  mkdir -p "$ITER_ARTIFACTS_DIR"

  START_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  START_EPOCH="$(python - <<'PY'
import time
print(f"{time.time():.6f}")
PY
)"

  set +e
  KAUCJA_BROWSER_ARTIFACTS_DIR="$ITER_ARTIFACTS_DIR" \
  KAUCJA_BROWSER_APP_LOG_PATH="$ITER_APP_LOG" \
  "$ROOT_DIR/scripts/browser/run_regression.sh" \
    --suite "$SUITE" \
    --run-id "$ITER_ID" \
    >"$ITER_STDOUT_LOG" \
    2>"$ITER_STDERR_LOG"
  EXIT_CODE=$?
  set -e

  END_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  END_EPOCH="$(python - <<'PY'
import time
print(f"{time.time():.6f}")
PY
)"

  python - <<PY
import json
from pathlib import Path

start_epoch = float("$START_EPOCH")
end_epoch = float("$END_EPOCH")
meta = {
    "iteration": "$ITER_ID",
    "suite": "$SUITE",
    "started_at": "$START_TS",
    "finished_at": "$END_TS",
    "duration_seconds": round(max(end_epoch - start_epoch, 0.0), 6),
    "status": "pass" if int("$EXIT_CODE") == 0 else "fail",
    "exit_code": int("$EXIT_CODE"),
    "junit_path": str(Path("$ITER_ARTIFACTS_DIR") / "junit.xml"),
    "app_log_path": str(Path("$ITER_APP_LOG")),
    "runner_stdout_path": str(Path("$ITER_STDOUT_LOG")),
    "runner_stderr_path": str(Path("$ITER_STDERR_LOG")),
}
Path("$ITER_META").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
PY
done

CAMPAIGN_ROOT_PATH="$CAMPAIGN_ROOT"
CAMPAIGN_SUITE="$SUITE"
export CAMPAIGN_ROOT_PATH
export CAMPAIGN_SUITE

python - <<'PY'
from __future__ import annotations

import json
import os
import statistics
from pathlib import Path
from xml.etree import ElementTree as ET

campaign_root = Path(os.environ["CAMPAIGN_ROOT_PATH"])
suite = os.environ["CAMPAIGN_SUITE"]
iteration_files = sorted(campaign_root.glob("iter_*/iteration.json"))

iterations: list[dict] = []
test_stats: dict[str, dict[str, int]] = {}
failed_iteration_details: list[dict] = []

for file_path in iteration_files:
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    iterations.append(payload)

    junit_path = Path(payload.get("junit_path", ""))
    failed_tests: list[str] = []
    if junit_path.exists():
        root = ET.fromstring(junit_path.read_text(encoding="utf-8"))
        for case in root.findall(".//testcase"):
            name = case.get("name") or "unknown"
            classname = case.get("classname") or "unknown"
            test_id = f"{classname}::{name}"

            failed = case.find("failure") is not None or case.find("error") is not None
            stats = test_stats.setdefault(test_id, {"pass": 0, "fail": 0})
            if failed:
                stats["fail"] += 1
                failed_tests.append(test_id)
            else:
                stats["pass"] += 1

    if payload.get("status") == "fail":
        failed_iteration_details.append(
            {
                "iteration": payload.get("iteration"),
                "exit_code": payload.get("exit_code"),
                "failed_tests": sorted(set(failed_tests)),
                "junit_path": payload.get("junit_path"),
                "app_log_path": payload.get("app_log_path"),
            }
        )

durations = [float(item.get("duration_seconds", 0.0)) for item in iterations]
pass_count = sum(1 for item in iterations if item.get("status") == "pass")
fail_count = len(iterations) - pass_count
flaky_tests = sorted(
    name for name, stats in test_stats.items() if stats.get("pass", 0) > 0 and stats.get("fail", 0) > 0
)

report = {
    "campaign_root": str(campaign_root),
    "suite": suite,
    "iterations_total": len(iterations),
    "pass_count": pass_count,
    "fail_count": fail_count,
    "pass_rate": round(pass_count / len(iterations), 6) if iterations else 0.0,
    "average_duration_seconds": round(statistics.mean(durations), 6) if durations else 0.0,
    "flaky_tests": flaky_tests,
    "failed_iterations": failed_iteration_details,
    "tests": {
        name: {
            "pass": stats.get("pass", 0),
            "fail": stats.get("fail", 0),
        }
        for name, stats in sorted(test_stats.items())
    },
    "iterations": iterations,
}

report_json_path = campaign_root / "report.json"
report_md_path = campaign_root / "report.md"

report_json_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

lines = [
    f"# Browser Campaign Report ({report['suite']})",
    "",
    f"- Campaign root: `{report['campaign_root']}`",
    f"- Iterations: `{report['iterations_total']}`",
    f"- Pass: `{report['pass_count']}`",
    f"- Fail: `{report['fail_count']}`",
    f"- Pass rate: `{report['pass_rate']}`",
    f"- Average duration (s): `{report['average_duration_seconds']}`",
    f"- Flaky tests: `{len(report['flaky_tests'])}`",
]

if report["flaky_tests"]:
    lines.append("")
    lines.append("## Flaky Tests")
    for test_name in report["flaky_tests"]:
        lines.append(f"- `{test_name}`")

if report["failed_iterations"]:
    lines.append("")
    lines.append("## Failed Iterations")
    for item in report["failed_iterations"]:
        lines.append(
            "- "
            f"iteration={item['iteration']} exit_code={item['exit_code']} "
            f"failed_tests={len(item['failed_tests'])}"
        )

report_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(json.dumps(
    {
        "campaign_root": report["campaign_root"],
        "report_json": str(report_json_path),
        "report_md": str(report_md_path),
        "pass_count": report["pass_count"],
        "fail_count": report["fail_count"],
        "flaky_tests": len(report["flaky_tests"]),
    },
    ensure_ascii=False,
))
PY
