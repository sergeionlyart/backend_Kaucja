import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pymongo import MongoClient


def _load_base_source_ids(config_path: str) -> list[str]:
    if not os.path.exists(config_path):
        return []
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return [s.get("source_id") for s in cfg.get("sources", []) if s.get("source_id")]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export MongoDB verification report for a specific ingest run."
    )
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--run-id", default=None)
    parser.add_argument(
        "--output",
        default="docs/reports/mongo_verification_export.json",
    )
    parser.add_argument(
        "--config",
        default="configs/config.full.runtime.yml",
        help="Used only to validate expected base source_ids.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    load_dotenv(args.env_file)

    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    mongo_db = os.environ.get("MONGO_DB")
    if not mongo_db:
        raise ValueError("MONGO_DB is required in environment")

    client = MongoClient(mongo_uri)
    db = client[mongo_db]

    if args.run_id:
        run_doc = db.ingest_runs.find_one({"run_id": args.run_id})
    else:
        run_doc = db.ingest_runs.find_one(sort=[("started_at", -1)])

    if not run_doc:
        raise ValueError("No ingest run found in MongoDB")

    run_id = run_doc["run_id"]
    started_at = run_doc.get("started_at")
    finished_at = run_doc.get("finished_at") or datetime.now(timezone.utc)

    source_rows = list(
        db.document_sources.find(
            {
                "fetched_at": {
                    "$gte": started_at,
                    "$lte": finished_at,
                }
            },
            {"_id": 0, "source_id": 1, "doc_uid": 1, "fetched_at": 1},
        )
    )

    unique_doc_uids = sorted({row["doc_uid"] for row in source_rows})
    docs_cursor = db.documents.find(
        {"doc_uid": {"$in": unique_doc_uids}},
        {
            "_id": 0,
            "doc_uid": 1,
            "access_status": 1,
            "title": 1,
            "doc_type": 1,
            "license_tag": 1,
        },
    )
    docs_map = {d["doc_uid"]: d for d in docs_cursor}

    documents = []
    for row in source_rows:
        doc = docs_map.get(row["doc_uid"], {})
        documents.append(
            {
                "source_id": row["source_id"],
                "doc_uid": row["doc_uid"],
                "access_status": doc.get("access_status", "UNKNOWN"),
                "title": doc.get("title", "UNKNOWN"),
                "doc_type": doc.get("doc_type", "UNKNOWN"),
                "license_tag": doc.get("license_tag", "UNKNOWN"),
            }
        )

    base_source_ids = _load_base_source_ids(args.config)
    observed_source_ids = {d["source_id"] for d in documents}
    base_seen = sorted([sid for sid in base_source_ids if sid in observed_source_ids])
    base_missing = sorted(
        [sid for sid in base_source_ids if sid not in observed_source_ids]
    )
    expanded_source_ids = sorted(
        [sid for sid in observed_source_ids if sid not in set(base_source_ids)]
    )

    export = {
        "mongo_db": mongo_db,
        "run_id": run_id,
        "run_started_at": str(started_at),
        "run_finished_at": str(finished_at),
        "run_stats": run_doc.get("stats", {}),
        "base_sources": {
            "expected_count": len(base_source_ids),
            "seen_count": len(base_seen),
            "missing_count": len(base_missing),
            "seen": base_seen,
            "missing": base_missing,
        },
        "expanded_sources_count": len(expanded_source_ids),
        "expanded_sources": expanded_source_ids,
        "documents_count": len(documents),
        "documents": documents,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)

    print(f"Exported to {output_path}")


if __name__ == "__main__":
    main()
