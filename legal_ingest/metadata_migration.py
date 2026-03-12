from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Mapping

from legal_ingest.backup import run_backup
from legal_ingest.config import ArtifactConfig, utc_timestamp_token
from legal_ingest.enrichment import build_section5_enrichment
from legal_ingest.migration_plan import load_migration_payload
from legal_ingest.mongo import MongoRuntime
from legal_ingest.normalization import (
    ACT_KINDS,
    ACT_LAYER_FIELDS,
    BROKEN_ARTIFACT_EXCLUSION_REASON,
    build_article_node_inventory,
    build_current_source_index,
    build_curated_entry_indexes,
    build_duplicate_resolution_index,
    build_key_provisions,
    clean_title,
    collect_checksum_validation_issues,
    collect_storage_uri_validation_issues,
    derive_act_id,
    derive_act_short_name,
    derive_external_id,
    entry_target_doc_uid,
    infer_document_kind,
    infer_source_tier,
    is_placeholder_title,
    normalize_url,
    select_source_url,
)

SAME_CASE_GROUPS: dict[str, tuple[str, ...]] = {
    "same_case:i_ca_56_18": (
        "saos_pl:360096",
        "courts_pl:urlsha:20c9c82554a6e7f2",
    ),
    "same_case:iii_ca_1707_18": (
        "saos_pl:385394",
        "courts_pl:urlsha:74cfe0dfc8b4592a",
    ),
    "same_case:v_aca_599_14": (
        "saos_pl:132635",
        "courts_pl:urlsha:9ea678728691b52e",
    ),
}

SAME_CASE_GROUP_BY_DOC_UID = {
    doc_uid: group_id
    for group_id, doc_uids in SAME_CASE_GROUPS.items()
    for doc_uid in doc_uids
}

OPTIONAL_MANAGED_FIELDS = (
    *ACT_LAYER_FIELDS,
    "duplicate_group_id",
    "duplicate_owner_doc_uid",
    "duplicate_role",
    "exclusion_reason",
    "is_search_page",
    "same_case_group_id",
    "superseded_by",
)


def run_metadata_migration(
    runtime: MongoRuntime,
    *,
    artifact_config: ArtifactConfig,
    apply_changes: bool,
    migration_map_path: str | None = None,
    scope: str = "required",
) -> dict[str, Any]:
    timestamp = utc_timestamp_token()
    report_dir = artifact_config.report_dir("metadata-migrate", timestamp)
    report_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "generated_at": _utc_now().isoformat(),
        "apply_changes": apply_changes,
        "scope": scope,
        "mongo_db": runtime.config.db_name,
        "report_dir": str(report_dir),
        "backup_manifest_path": None,
        "document_updates": [],
        "same_case_updates": [],
        "manual_review_items": [],
        "duplicate_groups": [],
    }

    if apply_changes:
        backup_manifest = run_backup(runtime, artifact_config=artifact_config)
        report["backup_manifest_path"] = backup_manifest["manifest_path"]

    payload = load_migration_payload(
        None if migration_map_path is None else migration_map_path
    )
    documents = runtime.load_collection("documents", projection={"_id": 0})
    document_sources = runtime.load_collection(
        "document_sources", projection={"_id": 0}
    )
    pages = runtime.load_collection(
        "pages", projection={"_id": 0, "doc_uid": 1, "page_no": 1, "text": 1}
    )
    docs_by_uid = {
        str(document.get("doc_uid")): document
        for document in documents
        if document.get("doc_uid")
    }
    page_text_by_doc_uid = _build_page_text_index(pages)
    current_sources = build_current_source_index(documents, document_sources)
    curated_by_doc_uid, curated_by_source_url = build_curated_entry_indexes(payload)
    status_hints = {
        doc_uid: str(entry.get("status") or "")
        for doc_uid, entry in curated_by_doc_uid.items()
    }
    duplicate_resolutions, duplicate_groups = build_duplicate_resolution_index(
        documents,
        document_sources,
        curated_doc_uids=set(curated_by_doc_uid),
        status_hints=status_hints,
    )
    report["duplicate_groups"] = duplicate_groups
    act_context = _build_act_context(
        documents=documents,
        current_sources=current_sources,
        curated_by_doc_uid=curated_by_doc_uid,
        curated_by_source_url=curated_by_source_url,
        duplicate_resolutions=duplicate_resolutions,
    )
    target_doc_uids = _resolve_target_doc_uids(
        payload=payload,
        docs_by_uid=docs_by_uid,
        scope=scope,
    )
    article_inventory_cache: dict[tuple[str, str], list[str]] = {}

    for doc_uid in target_doc_uids:
        document = docs_by_uid.get(doc_uid)
        if document is None:
            report["document_updates"].append(
                {
                    "doc_uid": doc_uid,
                    "entry_id": None,
                    "action": "skip_missing_document",
                }
            )
            continue

        current_source = current_sources.get(doc_uid)
        exact_entry = curated_by_doc_uid.get(doc_uid)
        source_entry = _resolve_source_entry(
            document=document,
            current_source=current_source,
            curated_by_source_url=curated_by_source_url,
            duplicate_resolution=duplicate_resolutions.get(doc_uid),
        )
        duplicate_resolution = duplicate_resolutions.get(doc_uid)
        act_context_item = act_context.get(doc_uid)
        owner_doc_uid = _resolve_owner_doc_uid(
            doc_uid=doc_uid,
            duplicate_resolution=duplicate_resolution,
            act_context_item=act_context_item,
        )
        owner_document = docs_by_uid.get(owner_doc_uid) if owner_doc_uid else None
        owner_current_source = (
            current_sources.get(owner_doc_uid) if owner_doc_uid else None
        )
        owner_entry = _resolve_owner_entry(
            owner_document=owner_document,
            owner_current_source=owner_current_source,
            curated_by_doc_uid=curated_by_doc_uid,
            curated_by_source_url=curated_by_source_url,
        )

        desired_payload, manual_review_reasons = _build_document_update(
            runtime=runtime,
            article_inventory_cache=article_inventory_cache,
            page_text_by_doc_uid=page_text_by_doc_uid,
            docs_by_uid=docs_by_uid,
            document=document,
            current_source=current_source,
            exact_entry=exact_entry,
            source_entry=source_entry,
            duplicate_resolution=duplicate_resolution,
            act_context_item=act_context_item,
            owner_document=owner_document,
            owner_current_source=owner_current_source,
            owner_entry=owner_entry,
        )
        set_payload, unset_fields = _compute_document_mutation(
            document=document,
            desired_payload=desired_payload,
        )

        entry_id = (exact_entry or source_entry or {}).get("entry_id")
        if not set_payload and not unset_fields:
            report["document_updates"].append(
                {
                    "doc_uid": doc_uid,
                    "entry_id": entry_id,
                    "action": "noop",
                    "status": document.get("status"),
                    "canonical_doc_uid": document.get("canonical_doc_uid"),
                    "same_case_group_id": document.get("same_case_group_id"),
                }
            )
        else:
            if apply_changes:
                update_command: dict[str, Any] = {
                    "$set": {
                        **set_payload,
                        "updated_at": _utc_now(),
                    }
                }
                if unset_fields:
                    update_command["$unset"] = {
                        field_name: "" for field_name in unset_fields
                    }
                runtime.collection("documents").update_one(
                    {"doc_uid": doc_uid},
                    update_command,
                    upsert=False,
                )
            report["document_updates"].append(
                {
                    "doc_uid": doc_uid,
                    "entry_id": entry_id,
                    "action": "update",
                    "status": set_payload.get("status", document.get("status")),
                    "canonical_doc_uid": set_payload.get(
                        "canonical_doc_uid",
                        document.get("canonical_doc_uid"),
                    ),
                    "same_case_group_id": set_payload.get(
                        "same_case_group_id",
                        document.get("same_case_group_id"),
                    ),
                    "duplicate_role": set_payload.get(
                        "duplicate_role",
                        document.get("duplicate_role"),
                    ),
                }
            )

        if manual_review_reasons:
            report["manual_review_items"].append(
                {
                    "doc_uid": doc_uid,
                    "reasons": manual_review_reasons,
                }
            )

    for group_id, doc_uids in SAME_CASE_GROUPS.items():
        planned_doc_uids: list[str] = []
        noop_doc_uids: list[str] = []
        for doc_uid in doc_uids:
            document = runtime.collection("documents").find_one(
                {"doc_uid": doc_uid},
                projection={"_id": 0, "doc_uid": 1, "same_case_group_id": 1},
            )
            if document is None:
                continue
            if document.get("same_case_group_id") == group_id:
                noop_doc_uids.append(doc_uid)
                continue
            if apply_changes:
                runtime.collection("documents").update_one(
                    {"doc_uid": doc_uid},
                    {
                        "$set": {
                            "same_case_group_id": group_id,
                            "updated_at": _utc_now(),
                        }
                    },
                    upsert=False,
                )
            planned_doc_uids.append(doc_uid)
        report["same_case_updates"].append(
            {
                "same_case_group_id": group_id,
                "doc_uids": list(doc_uids),
                "updated_doc_uids": planned_doc_uids,
                "noop_doc_uids": noop_doc_uids,
            }
        )

    report["summary"] = {
        "document_updates": sum(
            1 for item in report["document_updates"] if item["action"] == "update"
        ),
        "document_noops": sum(
            1 for item in report["document_updates"] if item["action"] == "noop"
        ),
        "manual_review_count": len(report["manual_review_items"]),
        "duplicate_groups": len(duplicate_groups),
        "act_documents": sum(
            1
            for document in documents
            if (document.get("document_kind") or document.get("doc_type")) in ACT_KINDS
        ),
        "same_case_groups": len(SAME_CASE_GROUPS),
    }
    report_path = report_dir / "metadata_migration_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report["report_path"] = str(report_path)
    return report


def _resolve_target_doc_uids(
    *,
    payload: Mapping[str, Any],
    docs_by_uid: Mapping[str, Mapping[str, Any]],
    scope: str,
) -> list[str]:
    if scope == "full":
        return sorted(docs_by_uid)

    target_doc_uids: list[str] = []
    for entry in _iter_metadata_target_entries(payload, scope=scope):
        target_doc_uid = entry_target_doc_uid(entry)
        if target_doc_uid:
            target_doc_uids.append(target_doc_uid)
    return target_doc_uids


def _iter_metadata_target_entries(payload: Mapping[str, Any], *, scope: str):
    for entry in payload.get("positions", []):
        if scope == "full":
            yield entry
            continue
        if entry.get("required_top_level"):
            yield entry
            continue
        if entry.get("status") in {"alias", "excluded"}:
            yield entry
    for group_key in ("derived_runtime_targets", "required_additions"):
        for entry in payload.get(group_key, []):
            yield entry


def _resolve_source_entry(
    *,
    document: Mapping[str, Any],
    current_source: Mapping[str, Any] | None,
    curated_by_source_url: Mapping[str, Mapping[str, Any]],
    duplicate_resolution: Any | None,
) -> dict[str, Any] | None:
    if duplicate_resolution is not None and duplicate_resolution.role != "owner":
        return None

    normalized_source_url = normalize_url(select_source_url(document, current_source))
    if normalized_source_url is None:
        return None
    entry = curated_by_source_url.get(normalized_source_url)
    if entry is None:
        return None
    return dict(entry)


def _resolve_owner_doc_uid(
    *,
    doc_uid: str,
    duplicate_resolution: Any | None,
    act_context_item: Mapping[str, Any] | None,
) -> str | None:
    if duplicate_resolution is not None and duplicate_resolution.role != "owner":
        return str(duplicate_resolution.owner_doc_uid)

    act_owner_doc_uid = (act_context_item or {}).get("owner_doc_uid")
    if act_owner_doc_uid and act_owner_doc_uid != doc_uid:
        return str(act_owner_doc_uid)
    return None


def _resolve_owner_entry(
    *,
    owner_document: Mapping[str, Any] | None,
    owner_current_source: Mapping[str, Any] | None,
    curated_by_doc_uid: Mapping[str, Mapping[str, Any]],
    curated_by_source_url: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any] | None:
    if owner_document is None:
        return None

    doc_uid = str(owner_document.get("doc_uid") or "")
    if doc_uid and doc_uid in curated_by_doc_uid:
        return dict(curated_by_doc_uid[doc_uid])

    normalized_source_url = normalize_url(
        select_source_url(owner_document, owner_current_source)
    )
    if normalized_source_url and normalized_source_url in curated_by_source_url:
        return dict(curated_by_source_url[normalized_source_url])
    return None


def _build_act_context(
    *,
    documents: list[Mapping[str, Any]],
    current_sources: Mapping[str, Mapping[str, Any]],
    curated_by_doc_uid: Mapping[str, Mapping[str, Any]],
    curated_by_source_url: Mapping[str, Mapping[str, Any]],
    duplicate_resolutions: Mapping[str, Any],
) -> dict[str, dict[str, str]]:
    candidates_by_act_id: dict[str, list[str]] = defaultdict(list)
    act_id_by_doc_uid: dict[str, str] = {}
    docs_by_uid = {
        str(document.get("doc_uid")): document
        for document in documents
        if document.get("doc_uid")
    }

    for document in documents:
        doc_uid = str(document.get("doc_uid") or "")
        if not doc_uid:
            continue
        current_source = current_sources.get(doc_uid)
        direct_entry = curated_by_doc_uid.get(doc_uid)
        source_entry = None
        if direct_entry is None:
            normalized_source_url = normalize_url(
                select_source_url(document, current_source)
            )
            if normalized_source_url:
                source_entry = curated_by_source_url.get(normalized_source_url)

        curated_entry = direct_entry or source_entry
        document_kind = infer_document_kind(document, curated_entry)
        if document_kind not in ACT_KINDS:
            continue

        act_id = derive_act_id(document, curated_entry=curated_entry)
        if act_id is None:
            continue
        act_id_by_doc_uid[doc_uid] = act_id
        candidates_by_act_id[act_id].append(doc_uid)

    owner_by_act_id: dict[str, str] = {}
    for act_id, doc_uids in candidates_by_act_id.items():
        owner_by_act_id[act_id] = _select_act_owner(
            act_id=act_id,
            doc_uids=doc_uids,
            docs_by_uid=docs_by_uid,
            curated_by_doc_uid=curated_by_doc_uid,
            duplicate_resolutions=duplicate_resolutions,
        )

    return {
        doc_uid: {
            "act_id": act_id,
            "owner_doc_uid": owner_by_act_id[act_id],
        }
        for doc_uid, act_id in act_id_by_doc_uid.items()
    }


def _select_act_owner(
    *,
    act_id: str,
    doc_uids: list[str],
    docs_by_uid: Mapping[str, Mapping[str, Any]],
    curated_by_doc_uid: Mapping[str, Mapping[str, Any]],
    duplicate_resolutions: Mapping[str, Any],
) -> str:
    ranked = sorted(
        doc_uids,
        key=lambda doc_uid: (
            -_act_owner_score(
                act_id=act_id,
                document=docs_by_uid[doc_uid],
                curated_entry=curated_by_doc_uid.get(doc_uid),
                duplicate_resolution=duplicate_resolutions.get(doc_uid),
            ),
            doc_uid,
        ),
    )
    return ranked[0]


def _act_owner_score(
    *,
    act_id: str,
    document: Mapping[str, Any],
    curated_entry: Mapping[str, Any] | None,
    duplicate_resolution: Any | None,
) -> int:
    doc_uid = str(document.get("doc_uid") or "")
    score = 0
    if curated_entry is not None:
        status = str(curated_entry.get("status") or "")
        if status in {"canonical", "optional"}:
            score += 100
        else:
            score += 70
    if duplicate_resolution is not None and duplicate_resolution.role == "owner":
        score += 30
    if "urlsha:" not in doc_uid:
        score += 25
    if str(document.get("status") or "") in {"canonical", "optional"}:
        score += 20
    if document.get("external_id") or document.get("external_ids"):
        score += 10

    source_system = str(document.get("source_system") or "").lower()
    if source_system in {"eli_pl", "isap_pl", "eurlex_eu"}:
        score += 10
    if source_system == "unknown":
        score -= 30
    if source_system == "lex_pl":
        score -= 10
    if act_id == "eli:DU/2001/733" and source_system in {"eli_pl", "isap_pl"}:
        score += 5
    return score


def _build_document_update(
    *,
    runtime: MongoRuntime,
    article_inventory_cache: dict[tuple[str, str], list[str]],
    page_text_by_doc_uid: Mapping[str, str] | None = None,
    docs_by_uid: Mapping[str, Mapping[str, Any]],
    document: Mapping[str, Any],
    current_source: Mapping[str, Any] | None,
    exact_entry: Mapping[str, Any] | None,
    source_entry: Mapping[str, Any] | None,
    duplicate_resolution: Any | None,
    act_context_item: Mapping[str, Any] | None,
    owner_document: Mapping[str, Any] | None,
    owner_current_source: Mapping[str, Any] | None,
    owner_entry: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    doc_uid = str(document.get("doc_uid"))
    document_kind = infer_document_kind(document, exact_entry or source_entry)
    status = _resolve_status(
        document=document,
        exact_entry=exact_entry,
        source_entry=source_entry,
        duplicate_resolution=duplicate_resolution,
        act_context_item=act_context_item,
    )
    act_id = (act_context_item or {}).get("act_id")
    source_url = select_source_url(document, current_source)
    external_id = _resolve_external_id(
        document=document,
        exact_entry=exact_entry,
        source_entry=source_entry,
        owner_document=owner_document,
        act_id=act_id,
    )
    canonical_title = _resolve_canonical_title(
        document=document,
        external_id=external_id,
        exact_entry=exact_entry,
        source_entry=source_entry,
        owner_document=owner_document,
    )
    canonical_doc_uid = _resolve_canonical_doc_uid(
        docs_by_uid=docs_by_uid,
        doc_uid=doc_uid,
        document_kind=document_kind,
        status=status,
        document=document,
        exact_entry=exact_entry,
        source_entry=source_entry,
        duplicate_resolution=duplicate_resolution,
        act_context_item=act_context_item,
    )
    checksum_sha256 = document.get("current_source_hash") or (current_source or {}).get(
        "source_hash"
    )
    storage_uri = _resolve_storage_uri(
        document=document,
        current_source=current_source,
        checksum_sha256=checksum_sha256,
    )
    artifact_review_reasons = sorted(
        set(
            collect_checksum_validation_issues(checksum_sha256)
            + collect_storage_uri_validation_issues(storage_uri)
        )
    )
    forced_broken_artifact_exclusion = bool(
        artifact_review_reasons
        and _should_force_broken_artifact_exclusion(
            status=status,
            exact_entry=exact_entry,
            source_entry=source_entry,
        )
    )
    if forced_broken_artifact_exclusion:
        status = "excluded"
    legal_role = _resolve_legal_role(
        document=document,
        status=status,
        document_kind=document_kind,
        exact_entry=exact_entry,
        source_entry=source_entry,
        duplicate_resolution=duplicate_resolution,
        act_context_item=act_context_item,
    )
    if forced_broken_artifact_exclusion:
        legal_role = "INVENTORY_ONLY"
    resolved_act_short_name = clean_title(document.get("act_short_name"))
    if (
        resolved_act_short_name is None
        and document_kind in ACT_KINDS
        and act_id is not None
    ):
        resolved_act_short_name = derive_act_short_name(act_id, canonical_title)
    same_case_group_id = SAME_CASE_GROUP_BY_DOC_UID.get(doc_uid) or document.get(
        "same_case_group_id"
    )
    enrichment_document = dict(document)
    source_text_blob = (page_text_by_doc_uid or {}).get(doc_uid)
    if source_text_blob:
        enrichment_document["_source_text_blob"] = source_text_blob
    section5_enrichment = build_section5_enrichment(
        document=enrichment_document,
        current_source=current_source,
        document_kind=document_kind,
        status=status,
        legal_role=legal_role,
        canonical_title=canonical_title,
        source_url=source_url,
        external_id=external_id,
        act_id=act_id,
        act_short_name=resolved_act_short_name,
        canonical_doc_uid=canonical_doc_uid,
        duplicate_owner_doc_uid=(duplicate_resolution or None).owner_doc_uid
        if duplicate_resolution is not None
        else None,
        same_case_group_id=same_case_group_id,
    )
    manual_review_reasons = _collect_manual_review_reasons(
        document=document,
        current_source=current_source,
        exact_entry=exact_entry,
        source_entry=source_entry,
        owner_document=owner_document,
        canonical_title=canonical_title,
        act_context_item=act_context_item,
        checksum_sha256=checksum_sha256,
        storage_uri=storage_uri,
        resolved_broken_artifact=forced_broken_artifact_exclusion,
    )

    update_payload: dict[str, Any] = {
        "status": status,
        "document_kind": document_kind,
        "legal_role": legal_role,
        "source_tier": infer_source_tier(document, current_source),
        "canonical_title": canonical_title,
        "source_url": source_url,
        "normalized_source_url": normalize_url(source_url),
        "external_id": external_id,
        "canonical_doc_uid": canonical_doc_uid,
        "checksum_sha256": checksum_sha256,
        "storage_uri": storage_uri,
        "title": canonical_title,
        "doc_type": document_kind,
    }
    update_payload.update(section5_enrichment)
    if source_url:
        update_payload["source_urls"] = [source_url]
    if section5_enrichment.get("same_case_group_id"):
        update_payload["same_case_group_id"] = section5_enrichment["same_case_group_id"]

    if duplicate_resolution is not None:
        update_payload["duplicate_group_id"] = duplicate_resolution.group_id
        update_payload["duplicate_owner_doc_uid"] = duplicate_resolution.owner_doc_uid
        update_payload["duplicate_role"] = duplicate_resolution.role

    if status == "excluded":
        update_payload["exclusion_reason"] = _resolve_exclusion_reason(
            exact_entry=exact_entry,
            source_entry=source_entry,
            duplicate_resolution=duplicate_resolution,
            document=document,
            broken_artifact_reasons=artifact_review_reasons,
        )

    if document_kind in ACT_KINDS:
        act_owner_doc_uid = _resolve_act_owner_doc_uid(
            doc_uid=doc_uid,
            act_context_item=act_context_item,
        )
        act_owner_document = docs_by_uid.get(act_owner_doc_uid, document)
        act_owner_source = (
            owner_current_source
            if owner_document is not None
            and act_owner_doc_uid == owner_document.get("doc_uid")
            else current_source
            if act_owner_doc_uid == doc_uid
            else None
        )
        act_article_nodes = _load_article_inventory(
            runtime=runtime,
            article_inventory_cache=article_inventory_cache,
            document=act_owner_document or document,
            current_source=act_owner_source,
        )
        if not act_id:
            act_id = derive_act_id(
                act_owner_document or document,
                curated_entry=owner_entry or exact_entry or source_entry,
            )
        act_short_name = (
            derive_act_short_name(act_id, canonical_title)
            if act_id
            else canonical_title
        )
        is_consolidated_text = _is_consolidated_text(
            source_url=source_url,
            act_owner_doc_uid=act_owner_doc_uid,
            doc_uid=doc_uid,
        )
        update_payload.update(
            {
                "act_id": act_id or doc_uid,
                "act_short_name": act_short_name,
                "article_nodes": act_article_nodes,
                "current_status": _derive_act_current_status(
                    source_url=source_url,
                    act_owner_doc_uid=act_owner_doc_uid,
                    doc_uid=doc_uid,
                    is_consolidated_text=is_consolidated_text,
                ),
                "current_text_ref": act_owner_doc_uid,
                "is_consolidated_text": is_consolidated_text,
                "key_provisions": build_key_provisions(act_article_nodes),
            }
        )

    return update_payload, manual_review_reasons


def _resolve_status(
    *,
    document: Mapping[str, Any],
    exact_entry: Mapping[str, Any] | None,
    source_entry: Mapping[str, Any] | None,
    duplicate_resolution: Any | None,
    act_context_item: Mapping[str, Any] | None,
) -> str:
    if exact_entry is not None:
        return str(exact_entry["status"])

    if source_entry is not None and str(source_entry.get("status")) in {
        "alias",
        "article_node",
        "excluded",
    }:
        return str(source_entry["status"])

    if duplicate_resolution is not None and duplicate_resolution.role != "owner":
        return str(duplicate_resolution.target_status)

    if source_entry is not None:
        return str(source_entry["status"])

    act_owner_doc_uid = (act_context_item or {}).get("owner_doc_uid")
    if act_owner_doc_uid and act_owner_doc_uid != document.get("doc_uid"):
        return "alias"

    existing_status = document.get("status")
    if existing_status:
        return str(existing_status)
    return "active"


def _resolve_external_id(
    *,
    document: Mapping[str, Any],
    exact_entry: Mapping[str, Any] | None,
    source_entry: Mapping[str, Any] | None,
    owner_document: Mapping[str, Any] | None,
    act_id: str | None,
) -> str:
    curated_entry = exact_entry or source_entry
    if curated_entry and curated_entry.get("expected_external_id"):
        return str(curated_entry["expected_external_id"])

    if owner_document and owner_document.get("external_id"):
        return str(owner_document["external_id"])

    if act_id:
        return act_id

    return derive_external_id(document, curated_entry=curated_entry)


def _resolve_canonical_title(
    *,
    document: Mapping[str, Any],
    external_id: str,
    exact_entry: Mapping[str, Any] | None,
    source_entry: Mapping[str, Any] | None,
    owner_document: Mapping[str, Any] | None,
) -> str:
    if exact_entry is not None and exact_entry.get("canonical_title"):
        return str(exact_entry["canonical_title"])

    if source_entry is not None and source_entry.get("canonical_title"):
        if str(source_entry.get("status")) in {"alias", "article_node", "excluded"}:
            owner_title = clean_title(
                (owner_document or {}).get("canonical_title")
                or (owner_document or {}).get("title")
            )
            if owner_title:
                return owner_title
        return str(source_entry["canonical_title"])

    owner_title = clean_title(
        (owner_document or {}).get("canonical_title")
        or (owner_document or {}).get("title")
    )
    if owner_title:
        return owner_title

    current_title = clean_title(
        document.get("canonical_title") or document.get("title")
    )
    if current_title and not is_placeholder_title(current_title):
        return current_title

    source_system = str(document.get("source_system") or "").lower()
    if source_system == "eurlex_eu":
        return f"EUR-Lex document {external_id}"
    if source_system == "curia_eu":
        return f"CURIA document {external_id}"
    return external_id


def _resolve_canonical_doc_uid(
    *,
    docs_by_uid: Mapping[str, Mapping[str, Any]],
    doc_uid: str,
    document_kind: str,
    status: str,
    document: Mapping[str, Any],
    exact_entry: Mapping[str, Any] | None,
    source_entry: Mapping[str, Any] | None,
    duplicate_resolution: Any | None,
    act_context_item: Mapping[str, Any] | None,
) -> str | None:
    if status == "canonical":
        if exact_entry and exact_entry.get("canonical_doc_uid"):
            return str(exact_entry["canonical_doc_uid"])
        return doc_uid

    if duplicate_resolution is not None and duplicate_resolution.role != "owner":
        return str(duplicate_resolution.owner_doc_uid)

    if exact_entry and exact_entry.get("canonical_doc_uid"):
        return str(exact_entry["canonical_doc_uid"])

    if source_entry and status in {"alias", "article_node", "excluded"}:
        if source_entry.get("canonical_doc_uid"):
            return str(source_entry["canonical_doc_uid"])

    if source_entry and status in {"optional", "active"}:
        target_doc_uid = entry_target_doc_uid(source_entry)
        if target_doc_uid and target_doc_uid in docs_by_uid:
            return target_doc_uid
        return doc_uid

    act_owner_doc_uid = (act_context_item or {}).get("owner_doc_uid")
    if act_owner_doc_uid:
        if act_owner_doc_uid != doc_uid:
            return str(act_owner_doc_uid)
        if document_kind in ACT_KINDS:
            return str(act_owner_doc_uid)

    existing_canonical_doc_uid = document.get("canonical_doc_uid")
    if existing_canonical_doc_uid:
        return str(existing_canonical_doc_uid)
    return None


def _resolve_legal_role(
    *,
    document: Mapping[str, Any],
    status: str,
    document_kind: str,
    exact_entry: Mapping[str, Any] | None,
    source_entry: Mapping[str, Any] | None,
    duplicate_resolution: Any | None,
    act_context_item: Mapping[str, Any] | None,
) -> str:
    source_system = str(document.get("source_system") or "").lower()

    if exact_entry is not None and status == "excluded" and source_system == "uokik_pl":
        return "INVENTORY_ONLY"
    if exact_entry is not None and exact_entry.get("legal_role"):
        return str(exact_entry["legal_role"])
    if source_entry is not None and source_entry.get("legal_role"):
        return str(source_entry["legal_role"])

    if duplicate_resolution is not None and duplicate_resolution.role != "owner":
        if status == "excluded":
            return "INVENTORY_ONLY"
        return "DUPLICATE_ALIAS"

    act_owner_doc_uid = (act_context_item or {}).get("owner_doc_uid")
    if act_owner_doc_uid and act_owner_doc_uid != document.get("doc_uid"):
        return "SECONDARY_SOURCE"

    if document_kind == "STATUTE_REF":
        return "ARTICLE_NODE"
    if document_kind == "COMMENTARY":
        return "COMMENTARY"
    if document_kind == "GUIDANCE":
        return "GUIDANCE"
    if document_kind in ACT_KINDS:
        if source_system in {"lex_pl", "unknown"}:
            return "SECONDARY_SOURCE"
        if source_system == "eurlex_eu":
            return "GENERAL_ACT"
        return "DIRECT_NORM"
    if document_kind == "CASELAW":
        if source_system in {"curia_eu", "eurlex_eu"}:
            return "OPTIONAL_EU"
        return "GENERAL_CASELAW"
    return "GENERAL_DOCUMENT"


def _resolve_exclusion_reason(
    *,
    exact_entry: Mapping[str, Any] | None,
    source_entry: Mapping[str, Any] | None,
    duplicate_resolution: Any | None,
    document: Mapping[str, Any],
    broken_artifact_reasons: list[str] | None = None,
) -> str:
    if broken_artifact_reasons:
        return (
            f"{BROKEN_ARTIFACT_EXCLUSION_REASON} Reasons: "
            f"{'; '.join(broken_artifact_reasons)}."
        )
    for entry in (exact_entry, source_entry):
        if entry is not None and entry.get("notes"):
            return str(entry["notes"])
    if duplicate_resolution is not None:
        return "Duplicate representation retained for inventory only."
    return f"Excluded by corpus-wide normalization for {document.get('doc_uid')}."


def _resolve_storage_uri(
    *,
    document: Mapping[str, Any],
    current_source: Mapping[str, Any] | None,
    checksum_sha256: str | None,
) -> str:
    storage_uri = (current_source or {}).get("raw_object_path") or document.get(
        "storage_uri"
    )
    if storage_uri:
        return str(storage_uri)
    if checksum_sha256:
        return f"document_sources:{document.get('doc_uid')}:{checksum_sha256}"
    return f"document:{document.get('doc_uid')}"


def _resolve_act_owner_doc_uid(
    *,
    doc_uid: str,
    act_context_item: Mapping[str, Any] | None,
) -> str:
    act_owner_doc_uid = (act_context_item or {}).get("owner_doc_uid")
    if act_owner_doc_uid:
        return str(act_owner_doc_uid)
    return doc_uid


def _load_article_inventory(
    *,
    runtime: MongoRuntime,
    article_inventory_cache: dict[tuple[str, str], list[str]],
    document: Mapping[str, Any],
    current_source: Mapping[str, Any] | None,
) -> list[str]:
    doc_uid = str(document.get("doc_uid"))
    source_hash = str(document.get("current_source_hash") or "")
    cache_key = (doc_uid, source_hash)
    if cache_key in article_inventory_cache:
        return article_inventory_cache[cache_key]

    query: dict[str, Any] = {
        "doc_uid": doc_uid,
        "node_id": {"$regex": "^art:"},
    }
    if source_hash:
        query["source_hash"] = source_hash
    nodes = list(
        runtime.collection("nodes").find(
            query,
            projection={"_id": 0, "node_id": 1, "order_index": 1},
        )
    )
    if not nodes and source_hash:
        nodes = list(
            runtime.collection("nodes").find(
                {"doc_uid": doc_uid, "node_id": {"$regex": "^art:"}},
                projection={"_id": 0, "node_id": 1, "order_index": 1},
            )
        )

    article_inventory_cache[cache_key] = build_article_node_inventory(nodes)
    return article_inventory_cache[cache_key]


def _is_consolidated_text(
    *,
    source_url: str | None,
    act_owner_doc_uid: str,
    doc_uid: str,
) -> bool:
    normalized_source_url = normalize_url(source_url) or ""
    if "/api/acts/DU/" in normalized_source_url:
        return "/text/U/" in normalized_source_url
    if "isap.sejm.gov.pl" in normalized_source_url:
        return "/U/" in normalized_source_url
    if "/eli/dir/" in normalized_source_url or "/eli/reg/" in normalized_source_url:
        return True
    return act_owner_doc_uid == doc_uid and normalized_source_url != ""


def _derive_act_current_status(
    *,
    source_url: str | None,
    act_owner_doc_uid: str,
    doc_uid: str,
    is_consolidated_text: bool,
) -> str:
    normalized_source_url = normalize_url(source_url) or ""
    if act_owner_doc_uid != doc_uid and is_consolidated_text:
        return "mirror"
    if "/text/O/" in normalized_source_url:
        return "archived"
    if act_owner_doc_uid != doc_uid:
        return "archived"
    if is_consolidated_text:
        return "current"
    return "archived"


def _collect_manual_review_reasons(
    *,
    document: Mapping[str, Any],
    current_source: Mapping[str, Any] | None,
    exact_entry: Mapping[str, Any] | None,
    source_entry: Mapping[str, Any] | None,
    owner_document: Mapping[str, Any] | None,
    canonical_title: str,
    act_context_item: Mapping[str, Any] | None,
    checksum_sha256: str | None,
    storage_uri: str | None,
    resolved_broken_artifact: bool,
) -> list[str]:
    reasons: list[str] = []
    source_system = str(document.get("source_system") or "").lower()
    is_official_secondary_mirror = _is_official_secondary_mirror(
        document=document,
        current_source=current_source,
        act_context_item=act_context_item,
    )

    if resolved_broken_artifact:
        return []

    if source_system == "unknown" and not is_official_secondary_mirror:
        reasons.append("unknown source_system")

    if current_source is None:
        reasons.append("missing current document_source")
    elif not current_source.get("raw_object_path"):
        reasons.append("missing raw_object_path")

    original_title = clean_title(document.get("title"))
    if (
        is_placeholder_title(original_title)
        and exact_entry is None
        and source_entry is None
        and owner_document is None
    ):
        reasons.append("placeholder title without curated mapping")

    act_owner_doc_uid = (act_context_item or {}).get("owner_doc_uid")
    if (
        source_system == "unknown"
        and act_owner_doc_uid
        and act_owner_doc_uid != document.get("doc_uid")
        and not is_official_secondary_mirror
    ):
        reasons.append("act owner inferred from non-official mirror")

    if clean_title(canonical_title) == str(document.get("doc_uid")):
        reasons.append("fallback canonical_title from doc_uid")

    reasons.extend(collect_checksum_validation_issues(checksum_sha256))
    reasons.extend(collect_storage_uri_validation_issues(storage_uri))

    return sorted(set(reasons))


def _is_official_secondary_mirror(
    *,
    document: Mapping[str, Any],
    current_source: Mapping[str, Any] | None,
    act_context_item: Mapping[str, Any] | None,
) -> bool:
    act_owner_doc_uid = (act_context_item or {}).get("owner_doc_uid")
    if not act_owner_doc_uid or act_owner_doc_uid == document.get("doc_uid"):
        return False
    return infer_source_tier(document, current_source) == "official"


def _should_force_broken_artifact_exclusion(
    *,
    status: str,
    exact_entry: Mapping[str, Any] | None,
    source_entry: Mapping[str, Any] | None,
) -> bool:
    if status in {"canonical", "article_node"}:
        return False
    curated_entry = exact_entry or source_entry
    if curated_entry is None:
        return True
    if curated_entry.get("required_top_level") and str(curated_entry.get("status")) == (
        "canonical"
    ):
        return False
    return True


def _compute_document_mutation(
    *,
    document: Mapping[str, Any],
    desired_payload: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    set_payload = {
        key: value
        for key, value in desired_payload.items()
        if document.get(key) != value
    }
    unset_fields = [
        field_name
        for field_name in OPTIONAL_MANAGED_FIELDS
        if field_name not in desired_payload and field_name in document
    ]
    return set_payload, unset_fields


def _build_page_text_index(pages: list[Mapping[str, Any]]) -> dict[str, str]:
    grouped: defaultdict[str, list[tuple[int, str]]] = defaultdict(list)
    for page in pages:
        doc_uid = clean_title(page.get("doc_uid"))
        text = clean_title(page.get("text"))
        if doc_uid is None or text is None:
            continue
        page_no = int(page.get("page_no") or 0)
        grouped[doc_uid].append((page_no, text))

    index: dict[str, str] = {}
    for doc_uid, items in grouped.items():
        ordered_items = sorted(items, key=lambda item: item[0])
        excerpt = clean_title(" ".join(text for _, text in ordered_items[:2]))
        if excerpt:
            index[doc_uid] = excerpt
    return index


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)
