from __future__ import annotations

import json
from collections.abc import Callable
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from legal_ingest.config import ArtifactConfig, utc_now_iso, utc_timestamp_token
from legal_ingest.enrichment import (
    extract_case_signature,
    has_avoidable_unknown_judgment_date,
    is_fallback_facts_tags,
    is_fallback_related_provisions,
    is_generic_holding_placeholder,
    is_unresolved_court_name,
    normalize_case_signature,
)
from legal_ingest.migration_plan import (
    get_required_runtime_entries,
    load_migration_payload,
)
from legal_ingest.mongo import MongoRuntime
from legal_ingest.normalization import (
    ACT_KINDS,
    ACT_LAYER_FIELDS,
    BASELINE_METADATA_FIELDS,
    build_duplicate_group_report,
    clean_title,
    collect_checksum_validation_issues,
    collect_storage_uri_validation_issues,
    is_explicit_broken_inventory_record,
    normalize_title,
    normalize_url,
)
from legal_ingest.schema import (
    ACT_REQUIRED_FIELDS,
    ACTIVE_REQUIRED_FIELDS,
    BASELINE_ENRICHMENT_FIELDS,
    CASELAW_REQUIRED_FIELDS,
    CASELAW_ENRICHMENT_FIELDS,
    EXCLUDED_REQUIRED_FIELDS,
    LEGACY_FIELD_HINTS,
    SECTION7_RULES,
)


def is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def compute_schema_gap(documents: list[Mapping[str, Any]]) -> dict[str, Any]:
    missing_counts: Counter[str] = Counter()
    sample_rows: list[dict[str, Any]] = []

    for document in documents:
        required_fields = list(ACTIVE_REQUIRED_FIELDS)
        kind = document.get("document_kind") or document.get("doc_type")
        status = str(document.get("status", "active")).lower()

        if kind in {"STATUTE", "EU_ACT"}:
            required_fields.extend(ACT_REQUIRED_FIELDS)
        if kind == "CASELAW":
            required_fields.extend(CASELAW_REQUIRED_FIELDS)
        if status in {"excluded", "archived"}:
            required_fields.extend(EXCLUDED_REQUIRED_FIELDS)

        missing_fields = [
            field_name
            for field_name in required_fields
            if is_missing_value(document.get(field_name))
        ]
        for field_name in missing_fields:
            missing_counts[field_name] += 1

        if len(sample_rows) < 10:
            sample_rows.append(
                {
                    "doc_uid": document.get("doc_uid"),
                    "doc_type": document.get("doc_type"),
                    "missing_fields": missing_fields,
                }
            )

    field_missing_counts = [
        {
            "field": field_name,
            "missing_documents": count,
            "coverage_ratio": round((len(documents) - count) / len(documents), 4)
            if documents
            else 0.0,
            "legacy_hints": LEGACY_FIELD_HINTS.get(field_name, []),
        }
        for field_name, count in sorted(
            missing_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]

    return {
        "total_documents": len(documents),
        "assumption": "Documents without TechSpec 3.1 status are treated as active for gap counting.",
        "field_missing_counts": field_missing_counts,
        "sample_documents": sample_rows,
    }


def compute_field_coverage(
    documents: list[Mapping[str, Any]],
    *,
    fields: tuple[str, ...],
    predicate: Callable[[Mapping[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    filtered_documents = [
        document
        for document in documents
        if predicate is None or bool(predicate(document))
    ]
    missing_counts: Counter[str] = Counter()
    missing_documents: list[dict[str, Any]] = []

    for document in filtered_documents:
        missing_fields = [
            field for field in fields if is_missing_value(document.get(field))
        ]
        for field in missing_fields:
            missing_counts[field] += 1
        if missing_fields:
            missing_documents.append(
                {
                    "doc_uid": str(document.get("doc_uid")),
                    "missing_fields": missing_fields,
                }
            )

    return {
        "total_documents": len(filtered_documents),
        "covered_documents": len(filtered_documents) - len(missing_documents),
        "missing_documents": len(missing_documents),
        "field_missing_counts": dict(sorted(missing_counts.items())),
        "sample_missing_documents": missing_documents[:10],
    }


def compute_baseline_metadata_coverage(
    documents: list[Mapping[str, Any]],
) -> dict[str, Any]:
    return compute_field_coverage(
        documents,
        fields=BASELINE_METADATA_FIELDS,
    )


def compute_baseline_metadata_validity(
    documents: list[Mapping[str, Any]],
    *,
    include_broken_inventory: bool = True,
) -> dict[str, Any]:
    filtered_documents = _filter_documents_for_validity(
        documents,
        include_broken_inventory=include_broken_inventory,
    )
    invalid_counts: Counter[str] = Counter()
    invalid_documents: list[dict[str, Any]] = []

    for document in filtered_documents:
        invalid_fields: list[str] = []
        for field in BASELINE_METADATA_FIELDS:
            if is_missing_value(document.get(field)):
                invalid_fields.append(field)
                invalid_counts[field] += 1
                continue
            if field == "checksum_sha256":
                if collect_checksum_validation_issues(document.get(field)):
                    invalid_fields.append(field)
                    invalid_counts[field] += 1
            if field == "storage_uri":
                if collect_storage_uri_validation_issues(document.get(field)):
                    invalid_fields.append(field)
                    invalid_counts[field] += 1

        if invalid_fields:
            invalid_documents.append(
                {
                    "doc_uid": str(document.get("doc_uid")),
                    "invalid_fields": invalid_fields,
                }
            )

    return {
        "total_documents": len(filtered_documents),
        "valid_documents": len(filtered_documents) - len(invalid_documents),
        "invalid_documents": len(invalid_documents),
        "field_invalid_counts": dict(sorted(invalid_counts.items())),
        "sample_invalid_documents": invalid_documents[:10],
    }


def compute_act_layer_coverage(documents: list[Mapping[str, Any]]) -> dict[str, Any]:
    return compute_field_coverage(
        documents,
        fields=ACT_LAYER_FIELDS,
        predicate=lambda document: (
            document.get("document_kind") or document.get("doc_type")
        )
        in ACT_KINDS,
    )


def compute_artifact_integrity(
    documents: list[Mapping[str, Any]],
    *,
    include_broken_inventory: bool = True,
) -> dict[str, Any]:
    filtered_documents = _filter_documents_for_validity(
        documents,
        include_broken_inventory=include_broken_inventory,
    )
    invalid_checksum_docs: set[str] = set()
    invalid_storage_docs: set[str] = set()
    affected_doc_uids: set[str] = set()

    for document in filtered_documents:
        doc_uid = str(document.get("doc_uid"))
        checksum_issues = collect_checksum_validation_issues(
            document.get("checksum_sha256")
        )
        storage_issues = collect_storage_uri_validation_issues(
            document.get("storage_uri")
        )
        if checksum_issues:
            invalid_checksum_docs.add(doc_uid)
            affected_doc_uids.add(doc_uid)
        if storage_issues:
            invalid_storage_docs.add(doc_uid)
            affected_doc_uids.add(doc_uid)

    return {
        "invalid_documents": len(affected_doc_uids),
        "total_invalid_checksum": len(invalid_checksum_docs),
        "total_invalid_storage_uri": len(invalid_storage_docs),
        "affected_doc_uids": sorted(affected_doc_uids),
    }


def compute_section5_enrichment_coverage(
    documents: list[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "all_documents": compute_field_coverage(
            documents,
            fields=BASELINE_ENRICHMENT_FIELDS,
        ),
        "caselaw_documents": compute_field_coverage(
            documents,
            fields=CASELAW_ENRICHMENT_FIELDS,
            predicate=lambda document: (
                document.get("document_kind") or document.get("doc_type")
            )
            == "CASELAW",
        ),
    }


def compute_section5_placeholder_metrics(
    documents: list[Mapping[str, Any]],
) -> dict[str, Any]:
    caselaw_documents = [
        document
        for document in documents
        if (document.get("document_kind") or document.get("doc_type")) == "CASELAW"
    ]
    placeholder_holding_doc_uids: list[str] = []
    fallback_facts_doc_uids: list[str] = []
    fallback_related_doc_uids: list[str] = []
    unknown_judgment_doc_uids: list[str] = []
    avoidable_unknown_judgment_doc_uids: list[str] = []
    unavoidable_unknown_judgment_doc_uids: list[str] = []
    unresolved_court_name_doc_uids: list[str] = []

    for document in caselaw_documents:
        doc_uid = str(document.get("doc_uid"))
        if is_generic_holding_placeholder(document.get("holding_1line")):
            placeholder_holding_doc_uids.append(doc_uid)
        if is_fallback_facts_tags(document.get("facts_tags")):
            fallback_facts_doc_uids.append(doc_uid)
        if is_fallback_related_provisions(document.get("related_provisions")):
            fallback_related_doc_uids.append(doc_uid)
        if clean_title(document.get("judgment_date")) == "unknown":
            unknown_judgment_doc_uids.append(doc_uid)
            if has_avoidable_unknown_judgment_date(document):
                avoidable_unknown_judgment_doc_uids.append(doc_uid)
            else:
                unavoidable_unknown_judgment_doc_uids.append(doc_uid)
        if is_unresolved_court_name(document.get("court_name")):
            unresolved_court_name_doc_uids.append(doc_uid)

    return {
        "total_documents": len(documents),
        "caselaw_documents": len(caselaw_documents),
        "placeholder_holding_1line": _metric_row(placeholder_holding_doc_uids),
        "fallback_facts_tags": _metric_row(fallback_facts_doc_uids),
        "fallback_related_provisions": _metric_row(fallback_related_doc_uids),
        "judgment_date_unknown_total": _metric_row(unknown_judgment_doc_uids),
        "judgment_date_unknown_avoidable": _metric_row(
            avoidable_unknown_judgment_doc_uids
        ),
        "judgment_date_unknown_unavoidable": _metric_row(
            unavoidable_unknown_judgment_doc_uids
        ),
        "unresolved_court_name": _metric_row(unresolved_court_name_doc_uids),
    }


def compute_required_runtime_section5_placeholder_metrics(
    documents: list[Mapping[str, Any]],
    required_entries: list[Mapping[str, Any]],
) -> dict[str, Any]:
    docs_by_uid = {
        str(document.get("doc_uid")): document
        for document in documents
        if document.get("doc_uid")
    }
    required_doc_uids = sorted(
        {
            str(entry.get("canonical_doc_uid"))
            for entry in required_entries
            if entry.get("document_kind") == "CASELAW"
            and entry.get("canonical_doc_uid")
        }
    )
    required_documents = [
        docs_by_uid[doc_uid] for doc_uid in required_doc_uids if doc_uid in docs_by_uid
    ]
    metrics = compute_section5_placeholder_metrics(required_documents)
    metrics["expected_doc_uids"] = required_doc_uids
    metrics["missing_doc_uids"] = [
        doc_uid for doc_uid in required_doc_uids if doc_uid not in docs_by_uid
    ]
    return metrics


def collect_broken_inventory_exemptions(
    documents: list[Mapping[str, Any]],
) -> dict[str, Any]:
    broken_documents = [
        document
        for document in documents
        if is_explicit_broken_inventory_record(document)
    ]
    return {
        "count": len(broken_documents),
        "doc_uids": sorted(
            str(document.get("doc_uid")) for document in broken_documents
        ),
        "reasons": {
            str(document.get("doc_uid")): sorted(
                set(
                    collect_checksum_validation_issues(document.get("checksum_sha256"))
                    + collect_storage_uri_validation_issues(document.get("storage_uri"))
                )
            )
            for document in sorted(
                broken_documents,
                key=lambda item: str(item.get("doc_uid")),
            )
        },
    }


def _filter_documents_for_validity(
    documents: list[Mapping[str, Any]],
    *,
    include_broken_inventory: bool,
) -> list[Mapping[str, Any]]:
    if include_broken_inventory:
        return list(documents)
    return [
        document
        for document in documents
        if not is_explicit_broken_inventory_record(document)
    ]


def _metric_row(doc_uids: list[str]) -> dict[str, Any]:
    ordered_doc_uids = sorted(doc_uids)
    return {
        "count": len(ordered_doc_uids),
        "doc_uids": ordered_doc_uids,
    }


def build_required_presence_report(
    documents: list[Mapping[str, Any]],
    required_entries: list[Mapping[str, Any]],
) -> dict[str, Any]:
    docs_by_uid = {
        str(document.get("doc_uid")): document
        for document in documents
        if document.get("doc_uid")
    }
    docs_by_source_url: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for document in documents:
        for source_url in document.get("source_urls", []):
            normalized = normalize_url(source_url)
            if normalized:
                docs_by_source_url[normalized].append(document)

    present_canonical: list[dict[str, Any]] = []
    present_noncanonical: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for entry in required_entries:
        matched_docs: dict[str, Mapping[str, Any]] = {}
        for doc_uid in entry.get("match_doc_uids", []):
            document = docs_by_uid.get(doc_uid)
            if document is not None:
                matched_docs[str(document["doc_uid"])] = document

        for source_url in entry.get("match_source_urls", []):
            for document in docs_by_source_url.get(normalize_url(source_url) or "", []):
                matched_docs[str(document["doc_uid"])] = document

        canonical_doc_uid = entry.get("canonical_doc_uid")
        expected_title = normalize_title(entry.get("canonical_title"))
        expected_source_url = normalize_url(entry.get("source_url"))
        matched_doc_uids = sorted(matched_docs)
        report_item = {
            "entry_id": entry["entry_id"],
            "canonical_title": entry["canonical_title"],
            "canonical_doc_uid": canonical_doc_uid,
            "status": entry["status"],
            "notes": entry["notes"],
            "matched_doc_uids": matched_doc_uids,
        }

        if canonical_doc_uid and canonical_doc_uid in matched_docs:
            canonical_document = matched_docs[canonical_doc_uid]
            current_status = str(canonical_document.get("status") or "").lower()
            current_canonical_doc_uid = canonical_document.get("canonical_doc_uid")
            current_title = normalize_title(
                canonical_document.get("canonical_title")
                or canonical_document.get("title")
            )
            current_source_url = normalize_url(
                canonical_document.get("source_url")
                or next(iter(canonical_document.get("source_urls", [])), None)
            )
            status_matches = current_status == "canonical"
            canonical_doc_uid_matches = current_canonical_doc_uid == canonical_doc_uid
            title_matches = expected_title is None or current_title == expected_title
            source_matches = (
                expected_source_url is None or current_source_url == expected_source_url
            )

            if (
                status_matches
                and canonical_doc_uid_matches
                and title_matches
                and source_matches
            ):
                present_canonical.append(report_item)
                continue

            report_item["present_titles"] = sorted(
                str(document.get("canonical_title") or document.get("title") or "")
                for document in matched_docs.values()
            )
            report_item["current_status"] = canonical_document.get("status")
            report_item["current_canonical_doc_uid"] = current_canonical_doc_uid
            report_item["current_source_url"] = canonical_document.get(
                "source_url"
            ) or next(iter(canonical_document.get("source_urls", [])), None)
            present_noncanonical.append(report_item)
        elif matched_docs:
            report_item["present_titles"] = sorted(
                str(document.get("canonical_title") or document.get("title") or "")
                for document in matched_docs.values()
            )
            present_noncanonical.append(report_item)
        else:
            missing.append(report_item)

    return {
        "required_total": len(required_entries),
        "present_canonical": sorted(
            present_canonical,
            key=lambda item: item["canonical_title"],
        ),
        "present_noncanonical": sorted(
            present_noncanonical,
            key=lambda item: item["canonical_title"],
        ),
        "missing": sorted(missing, key=lambda item: item["canonical_title"]),
    }


def group_duplicate_final_urls(
    document_sources: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for source in document_sources:
        normalized = normalize_url(source.get("final_url"))
        if normalized is None:
            continue
        groups[normalized].append(source)

    results: list[dict[str, Any]] = []
    for final_url, items in groups.items():
        if len(items) < 2:
            continue
        doc_uids = sorted(
            {str(item.get("doc_uid")) for item in items if item.get("doc_uid")}
        )
        source_hashes = sorted(
            {str(item.get("source_hash")) for item in items if item.get("source_hash")}
        )
        results.append(
            {
                "final_url": final_url,
                "entry_count": len(items),
                "distinct_doc_uids": doc_uids,
                "distinct_doc_uid_count": len(doc_uids),
                "source_hash_count": len(source_hashes),
                "kind": "multi_doc_duplicate"
                if len(doc_uids) > 1
                else "reingest_same_doc",
            }
        )

    results.sort(
        key=lambda item: (
            item["kind"] != "multi_doc_duplicate",
            -item["entry_count"],
            item["final_url"],
        )
    )
    return results


def group_same_case_candidates(
    documents: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    docs_by_uid = {
        str(document.get("doc_uid")): document
        for document in documents
        if document.get("doc_uid")
    }

    for document in documents:
        source_system = document.get("source_system")
        if source_system not in {"saos_pl", "courts_pl"}:
            continue

        signature = extract_case_signature(document)
        if not signature:
            continue

        normalized_signature = normalize_case_signature(signature)
        grouped[normalized_signature].append(
            {
                "doc_uid": document.get("doc_uid"),
                "title": document.get("title"),
                "source_system": source_system,
                "raw_signature": signature,
            }
        )

    results: list[dict[str, Any]] = []
    for signature, items in grouped.items():
        source_systems = {item["source_system"] for item in items}
        if not {"saos_pl", "courts_pl"}.issubset(source_systems):
            continue

        ordered_items = sorted(
            items,
            key=lambda item: (str(item["source_system"]), str(item["doc_uid"])),
        )
        ordered_doc_uids = [str(item["doc_uid"]) for item in ordered_items]
        same_case_group_ids = [
            str(docs_by_uid[doc_uid].get("same_case_group_id"))
            for doc_uid in ordered_doc_uids
            if docs_by_uid[doc_uid].get("same_case_group_id")
        ]
        results.append(
            {
                "case_signature": signature,
                "doc_uids": ordered_doc_uids,
                "source_systems": sorted(source_systems),
                "titles": [str(item["title"]) for item in ordered_items],
                "same_case_group_ids": same_case_group_ids,
                "all_members_have_same_case_group_id": len(same_case_group_ids)
                == len(ordered_doc_uids),
                "group_id_consistent": len(set(same_case_group_ids)) == 1
                and len(same_case_group_ids) == len(ordered_doc_uids),
            }
        )

    results.sort(key=lambda item: item["case_signature"])
    return results


def find_bad_titles(documents: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    docs_by_uid = {
        str(document.get("doc_uid")): document
        for document in documents
        if document.get("doc_uid")
    }
    findings: list[dict[str, Any]] = []

    for rule in SECTION7_RULES:
        document = docs_by_uid.get(rule.doc_uid)
        if document is None:
            continue
        if rule.issue_type == "excluded_candidate":
            if (
                str(document.get("status") or "").lower() == "excluded"
                and clean_title(document.get("canonical_title"))
                and clean_title(document.get("title"))
                == clean_title(document.get("canonical_title"))
                and document.get("exclusion_reason")
            ):
                continue
        title = document.get("title")
        if not rule.matches(title):
            continue
        findings.append(
            {
                "doc_uid": rule.doc_uid,
                "issue_type": rule.issue_type,
                "reason": rule.reason,
                "current_title": title,
                "expected_title": rule.expected_title,
                "source_system": document.get("source_system"),
            }
        )

    findings.sort(key=lambda item: item["doc_uid"])
    return findings


def find_canonical_invariant_violations(
    documents: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for document in documents:
        if str(document.get("status") or "").lower() != "canonical":
            continue
        if document.get("canonical_doc_uid"):
            continue
        violations.append(
            {
                "doc_uid": str(document.get("doc_uid")),
                "title": document.get("canonical_title") or document.get("title"),
                "status": document.get("status"),
            }
        )

    violations.sort(key=lambda item: item["doc_uid"])
    return violations


def build_audit_report(
    runtime: MongoRuntime,
    *,
    migration_map_path: Path | None = None,
) -> dict[str, Any]:
    collection_counts = runtime.get_collection_counts(
        ("documents", "pages", "nodes", "citations", "document_sources", "ingest_runs")
    )
    documents = runtime.load_collection("documents", projection={"_id": 0})
    document_sources = runtime.load_collection(
        "document_sources", projection={"_id": 0}
    )
    migration_payload = load_migration_payload(migration_map_path)
    required_entries = get_required_runtime_entries(migration_payload)

    duplicates = build_duplicate_group_report(documents, document_sources)
    same_case_groups = group_same_case_candidates(documents)
    bad_titles = find_bad_titles(documents)
    canonical_invariant_violations = find_canonical_invariant_violations(documents)
    broken_inventory_exemptions = collect_broken_inventory_exemptions(documents)

    return {
        "generated_at": utc_now_iso(),
        "mongo": {
            "uri": runtime.config.uri,
            "db_name": runtime.config.db_name,
        },
        "collection_counts": collection_counts,
        "baseline_metadata_coverage": compute_baseline_metadata_coverage(documents),
        "baseline_metadata_validity_all_docs": compute_baseline_metadata_validity(
            documents,
            include_broken_inventory=True,
        ),
        "baseline_metadata_validity_operational": compute_baseline_metadata_validity(
            documents,
            include_broken_inventory=False,
        ),
        "artifact_integrity_all_docs": compute_artifact_integrity(
            documents,
            include_broken_inventory=True,
        ),
        "artifact_integrity_operational": compute_artifact_integrity(
            documents,
            include_broken_inventory=False,
        ),
        "broken_inventory_exemptions": broken_inventory_exemptions,
        "act_layer_coverage": compute_act_layer_coverage(documents),
        "section5_enrichment_coverage": compute_section5_enrichment_coverage(documents),
        "section5_placeholder_metrics_all_docs": compute_section5_placeholder_metrics(
            documents
        ),
        "section5_placeholder_metrics_required_runtime": compute_required_runtime_section5_placeholder_metrics(
            documents,
            required_entries,
        ),
        "schema_gap": compute_schema_gap(documents),
        "required_documents": build_required_presence_report(
            documents, required_entries
        ),
        "duplicate_final_url_groups": {
            "total_groups": len(duplicates),
            "multi_doc_groups": sum(
                1 for group in duplicates if group["kind"] == "multi_doc_duplicate"
            ),
            "resolved_multi_doc_duplicates": sum(
                1
                for group in duplicates
                if group["kind"] == "multi_doc_duplicate" and group.get("resolved")
            ),
            "unresolved_multi_doc_duplicates": sum(
                1
                for group in duplicates
                if group["kind"] == "multi_doc_duplicate" and not group.get("resolved")
            ),
            "groups": duplicates,
        },
        "same_case_candidates": {
            "total_groups": len(same_case_groups),
            "groups_with_full_same_case_group_id": sum(
                1
                for group in same_case_groups
                if group["all_members_have_same_case_group_id"]
                and group["group_id_consistent"]
            ),
            "groups": same_case_groups,
        },
        "section7_findings": {
            "total_findings": len(bad_titles),
            "findings": bad_titles,
        },
        "canonical_invariants": {
            "null_canonical_doc_uid_count": len(canonical_invariant_violations),
            "violations": canonical_invariant_violations,
        },
    }


def render_audit_markdown(report: Mapping[str, Any]) -> str:
    baseline = report["baseline_metadata_coverage"]
    baseline_validity_all_docs = report["baseline_metadata_validity_all_docs"]
    baseline_validity_operational = report["baseline_metadata_validity_operational"]
    artifact_integrity_all_docs = report["artifact_integrity_all_docs"]
    artifact_integrity_operational = report["artifact_integrity_operational"]
    broken_inventory_exemptions = report["broken_inventory_exemptions"]
    act_layer = report["act_layer_coverage"]
    section5 = report["section5_enrichment_coverage"]
    section5_placeholders_all_docs = report["section5_placeholder_metrics_all_docs"]
    section5_placeholders_required_runtime = report[
        "section5_placeholder_metrics_required_runtime"
    ]
    required = report["required_documents"]
    duplicates = report["duplicate_final_url_groups"]
    same_case = report["same_case_candidates"]
    section7 = report["section7_findings"]
    canonical_invariants = report["canonical_invariants"]
    schema_gap = report["schema_gap"]["field_missing_counts"][:10]

    lines = [
        "# Legal Ingest Audit",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Mongo DB: {report['mongo']['db_name']}",
        f"- Collection counts: {report['collection_counts']}",
        "",
        "## Schema Gap",
        "",
    ]
    for field in schema_gap:
        lines.append(
            f"- `{field['field']}` missing in {field['missing_documents']} docs"
        )

    lines.extend(
        [
            "",
            "## Baseline Coverage",
            "",
            f"- Baseline metadata: {baseline['covered_documents']} / {baseline['total_documents']}",
            f"- Baseline metadata validity (all docs): {baseline_validity_all_docs['valid_documents']} / {baseline_validity_all_docs['total_documents']}",
            f"- Baseline metadata validity (operational docs): {baseline_validity_operational['valid_documents']} / {baseline_validity_operational['total_documents']}",
            f"- Act layer: {act_layer['covered_documents']} / {act_layer['total_documents']}",
        ]
    )

    lines.extend(
        [
            "",
            "## Artifact Integrity",
            "",
            f"- All docs invalid documents: {artifact_integrity_all_docs['invalid_documents']}",
            f"- All docs invalid checksum_sha256: {artifact_integrity_all_docs['total_invalid_checksum']}",
            f"- All docs invalid storage_uri: {artifact_integrity_all_docs['total_invalid_storage_uri']}",
            f"- Operational invalid documents: {artifact_integrity_operational['invalid_documents']}",
            f"- Operational invalid checksum_sha256: {artifact_integrity_operational['total_invalid_checksum']}",
            f"- Operational invalid storage_uri: {artifact_integrity_operational['total_invalid_storage_uri']}",
            f"- Broken inventory exemptions: {broken_inventory_exemptions['count']}",
        ]
    )
    for doc_uid in artifact_integrity_all_docs["affected_doc_uids"][:20]:
        lines.append(f"- All-doc artifact issue: {doc_uid}")
    for doc_uid in broken_inventory_exemptions["doc_uids"][:20]:
        reasons = ", ".join(broken_inventory_exemptions["reasons"].get(doc_uid, []))
        lines.append(f"- Broken inventory exemption: {doc_uid} | reasons={reasons}")

    lines.extend(
        [
            "",
            "## Section 5 Enrichment",
            "",
            f"- Baseline enrichment fields: {section5['all_documents']['covered_documents']} / {section5['all_documents']['total_documents']}",
            f"- Caselaw enrichment fields: {section5['caselaw_documents']['covered_documents']} / {section5['caselaw_documents']['total_documents']}",
            f"- All-doc placeholder slice: {section5_placeholders_all_docs['caselaw_documents']} caselaw docs inside {section5_placeholders_all_docs['total_documents']} total docs",
            f"- Required runtime placeholder slice: {section5_placeholders_required_runtime['caselaw_documents']} / {len(section5_placeholders_required_runtime['expected_doc_uids'])} caselaw docs",
            f"- All docs placeholder holding_1line: {section5_placeholders_all_docs['placeholder_holding_1line']['count']}",
            f"- All docs fallback facts_tags: {section5_placeholders_all_docs['fallback_facts_tags']['count']}",
            f"- All docs fallback related_provisions: {section5_placeholders_all_docs['fallback_related_provisions']['count']}",
            f"- All docs judgment_date='unknown': {section5_placeholders_all_docs['judgment_date_unknown_total']['count']}",
            f"- All docs avoidable judgment_date='unknown': {section5_placeholders_all_docs['judgment_date_unknown_avoidable']['count']}",
            f"- All docs unresolved court_name: {section5_placeholders_all_docs['unresolved_court_name']['count']}",
            f"- Required runtime placeholder holding_1line: {section5_placeholders_required_runtime['placeholder_holding_1line']['count']}",
            f"- Required runtime fallback facts_tags: {section5_placeholders_required_runtime['fallback_facts_tags']['count']}",
            f"- Required runtime fallback related_provisions: {section5_placeholders_required_runtime['fallback_related_provisions']['count']}",
            f"- Required runtime judgment_date='unknown': {section5_placeholders_required_runtime['judgment_date_unknown_total']['count']}",
            f"- Required runtime avoidable judgment_date='unknown': {section5_placeholders_required_runtime['judgment_date_unknown_avoidable']['count']}",
            f"- Required runtime unresolved court_name: {section5_placeholders_required_runtime['unresolved_court_name']['count']}",
        ]
    )
    for metric_name in (
        "placeholder_holding_1line",
        "fallback_facts_tags",
        "fallback_related_provisions",
        "judgment_date_unknown_avoidable",
        "unresolved_court_name",
    ):
        for doc_uid in section5_placeholders_required_runtime[metric_name]["doc_uids"][
            :10
        ]:
            lines.append(f"- Required runtime issue: {metric_name} -> {doc_uid}")

    lines.extend(
        [
            "",
            "## Required Runtime Documents",
            "",
            f"- Present canonical: {len(required['present_canonical'])}",
            f"- Present noncanonical: {len(required['present_noncanonical'])}",
            f"- Missing: {len(required['missing'])}",
        ]
    )
    for item in required["missing"]:
        lines.append(f"- Missing: {item['canonical_title']}")
    for item in required["present_noncanonical"]:
        lines.append(
            f"- Needs canonicalization: {item['canonical_title']} -> {', '.join(item['matched_doc_uids'])}"
        )

    lines.extend(
        [
            "",
            "## Duplicate final_url Groups",
            "",
            f"- Total groups: {duplicates['total_groups']}",
            f"- Multi-doc groups: {duplicates['multi_doc_groups']}",
            f"- Resolved multi-doc groups: {duplicates['resolved_multi_doc_duplicates']}",
            f"- Unresolved multi-doc groups: {duplicates['unresolved_multi_doc_duplicates']}",
        ]
    )
    for group in duplicates["groups"][:10]:
        suffix = ""
        if group["kind"] == "multi_doc_duplicate":
            suffix = (
                f" | resolved={group['resolved']} | owner={group.get('owner_doc_uid')}"
            )
        lines.append(
            f"- {group['kind']}: {group['final_url']} ({group['entry_count']} entries, {group['distinct_doc_uid_count']} doc_uids){suffix}"
        )

    lines.extend(
        [
            "",
            "## same-case Candidates",
            "",
            f"- Total groups: {same_case['total_groups']}",
            f"- Groups with consistent same_case_group_id: {same_case['groups_with_full_same_case_group_id']}",
        ]
    )
    for group in same_case["groups"]:
        lines.append(
            f"- {group['case_signature']}: {', '.join(group['doc_uids'])} | group_ids={group['same_case_group_ids']}"
        )

    lines.extend(
        [
            "",
            "## Canonical Invariants",
            "",
            f"- status=canonical with null canonical_doc_uid: {canonical_invariants['null_canonical_doc_uid_count']}",
        ]
    )
    for item in canonical_invariants["violations"]:
        lines.append(f"- {item['doc_uid']}: {item['title']}")

    lines.extend(
        [
            "",
            "## Section 7 Findings",
            "",
            f"- Total findings: {section7['total_findings']}",
        ]
    )
    for finding in section7["findings"]:
        lines.append(
            f"- {finding['doc_uid']}: {finding['issue_type']} ({finding['current_title']})"
        )

    lines.append("")
    return "\n".join(lines)


def write_audit_artifacts(
    report: Mapping[str, Any],
    *,
    artifact_config: ArtifactConfig,
) -> dict[str, str]:
    timestamp = utc_timestamp_token()
    audit_dir = artifact_config.audit_dir(timestamp)
    audit_dir.mkdir(parents=True, exist_ok=True)

    json_path = audit_dir / "audit_report.json"
    markdown_path = audit_dir / "audit_report.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_audit_markdown(report), encoding="utf-8")
    return {
        "audit_dir": str(audit_dir),
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }
