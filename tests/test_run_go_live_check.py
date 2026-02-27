import subprocess
import os
import tempfile
from pathlib import Path


def test_run_go_live_check_dry_run_missing_keys():
    repo_root = Path(__file__).resolve().parents[1]
    # Call the actual underlying script to bypass the wrapper's relative pathing
    script_path = repo_root / "scripts" / "release" / "run_go_live_check.sh"

    env = os.environ.copy()
    keys_to_remove = [
        "OPENAI_API_KEY", "GOOGLE_API_KEY", "MISTRAL_API_KEY", 
        "OCR_API_KEY", "KAUCJA_MISTRAL_API_KEY"
    ]
    for k in keys_to_remove:
        if k in env:
            del env[k]

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an empty .env so the script 'sources' it but it adds nothing
        (Path(tmpdir) / ".env").touch()
        
        # Invoke the script from the tempdir.
        # However, the script itself has `cd "$REPO_ROOT"`, which will bring it back to the project root.
        # But `source .env` happens BEFORE the `cd "$REPO_ROOT"` inside the script!
        result = subprocess.run(
            [str(script_path)],
            env=env,
            cwd=tmpdir,
            capture_output=True,
            text=True
        )

    assert result.returncode == 1
    assert "Missing required keys" in result.stdout
    assert "[-] OPENAI_API_KEY is missing" in result.stdout
