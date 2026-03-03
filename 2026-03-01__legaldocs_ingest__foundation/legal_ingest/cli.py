import argparse
import json
import sys
import os
from dotenv import load_dotenv
from .config import load_config
from pydantic import ValidationError
from .pipeline import run_pipeline
from .store.mongo import ensure_indexes


def _check_playwright():
    """Check if Playwright + Chromium are available."""
    try:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        br = pw.chromium.launch(headless=True)
        br.close()
        pw.stop()
        return {"status": "ok", "detail": "Chromium available"}
    except Exception as e:
        return {"status": "missing", "detail": str(e)[:200]}


def _check_mongo(config):
    """Check MongoDB connectivity."""
    try:
        from pymongo import MongoClient
        client = MongoClient(config.mongo.uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        client.close()
        return {"status": "ok", "detail": f"db={config.mongo.db}"}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:200]}


def _check_env_keys():
    """Check required environment variables."""
    required = ["MONGO_URI", "MONGO_DB"]
    optional = ["LEX_SESSION_ID", "MISTRAL_API_KEY"]
    result = {"required": {}, "optional": {}}
    for k in required:
        result["required"][k] = "set" if os.environ.get(k) else "MISSING"
    for k in optional:
        result["optional"][k] = "set" if os.environ.get(k) else "not set"
    return result


def run_doctor(config):
    """Run preflight checks and output machine-readable JSON."""
    checks = {}
    critical_fail = False

    # Playwright + Chromium
    checks["playwright"] = _check_playwright()
    if checks["playwright"]["status"] == "missing":
        # Not critical — pipeline degrades gracefully
        pass

    # MongoDB
    checks["mongodb"] = _check_mongo(config)
    if checks["mongodb"]["status"] != "ok":
        critical_fail = True

    # Environment
    checks["env_keys"] = _check_env_keys()
    for k, v in checks["env_keys"]["required"].items():
        if v == "MISSING":
            critical_fail = True

    # Browser fallback config
    bf = config.run.browser_fallback
    checks["browser_fallback_config"] = {
        "enabled": bf.enabled,
        "allowed_domains": bf.allowed_domains,
        "max_browser_fallbacks_per_run": bf.max_browser_fallbacks_per_run,
    }

    # Overall
    checks["overall"] = "FAIL" if critical_fail else "PASS"

    print(json.dumps(checks, indent=2))
    return 0 if not critical_fail else 1


def main():
    parser = argparse.ArgumentParser(prog="legal_ingest")
    parser.add_argument(
        "--env-file", type=str, default=".env", help="Path to .env file"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate-config
    p_val = subparsers.add_parser("validate-config")
    p_val.add_argument("--config", required=True)

    # ensure-indexes
    p_idx = subparsers.add_parser("ensure-indexes")
    p_idx.add_argument("--config", required=True)

    # ingest
    p_ing = subparsers.add_parser("ingest")
    p_ing.add_argument("--config", required=True)
    p_ing.add_argument("--run-id", type=str, default=None, help="Override run_id from config")
    p_ing.add_argument("--artifact-dir", type=str, default=None, help="Override artifact_dir from config")
    p_ing.add_argument(
        "--strict-ok",
        action="store_true",
        help="Fail with non-zero exit if any document is RESTRICTED or ERROR",
    )

    # dry-run
    p_dry = subparsers.add_parser("dry-run")
    p_dry.add_argument("--config", required=True)
    p_dry.add_argument("--limit", type=int, default=5)

    # doctor
    p_doc = subparsers.add_parser("doctor", help="Preflight runtime checks")
    p_doc.add_argument("--config", required=True)

    args = parser.parse_args()

    if os.path.exists(args.env_file):
        load_dotenv(dotenv_path=args.env_file)
    else:
        pass

    try:
        config = load_config(args.config)
    except ValueError as e:
        print(f"Environment configuration error:\n{e}", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(f"Config validation error:\n{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to load config: {e}", file=sys.stderr)
        sys.exit(1)

    if args.command == "validate-config":
        print("Config is valid.")
        sys.exit(0)

    elif args.command == "ensure-indexes":
        ensure_indexes(config.mongo)

    elif args.command == "doctor":
        exit_code = run_doctor(config)
        sys.exit(exit_code)

    elif args.command == "ingest":
        # Apply CLI overrides
        if args.run_id:
            config.run.run_id = args.run_id
        if args.artifact_dir:
            config.run.artifact_dir = args.artifact_dir

        metrics = run_pipeline(config, limit=None)
        if args.strict_ok:
            if (
                metrics.get("docs_restricted", 0) > 0
                or metrics.get("docs_error", 0) > 0
            ):
                print(
                    "Strict mode failed: Pipeline yielded RESTRICTED or ERROR documents.",
                    file=sys.stderr,
                )
                sys.exit(1)

    elif args.command == "dry-run":
        config.run.dry_run = True
        run_pipeline(config, limit=args.limit)


if __name__ == "__main__":
    main()
