#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

TIMESTAMP="${KAUCJA_RELEASE_PREFLIGHT_TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
REPORT_ROOT="${KAUCJA_RELEASE_PREFLIGHT_ROOT:-$ROOT_DIR/artifacts/release_preflight/$TIMESTAMP}"
mkdir -p "$REPORT_ROOT"

STAGES_JSONL="$REPORT_ROOT/stages.jsonl"
: >"$STAGES_JSONL"

STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
START_EPOCH="$(python - <<'PY'
import time
print(f"{time.time():.6f}")
PY
)"

append_stage() {
  local stage_name="$1"
  local stage_status="$2"
  local exit_code="$3"
  local duration_seconds="$4"
  local command_text="$5"
  local log_path="$6"

  STAGE_NAME="$stage_name" \
  STAGE_STATUS="$stage_status" \
  STAGE_EXIT_CODE="$exit_code" \
  STAGE_DURATION_SECONDS="$duration_seconds" \
  STAGE_COMMAND="$command_text" \
  STAGE_LOG_PATH="$log_path" \
  STAGES_JSONL_PATH="$STAGES_JSONL" \
  python - <<'PY'
import json
import os
from pathlib import Path

entry = {
    "command": os.environ["STAGE_COMMAND"],
    "duration_seconds": round(float(os.environ["STAGE_DURATION_SECONDS"]), 6),
    "exit_code": int(os.environ["STAGE_EXIT_CODE"]),
    "log_path": os.environ["STAGE_LOG_PATH"],
    "name": os.environ["STAGE_NAME"],
    "status": os.environ["STAGE_STATUS"],
}

stages_path = Path(os.environ["STAGES_JSONL_PATH"])
with stages_path.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
    handle.write("\n")
PY
}

run_stage() {
  local stage_name="$1"
  shift

  local log_path="$REPORT_ROOT/${stage_name}.log"
  local command_text
  command_text="$(printf '%q ' "$@")"
  command_text="${command_text% }"

  local started_epoch
  local finished_epoch
  local duration_seconds
  local exit_code
  local status

  started_epoch="$(python - <<'PY'
import time
print(f"{time.time():.6f}")
PY
)"

  set +e
  "$@" >"$log_path" 2>&1
  exit_code=$?
  set -e

  finished_epoch="$(python - <<'PY'
import time
print(f"{time.time():.6f}")
PY
)"

  duration_seconds="$(python - <<PY
start = float("$started_epoch")
finish = float("$finished_epoch")
print(f"{max(finish - start, 0.0):.6f}")
PY
)"

  if [[ "$exit_code" -eq 0 ]]; then
    status="pass"
  else
    status="fail"
  fi

  append_stage "$stage_name" "$status" "$exit_code" "$duration_seconds" "$command_text" "$log_path"

  if [[ "$status" == "fail" ]]; then
    echo "[preflight] stage=${stage_name} status=fail log=${log_path}"
    return 1
  fi

  echo "[preflight] stage=${stage_name} status=pass log=${log_path}"
  return 0
}

append_skipped_stage() {
  local stage_name="$1"
  local reason="$2"
  local command_text="$3"

  local log_path="$REPORT_ROOT/${stage_name}.log"
  printf '%s\n' "$reason" >"$log_path"

  append_stage "$stage_name" "skipped" 0 "0.000000" "$command_text" "$log_path"
  echo "[preflight] stage=${stage_name} status=skipped reason=${reason} log=${log_path}"
}

overall_fail=0

if ! run_stage "ruff_check" ruff check .; then
  overall_fail=1
fi

if ! run_stage "pytest_core" pytest -q; then
  overall_fail=1
fi

if ! run_stage \
  "browser_p0" \
  env \
  KAUCJA_BROWSER_ARTIFACTS_DIR="$REPORT_ROOT/browser_p0" \
  KAUCJA_BROWSER_APP_LOG_PATH="$REPORT_ROOT/browser_p0_app.log" \
  ./scripts/browser/run_regression.sh \
  --suite p0 \
  --run-id release-preflight-p0; then
  overall_fail=1
fi

if ! run_stage \
  "browser_full" \
  env \
  KAUCJA_BROWSER_ARTIFACTS_DIR="$REPORT_ROOT/browser_full" \
  KAUCJA_BROWSER_APP_LOG_PATH="$REPORT_ROOT/browser_full_app.log" \
  ./scripts/browser/run_regression.sh \
  --suite full \
  --run-id release-preflight-full; then
  overall_fail=1
fi

LIVE_SMOKE_KEYS_AVAILABLE="$(python - <<'PY'
from app.config.settings import get_settings

settings = get_settings()
has_any_key = bool(
    settings.openai_api_key or settings.google_api_key or settings.mistral_api_key
)
print("1" if has_any_key else "0")
PY
)"

LIVE_SMOKE_JSON="$REPORT_ROOT/live_smoke_report.json"
LIVE_SMOKE_COMMAND="python -m app.ops.live_smoke --required-providers '' --output $LIVE_SMOKE_JSON"
if [[ "$LIVE_SMOKE_KEYS_AVAILABLE" == "1" ]]; then
  if ! run_stage \
    "live_smoke" \
    python -m app.ops.live_smoke \
    --required-providers "" \
    --output "$LIVE_SMOKE_JSON"; then
    echo "[preflight] live_smoke failed but is optional for release gate."
  fi
else
  append_skipped_stage \
    "live_smoke" \
    "Skipped: no provider API keys configured (OPENAI/GOOGLE/MISTRAL)." \
    "$LIVE_SMOKE_COMMAND"
fi

FINISHED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
FINISH_EPOCH="$(python - <<'PY'
import time
print(f"{time.time():.6f}")
PY
)"
TOTAL_DURATION="$(python - <<PY
start = float("$START_EPOCH")
finish = float("$FINISH_EPOCH")
print(f"{max(finish - start, 0.0):.6f}")
PY
)"

REPORT_JSON="$REPORT_ROOT/report.json"
REPORT_MD="$REPORT_ROOT/report.md"

REPORT_ROOT_PATH="$REPORT_ROOT" \
REPORT_JSON_PATH="$REPORT_JSON" \
REPORT_MD_PATH="$REPORT_MD" \
STAGES_JSONL_PATH="$STAGES_JSONL" \
STARTED_AT="$STARTED_AT" \
FINISHED_AT="$FINISHED_AT" \
TOTAL_DURATION="$TOTAL_DURATION" \
OVERALL_FAIL="$overall_fail" \
python - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

report_root = Path(os.environ["REPORT_ROOT_PATH"])
stages_path = Path(os.environ["STAGES_JSONL_PATH"])
report_json = Path(os.environ["REPORT_JSON_PATH"])
report_md = Path(os.environ["REPORT_MD_PATH"])

stages: list[dict[str, object]] = []
for line in stages_path.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    payload = json.loads(line)
    stages.append(payload)

status_counts = {"pass": 0, "fail": 0, "skipped": 0}
optional_stages = {"live_smoke"}
optional_failures = 0
mandatory_failures = 0
for stage in stages:
    stage_status = str(stage.get("status", "fail"))
    stage_name = str(stage.get("name", "unknown"))
    if stage_status in status_counts:
        status_counts[stage_status] += 1
    if stage_status == "fail":
        if stage_name in optional_stages:
            optional_failures += 1
        else:
            mandatory_failures += 1

overall_status = "fail" if mandatory_failures > 0 or int(os.environ["OVERALL_FAIL"]) else "pass"
go_no_go = "GO" if overall_status == "pass" else "NO-GO"

report = {
    "finished_at": os.environ["FINISHED_AT"],
    "go_no_go": go_no_go,
    "overall_status": overall_status,
    "report_root": str(report_root),
    "started_at": os.environ["STARTED_AT"],
    "stages": stages,
    "summary": {
        "fail": status_counts["fail"],
        "mandatory_failures": mandatory_failures,
        "optional_failures": optional_failures,
        "pass": status_counts["pass"],
        "skipped": status_counts["skipped"],
        "total": len(stages),
    },
    "total_duration_seconds": round(float(os.environ["TOTAL_DURATION"]), 6),
}

report_json.write_text(
    json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)

lines: list[str] = [
    "# Release Preflight Report",
    "",
    f"- Status: `{report['overall_status']}`",
    f"- GO/NO-GO: `{report['go_no_go']}`",
    f"- Started at: `{report['started_at']}`",
    f"- Finished at: `{report['finished_at']}`",
    f"- Total duration (s): `{report['total_duration_seconds']}`",
    f"- Report root: `{report['report_root']}`",
    "",
    "## Stage Summary",
    "",
    "| Stage | Status | Duration (s) | Exit code | Log |",
    "|---|---|---:|---:|---|",
]

for stage in stages:
    lines.append(
        "| "
        f"{stage['name']} | {stage['status']} | {stage['duration_seconds']} | "
        f"{stage['exit_code']} | {stage['log_path']} |"
    )

report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(
    json.dumps(
        {
            "overall_status": report["overall_status"],
            "go_no_go": report["go_no_go"],
            "report_json": str(report_json),
            "report_md": str(report_md),
        },
        ensure_ascii=False,
    )
)
PY

if [[ "$overall_fail" -ne 0 ]]; then
  exit 1
fi
