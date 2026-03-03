#!/usr/bin/env python3
"""Build reports from pipeline logs and fetch_attempts.jsonl.

Supports symmetric Mode A / Mode B reporting.
Invariant: all 38 primary source_ids must have attempt records (38/38 coverage).

Usage:
  python scripts/build_iter5_reports.py <run_id> <prefix> <artifact_base_dir> [config_path]

Example:
  python scripts/build_iter5_reports.py iter5_3_mode_a iter5_3_mode_a artifacts_iter5_3
  python scripts/build_iter5_reports.py iter5_3_mode_b iter5_3_mode_b artifacts_iter5_3
"""
import json
import os
import sys
import yaml

FDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_ID = sys.argv[1] if len(sys.argv) > 1 else "auto"
REPORT_PREFIX = sys.argv[2] if len(sys.argv) > 2 else "iter5"
ARTIFACT_BASE = sys.argv[3] if len(sys.argv) > 3 else None
CONFIG_PATH = sys.argv[4] if len(sys.argv) > 4 else os.path.join(
    FDIR, "configs/config.caslaw_v22.full.yml"
)

# Resolve artifact dir
if ARTIFACT_BASE:
    ARTIFACT_DIR = os.path.join(FDIR, ARTIFACT_BASE, "runs", RUN_ID)
else:
    for d in ["artifacts", "artifacts_iter5", "artifacts_iter5_1",
              "artifacts_iter5_2", "artifacts_iter5_3"]:
        candidate = os.path.join(FDIR, d, "runs", RUN_ID)
        if os.path.exists(candidate):
            ARTIFACT_DIR = candidate
            break
    else:
        print(f"ERROR: Cannot find artifact dir for run_id={RUN_ID}", file=sys.stderr)
        sys.exit(1)

LOGS_PATH = os.path.join(ARTIFACT_DIR, "logs.jsonl")
RUN_REPORT_PATH = os.path.join(ARTIFACT_DIR, "run_report.json")
ATTEMPTS_PATH = os.path.join(ARTIFACT_DIR, "fetch_attempts.jsonl")


def load_config_sources():
    with open(CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg["sources"]


def load_attempts(path):
    attempts = {}
    if not os.path.exists(path):
        return attempts
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            sid = d.get("source_id", "")
            if sid not in attempts:
                attempts[sid] = []
            attempts[sid].append(d)
    return attempts


def parse_logs(logs_path, run_id, attempts_by_source):
    statuses = {}
    expanded_ids = []

    with open(logs_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("run_id") != run_id:
                continue
            sid = d.get("source_id")
            if not sid:
                continue

            stage = d.get("stage", "")
            msg = d.get("msg", "")

            if sid not in statuses:
                statuses[sid] = {
                    "status": "UNKNOWN",
                    "reason_text": "",
                    "reason_code": "",
                    "last_transport_method": "direct_httpx",
                    "last_exception_class": None,
                }

            if stage == "save" and "Document saved successfully" in msg:
                statuses[sid]["status"] = "OK"
                statuses[sid]["reason_code"] = "OK"
                statuses[sid]["reason_text"] = "Document saved successfully"
            elif "Error processing source" in msg:
                statuses[sid]["status"] = "ERROR"
                err_line = msg.split("\n")[0].strip()[:300]

                exc_class = None
                for tb_line in msg.split("\n"):
                    if (tb_line.strip() and not tb_line.startswith(" ")
                            and "Error" in tb_line):
                        exc_class = tb_line.strip().split(":")[0]

                att_list = attempts_by_source.get(sid, [])
                if att_list:
                    last_att = att_list[-1]
                    statuses[sid]["reason_code"] = last_att.get(
                        "reason_code", "UNKNOWN_ERROR"
                    )
                    statuses[sid]["last_transport_method"] = last_att.get(
                        "method", "unknown"
                    )
                    statuses[sid]["reason_text"] = (
                        f"{last_att.get('reason_code', '')}: {err_line}"
                    )
                else:
                    sys.path.insert(0, FDIR)
                    from legal_ingest.reason_codes import ReasonCode
                    statuses[sid]["reason_code"] = ReasonCode.classify_error(err_line)
                    statuses[sid]["reason_text"] = (
                        f"{statuses[sid]['reason_code']}: {err_line}"
                    )

                statuses[sid]["last_exception_class"] = exc_class

            if sid.startswith("s11_saos_search_"):
                n = sid.replace("s11_saos_search_", "")
                if n not in expanded_ids:
                    expanded_ids.append(n)

    # Enrich transport method from successful attempts
    for sid, att_list in attempts_by_source.items():
        if sid in statuses:
            for att in reversed(att_list):
                if att.get("final_outcome") == "OK":
                    statuses[sid]["last_transport_method"] = att.get(
                        "method", "unknown"
                    )
                    break

    # s11_saos_search: derive from expansion attempt record or logs
    if "s11_saos_search" not in statuses:
        saos_att = attempts_by_source.get("s11_saos_search", [])
        if saos_att:
            last = saos_att[-1]
            statuses["s11_saos_search"] = {
                "status": "OK" if last.get("final_outcome") == "OK" else "ERROR",
                "reason_text": f"SAOS expansion: {last.get('expanded_count', '?')} judgments",
                "reason_code": last.get("reason_code", "OK"),
                "last_transport_method": "saos_expansion",
                "last_exception_class": None,
            }
        else:
            statuses["s11_saos_search"] = {
                "status": "OK",
                "reason_text": f"SAOS search expanded into {len(expanded_ids)} judgments.",
                "reason_code": "OK",
                "last_transport_method": "saos_expansion",
                "last_exception_class": None,
            }

    return statuses, expanded_ids


def main():
    sources_cfg = load_config_sources()
    attempts_by_source = load_attempts(ATTEMPTS_PATH)
    statuses, expanded_ids = parse_logs(LOGS_PATH, RUN_ID, attempts_by_source)

    entries = []
    not_loaded = []
    for i, src in enumerate(sources_cfg, 1):
        sid = src["source_id"]
        info = statuses.get(sid, {
            "status": "ERROR",
            "reason_text": "Not processed by pipeline",
            "reason_code": "NOT_PROCESSED",
            "last_transport_method": "none",
            "last_exception_class": None,
        })
        e = {
            "index": i,
            "source_id": sid,
            "url": src["url"],
            "fetch_strategy": src["fetch_strategy"],
            "status": info["status"],
            "reason_code": info.get("reason_code", "UNKNOWN_ERROR"),
            "reason_text": info.get("reason_text", "No details available"),
            "last_transport_method": info.get("last_transport_method", "unknown"),
            "last_exception_class": info.get("last_exception_class"),
            "run_id": RUN_ID,
        }
        if sid == "s11_saos_search":
            e["expanded_count"] = len(expanded_ids)
        entries.append(e)
        if info["status"] != "OK":
            not_loaded.append(e)

    # Write JSON reports
    os.makedirs(os.path.join(FDIR, "docs/reports"), exist_ok=True)
    status_path = os.path.join(
        FDIR, f"docs/reports/{REPORT_PREFIX}_source_status.json"
    )
    not_loaded_path = os.path.join(
        FDIR, f"docs/reports/{REPORT_PREFIX}_not_loaded.json"
    )
    with open(status_path, "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    with open(not_loaded_path, "w") as f:
        json.dump(not_loaded, f, indent=2, ensure_ascii=False)

    # Load run_report
    with open(RUN_REPORT_PATH, "r") as f:
        run_report = json.load(f)
    rr_stats = run_report.get("stats", {})

    ok_count = sum(1 for e in entries if e["status"] == "OK")
    restricted_count = sum(1 for e in entries if e["status"] == "RESTRICTED")
    error_count = sum(1 for e in entries if e["status"] == "ERROR")

    print(f"=== Run ID: {RUN_ID} ===")
    print(f"Primary: OK={ok_count}  RESTRICTED={restricted_count}"
          f"  ERROR={error_count}  total={len(entries)}")
    print(f"SAOS expanded: {len(expanded_ids)}")
    rr = rr_stats
    print(f"run_report: docs_ok={rr.get('docs_ok')}"
          f"  docs_restricted={rr.get('docs_restricted')}"
          f"  docs_error={rr.get('docs_error')}"
          f"  sources_total={rr.get('sources_total')}")
    tm = rr.get("transport_metrics", {})
    print(f"transport: direct={tm.get('direct_attempts', 0)}"
          f"  browser={tm.get('browser_attempts', 0)}"
          f"  browser_ok={tm.get('browser_success', 0)}"
          f"  browser_fail={tm.get('browser_fail', 0)}")
    print(f"Not loaded ({len(not_loaded)}):")
    for nl in not_loaded:
        print(f"  #{nl['index']} {nl['source_id']}: {nl['status']}"
              f" [{nl['reason_code']}] via {nl['last_transport_method']}")

    # === INVARIANT CHECKS ===
    print("\n=== Invariant checks ===")
    checks = []
    fail = False

    # 1. Consistency: restricted/error match run_report
    rr_restricted = rr_stats.get("docs_restricted", 0)
    rr_error = rr_stats.get("docs_error", 0)
    c1 = restricted_count == rr_restricted
    checks.append(
        f"  {'PASS' if c1 else 'FAIL'}: restricted({restricted_count})"
        f" {'==' if c1 else '!='} docs_restricted({rr_restricted})"
    )
    if not c1:
        fail = True

    c2 = error_count == rr_error
    checks.append(
        f"  {'PASS' if c2 else 'FAIL'}: error({error_count})"
        f" {'==' if c2 else '!='} docs_error({rr_error})"
    )
    if not c2:
        fail = True

    c3 = len(not_loaded) == restricted_count + error_count
    checks.append(
        f"  {'PASS' if c3 else 'FAIL'}: not_loaded({len(not_loaded)})"
        f" {'==' if c3 else '!='} restricted+error({restricted_count + error_count})"
    )
    if not c3:
        fail = True

    # 2. Telemetry coverage: ALL 38 primary source_ids in fetch_attempts
    primary_sids = {src["source_id"] for src in sources_cfg}
    attempt_sids = set(attempts_by_source.keys())
    missing = primary_sids - attempt_sids
    c4 = len(missing) == 0
    checks.append(
        f"  {'PASS' if c4 else 'FAIL'}: telemetry coverage"
        f" {len(primary_sids) - len(missing)}/{len(primary_sids)} primary source_ids"
        + (f" (missing: {missing})" if missing else "")
    )
    if not c4:
        fail = True

    # 3. Reason completeness: no null reason in not_loaded
    null_reasons = [
        nl for nl in not_loaded
        if not nl.get("reason_code") or not nl.get("reason_text")
    ]
    c5 = len(null_reasons) == 0
    checks.append(
        f"  {'PASS' if c5 else 'FAIL'}: reason completeness"
        f" ({len(null_reasons)} null reasons)"
    )
    if not c5:
        fail = True

    for c in checks:
        print(c)

    print(f"\n  Overall: {'ALL PASS' if not fail else 'SOME FAIL'}")

    if fail:
        sys.exit(1)
    return 0


if __name__ == "__main__":
    main()
