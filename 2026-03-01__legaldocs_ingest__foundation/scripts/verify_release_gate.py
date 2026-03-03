#!/usr/bin/env python3
"""Verify release gate: PR open, base matches branch policy, required checks SUCCESS, tree clean.

Branch policy:
  exp/*           -> labs
  feature/*|hotfix/* -> main

Usage:
  python scripts/verify_release_gate.py
  python scripts/verify_release_gate.py --pr 6 --expected-base labs
  python scripts/verify_release_gate.py --no-strict-base   # downgrades base mismatch to WARN
"""

import argparse
import json
import subprocess
import sys


REQUIRED_CHECKS = ["lint-test", "smoke-mode-a", "smoke-mode-b"]

# branch prefix -> expected base
BASE_POLICY = {
    "exp/": "labs",
    "feature/": "main",
    "hotfix/": "main",
}


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def infer_expected_base(branch: str) -> str | None:
    """Return expected base branch from policy, or None if unknown."""
    for prefix, base in BASE_POLICY.items():
        if branch.startswith(prefix):
            return base
    return None


def check_git_clean() -> bool:
    r = run(["git", "status", "--porcelain"])
    if r.stdout.strip():
        print(f"FAIL: working tree not clean:\n{r.stdout.strip()}")
        return False
    print("PASS: working tree clean")
    return True


def check_pr(pr_number: str) -> dict | None:
    r = run(["gh", "pr", "view", pr_number, "--json",
             "state,baseRefName,headRefName,headRefOid,statusCheckRollup"])
    if r.returncode != 0:
        print(f"FAIL: cannot read PR #{pr_number}: {r.stderr.strip()}")
        return None
    data = json.loads(r.stdout)
    if data["state"] != "OPEN":
        print(f"FAIL: PR #{pr_number} state={data['state']}, expected OPEN")
        return None
    print(f"PASS: PR #{pr_number} is OPEN")
    return data


def check_base(pr_data: dict, expected_base: str | None, strict: bool) -> bool:
    actual = pr_data.get("baseRefName", "")
    branch = pr_data.get("headRefName", "")

    if expected_base is None:
        expected_base = infer_expected_base(branch)

    if expected_base is None:
        print(f"WARN: cannot infer expected base for branch '{branch}'")
        return True

    if actual != expected_base:
        msg = f"base='{actual}', expected='{expected_base}' (branch='{branch}')"
        if strict:
            print(f"FAIL: {msg}")
            return False
        else:
            print(f"WARN: {msg}")
            return True

    print(f"PASS: base='{actual}' matches policy for '{branch}'")
    return True


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
    seen: dict[str, str] = {}
    for c in checks:
        name = c.get("name", "")
        conclusion = c.get("conclusion", "UNKNOWN")
        if name in REQUIRED_CHECKS:
            if conclusion == "SUCCESS":
                seen[name] = conclusion
            else:
                print(f"FAIL: {name} = {conclusion} (expected SUCCESS)")
                ok = False
                seen[name] = conclusion

    for name in REQUIRED_CHECKS:
        if name in seen:
            if seen[name] == "SUCCESS":
                print(f"PASS: {name} = SUCCESS")
        else:
            print(f"FAIL: {name} not found in statusCheckRollup")
            ok = False

    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify release gate")
    parser.add_argument("--pr", default="6", help="PR number (default: 6)")
    parser.add_argument("--expected-base", default=None,
                        help="Override expected base branch (default: infer from branch policy)")
    parser.add_argument("--strict-base", action="store_true", default=True,
                        dest="strict_base", help="Fail on base mismatch (default)")
    parser.add_argument("--no-strict-base", action="store_false", dest="strict_base",
                        help="Downgrade base mismatch to WARN")
    args = parser.parse_args()

    print("=" * 60)
    print("Release Gate Verification")
    print("=" * 60)

    results = []

    # 1. Git clean
    results.append(check_git_clean())

    # 2. PR state
    pr_data = check_pr(args.pr)
    results.append(pr_data is not None)

    if pr_data:
        # 3. Base policy
        results.append(check_base(pr_data, args.expected_base, args.strict_base))

        # 4. HEAD match
        results.append(check_head_matches(pr_data))

        # 5. Required checks
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
