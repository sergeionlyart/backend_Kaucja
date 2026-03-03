#!/usr/bin/env python3
"""Targeted recovery probe for problematic sources.

Runs 3 rounds with exponential backoff. For each source:
- SAOS judgments (#12-21): tries API→HTML with maintenance detection.
- EUR-Lex (#25-34): direct fetch with WAF challenge detection.
- Katowice (#24): direct fetch with extended timeout.
- UOKiK (#35): direct fetch with extended timeout.

Writes per-source results to docs/reports/iter4_4_recovery_probes.json.

Usage:
    cd 2026-03-01__legaldocs_ingest__foundation
    source venv/bin/activate
    python scripts/recover_iter4_sources.py
"""
import json
import os
import sys
import time
import httpx

FDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, FDIR)

from legal_ingest.fetch import (  # noqa: E402
    is_saos_maintenance,
    is_eurlex_waf_challenge,
)

RECOVERY_TARGETS = [
    {"source_id": "s12_saos_171957", "saos_id": "171957", "type": "saos"},
    {"source_id": "s13_saos_205996", "saos_id": "205996", "type": "saos"},
    {"source_id": "s14_saos_279345", "saos_id": "279345", "type": "saos"},
    {"source_id": "s15_saos_330695", "saos_id": "330695", "type": "saos"},
    {"source_id": "s16_saos_346698", "saos_id": "346698", "type": "saos"},
    {"source_id": "s17_saos_472812", "saos_id": "472812", "type": "saos"},
    {"source_id": "s18_saos_486542", "saos_id": "486542", "type": "saos"},
    {"source_id": "s19_saos_487012", "saos_id": "487012", "type": "saos"},
    {"source_id": "s20_saos_505310", "saos_id": "505310", "type": "saos"},
    {"source_id": "s21_saos_521555", "saos_id": "521555", "type": "saos"},
    {
        "source_id": "s24_orzeczenia_katowice",
        "url": "https://orzeczenia.katowice.sa.gov.pl/content/$N/151500000002503_V_ACa_000599_2014_Uz_2015-02-18_001",
        "type": "direct",
    },
    {
        "source_id": "s25_eurlex_dir13",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32011L0083",
        "type": "eurlex",
    },
    {
        "source_id": "s31_curia_137830",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415",
        "type": "eurlex",
    },
    {
        "source_id": "s35_uokik_dec",
        "url": "https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/43104c28a7a1be23c1257eac006d8dd4/6168c41ed23328e8c1257ec6007ba3ca/$FILE/RKR-37-2013%20Novis%20MSK.pdf",
        "type": "direct",
    },
]

MAX_ROUNDS = 3
BACKOFF_SECONDS = [10, 30, 60]
TIMEOUT = 30


def probe_saos(saos_id: str, timeout: int = TIMEOUT) -> dict:
    """Probe SAOS API + HTML for a judgment."""
    result = {"api_status": None, "html_status": None, "maintenance": None, "bytes": None, "error": None}
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        try:
            api_url = f"https://www.saos.org.pl/api/judgments/{saos_id}"
            resp = client.get(api_url)
            result["api_status"] = resp.status_code
            ct = resp.headers.get("content-type", "")
            if "application/json" in ct and not is_saos_maintenance(resp.content):
                result["maintenance"] = False
                result["bytes"] = len(resp.content)
                return result
            result["maintenance"] = is_saos_maintenance(resp.content)
        except Exception as e:
            result["api_status"] = f"ERR: {type(e).__name__}"

        try:
            html_url = f"https://www.saos.org.pl/judgments/{saos_id}"
            resp_html = client.get(html_url)
            result["html_status"] = resp_html.status_code
            result["bytes"] = len(resp_html.content)
            result["maintenance"] = is_saos_maintenance(resp_html.content)
        except Exception as e:
            result["html_status"] = f"ERR: {type(e).__name__}"
            result["error"] = str(e)[:200]

    return result


def probe_eurlex(url: str, timeout: int = TIMEOUT) -> dict:
    """Probe EUR-Lex with WAF challenge detection."""
    result = {"http_status": None, "bytes": None, "waf_challenge": None, "error": None}
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            result["http_status"] = resp.status_code
            result["bytes"] = len(resp.content)
            result["waf_challenge"] = is_eurlex_waf_challenge(
                str(resp.url), resp.status_code, resp.content
            )
    except Exception as e:
        result["http_status"] = f"ERR: {type(e).__name__}"
        result["error"] = str(e)[:200]
    return result


def probe_direct(url: str, timeout: int = TIMEOUT) -> dict:
    """Probe a direct URL."""
    result = {"http_status": None, "bytes": None, "error": None}
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            result["http_status"] = resp.status_code
            result["bytes"] = len(resp.content)
    except Exception as e:
        result["http_status"] = f"ERR: {type(e).__name__}"
        result["error"] = str(e)[:200]
    return result


def main():
    all_results = {}

    for round_num in range(1, MAX_ROUNDS + 1):
        print(f"\n=== Round {round_num}/{MAX_ROUNDS} ===")

        for target in RECOVERY_TARGETS:
            sid = target["source_id"]
            if sid in all_results and all_results[sid].get("final_status") == "OK":
                continue

            if target["type"] == "saos":
                probe = probe_saos(target["saos_id"])
                status = "OK" if probe.get("maintenance") is False and probe.get("bytes", 0) > 1500 else "SAOS_MAINTENANCE"
                probe["probe_type"] = "saos"
            elif target["type"] == "eurlex":
                probe = probe_eurlex(target["url"])
                if probe.get("waf_challenge"):
                    status = "EURLEX_WAF_CHALLENGE"
                elif isinstance(probe.get("http_status"), int) and probe["http_status"] == 200 and probe.get("bytes", 0) > 500:
                    status = "OK"
                elif probe.get("error"):
                    status = "ERROR"
                else:
                    status = "EURLEX_WAF_CHALLENGE"
                probe["probe_type"] = "eurlex"
            else:
                probe = probe_direct(target["url"])
                if isinstance(probe.get("http_status"), int) and probe["http_status"] == 200:
                    status = "OK"
                elif probe.get("error") and "timed out" in probe["error"].lower():
                    status = "EXTERNAL_TIMEOUT"
                elif probe.get("error") and "illegal header" in probe["error"].lower():
                    status = "EXTERNAL_MALFORMED_HEADERS"
                else:
                    status = "ERROR"
                probe["probe_type"] = "direct"

            probe["round"] = round_num
            probe["final_status"] = status

            if sid not in all_results or status == "OK":
                all_results[sid] = probe

            err_str = (probe.get("error") or "-")[:60]
            print(f"  {sid}: {status} (bytes={probe.get('bytes')}, err={err_str})")

        if round_num < MAX_ROUNDS:
            wait = BACKOFF_SECONDS[round_num - 1]
            all_ok = all(r.get("final_status") == "OK" for r in all_results.values())
            if all_ok:
                print("\nAll recovered! Stopping early.")
                break
            print(f"\nWaiting {wait}s before next round...")
            time.sleep(wait)

    out_path = os.path.join(FDIR, "docs/reports/iter4_4_recovery_probes.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    print("\n=== Summary ===")
    ok = sum(1 for r in all_results.values() if r.get("final_status") == "OK")
    not_ok = len(all_results) - ok
    print(f"Recovered: {ok}/{len(all_results)}")
    print(f"Still failing: {not_ok}/{len(all_results)}")
    for sid, r in all_results.items():
        if r.get("final_status") != "OK":
            print(f"  {sid}: {r.get('final_status')} — {(r.get('error') or 'see details')[:80]}")

    print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
