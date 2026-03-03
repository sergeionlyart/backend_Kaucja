#!/usr/bin/env python3
"""Build iter4 reports from pipeline logs.

Status resolution: for each source_id the LAST terminal event wins.
Terminal events:
  - "Document saved successfully" => OK
  - "Restricted content detected"  => RESTRICTED
  - "Error processing source"      => ERROR

Usage: python scripts/build_iter4_reports.py <run_id>
"""
import json
import os
import sys
import yaml

FDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_ID = sys.argv[1] if len(sys.argv) > 1 else "iter4_caslaw_v22_full_final"
LOGS_PATH = os.path.join(FDIR, f"artifacts_iter4/runs/{RUN_ID}/logs.jsonl")
RUN_REPORT_PATH = os.path.join(FDIR, f"artifacts_iter4/runs/{RUN_ID}/run_report.json")
CONFIG_PATH = os.path.join(FDIR, "configs/config.caslaw_v22.full.yml")


def load_config_sources():
    with open(CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg["sources"]


def parse_logs(logs_path, run_id):
    """Parse logs and return per-source_id status using LAST terminal event."""
    statuses = {}  # source_id -> {status, reason, http_status}
    expanded_ids = []

    with open(logs_path, "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            # Only process lines from this run_id
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
                    "reason": "",
                    "http_status": None,
                    "_was_restricted": False,
                }

            # Track restricted flag (set once, never cleared by save)
            if "Restricted content detected" in msg:
                statuses[sid]["_was_restricted"] = True

            # Terminal events — last one wins, but restricted flag is sticky
            if stage == "save" and "Document saved successfully" in msg:
                if statuses[sid]["_was_restricted"]:
                    statuses[sid]["status"] = "RESTRICTED"
                    statuses[sid]["reason"] = "Saved with restricted content (low char count)"
                else:
                    statuses[sid]["status"] = "OK"
                    statuses[sid]["reason"] = "Saved"
            elif "Error processing source" in msg:
                statuses[sid]["status"] = "ERROR"
                statuses[sid]["reason"] = msg.split("\n")[0].strip()[:300]

            if stage == "fetch" and "Fetched source" in msg:
                statuses[sid]["http_status"] = 200

            # Track SAOS expansion
            if sid.startswith("s11_saos_search_"):
                n = sid.replace("s11_saos_search_", "")
                if n not in expanded_ids:
                    expanded_ids.append(n)

    # SAOS search source itself is expanded, not fetched directly
    if "s11_saos_search" not in statuses:
        statuses["s11_saos_search"] = {
            "status": "OK",
            "reason": f"SAOS search expanded into {len(expanded_ids)} judgments.",
            "http_status": None,
        }

    return statuses, expanded_ids


def main():
    sources_cfg = load_config_sources()
    statuses, expanded_ids = parse_logs(LOGS_PATH, RUN_ID)

    entries = []
    not_loaded = []
    for i, src in enumerate(sources_cfg, 1):
        sid = src["source_id"]
        info = statuses.get(
            sid, {"status": "ERROR", "reason": "Not processed by pipeline", "http_status": None}
        )
        e = {
            "index": i,
            "source_id": sid,
            "url": src["url"],
            "fetch_strategy": src["fetch_strategy"],
            "status": info["status"],
            "reason": info["reason"],
            "http_status": info.get("http_status"),
            "run_id": RUN_ID,
        }
        if sid == "s11_saos_search":
            e["expanded_count"] = len(expanded_ids)
        entries.append(e)
        if info["status"] != "OK":
            not_loaded.append(e)

    # Write JSON reports
    os.makedirs(os.path.join(FDIR, "docs/reports"), exist_ok=True)
    with open(os.path.join(FDIR, "docs/reports/iter4_source_status.json"), "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    with open(os.path.join(FDIR, "docs/reports/iter4_not_loaded.json"), "w") as f:
        json.dump(not_loaded, f, indent=2, ensure_ascii=False)

    # Load run_report for cross-check
    with open(RUN_REPORT_PATH, "r") as f:
        run_report = json.load(f)
    rr_stats = run_report.get("stats", {})

    ok_count = sum(1 for e in entries if e["status"] == "OK")
    restricted_count = sum(1 for e in entries if e["status"] == "RESTRICTED")
    error_count = sum(1 for e in entries if e["status"] == "ERROR")
    total_primary = len(entries)

    print(f"=== Run ID: {RUN_ID} ===")
    print(f"Primary sources: OK={ok_count}  RESTRICTED={restricted_count}  ERROR={error_count}  total={total_primary}")
    print(f"SAOS expanded: {len(expanded_ids)}")
    print(f"run_report totals: docs_ok={rr_stats.get('docs_ok')}  docs_restricted={rr_stats.get('docs_restricted')}  docs_error={rr_stats.get('docs_error')}  sources_total={rr_stats.get('sources_total')}")
    print(f"Not loaded ({len(not_loaded)}):")
    for nl in not_loaded:
        print(f"  #{nl['index']} {nl['source_id']}: {nl['status']} — {nl['reason'][:100]}")

    # Consistency check
    print("\n=== Consistency check ===")
    print(f"  primary: OK={ok_count} RESTRICTED={restricted_count} ERROR={error_count}")
    print(f"  run_report: docs_ok={rr_stats.get('docs_ok')} docs_restricted={rr_stats.get('docs_restricted')} docs_error={rr_stats.get('docs_error')}")
    print(f"  not_loaded_count={len(not_loaded)} (RESTRICTED={restricted_count} + ERROR={error_count})")

    rr_restricted = rr_stats.get("docs_restricted", 0)
    rr_error = rr_stats.get("docs_error", 0)

    checks = []
    if restricted_count == rr_restricted:
        checks.append(f"  PASS: restricted_count({restricted_count}) == run_report.docs_restricted({rr_restricted})")
    else:
        checks.append(f"  FAIL: restricted_count({restricted_count}) != run_report.docs_restricted({rr_restricted})")

    if error_count == rr_error:
        checks.append(f"  PASS: error_count({error_count}) == run_report.docs_error({rr_error})")
    else:
        checks.append(f"  FAIL: error_count({error_count}) != run_report.docs_error({rr_error})")

    if len(not_loaded) == restricted_count + error_count:
        checks.append(f"  PASS: not_loaded({len(not_loaded)}) == restricted+error({restricted_count + error_count})")
    else:
        checks.append(f"  FAIL: not_loaded({len(not_loaded)}) != restricted+error({restricted_count + error_count})")

    for c in checks:
        print(c)

    all_pass = all("PASS" in c for c in checks)
    print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAIL'}")


if __name__ == "__main__":
    main()
