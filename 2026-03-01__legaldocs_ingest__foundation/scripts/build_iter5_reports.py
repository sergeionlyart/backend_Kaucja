#!/usr/bin/env python3
"""Build iter5 reports from pipeline logs and fetch_attempts.jsonl.

Status resolution uses canonical reason codes from fetch_attempts.jsonl
when available, falling back to log heuristics.

Usage: python scripts/build_iter5_reports.py [run_id] [prefix]
"""
import json
import os
import sys
import yaml

FDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_ID = sys.argv[1] if len(sys.argv) > 1 else "iter5_caslaw_v22_full_browser"
REPORT_PREFIX = sys.argv[2] if len(sys.argv) > 2 else "iter5"
LOGS_PATH = os.path.join(FDIR, f"artifacts_iter5/runs/{RUN_ID}/logs.jsonl")
RUN_REPORT_PATH = os.path.join(FDIR, f"artifacts_iter5/runs/{RUN_ID}/run_report.json")
ATTEMPTS_PATH = os.path.join(FDIR, f"artifacts_iter5/runs/{RUN_ID}/fetch_attempts.jsonl")
CONFIG_PATH = os.path.join(FDIR, "configs/config.caslaw_v22.full.yml")


def load_config_sources():
    with open(CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg["sources"]


def load_attempts(path):
    """Load fetch_attempts.jsonl into a dict keyed by source_id."""
    attempts = {}  # source_id -> list of attempt dicts
    if not os.path.exists(path):
        return attempts
    with open(path, "r") as f:
        for line in f:
            d = json.loads(line)
            sid = d.get("source_id", "")
            if sid not in attempts:
                attempts[sid] = []
            attempts[sid].append(d)
    return attempts


def parse_logs(logs_path, run_id, attempts_by_source):
    """Parse logs and return per-source_id status."""
    statuses = {}
    expanded_ids = []

    with open(logs_path, "r", encoding="utf-8") as f:
        for line in f:
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
                    "reason": "",
                    "reason_code": "",
                    "http_status": None,
                    "transport_method": "direct_httpx",
                    "_was_restricted": False,
                }

            if "Restricted content detected" in msg:
                statuses[sid]["_was_restricted"] = True
                statuses[sid]["reason_code"] = "RESTRICTED_LOW_CHARS"
            if "SAOS maintenance page detected" in msg:
                statuses[sid]["_was_restricted"] = True
                statuses[sid]["reason_code"] = "SAOS_MAINTENANCE"

            if stage == "save" and "Document saved successfully" in msg:
                if statuses[sid]["_was_restricted"]:
                    statuses[sid]["status"] = "RESTRICTED"
                    statuses[sid]["reason"] = f"Saved with restricted content ({statuses[sid]['reason_code']})"
                else:
                    statuses[sid]["status"] = "OK"
                    statuses[sid]["reason"] = "Saved"
                    statuses[sid]["reason_code"] = "OK"
            elif "Error processing source" in msg:
                statuses[sid]["status"] = "ERROR"
                err_msg = msg.split("\n")[0].strip()[:300]
                # Use reason_code from attempts if available
                att_list = attempts_by_source.get(sid, [])
                if att_list:
                    last_att = att_list[-1]
                    statuses[sid]["reason_code"] = last_att.get("reason_code", "UNKNOWN_ERROR")
                    statuses[sid]["transport_method"] = last_att.get("method", "unknown")
                    statuses[sid]["reason"] = f"{last_att.get('reason_code', '')}: {err_msg}"
                else:
                    # Fallback classification
                    from legal_ingest.reason_codes import ReasonCode
                    statuses[sid]["reason_code"] = ReasonCode.classify_error(err_msg)
                    statuses[sid]["reason"] = f"{statuses[sid]['reason_code']}: {err_msg}"

            if stage == "fetch" and "Fetched source" in msg:
                statuses[sid]["http_status"] = 200

            if sid.startswith("s11_saos_search_"):
                n = sid.replace("s11_saos_search_", "")
                if n not in expanded_ids:
                    expanded_ids.append(n)

    # Enrich with transport method from attempts
    for sid, att_list in attempts_by_source.items():
        if sid in statuses:
            # Use the last successful attempt's method
            for att in reversed(att_list):
                if att.get("final_outcome") == "OK":
                    statuses[sid]["transport_method"] = att.get("method", "unknown")
                    break

    if "s11_saos_search" not in statuses:
        statuses["s11_saos_search"] = {
            "status": "OK",
            "reason": f"SAOS search expanded into {len(expanded_ids)} judgments.",
            "reason_code": "OK",
            "http_status": None,
            "transport_method": "direct_httpx",
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
        info = statuses.get(
            sid, {"status": "ERROR", "reason": "Not processed", "reason_code": "NOT_PROCESSED",
                  "http_status": None, "transport_method": "none"}
        )
        e = {
            "index": i,
            "source_id": sid,
            "url": src["url"],
            "fetch_strategy": src["fetch_strategy"],
            "status": info["status"],
            "reason": info["reason"],
            "reason_code": info.get("reason_code", ""),
            "transport_method": info.get("transport_method", "unknown"),
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
    with open(os.path.join(FDIR, f"docs/reports/{REPORT_PREFIX}_source_status.json"), "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    with open(os.path.join(FDIR, f"docs/reports/{REPORT_PREFIX}_not_loaded.json"), "w") as f:
        json.dump(not_loaded, f, indent=2, ensure_ascii=False)

    # Load run_report
    with open(RUN_REPORT_PATH, "r") as f:
        run_report = json.load(f)
    rr_stats = run_report.get("stats", {})

    ok_count = sum(1 for e in entries if e["status"] == "OK")
    restricted_count = sum(1 for e in entries if e["status"] == "RESTRICTED")
    error_count = sum(1 for e in entries if e["status"] == "ERROR")
    total_primary = len(entries)

    print(f"=== Run ID: {RUN_ID} ===")
    print(f"Primary: OK={ok_count}  RESTRICTED={restricted_count}  ERROR={error_count}  total={total_primary}")
    print(f"SAOS expanded: {len(expanded_ids)}")
    print(f"run_report: docs_ok={rr_stats.get('docs_ok')}  docs_restricted={rr_stats.get('docs_restricted')}  docs_error={rr_stats.get('docs_error')}  sources_total={rr_stats.get('sources_total')}")
    print(f"Not loaded ({len(not_loaded)}):")
    for nl in not_loaded:
        rc = nl.get("reason_code", "")
        tm = nl.get("transport_method", "")
        print(f"  #{nl['index']} {nl['source_id']}: {nl['status']} [{rc}] via {tm}")

    # Fetch attempts summary
    if attempts_by_source:
        browser_attempts = sum(
            1 for sid_atts in attempts_by_source.values()
            for a in sid_atts if a.get("method") == "browser_playwright"
        )
        browser_ok = sum(
            1 for sid_atts in attempts_by_source.values()
            for a in sid_atts
            if a.get("method") == "browser_playwright" and a.get("final_outcome") == "OK"
        )
        print(f"\nFetch attempts: browser_attempts={browser_attempts}, browser_ok={browser_ok}")

    # Consistency check
    print("\n=== Consistency check ===")
    rr_restricted = rr_stats.get("docs_restricted", 0)
    rr_error = rr_stats.get("docs_error", 0)

    checks = []
    if restricted_count == rr_restricted:
        checks.append(f"  PASS: restricted({restricted_count}) == docs_restricted({rr_restricted})")
    else:
        checks.append(f"  FAIL: restricted({restricted_count}) != docs_restricted({rr_restricted})")
    if error_count == rr_error:
        checks.append(f"  PASS: error({error_count}) == docs_error({rr_error})")
    else:
        checks.append(f"  FAIL: error({error_count}) != docs_error({rr_error})")
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
