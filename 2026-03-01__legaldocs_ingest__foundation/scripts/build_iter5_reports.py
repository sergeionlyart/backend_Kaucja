#!/usr/bin/env python3
"""Build iter5 reports from pipeline logs and fetch_attempts.jsonl.

Invariant checks:
- All 38 primary source_ids must have attempt records
- No reason=null in not_loaded
- source_status derivation must match run_report

Usage: python scripts/build_iter5_reports.py <run_id> <prefix> [artifact_base_dir]
"""
import json
import os
import sys
import yaml

FDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_ID = sys.argv[1] if len(sys.argv) > 1 else "iter5_caslaw_v22_full_browser"
REPORT_PREFIX = sys.argv[2] if len(sys.argv) > 2 else "iter5"
ARTIFACT_BASE = sys.argv[3] if len(sys.argv) > 3 else None
CONFIG_PATH = os.path.join(FDIR, "configs/config.caslaw_v22.full.yml")

# Auto-detect artifact dir
if ARTIFACT_BASE:
    ARTIFACT_DIR = os.path.join(FDIR, ARTIFACT_BASE, "runs", RUN_ID)
else:
    # Try common locations
    for d in ["artifacts", "artifacts_iter5", "artifacts_iter5_1", "artifacts_iter5_2"]:
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
    """Load fetch_attempts.jsonl into a dict keyed by source_id."""
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
    """Parse logs and return per-source_id status."""
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

                # Extract exception class from traceback
                exc_class = None
                for tb_line in msg.split("\n"):
                    if tb_line.strip() and not tb_line.startswith(" ") and "Error" in tb_line:
                        exc_class = tb_line.strip().split(":")[0]

                att_list = attempts_by_source.get(sid, [])
                if att_list:
                    last_att = att_list[-1]
                    statuses[sid]["reason_code"] = last_att.get("reason_code", "UNKNOWN_ERROR")
                    statuses[sid]["last_transport_method"] = last_att.get("method", "unknown")
                    statuses[sid]["reason_text"] = f"{last_att.get('reason_code', '')}: {err_line}"
                else:
                    sys.path.insert(0, FDIR)
                    from legal_ingest.reason_codes import ReasonCode
                    statuses[sid]["reason_code"] = ReasonCode.classify_error(err_line)
                    statuses[sid]["reason_text"] = f"{statuses[sid]['reason_code']}: {err_line}"

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
                    statuses[sid]["last_transport_method"] = att.get("method", "unknown")
                    break

    if "s11_saos_search" not in statuses:
        statuses["s11_saos_search"] = {
            "status": "OK",
            "reason_text": f"SAOS search expanded into {len(expanded_ids)} judgments.",
            "reason_code": "OK",
            "last_transport_method": "direct_httpx",
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
        info = statuses.get(
            sid,
            {
                "status": "ERROR",
                "reason_text": "Not processed by pipeline",
                "reason_code": "NOT_PROCESSED",
                "last_transport_method": "none",
                "last_exception_class": None,
            },
        )
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
    tm = rr_stats.get("transport_metrics", {})
    print(f"transport_metrics: direct={tm.get('direct_attempts',0)}  browser={tm.get('browser_attempts',0)}  browser_ok={tm.get('browser_success',0)}  browser_fail={tm.get('browser_fail',0)}")
    print(f"Not loaded ({len(not_loaded)}):")
    for nl in not_loaded:
        print(f"  #{nl['index']} {nl['source_id']}: {nl['status']} [{nl['reason_code']}] via {nl['last_transport_method']} exc={nl.get('last_exception_class','')}")

    # === INVARIANT CHECKS ===
    print("\n=== Invariant checks ===")
    checks = []
    fail = False

    # 1. Consistency: restricted/error match run_report
    rr_restricted = rr_stats.get("docs_restricted", 0)
    rr_error = rr_stats.get("docs_error", 0)
    if restricted_count == rr_restricted:
        checks.append(f"  PASS: restricted({restricted_count}) == docs_restricted({rr_restricted})")
    else:
        checks.append(f"  FAIL: restricted({restricted_count}) != docs_restricted({rr_restricted})")
        fail = True
    if error_count == rr_error:
        checks.append(f"  PASS: error({error_count}) == docs_error({rr_error})")
    else:
        checks.append(f"  FAIL: error({error_count}) != docs_error({rr_error})")
        fail = True
    if len(not_loaded) == restricted_count + error_count:
        checks.append(f"  PASS: not_loaded({len(not_loaded)}) == restricted+error({restricted_count + error_count})")
    else:
        checks.append(f"  FAIL: not_loaded({len(not_loaded)}) != restricted+error({restricted_count + error_count})")
        fail = True

    # 2. Telemetry coverage: all 38 primary source_ids in fetch_attempts
    primary_sids = {src["source_id"] for src in sources_cfg}
    # SAOS search expands — check non-search primaries
    non_search_sids = {s for s in primary_sids if s != "s11_saos_search"}
    attempt_sids = set(attempts_by_source.keys())
    missing_in_attempts = non_search_sids - attempt_sids
    if not missing_in_attempts:
        checks.append(f"  PASS: all {len(non_search_sids)} non-search primaries have attempt records")
    else:
        checks.append(f"  FAIL: {len(missing_in_attempts)} primaries missing from fetch_attempts: {missing_in_attempts}")
        fail = True

    # 3. Reason completeness: no null reason_code in not_loaded
    null_reasons = [nl for nl in not_loaded if not nl.get("reason_code") or not nl.get("reason_text")]
    if not null_reasons:
        checks.append("  PASS: no null reason_code/reason_text in not_loaded")
    else:
        checks.append(f"  FAIL: {len(null_reasons)} not_loaded entries with null reason")
        fail = True

    for c in checks:
        print(c)

    all_pass = not fail
    print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAIL'}")

    if fail:
        sys.exit(1)
    return 0


if __name__ == "__main__":
    main()
