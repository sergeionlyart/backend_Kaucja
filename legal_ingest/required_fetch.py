from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from legal_ingest.backup import run_backup
from legal_ingest.config import ArtifactConfig, utc_timestamp_token
from legal_ingest.http import fetch_binary
from legal_ingest.mongo import MongoRuntime
from legal_ingest.pdf_ingest import parse_pdf_bytes, write_pdf_artifacts
from legal_ingest.source_catalog import REQUIRED_CURRENT_SOURCES, RequiredCurrentSource


def run_required_fetch(
    runtime: MongoRuntime,
    *,
    artifact_config: ArtifactConfig,
    apply_changes: bool,
) -> dict[str, Any]:
    timestamp = utc_timestamp_token()
    report_dir = artifact_config.report_dir("required-fetch", timestamp)
    report_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "generated_at": _utc_now().isoformat(),
        "apply_changes": apply_changes,
        "mongo_db": runtime.config.db_name,
        "report_dir": str(report_dir),
        "actions": [],
        "backup_manifest_path": None,
    }

    if apply_changes:
        backup_manifest = run_backup(runtime, artifact_config=artifact_config)
        report["backup_manifest_path"] = backup_manifest["manifest_path"]

    for source in REQUIRED_CURRENT_SOURCES:
        response = fetch_binary(source.source_url)
        if response.status_code >= 400:
            report["actions"].append(
                {
                    "entry_id": source.entry_id,
                    "doc_uid": source.doc_uid,
                    "action": "error",
                    "status_code": response.status_code,
                    "source_url": source.source_url,
                }
            )
            continue

        parsed = parse_pdf_bytes(response.body, canonical_title=source.canonical_title)
        current_document = runtime.collection("documents").find_one(
            {"doc_uid": source.doc_uid},
            projection={"_id": 0, "current_source_hash": 1, "source_urls": 1},
        )
        source_collection = runtime.collection("document_sources")
        existing_source = source_collection.find_one(
            {"doc_uid": source.doc_uid, "source_hash": parsed.source_hash},
            projection={"_id": 0, "raw_object_path": 1},
        )
        pages_count = runtime.collection("pages").count_documents(
            {"doc_uid": source.doc_uid, "source_hash": parsed.source_hash}
        )
        nodes_count = runtime.collection("nodes").count_documents(
            {"doc_uid": source.doc_uid, "source_hash": parsed.source_hash}
        )

        action = _decide_fetch_action(
            current_document=current_document,
            source=source,
            source_hash=parsed.source_hash,
            existing_source=existing_source,
            pages_count=pages_count,
            nodes_count=nodes_count,
        )

        report_action = {
            "entry_id": source.entry_id,
            "doc_uid": source.doc_uid,
            "action": action,
            "source_url": source.source_url,
            "source_hash": parsed.source_hash,
            "page_count": parsed.page_count,
            "pages_present": pages_count,
            "nodes_present": nodes_count,
        }

        if apply_changes and action != "noop":
            _apply_required_fetch(
                runtime=runtime,
                artifact_config=artifact_config,
                source=source,
                response=response,
                parsed=parsed,
            )
        report["actions"].append(report_action)

    report["summary"] = {
        "noop": sum(1 for item in report["actions"] if item["action"] == "noop"),
        "applied": sum(
            1
            for item in report["actions"]
            if item["action"]
            in {"ingest", "promote_current_source", "repair_parsed_data"}
        ),
        "errors": sum(1 for item in report["actions"] if item["action"] == "error"),
    }
    report_path = report_dir / "required_fetch_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report["report_path"] = str(report_path)
    return report


def _decide_fetch_action(
    *,
    current_document: dict[str, Any] | None,
    source: RequiredCurrentSource,
    source_hash: str,
    existing_source: dict[str, Any] | None,
    pages_count: int,
    nodes_count: int,
) -> str:
    if existing_source and pages_count > 0 and nodes_count > 0:
        if (
            current_document is not None
            and current_document.get("current_source_hash") == source_hash
        ):
            current_urls = current_document.get("source_urls", [])
            if current_urls == [source.source_url]:
                return "noop"
            return "promote_current_source"
        return "promote_current_source"

    if existing_source:
        return "repair_parsed_data"
    return "ingest"


def _apply_required_fetch(
    *,
    runtime: MongoRuntime,
    artifact_config: ArtifactConfig,
    source: RequiredCurrentSource,
    response: Any,
    parsed: Any,
) -> None:
    now = _utc_now()
    pages_payload = [
        page.to_mongo(doc_uid=source.doc_uid, source_hash=parsed.source_hash)
        for page in parsed.pages
    ]
    nodes_payload = [
        node.to_mongo(doc_uid=source.doc_uid, source_hash=parsed.source_hash)
        for node in parsed.nodes
    ]
    document_source_payload = {
        "doc_uid": source.doc_uid,
        "source_hash": parsed.source_hash,
        "source_id": source.source_id,
        "url": source.source_url,
        "final_url": response.url,
        "fetched_at": now,
        "http": {
            "status_code": response.status_code,
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "content_length": response.headers.get("Content-Length"),
        },
        "raw_object_path": None,
        "raw_mime": response.headers.get("Content-Type", parsed.mime),
        "license_tag": source.license_tag,
        "ingested_at": now,
    }
    artifact_paths = write_pdf_artifacts(
        artifact_root=artifact_config.corpus_docs_dir(),
        doc_uid=source.doc_uid,
        source_hash=parsed.source_hash,
        body=response.body,
        document_source=document_source_payload,
        pages=pages_payload,
        nodes=nodes_payload,
    )
    document_source_payload["raw_object_path"] = artifact_paths["raw_object_path"]

    runtime.collection("document_sources").update_one(
        {"doc_uid": source.doc_uid, "source_hash": parsed.source_hash},
        {"$set": document_source_payload},
        upsert=True,
    )

    for page in pages_payload:
        runtime.collection("pages").update_one(
            {
                "doc_uid": source.doc_uid,
                "source_hash": parsed.source_hash,
                "page_index": page["page_index"],
            },
            {"$set": page},
            upsert=True,
        )

    for node in nodes_payload:
        runtime.collection("nodes").update_one(
            {
                "doc_uid": source.doc_uid,
                "source_hash": parsed.source_hash,
                "node_id": node["node_id"],
            },
            {"$set": node},
            upsert=True,
        )

    runtime.collection("documents").update_one(
        {"doc_uid": source.doc_uid},
        {
            "$set": {
                "doc_uid": source.doc_uid,
                "doc_type": source.document_kind,
                "jurisdiction": source.jurisdiction,
                "language": source.language,
                "source_system": source.source_system,
                "title": source.canonical_title,
                "source_urls": [source.source_url],
                "external_ids": source.external_ids,
                "license_tag": source.license_tag,
                "access_status": "OK",
                "current_source_hash": parsed.source_hash,
                "mime": parsed.mime,
                "page_count": parsed.page_count,
                "content_stats": parsed.content_stats,
                "pageindex_tree": parsed.pageindex_tree,
                "updated_at": now,
            },
            "$setOnInsert": {
                "ingested_at": now,
                "date_published": None,
                "date_decision": None,
                "version_label": None,
            },
        },
        upsert=True,
    )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)
