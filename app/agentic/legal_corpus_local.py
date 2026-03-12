from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.agentic.legal_corpus_contract import (
    ExpandRelatedRequest,
    FetchFragmentsRequest,
    ProvenanceRequest,
    SearchRequest,
)
from app.ops.legal_collection import canonicalize_url


_FRAGMENT_PREVIEW_CHARS = 220
_SUPPORTED_BACKEND = "local"
_ACT_SHORT_NAME_PATTERN = re.compile(r"^eli_pl:DU/(?P<year>\d{4})/(?P<position>\d+)$")
_SUPPORTED_FILTER_KEYS = {
    "act_id",
    "category",
    "court_name",
    "doc_uid",
    "document_kind",
    "fetch_strategy",
    "jurisdiction",
    "license_tag",
    "source_hash",
    "source_id",
    "source_system",
    "status",
}
_SUPPORTED_LOCATOR_KEYS = {
    "act_id",
    "court_name",
    "doc_uid",
    "jurisdiction",
    "source_id",
    "source_system",
}

_ACT_SOURCE_SYSTEMS = {
    "eli_pl",
    "isap_pl",
    "lex_pl",
    "eurlex_eu",
    "prawo_pl",
    "uokik_pl",
}
_CASE_LAW_SOURCE_SYSTEMS = {
    "saos_pl",
    "sn_pl",
    "curia_eu",
    "courts_pl",
}
_COURT_NAME_BY_SOURCE_SYSTEM = {
    "curia_eu": "Trybunał Sprawiedliwości UE",
    "sn_pl": "Sąd Najwyższy",
}


@dataclass(frozen=True, slots=True)
class _LocalCorpusDocument:
    doc_uid: str
    source_id: str
    category: str
    source_system: str
    jurisdiction: str
    license_tag: str
    fetch_strategy: str
    source_url: str
    normalized_source_url: str
    final_url: str | None
    source_hash: str
    raw_object_path: Path
    response_meta_path: Path
    doc_root: Path
    normalized_artifact_hint: str
    updated_at: str | None
    downloaded_at: str | None
    http_status: int | None
    content_type: str | None
    text: str

    @property
    def scope(self) -> str:
        if self.source_system in _ACT_SOURCE_SYSTEMS:
            return "acts"
        if self.source_system in _CASE_LAW_SOURCE_SYSTEMS:
            return "case_law"
        return "mixed"

    @property
    def document_kind(self) -> str:
        if self.scope == "acts":
            return "act"
        if self.scope == "case_law":
            return "judgment"
        return "document"

    @property
    def source_label(self) -> str:
        if self.act_short_name:
            return self.act_short_name
        if self.court_name:
            return f"{self.court_name} [{self.source_id}]"
        return self.source_id or self.doc_uid

    @property
    def act_short_name(self) -> str | None:
        match = _ACT_SHORT_NAME_PATTERN.match(self.doc_uid)
        if match is None:
            return None
        return f"Dz.U. {match.group('year')} poz. {match.group('position')}"

    @property
    def court_name(self) -> str | None:
        return _COURT_NAME_BY_SOURCE_SYSTEM.get(self.source_system)

    @property
    def deep_link(self) -> str:
        if self.final_url:
            return self.final_url
        if self.source_url:
            return self.source_url
        return f"local://legal_corpus/{self.doc_uid}"

    @property
    def display_citation(self) -> str:
        if self.act_short_name:
            return f"{self.act_short_name} [{self.doc_uid}]"
        if self.court_name:
            return f"{self.court_name}, {self.doc_uid}"
        if self.document_kind == "judgment":
            return f"Judgment {self.doc_uid}"
        return f"{self.doc_uid} [{self.source_id}]"


@dataclass(frozen=True, slots=True)
class _MatchResult:
    start: int
    end: int
    matched_terms: tuple[str, ...]
    matched_fields: tuple[str, ...]
    field_hits: dict[str, int]


@dataclass(slots=True)
class _SearchConstraintState:
    filter_constraints: dict[str, Any]
    locator_constraints: dict[str, Any]
    applied_filters: dict[str, dict[str, Any]]
    ignored_filters: dict[str, dict[str, Any]]
    unsupported_filters: dict[str, dict[str, Any]]
    limitations: list[str]
    effective_return_level: str


class LocalLegalCorpusTool:
    """Read-only legal corpus adapter for local/dev collections."""

    def __init__(self, *, root: Path) -> None:
        self.root = root.resolve()
        self._documents = self._load_documents()

    def search(self, request: SearchRequest) -> dict[str, Any]:
        query = str(request["query"]).strip()
        scope = str(request["scope"])
        requested_return_level = str(request["return_level"])
        top_k = max(int(request.get("top_k") or 5), 1)
        query_terms = _query_terms(
            query=query,
            expansions=request.get("query_expansions") or [],
        )
        constraint_state = _evaluate_search_constraints(request)

        if not query:
            return {
                "results": [],
                "result_count": 0,
                "total_matches": 0,
                "query": query,
                "scope": scope,
                "return_level": requested_return_level,
                "effective_return_level": constraint_state.effective_return_level,
                "applied_filters": constraint_state.applied_filters,
                "ignored_filters": constraint_state.ignored_filters,
                "unsupported_filters": constraint_state.unsupported_filters,
                "diagnostics": _build_search_diagnostics(
                    query_terms=query_terms,
                    result_count=0,
                    total_matches=0,
                    limitations=[
                        *constraint_state.limitations,
                        "query: empty query string returns no results.",
                    ],
                    effective_return_level=constraint_state.effective_return_level,
                ),
            }

        results: list[dict[str, Any]] = []
        for document in self._documents.values():
            if not _scope_matches(document=document, scope=scope):
                continue
            if not _document_matches_constraints(
                document=document,
                constraints=constraint_state.filter_constraints,
            ):
                continue
            if not _document_matches_constraints(
                document=document,
                constraints=constraint_state.locator_constraints,
            ):
                continue

            match = _best_match(document=document, terms=query_terms)
            if match is None:
                continue

            machine_ref = _build_machine_ref(
                document=document,
                start=match.start,
                end=match.end,
            )
            score = float(len(match.matched_terms) + (0.25 * len(match.matched_fields)))
            results.append(
                {
                    "preview": _snippet(document.text, match.start, match.end),
                    "machine_ref": machine_ref,
                    "display_citation": document.display_citation,
                    "score": score,
                    "score_breakdown": {
                        "matched_terms": len(match.matched_terms),
                        "matched_fields": list(match.matched_fields),
                        "field_hits": match.field_hits,
                        "metadata_match": sum(
                            hits
                            for field_name, hits in match.field_hits.items()
                            if field_name != "text"
                        ),
                    },
                    "why_relevant": _build_why_relevant(
                        matched_terms=match.matched_terms,
                        matched_fields=match.matched_fields,
                    ),
                    "source_label": document.source_label,
                    "document_kind": document.document_kind,
                    "act_short_name": document.act_short_name,
                    "court_name": document.court_name,
                    "judgment_date": None,
                    "version_date": None,
                    "matched_fields": list(match.matched_fields),
                    "deep_link": document.deep_link,
                    "doc_uid": document.doc_uid,
                    "source_hash": document.source_hash,
                    "node_id": machine_ref["node_id"],
                    "unit_id": machine_ref["unit_id"],
                    "page_range": machine_ref["page_range"],
                    "metadata": {
                        "doc_uid": document.doc_uid,
                        "source_id": document.source_id,
                        "scope": document.scope,
                        "category": document.category,
                        "source_system": document.source_system,
                        "jurisdiction": document.jurisdiction,
                        "license_tag": document.license_tag,
                        "return_level": requested_return_level,
                        "effective_return_level": (
                            constraint_state.effective_return_level
                        ),
                        "source_label": document.source_label,
                        "document_kind": document.document_kind,
                        "fetch_strategy": document.fetch_strategy,
                        "collection_updated_at": document.updated_at,
                        "downloaded_at": document.downloaded_at,
                    },
                    "diagnostics": {
                        "backend": _SUPPORTED_BACKEND,
                        "page_truth_status": "not_available_local",
                        "locator_precision": "char_offsets_only",
                    },
                }
            )

        results.sort(
            key=lambda item: (
                -float(item["score"]),
                str(item["doc_uid"]),
            )
        )
        limited = results[:top_k]
        return {
            "results": limited,
            "result_count": len(limited),
            "total_matches": len(results),
            "query": query,
            "scope": scope,
            "return_level": requested_return_level,
            "effective_return_level": constraint_state.effective_return_level,
            "applied_filters": constraint_state.applied_filters,
            "ignored_filters": constraint_state.ignored_filters,
            "unsupported_filters": constraint_state.unsupported_filters,
            "diagnostics": _build_search_diagnostics(
                query_terms=query_terms,
                result_count=len(limited),
                total_matches=len(results),
                limitations=constraint_state.limitations,
                effective_return_level=constraint_state.effective_return_level,
            ),
        }

    def fetch_fragments(self, request: FetchFragmentsRequest) -> dict[str, Any]:
        refs = request["refs"]
        include_neighbors = bool(request.get("include_neighbors", False))
        neighbor_window = max(int(request.get("neighbor_window") or 1), 0)
        max_chars = max(int(request.get("max_chars_per_fragment") or 600), 1)

        fragments: list[dict[str, Any]] = []
        for ref in refs:
            document = self._require_document(ref)
            start, end = _resolve_fragment_bounds(
                ref=ref,
                text=document.text,
            )
            if include_neighbors:
                extra = _FRAGMENT_PREVIEW_CHARS * neighbor_window
                start = max(0, start - extra)
                end = min(len(document.text), end + extra)
            fragment_text = document.text[start:end][:max_chars].strip()
            resolved_locator = _build_locator(start=start, end=end)
            fragments.append(
                {
                    "machine_ref": ref,
                    "doc_uid": document.doc_uid,
                    "source_hash": document.source_hash,
                    "text": fragment_text,
                    "title_path": [document.category, document.source_id],
                    "page_start": None,
                    "page_end": None,
                    "page_range": None,
                    "node_id": ref.get("node_id"),
                    "unit_id": ref.get("unit_id"),
                    "locator": resolved_locator,
                    "locator_precision": "char_offsets_only",
                    "page_truth_status": "not_available_local",
                    "display_citation": document.display_citation,
                    "source_label": document.source_label,
                    "document_kind": document.document_kind,
                    "deep_link": document.deep_link,
                    "citation": {
                        "display_citation": document.display_citation,
                        "deep_link": document.deep_link,
                        "locator_kind": "char_offsets",
                        "page_truth_status": "not_available_local",
                    },
                    "quote_checksum": hashlib.sha256(
                        fragment_text.encode("utf-8")
                    ).hexdigest(),
                    "diagnostics": {
                        "backend": _SUPPORTED_BACKEND,
                        "text_source": "raw_object_text",
                        "fallback_used": True,
                        "fallback_reason": (
                            "Local backend does not expose a normalized fragment "
                            "extraction layer; fragment text is read from the raw "
                            "downloaded object."
                        ),
                        "page_truth_status": "not_available_local",
                        "locator_precision": "char_offsets_only",
                    },
                }
            )

        return {
            "fragments": fragments,
            "ref_count": len(refs),
            "diagnostics": {
                "backend": _SUPPORTED_BACKEND,
                "fragment_source": "raw_object_text",
                "page_truth_status": "not_available_local",
                "fallback_fragment_count": len(fragments),
            },
        }

    def expand_related(self, request: ExpandRelatedRequest) -> dict[str, Any]:
        return {
            "results": [],
            "expanded_from": request["refs"],
            "relation_types": request["relation_types"],
            "status": "not_available_local",
            "why_relevant": (
                "Local legal corpus adapter does not provide relation graph "
                "expansion in this iteration."
            ),
            "explanation": {
                "backend": _SUPPORTED_BACKEND,
                "supported": False,
                "reason": (
                    "The local/dev corpus stores source snapshots only and does not "
                    "persist citation graph, same-case grouping, or supersession "
                    "edges."
                ),
                "requested_relation_types": request["relation_types"],
                "next_supported_backend": "production_corpus_backend",
            },
        }

    def get_provenance(self, request: ProvenanceRequest) -> dict[str, Any]:
        ref = request["ref"]
        include_artifacts = bool(request.get("include_artifacts", False))
        debug = bool(request.get("debug", False))
        document = self._require_document(ref)
        raw_exists = document.raw_object_path.is_file()
        meta_exists = document.response_meta_path.is_file()
        integrity_status = "ok" if raw_exists and meta_exists else "missing_artifact"
        payload: dict[str, Any] = {
            "doc_uid": document.doc_uid,
            "source_hash": document.source_hash,
            "source_url": document.source_url,
            "final_url": document.final_url,
            "normalized_source_url": document.normalized_source_url,
            "license_tag": document.license_tag,
            "source_label": document.source_label,
            "document_kind": document.document_kind,
            "deep_link": document.deep_link,
            "provenance_status": ("ok" if integrity_status == "ok" else "incomplete"),
            "has_history": False,
            "artifact_uri": document.normalized_artifact_hint,
            "normalized_artifact_hint": document.normalized_artifact_hint,
            "current_version": {
                "status": "current_snapshot_only_local",
                "has_history": False,
                "version_date": None,
                "collection_updated_at": document.updated_at,
                "downloaded_at": document.downloaded_at,
                "as_of_date_supported": False,
            },
            "artifact_integrity": {
                "raw_object_exists": raw_exists,
                "response_meta_exists": meta_exists,
                "status": integrity_status,
            },
            "integrity_status": integrity_status,
            "limitations": [
                "Local backend exposes only the currently downloaded snapshot.",
                "Version history and as_of_date replay are not available.",
                "Artifact paths point to local filesystem snapshots, not normalized "
                "Mongo retrieval units.",
            ],
        }
        if include_artifacts:
            payload["raw_object_path"] = str(document.raw_object_path)
            payload["response_meta_path"] = str(document.response_meta_path)
        if debug:
            payload["debug"] = {
                "backend": _SUPPORTED_BACKEND,
                "doc_root": str(document.doc_root),
                "fetch_strategy": document.fetch_strategy,
                "http_status": document.http_status,
                "content_type": document.content_type,
            }
        return payload

    def _load_documents(self) -> dict[str, _LocalCorpusDocument]:
        manifest_path = self.root / "collection_manifest.json"
        docs_dir = self.root / "docs"
        if not self.root.is_dir():
            raise FileNotFoundError(
                f"Scenario 2 local legal corpus root not found: {self.root}"
            )
        if not manifest_path.is_file():
            raise FileNotFoundError(
                f"Scenario 2 local legal corpus manifest is missing: {manifest_path}"
            )
        if not docs_dir.is_dir():
            raise FileNotFoundError(
                f"Scenario 2 local legal corpus docs directory is missing: {docs_dir}"
            )

        documents: dict[str, _LocalCorpusDocument] = {}
        for document_path in sorted(docs_dir.glob("*/document.json")):
            payload = json.loads(document_path.read_text(encoding="utf-8"))
            doc_root = document_path.parent
            raw_object_path = _resolve_stored_path(
                payload.get("raw_object_path"),
                base_dir=doc_root,
            )
            response_meta_path = _resolve_stored_path(
                payload.get("response_meta_path"),
                base_dir=doc_root,
            )
            response_meta = _safe_json_load(response_meta_path)
            headers = response_meta.get("headers") or {}
            source_urls = payload.get("source_urls") or []
            source_url = str(source_urls[0]) if source_urls else ""
            final_url = response_meta.get("final_url")
            documents[str(payload["doc_uid"])] = _LocalCorpusDocument(
                doc_uid=str(payload["doc_uid"]),
                source_id=str(payload.get("source_id") or ""),
                category=str(payload.get("category") or ""),
                source_system=str(payload.get("source_system") or ""),
                jurisdiction=str(payload.get("jurisdiction") or ""),
                license_tag=str(payload.get("license_tag") or ""),
                fetch_strategy=str(payload.get("fetch_strategy") or ""),
                source_url=source_url,
                normalized_source_url=(
                    canonicalize_url(source_url) if source_url else ""
                ),
                final_url=str(final_url) if final_url else None,
                source_hash=str(payload.get("current_source_hash") or ""),
                raw_object_path=raw_object_path,
                response_meta_path=response_meta_path,
                doc_root=doc_root,
                normalized_artifact_hint=_artifact_hint(
                    root=self.root,
                    path=raw_object_path,
                ),
                updated_at=_as_optional_str(payload.get("updated_at")),
                downloaded_at=_as_optional_str(response_meta.get("downloaded_at")),
                http_status=_as_optional_int(response_meta.get("http_status")),
                content_type=_as_optional_str(headers.get("Content-Type")),
                text=_read_text_payload(raw_object_path),
            )

        if not documents:
            raise FileNotFoundError(
                "Scenario 2 local legal corpus does not contain any document.json "
                f"entries under {docs_dir}"
            )

        return documents

    def _require_document(self, ref: dict[str, Any]) -> _LocalCorpusDocument:
        doc_uid = str(ref.get("doc_uid") or "").strip()
        if not doc_uid:
            raise KeyError("machine_ref.doc_uid is required")
        document = self._documents.get(doc_uid)
        if document is None:
            raise KeyError(f"Unknown doc_uid in local legal corpus: {doc_uid}")
        return document


def _query_terms(*, query: str, expansions: list[str]) -> list[str]:
    parts = [query, *expansions]
    terms: list[str] = []
    for part in parts:
        for token in str(part).lower().split():
            cleaned = token.strip()
            if cleaned and cleaned not in terms:
                terms.append(cleaned)
    return terms


def _scope_matches(*, document: _LocalCorpusDocument, scope: str) -> bool:
    if scope == "mixed":
        return True
    return document.scope == scope


def _evaluate_search_constraints(request: SearchRequest) -> _SearchConstraintState:
    filter_constraints: dict[str, Any] = {}
    locator_constraints: dict[str, Any] = {}
    applied_filters = _empty_marker_tree()
    ignored_filters = _empty_marker_tree()
    unsupported_filters = _empty_marker_tree()
    limitations: list[str] = []

    for key, value in (request.get("filters") or {}).items():
        if _is_blank_value(value):
            ignored_filters["filters"][key] = {
                "value": value,
                "reason": "Empty filter value was ignored.",
            }
            continue
        if key in _SUPPORTED_FILTER_KEYS:
            filter_constraints[key] = value
            applied_filters["filters"][key] = value
            continue
        reason = _unsupported_reason(key=key, location="filters")
        unsupported_filters["filters"][key] = {
            "value": value,
            "reason": reason,
        }
        limitations.append(f"filters.{key}: {reason}")

    for key, value in (request.get("locator") or {}).items():
        if _is_blank_value(value):
            ignored_filters["locator"][key] = {
                "value": value,
                "reason": "Empty locator value was ignored.",
            }
            continue
        if key in _SUPPORTED_LOCATOR_KEYS:
            locator_constraints[key] = value
            applied_filters["locator"][key] = value
            continue
        reason = _unsupported_reason(key=key, location="locator")
        unsupported_filters["locator"][key] = {
            "value": value,
            "reason": reason,
        }
        limitations.append(f"locator.{key}: {reason}")

    effective_return_level = "fragment"
    requested_return_level = str(request["return_level"])
    if requested_return_level == "fragment":
        applied_filters["options"]["return_level"] = requested_return_level
    else:
        ignored_filters["options"]["return_level"] = {
            "value": requested_return_level,
            "reason": ("Local backend currently returns fragment candidates only."),
        }
        limitations.append(
            "return_level: local backend currently returns fragment candidates only."
        )

    query_expansions = request.get("query_expansions") or []
    if query_expansions:
        applied_filters["options"]["query_expansions"] = list(query_expansions)

    as_of_date = request.get("as_of_date")
    if as_of_date:
        unsupported_filters["options"]["as_of_date"] = {
            "value": as_of_date,
            "reason": (
                "Local backend stores only the current snapshot and cannot resolve "
                "historical versions by date."
            ),
        }
        limitations.append(
            "as_of_date: local backend stores only the current snapshot."
        )

    include_history = bool(request.get("include_history", False))
    if include_history:
        unsupported_filters["options"]["include_history"] = {
            "value": True,
            "reason": "Local backend does not persist version history.",
        }
        limitations.append(
            "include_history: local backend does not persist version history."
        )

    expand_citations = bool(request.get("expand_citations", False))
    if expand_citations:
        unsupported_filters["options"]["expand_citations"] = {
            "value": True,
            "reason": "Local backend does not maintain citation expansion graph.",
        }
        limitations.append(
            "expand_citations: local backend does not maintain citation graph."
        )

    applied_filters["options"]["top_k"] = max(int(request.get("top_k") or 5), 1)
    return _SearchConstraintState(
        filter_constraints=filter_constraints,
        locator_constraints=locator_constraints,
        applied_filters=applied_filters,
        ignored_filters=ignored_filters,
        unsupported_filters=unsupported_filters,
        limitations=limitations,
        effective_return_level=effective_return_level,
    )


def _build_search_diagnostics(
    *,
    query_terms: list[str],
    result_count: int,
    total_matches: int,
    limitations: list[str],
    effective_return_level: str,
) -> dict[str, Any]:
    return {
        "backend": _SUPPORTED_BACKEND,
        "query_term_count": len(query_terms),
        "result_count": result_count,
        "total_matches": total_matches,
        "effective_return_level": effective_return_level,
        "supports_history": False,
        "supports_citation_expansion": False,
        "supports_page_level_locators": False,
        "limitations": limitations,
    }


def _document_matches_constraints(
    *,
    document: _LocalCorpusDocument,
    constraints: dict[str, Any],
) -> bool:
    for key, expected in constraints.items():
        actual = _document_field_value(document=document, key=key)
        if not _value_matches(actual=actual, expected=expected):
            return False
    return True


def _document_field_value(
    *,
    document: _LocalCorpusDocument,
    key: str,
) -> Any:
    if key == "act_id":
        return document.doc_uid if document.document_kind == "act" else None
    if key == "category":
        return document.category
    if key == "court_name":
        return document.court_name
    if key == "doc_uid":
        return document.doc_uid
    if key == "document_kind":
        return document.document_kind
    if key == "fetch_strategy":
        return document.fetch_strategy
    if key == "jurisdiction":
        return document.jurisdiction
    if key == "license_tag":
        return document.license_tag
    if key == "source_hash":
        return document.source_hash
    if key == "source_id":
        return document.source_id
    if key == "source_system":
        return document.source_system
    if key == "status":
        return ["current", "operational", "current_snapshot_only_local"]
    return None


def _value_matches(*, actual: Any, expected: Any) -> bool:
    if actual is None:
        return False
    if isinstance(expected, (list, tuple, set)) and not isinstance(expected, str):
        return any(_value_matches(actual=actual, expected=item) for item in expected)
    if isinstance(actual, (list, tuple, set)) and not isinstance(actual, str):
        return any(_value_matches(actual=item, expected=expected) for item in actual)
    if isinstance(actual, str) or isinstance(expected, str):
        return str(actual).casefold() == str(expected).casefold()
    return actual == expected


def _best_match(
    *,
    document: _LocalCorpusDocument,
    terms: list[str],
) -> _MatchResult | None:
    searchable_fields = _searchable_fields(document)
    matched_terms: set[str] = set()
    matched_fields: set[str] = set()
    field_hits: dict[str, int] = {}
    lower_text = document.text.lower()
    first_index = len(document.text)

    for term in terms:
        term_matched = False
        for field_name, value in searchable_fields.items():
            if term in value:
                matched_fields.add(field_name)
                field_hits[field_name] = field_hits.get(field_name, 0) + 1
                term_matched = True
        if term_matched:
            matched_terms.add(term)
            text_index = lower_text.find(term)
            if text_index >= 0:
                first_index = min(first_index, text_index)

    if not matched_terms:
        return None

    if first_index == len(document.text):
        first_index = 0
    start = max(0, first_index - (_FRAGMENT_PREVIEW_CHARS // 2))
    end = min(len(document.text), start + _FRAGMENT_PREVIEW_CHARS)
    return _MatchResult(
        start=start,
        end=end,
        matched_terms=tuple(sorted(matched_terms)),
        matched_fields=tuple(sorted(matched_fields)),
        field_hits=field_hits,
    )


def _searchable_fields(document: _LocalCorpusDocument) -> dict[str, str]:
    fields = {
        "doc_uid": document.doc_uid,
        "source_id": document.source_id,
        "category": document.category,
        "source_system": document.source_system,
        "source_label": document.source_label,
        "display_citation": document.display_citation,
        "document_kind": document.document_kind,
        "text": document.text,
    }
    if document.act_short_name:
        fields["act_short_name"] = document.act_short_name
    if document.court_name:
        fields["court_name"] = document.court_name
    return {key: value.lower() for key, value in fields.items() if value}


def _build_why_relevant(
    *,
    matched_terms: tuple[str, ...],
    matched_fields: tuple[str, ...],
) -> str:
    return (
        "Matched local corpus terms "
        + ", ".join(matched_terms)
        + " in fields "
        + ", ".join(matched_fields)
        + "."
    )


def _build_machine_ref(
    *,
    document: _LocalCorpusDocument,
    start: int,
    end: int,
) -> dict[str, Any]:
    return {
        "doc_uid": document.doc_uid,
        "source_hash": document.source_hash,
        "unit_id": f"fragment:{start}:{end}",
        "node_id": f"offset:{start}",
        "page_range": None,
        "locator": _build_locator(start=start, end=end),
    }


def _build_locator(*, start: int, end: int) -> dict[str, Any]:
    return {
        "start_char": start,
        "end_char": end,
        "backend": _SUPPORTED_BACKEND,
        "precision": "char_offsets_only",
        "page_truth": "not_available_local",
    }


def _resolve_fragment_bounds(
    *,
    ref: dict[str, Any],
    text: str,
) -> tuple[int, int]:
    locator = ref.get("locator")
    if isinstance(locator, dict):
        start = int(locator.get("start_char") or 0)
        end = int(locator.get("end_char") or min(len(text), _FRAGMENT_PREVIEW_CHARS))
        return max(start, 0), min(max(end, start + 1), len(text))

    unit_id = str(ref.get("unit_id") or "")
    if unit_id.startswith("fragment:"):
        _, raw_start, raw_end = unit_id.split(":", 2)
        start = int(raw_start)
        end = int(raw_end)
        return max(start, 0), min(max(end, start + 1), len(text))

    return 0, min(len(text), _FRAGMENT_PREVIEW_CHARS)


def _snippet(text: str, start: int, end: int) -> str:
    return text[start:end].strip()


def _read_text_payload(path: Path) -> str:
    if not path.is_file():
        return ""
    data = path.read_bytes()
    return data.decode("utf-8", errors="ignore")


def _safe_json_load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _artifact_hint(*, root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _resolve_stored_path(value: Any, *, base_dir: Path) -> Path:
    raw_value = str(value or "").strip()
    if not raw_value:
        return base_dir / "__missing__"
    path = Path(raw_value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _empty_marker_tree() -> dict[str, dict[str, Any]]:
    return {"filters": {}, "locator": {}, "options": {}}


def _unsupported_reason(*, key: str, location: str) -> str:
    specific_reasons = {
        "issue_tags": "Local backend does not index issue tags.",
        "facts_tags": "Local backend does not index fact tags.",
        "court_level": "Local backend does not persist court hierarchy metadata.",
        "judgment_date": "Local backend does not persist normalized judgment dates.",
        "related_provisions": "Local backend does not persist citation-linked provisions.",
        "legal_role": "Local backend does not persist legal role metadata.",
        "case_signature": "Local backend does not persist normalized case signatures.",
        "article": "Local backend does not expose normalized article-level locators.",
    }
    default_reason = (
        f"Local backend does not support {location} key '{key}' for retrieval."
    )
    return specific_reasons.get(key, default_reason)


def _is_blank_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _as_optional_str(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _as_optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)
