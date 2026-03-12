from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlsplit, urlunsplit

BASELINE_METADATA_FIELDS = (
    "status",
    "document_kind",
    "legal_role",
    "source_tier",
    "canonical_title",
    "source_url",
    "normalized_source_url",
    "external_id",
    "checksum_sha256",
    "storage_uri",
)

ACT_LAYER_FIELDS = (
    "act_id",
    "act_short_name",
    "article_nodes",
    "current_status",
    "current_text_ref",
    "is_consolidated_text",
    "key_provisions",
)

ACT_KINDS = {"STATUTE", "EU_ACT"}

OFFICIAL_SOURCE_SYSTEMS = {
    "curia_eu",
    "eli_pl",
    "eurlex_eu",
    "isap_pl",
    "sn_pl",
    "uokik_pl",
}

OFFICIAL_SOURCE_HOSTS = {
    "curia.europa.eu",
    "decyzje.uokik.gov.pl",
    "dziennikustaw.gov.pl",
    "eli.gov.pl",
    "eur-lex.europa.eu",
    "isap.sejm.gov.pl",
    "sn.pl",
    "www.sn.pl",
}

PLACEHOLDER_TITLES = {"error", "rpex", "sn", "untitled html document"}

KNOWN_ACT_SHORT_NAMES = {
    "eli:DU/1964/296": "Kodeks postepowania cywilnego",
    "eli:DU/2001/733": "Ustawa o ochronie praw lokatorow",
    "eli:DU/2005/1398": "Ustawa o kosztach sadowych",
    "eli:DU/2007/331": "Ustawa o ochronie konkurencji i konsumentow",
    "eli:dir/1993/13/oj/eng": "Directive 93/13/EEC",
    "eli:reg/2004/805/oj/eng": "Regulation (EC) No 805/2004",
    "eli:reg/2006/1896/oj/eng": "Regulation (EC) No 1896/2006",
    "eli:reg/2007/861/oj/eng": "Regulation (EC) No 861/2007",
    "isap:WDU19640160093": "Kodeks cywilny",
}

CURIA_DOCID_PATTERN = re.compile(r"[?&]docid=(\d+)", re.IGNORECASE)
CURIA_JCMS_PATTERN = re.compile(r"/jcms/(jcms/)?(p1_\d+)", re.IGNORECASE)
CELEX_PATTERN = re.compile(r"CELEX[:=]([0-9A-Z()]+)", re.IGNORECASE)
ELI_ACT_URL_PATTERN = re.compile(r"/api/acts/DU/(\d{4})/(\d+)", re.IGNORECASE)
ELI_EU_PATTERN = re.compile(
    r"/eli/(dir|reg)/(\d{4})/(\d+)/oj(?:/([a-z]{2,3}))?",
    re.IGNORECASE,
)
DZIENNIK_USTAW_PATTERN = re.compile(r"/DU/(\d{4})/(\d+)", re.IGNORECASE)
ISAP_WDU_PATTERN = re.compile(r"WDU\d{4}\d+", re.IGNORECASE)
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)

BROKEN_ARTIFACT_EXCLUSION_REASON = (
    "Broken imported artifact retained for inventory only."
)
STRICT_STORAGE_PATH_PREFIXES = (
    "docs/",
    "./docs/",
    "/",
    "artifacts/legal_ingest/",
    "./artifacts/legal_ingest/",
)


@dataclass(frozen=True, slots=True)
class DuplicateResolution:
    final_url: str
    group_id: str
    owner_doc_uid: str
    role: str
    target_status: str


def iter_migration_entries(payload: Mapping[str, Any]):
    for group_key in ("positions", "derived_runtime_targets", "required_additions"):
        yield from payload.get(group_key, [])


def entry_target_doc_uid(entry: Mapping[str, Any]) -> str | None:
    if entry.get("status") == "canonical":
        value = entry.get("canonical_doc_uid")
    else:
        value = entry.get("source_doc_uid")
    return str(value) if value else None


def build_curated_entry_indexes(
    payload: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_doc_uid: dict[str, dict[str, Any]] = {}
    by_source_url: dict[str, dict[str, Any]] = {}
    for entry in iter_migration_entries(payload):
        target_doc_uid = entry_target_doc_uid(entry)
        if target_doc_uid:
            existing = by_doc_uid.get(target_doc_uid)
            if existing is None or _curated_entry_priority(
                entry
            ) > _curated_entry_priority(existing):
                by_doc_uid[target_doc_uid] = dict(entry)
        normalized_source_url = normalize_url(entry.get("source_url"))
        if normalized_source_url:
            existing = by_source_url.get(normalized_source_url)
            if existing is None or _curated_entry_priority(
                entry
            ) > _curated_entry_priority(existing):
                by_source_url[normalized_source_url] = dict(entry)
    return by_doc_uid, by_source_url


def normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlsplit(url)
    normalized_query = "&".join(
        f"{key}={value}"
        for key, value in sorted(parse_qsl(parsed.query, keep_blank_values=True))
    )
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            normalized_query,
            "",
        )
    )


def normalize_title(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = clean_title(value)
    return normalized.casefold() or None


def collect_checksum_validation_issues(value: Any) -> list[str]:
    if value is None:
        return []
    normalized = str(value).strip()
    if not normalized:
        return []
    if normalized == "ERROR":
        return ["invalid checksum sentinel"]
    if SHA256_HEX_PATTERN.fullmatch(normalized) is None:
        return ["non-hex checksum_sha256"]
    return []


def collect_storage_uri_validation_issues(value: Any) -> list[str]:
    if value is None:
        return []
    normalized = str(value).strip()
    if not normalized:
        return []

    issues: list[str] = []
    if normalized.startswith("document_sources:"):
        issues.append("synthetic storage_uri")
    if "/ERROR/" in normalized:
        issues.append("broken imported artifact path")
    if _should_validate_storage_path_existence(normalized) and not Path(
        normalized
    ).exists():
        issues.append("nonexistent storage path")
    return issues


def is_explicit_broken_inventory_record(document: Mapping[str, Any]) -> bool:
    return (
        str(document.get("status") or "").lower() == "excluded"
        and str(document.get("legal_role") or "") == "INVENTORY_ONLY"
        and BROKEN_ARTIFACT_EXCLUSION_REASON.lower()
        in str(document.get("exclusion_reason") or "").lower()
    )


def clean_title(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    return normalized or None


def is_placeholder_title(title: str | None) -> bool:
    normalized = normalize_title(title)
    if normalized is None:
        return True
    return normalized in PLACEHOLDER_TITLES


def select_source_url(
    document: Mapping[str, Any],
    current_source: Mapping[str, Any] | None = None,
) -> str | None:
    source_url = document.get("source_url")
    if isinstance(source_url, str) and source_url.strip():
        return source_url

    source_urls = document.get("source_urls")
    if isinstance(source_urls, list):
        for item in source_urls:
            if isinstance(item, str) and item.strip():
                return item

    for key in ("url", "final_url"):
        value = (current_source or {}).get(key)
        if isinstance(value, str) and value.strip():
            return value

    return None


def infer_document_kind(
    document: Mapping[str, Any],
    curated_entry: Mapping[str, Any] | None = None,
) -> str:
    if curated_entry and str(curated_entry.get("status") or "") == "article_node":
        return "STATUTE_REF"

    doc_type = document.get("doc_type")
    if doc_type == "STATUTE_REF":
        return "STATUTE_REF"

    if curated_entry and curated_entry.get("document_kind"):
        return str(curated_entry["document_kind"])

    existing_kind = document.get("document_kind") or doc_type
    if existing_kind:
        return str(existing_kind)

    source_system = str(document.get("source_system") or "").lower()
    if source_system == "prawo_pl":
        return "COMMENTARY"
    if source_system == "uokik_pl":
        return "GUIDANCE"
    return "DOCUMENT"


def infer_source_tier(
    document: Mapping[str, Any],
    current_source: Mapping[str, Any] | None = None,
) -> str:
    source_system = str(document.get("source_system", "")).lower()
    if source_system in OFFICIAL_SOURCE_SYSTEMS:
        return "official"
    source_url = normalize_url(select_source_url(document, current_source))
    if source_url:
        host = urlsplit(source_url).netloc.lower()
        if host in OFFICIAL_SOURCE_HOSTS:
            return "official"
    if source_system == "saos_pl":
        return "saos"
    if source_system == "courts_pl":
        return "court_portal"
    if source_system == "lex_pl":
        return "commercial_secondary"
    if source_system == "prawo_pl":
        return "commentary"
    return "unknown"


def build_current_source_index(
    documents: list[Mapping[str, Any]],
    document_sources: list[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    by_doc_hash: dict[tuple[str, str], dict[str, Any]] = {}
    latest_by_doc: dict[str, dict[str, Any]] = {}

    for source in document_sources:
        doc_uid = str(source.get("doc_uid") or "")
        if not doc_uid:
            continue
        source_hash = str(source.get("source_hash") or "")
        if source_hash:
            key = (doc_uid, source_hash)
            existing = by_doc_hash.get(key)
            if existing is None or _source_sort_key(source) > _source_sort_key(
                existing
            ):
                by_doc_hash[key] = dict(source)

        current = latest_by_doc.get(doc_uid)
        if current is None or _source_sort_key(source) > _source_sort_key(current):
            latest_by_doc[doc_uid] = dict(source)

    current_sources: dict[str, dict[str, Any]] = {}
    for document in documents:
        doc_uid = str(document.get("doc_uid") or "")
        if not doc_uid:
            continue
        source_hash = str(document.get("current_source_hash") or "")
        if source_hash and (doc_uid, source_hash) in by_doc_hash:
            current_sources[doc_uid] = by_doc_hash[(doc_uid, source_hash)]
            continue
        if doc_uid in latest_by_doc:
            current_sources[doc_uid] = latest_by_doc[doc_uid]
    return current_sources


def build_duplicate_resolution_index(
    documents: list[Mapping[str, Any]],
    document_sources: list[Mapping[str, Any]],
    *,
    curated_doc_uids: set[str],
    status_hints: Mapping[str, str] | None = None,
) -> tuple[dict[str, DuplicateResolution], list[dict[str, Any]]]:
    docs_by_uid = {
        str(document.get("doc_uid")): document
        for document in documents
        if document.get("doc_uid")
    }
    grouped_sources: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for source in document_sources:
        final_url = normalize_url(source.get("final_url"))
        if final_url is None:
            continue
        grouped_sources[final_url].append(source)

    resolutions: dict[str, DuplicateResolution] = {}
    summaries: list[dict[str, Any]] = []

    for final_url, items in grouped_sources.items():
        doc_uids = sorted(
            {str(item.get("doc_uid")) for item in items if item.get("doc_uid")}
        )
        if len(doc_uids) < 2:
            continue

        owner_doc_uid = _select_duplicate_owner(
            doc_uids=doc_uids,
            docs_by_uid=docs_by_uid,
            curated_doc_uids=curated_doc_uids,
        )
        owner_status = (
            (status_hints or {}).get(owner_doc_uid)
            or str(docs_by_uid[owner_doc_uid].get("status") or "")
            or "active"
        )
        target_status = "excluded" if owner_status == "excluded" else "alias"
        group_id = f"duplicate:{owner_doc_uid}"

        for doc_uid in doc_uids:
            role = "owner" if doc_uid == owner_doc_uid else target_status
            resolutions[doc_uid] = DuplicateResolution(
                final_url=final_url,
                group_id=group_id,
                owner_doc_uid=owner_doc_uid,
                role=role,
                target_status=target_status
                if doc_uid != owner_doc_uid
                else owner_status,
            )

        summaries.append(
            {
                "final_url": final_url,
                "entry_count": len(items),
                "doc_uids": doc_uids,
                "owner_doc_uid": owner_doc_uid,
                "group_id": group_id,
                "target_status": target_status,
            }
        )

    summaries.sort(key=lambda item: (-len(item["doc_uids"]), item["final_url"]))
    return resolutions, summaries


def build_duplicate_group_report(
    documents: list[Mapping[str, Any]],
    document_sources: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    docs_by_uid = {
        str(document.get("doc_uid")): document
        for document in documents
        if document.get("doc_uid")
    }
    grouped_sources: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for source in document_sources:
        final_url = normalize_url(source.get("final_url"))
        if final_url is None:
            continue
        grouped_sources[final_url].append(source)

    results: list[dict[str, Any]] = []
    for final_url, items in grouped_sources.items():
        doc_uids = sorted(
            {str(item.get("doc_uid")) for item in items if item.get("doc_uid")}
        )
        source_hashes = sorted(
            {str(item.get("source_hash")) for item in items if item.get("source_hash")}
        )
        if len(doc_uids) < 2:
            if len(doc_uids) == 1 and len(items) > 1:
                results.append(
                    {
                        "final_url": final_url,
                        "entry_count": len(items),
                        "distinct_doc_uids": doc_uids,
                        "distinct_doc_uid_count": 1,
                        "source_hash_count": len(source_hashes),
                        "kind": "reingest_same_doc",
                    }
                )
            continue

        owner_doc_uids = [
            doc_uid
            for doc_uid in doc_uids
            if docs_by_uid.get(doc_uid, {}).get("duplicate_role") == "owner"
        ]
        owner_doc_uid = owner_doc_uids[0] if len(owner_doc_uids) == 1 else None
        group_ids = {
            str(docs_by_uid[doc_uid].get("duplicate_group_id"))
            for doc_uid in doc_uids
            if docs_by_uid.get(doc_uid, {}).get("duplicate_group_id")
        }
        owner_refs = {
            str(docs_by_uid[doc_uid].get("duplicate_owner_doc_uid"))
            for doc_uid in doc_uids
            if docs_by_uid.get(doc_uid, {}).get("duplicate_owner_doc_uid")
        }
        non_owner_statuses = {
            doc_uid: str(docs_by_uid.get(doc_uid, {}).get("status"))
            for doc_uid in doc_uids
            if doc_uid != owner_doc_uid
        }

        resolved = (
            owner_doc_uid is not None
            and len(group_ids) == 1
            and len(owner_refs) == 1
            and owner_doc_uid in owner_refs
            and all(
                status in {"alias", "excluded"}
                for status in non_owner_statuses.values()
            )
        )
        results.append(
            {
                "final_url": final_url,
                "entry_count": len(items),
                "distinct_doc_uids": doc_uids,
                "distinct_doc_uid_count": len(doc_uids),
                "source_hash_count": len(source_hashes),
                "kind": "multi_doc_duplicate",
                "owner_doc_uid": owner_doc_uid,
                "duplicate_group_ids": sorted(group_ids),
                "resolved": resolved,
                "non_owner_statuses": non_owner_statuses,
            }
        )

    results.sort(
        key=lambda item: (
            item["kind"] != "multi_doc_duplicate",
            item.get("resolved", False),
            -item["entry_count"],
            item["final_url"],
        )
    )
    return results


def derive_external_id(
    document: Mapping[str, Any],
    *,
    curated_entry: Mapping[str, Any] | None = None,
) -> str:
    if curated_entry and curated_entry.get("expected_external_id"):
        return str(curated_entry["expected_external_id"])

    external_id = document.get("external_id")
    if external_id:
        return str(external_id)

    document_kind = infer_document_kind(document, curated_entry)
    if document_kind in ACT_KINDS:
        act_id = derive_act_id(document, curated_entry=curated_entry)
        if act_id:
            return act_id

    external_ids = document.get("external_ids")
    if isinstance(external_ids, dict):
        for key in ("saos_id", "sn_signature", "isap_wdu", "eli"):
            value = external_ids.get(key)
            if not value:
                continue
            if key == "saos_id":
                return f"saos:{value}"
            if key == "sn_signature":
                return f"sn:{value}"
            if key == "isap_wdu":
                return f"isap:{value}"
            if key == "eli":
                normalized_value = _normalize_known_act_id(str(value))
                return normalized_value or f"eli:{value}"

        for key in sorted(external_ids):
            value = external_ids.get(key)
            if value:
                return f"{key}:{value}"

    source_url = select_source_url(document)
    if source_url:
        if docid := _extract_curia_docid(source_url):
            return f"curia:{docid}"
        if jcms_id := _extract_curia_jcms(source_url):
            return f"curia:{jcms_id}"
        if celex := _extract_celex(source_url):
            normalized_act_id = _normalize_known_act_id(f"celex:{celex}")
            if normalized_act_id and document_kind in ACT_KINDS:
                return normalized_act_id
            return f"celex:{celex}"

    return str(document.get("doc_uid"))


def derive_act_id(
    document: Mapping[str, Any],
    *,
    curated_entry: Mapping[str, Any] | None = None,
) -> str | None:
    if curated_entry and curated_entry.get("expected_external_id"):
        expected = str(curated_entry["expected_external_id"])
        if expected.startswith(("eli:", "isap:", "celex:")):
            normalized_expected = _normalize_known_act_id(expected)
            return normalized_expected or expected

    source_url = select_source_url(document)
    if source_url:
        normalized_source_url = normalize_url(source_url) or source_url
        if "sip.lex.pl" in normalized_source_url:
            if "16903658" in normalized_source_url:
                return "eli:DU/2001/733"
            if "16785996" in normalized_source_url:
                return "isap:WDU19640160093"
        if match := ELI_ACT_URL_PATTERN.search(normalized_source_url):
            year, number = match.groups()
            return f"eli:DU/{year}/{int(number)}"
        if match := ELI_EU_PATTERN.search(normalized_source_url):
            kind, year, number, language = match.groups()
            return f"eli:{kind.lower()}/{year}/{int(number)}/oj/{(language or 'eng').lower()}"
        if match := DZIENNIK_USTAW_PATTERN.search(normalized_source_url):
            year, number = match.groups()
            return f"eli:DU/{year}/{int(number)}"
        if match := ISAP_WDU_PATTERN.search(normalized_source_url):
            return f"isap:{match.group(0).upper()}"
        if celex := _extract_celex(normalized_source_url):
            normalized_celex = _normalize_known_act_id(f"celex:{celex}")
            return normalized_celex or f"celex:{celex}"

    external_ids = document.get("external_ids")
    if isinstance(external_ids, dict):
        if value := external_ids.get("eli"):
            normalized_value = _normalize_known_act_id(str(value))
            return normalized_value or f"eli:{value}"
        if value := external_ids.get("isap_wdu"):
            return f"isap:{value}"

    doc_uid = str(document.get("doc_uid") or "")
    if doc_uid.startswith("eli_pl:DU/"):
        return f"eli:{doc_uid.split(':', 1)[1]}"
    if doc_uid.startswith("isap_pl:"):
        return f"isap:{doc_uid.split(':', 1)[1]}"

    title = clean_title(document.get("canonical_title") or document.get("title"))
    if title and "2001" in title and "733" in title and "Dziennik Ustaw" in title:
        return "eli:DU/2001/733"

    return None


def derive_act_short_name(act_id: str | None, canonical_title: str) -> str:
    if act_id and act_id in KNOWN_ACT_SHORT_NAMES:
        return KNOWN_ACT_SHORT_NAMES[act_id]

    if canonical_title.startswith("Ustawa z dnia 21 czerwca 2001 r. o ochronie praw"):
        return "Ustawa o ochronie praw lokatorow"
    if canonical_title.startswith("Council Directive 93/13/EEC"):
        return "Directive 93/13/EEC"
    if canonical_title.startswith("Regulation (EC) No"):
        return canonical_title
    return canonical_title[:120]


def build_article_node_inventory(nodes: list[Mapping[str, Any]]) -> list[str]:
    ordered = sorted(
        (node for node in nodes if str(node.get("node_id") or "").startswith("art:")),
        key=lambda item: (
            int(item.get("order_index") or 0),
            str(item.get("node_id") or ""),
        ),
    )
    return [str(node["node_id"]) for node in ordered]


def build_key_provisions(article_nodes: list[str]) -> list[str]:
    return article_nodes[:5]


def _should_validate_storage_path_existence(storage_uri: str) -> bool:
    if "://" in storage_uri:
        return False
    if storage_uri.startswith(("document:", "document_sources:")):
        return False
    return storage_uri.startswith(STRICT_STORAGE_PATH_PREFIXES)


def _select_duplicate_owner(
    *,
    doc_uids: list[str],
    docs_by_uid: Mapping[str, Mapping[str, Any]],
    curated_doc_uids: set[str],
) -> str:
    ranked = sorted(
        doc_uids,
        key=lambda doc_uid: (
            -_duplicate_owner_score(
                document=docs_by_uid[doc_uid],
                curated_doc_uids=curated_doc_uids,
            ),
            doc_uid,
        ),
    )
    return ranked[0]


def _duplicate_owner_score(
    *,
    document: Mapping[str, Any],
    curated_doc_uids: set[str],
) -> int:
    doc_uid = str(document.get("doc_uid") or "")
    score = 0
    if doc_uid in curated_doc_uids:
        score += 100
    if "urlsha:" not in doc_uid:
        score += 50
    if document.get("status"):
        score += 25
    if document.get("external_id") or document.get("external_ids"):
        score += 10
    if str(document.get("source_system") or "") in OFFICIAL_SOURCE_SYSTEMS:
        score += 5
    return score


def _source_sort_key(source: Mapping[str, Any]) -> tuple[str, str]:
    fetched_at = str(source.get("fetched_at") or "")
    ingested_at = str(source.get("ingested_at") or "")
    return fetched_at, ingested_at


def _extract_celex(value: str) -> str | None:
    match = CELEX_PATTERN.search(value)
    if match is None:
        return None
    return match.group(1).upper()


def _extract_curia_docid(value: str) -> str | None:
    match = CURIA_DOCID_PATTERN.search(value)
    if match is None:
        return None
    return match.group(1)


def _extract_curia_jcms(value: str) -> str | None:
    match = CURIA_JCMS_PATTERN.search(value)
    if match is None:
        return None
    return f"jcms:{match.group(2)}"


def _normalize_known_act_id(value: str) -> str | None:
    normalized_value = value.strip()
    if normalized_value.startswith("eli:http://data.europa.eu/eli/dir/1993/13/oj"):
        return "eli:dir/1993/13/oj/eng"
    if normalized_value in {
        "celex:31993L0013",
        "eli:dir/1993/13/oj",
        "http://data.europa.eu/eli/dir/1993/13/oj",
    }:
        return "eli:dir/1993/13/oj/eng"
    return None


def _curated_entry_priority(entry: Mapping[str, Any]) -> tuple[int, int, int]:
    status = str(entry.get("status") or "")
    status_priority = {
        "canonical": 5,
        "alias": 4,
        "excluded": 4,
        "article_node": 3,
        "optional": 2,
        "missing_fetch": 1,
    }.get(status, 0)
    return (
        1 if entry.get("required_top_level") else 0,
        status_priority,
        1 if entry.get("position") is None else 0,
    )
