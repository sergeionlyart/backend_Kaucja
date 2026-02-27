import subprocess
import os
from pathlib import Path


def test_run_go_live_check_dry_run_missing_keys():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_go_live_check.sh"

    env = os.environ.copy()
    if "OPENAI_API_KEY" in env:
        del env["OPENAI_API_KEY"]
    if "GOOGLE_API_KEY" in env:
        del env["GOOGLE_API_KEY"]
    if "MISTRAL_API_KEY" in env:
        del env["MISTRAL_API_KEY"]

    result = subprocess.run([str(script_path)], env=env, capture_output=True, text=True)

    assert result.returncode == 1
    assert "Missing required keys" in result.stdout
    assert "[-] OPENAI_API_KEY is missing" in result.stdout
