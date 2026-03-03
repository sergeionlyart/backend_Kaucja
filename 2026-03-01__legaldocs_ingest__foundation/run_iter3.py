#!/usr/bin/env python3
"""Thin wrapper — canonical ingest is via CLI + YAML config.

Usage:
    python run_iter3.py [--dry-run]

This script is NOT the source of truth for the source list.
The canonical source is: configs/config.caslaw_v22.full.yml
"""
import subprocess
import sys

CONFIG = "configs/config.caslaw_v22.full.yml"
ENV_FILE = ".env"


def main():
    dry = "--dry-run" in sys.argv

    cmds = [
        [sys.executable, "-m", "legal_ingest.cli", "--env-file", ENV_FILE,
         "validate-config", "--config", CONFIG],
        [sys.executable, "-m", "legal_ingest.cli", "--env-file", ENV_FILE,
         "ensure-indexes", "--config", CONFIG],
    ]

    if dry:
        cmds.append(
            [sys.executable, "-m", "legal_ingest.cli", "--env-file", ENV_FILE,
             "dry-run", "--config", CONFIG, "--limit", "5"]
        )
    else:
        cmds.append(
            [sys.executable, "-m", "legal_ingest.cli", "--env-file", ENV_FILE,
             "ingest", "--config", CONFIG]
        )

    for cmd in cmds:
        print(f">>> {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"FAILED with exit code {result.returncode}", file=sys.stderr)
            sys.exit(result.returncode)

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
