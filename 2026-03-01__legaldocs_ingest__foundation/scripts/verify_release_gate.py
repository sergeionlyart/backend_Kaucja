#!/usr/bin/env python3
"""Verify release gate: PR open, required checks SUCCESS, working tree clean."""

import json
import subprocess
import sys


REQUIRED_CHECKS = ["lint-test", "smoke-mode-a", "smoke-mode-b"]
PR_NUMBER = "6"
EXPECTED_BASE = "main"


def run(cmd: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=capture, text=True)


def check_git_clean() -> bool:
    r = run(["git", "status", "--porcelain"])
    if r.stdout.strip():
        print(f"FAIL: working tree not clean:\n{r.stdout.strip()}")
        return False
    print("PASS: working tree clean")
    return True


def check_pr_open() -> dict | None:
    r = run(["gh", "pr", "view", PR_NUMBER, "--json",
             "state,baseRefName,headRefOid,statusCheckRollup"])
    if r.returncode != 0:
        print(f"FAIL: cannot read PR #{PR_NUMBER}: {r.stderr.strip()}")
        return None
    data = json.loads(r.stdout)
    if data["state"] != "OPEN":
        print(f"FAIL: PR #{PR_NUMBER} state={data['state']}, expected OPEN")
        return None
    print(f"PASS: PR #{PR_NUMBER} is OPEN")
    if EXPECTED_BASE not in data.get("baseRefName", ""):
        print(f"WARN: base={data.get('baseRefName')}, expected contains '{EXPECTED_BASE}'")
    else:
        print(f"PASS: base={data['baseRefName']}")
    return data


def check_head_matches(pr_data: dict) -> bool:
    r = run(["git", "rev-parse", "HEAD"])
    local_head = r.stdout.strip()
    pr_head = pr_data.get("headRefOid", "")
    if local_head != pr_head:
        print(f"FAIL: local HEAD={local_head[:12]} != PR head={pr_head[:12]}")
        return False
    print(f"PASS: HEAD matches PR ({local_head[:12]})")
    return True


def check_required_checks(pr_data: dict) -> bool:
    checks = pr_data.get("statusCheckRollup", [])
    ok = True
    seen = set()
    for c in checks:
        name = c.get("name", "")
        conclusion = c.get("conclusion", "UNKNOWN")
        if name in REQUIRED_CHECKS:
            seen.add(name)
            if conclusion == "SUCCESS":
                print(f"PASS: {name} = {conclusion}")
            else:
                print(f"FAIL: {name} = {conclusion} (expected SUCCESS)")
                ok = False
    missing = set(REQUIRED_CHECKS) - seen
    if missing:
        print(f"FAIL: missing required checks: {missing}")
        ok = False
    return ok


def main() -> int:
    print("=" * 60)
    print("Release Gate Verification")
    print("=" * 60)

    results = []

    # 1. Git clean
    results.append(check_git_clean())

    # 2. PR state
    pr_data = check_pr_open()
    results.append(pr_data is not None)

    if pr_data:
        # 3. HEAD match
        results.append(check_head_matches(pr_data))

        # 4. Required checks
        results.append(check_required_checks(pr_data))

    print("=" * 60)
    if all(results):
        print("RESULT: ALL GATES PASS ✅")
        return 0
    else:
        print("RESULT: GATES FAILED ❌")
        return 1


if __name__ == "__main__":
    sys.exit(main())
