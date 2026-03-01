import argparse
import sys
import os
from dotenv import load_dotenv
from .config import load_config
from pydantic import ValidationError
from .pipeline import run_pipeline
from .store.mongo import ensure_indexes


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

    # dry-run
    p_dry = subparsers.add_parser("dry-run")
    p_dry.add_argument("--config", required=True)
    p_dry.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()

    if os.path.exists(args.env_file):
        load_dotenv(dotenv_path=args.env_file)
    else:
        # Fallback to pure environment variables silently if explicitly named one isn't there
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

    elif args.command == "ingest":
        run_pipeline(config, limit=None)

    elif args.command == "dry-run":
        # dry-run modifies config to effectively dry_run and applies limit
        config.run.dry_run = True
        run_pipeline(config, limit=args.limit)


if __name__ == "__main__":
    main()
