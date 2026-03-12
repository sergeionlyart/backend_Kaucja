from __future__ import annotations

import json
from typing import Any

from bson import json_util

from legal_ingest.config import (
    DEFAULT_COLLECTIONS,
    ArtifactConfig,
    utc_now_iso,
    utc_timestamp_token,
)
from legal_ingest.mongo import MongoRuntime


def run_backup(
    runtime: MongoRuntime,
    *,
    artifact_config: ArtifactConfig,
    collections: tuple[str, ...] = DEFAULT_COLLECTIONS,
) -> dict[str, Any]:
    timestamp = utc_timestamp_token()
    backup_dir = artifact_config.backup_dir(timestamp)
    backup_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "generated_at": utc_now_iso(),
        "mongo_db": runtime.config.db_name,
        "backup_dir": str(backup_dir),
        "collections": {},
    }

    for collection_name in collections:
        output_path = backup_dir / f"{collection_name}.jsonl"
        written = 0
        with output_path.open("w", encoding="utf-8") as handle:
            for document in runtime.iter_collection(collection_name):
                handle.write(json_util.dumps(document, ensure_ascii=False))
                handle.write("\n")
                written += 1

        manifest["collections"][collection_name] = {
            "written": written,
            "path": str(output_path),
        }

    manifest_path = backup_dir / "backup_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest
