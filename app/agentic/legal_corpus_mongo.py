from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping, Protocol, Sequence

from legal_ingest.config import MongoConfig
from legal_ingest.mongo import MongoRuntime
from legal_ingest.normalization import (
    ACT_KINDS,
    build_current_source_index,
    normalize_url,
)

from app.agentic.legal_corpus_contract import (
    ExpandRelatedRequest,
    FetchFragmentsRequest,
    ProvenanceRequest,
    SearchRequest,
)


_RETRIEVAL_UNITS_COLLECTION = "retrieval_units"
_CITATION_RESOLUTIONS_COLLECTION = "citation_resolutions"
_RETRIEVAL_INDEX_RUNS_COLLECTION = "retrieval_index_runs"
_DOCUMENTS_COLLECTION = "documents"
_DOCUMENT_SOURCES_COLLECTION = "document_sources"
_NODES_COLLECTION = "nodes"
_PAGES_COLLECTION = "pages"
_CITATIONS_COLLECTION = "citations"
_INGEST_RUNS_COLLECTION = "ingest_runs"

_SUPPORTED_FILTER_KEYS = {
    "act_id",
    "canonical_doc_uid",
    "court_level",
    "current_only",
    "current_status",
    "doc_uid",
    "document_kind",
    "facts_tags",
    "is_indexable",
    "issue_tags",
    "jurisdiction",
    "judgment_date",
    "legal_role",
    "operational_status",
    "related_provisions",
    "same_case_group_id",
    "source_hash",
    "status",
}
_SUPPORTED_LOCATOR_KEYS = {"doc_uid", "node_id", "source_hash", "unit_id"}
_ACT_ROLES = {"PROCESS_NORM", "SUBSTANTIVE_NORM", "TENANCY_NORM", "EU_NORM"}
_CASELAW_KINDS = {"CASELAW"}
_MAX_PREVIEW_CHARS = 220
_TOKEN_FILTER_KEYS = {"issue_tags", "facts_tags", "related_provisions"}


class _CollectionProtocol(Protocol):
    def delete_many(self, query: dict[str, Any]) -> Any: ...

    def insert_many(self, rows: Sequence[dict[str, Any]]) -> Any: ...

    def insert_one(self, row: dict[str, Any]) -> Any: ...

    def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> dict[str, Any] | None: ...

    def create_index(self, keys: list[tuple[str, int]], **kwargs: Any) -> Any: ...


class _MongoRuntimeProtocol(Protocol):
    config: Any

    def load_collection(
        self,
        name: str,
        *,
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]: ...

    def collection(self, name: str) -> _CollectionProtocol: ...


@dataclass(frozen=True, slots=True)
class RetrievalIndexBuildReport:
    built_at: str
    source_ingest_run_id: str | None
    units_count: int
    citation_resolutions_count: int
    documents_count: int


@dataclass(frozen=True, slots=True)
class _DocumentVersionSelection:
    source_hash: str | None
    version_status: str
    current_only: bool
    historical_version_found: bool
    effective_from: str | None
    effective_to: str | None
    version_date: str | None


@dataclass(frozen=True, slots=True)
class _SearchCandidate:
    unit: dict[str, Any]
    score: float
    matched_terms: tuple[str, ...]
    matched_fields: tuple[str, ...]
    score_breakdown: dict[str, Any]


class MongoLegalCorpusMaterializer:
    """Build materialized retrieval collections on top of legal_ingest Mongo data."""

    def __init__(self, *, runtime: _MongoRuntimeProtocol) -> None:
        self._runtime = runtime

    def rebuild(self) -> RetrievalIndexBuildReport:
        documents = self._runtime.load_collection(
            _DOCUMENTS_COLLECTION, projection={"_id": 0}
        )
        document_sources = self._runtime.load_collection(
            _DOCUMENT_SOURCES_COLLECTION,
            projection={"_id": 0},
        )
        nodes = self._runtime.load_collection(_NODES_COLLECTION, projection={"_id": 0})
        pages = self._runtime.load_collection(_PAGES_COLLECTION, projection={"_id": 0})
        citations = self._runtime.load_collection(
            _CITATIONS_COLLECTION,
            projection={"_id": 0},
        )
        ingest_runs = self._runtime.load_collection(
            _INGEST_RUNS_COLLECTION,
            projection={"_id": 0},
        )

        retrieval_units = _dedupe_retrieval_units(
            _build_retrieval_units(
                documents=documents,
                document_sources=document_sources,
                nodes=nodes,
                pages=pages,
            )
        )
        citation_resolutions = _build_citation_resolutions(
            citations=citations,
            documents=documents,
        )
        latest_successful_ingest = _latest_successful_ingest_run(ingest_runs)
        built_at = _utc_now_build_iso()
        build_id = f"retrieval-index:{built_at}"
        retrieval_collection_name = _materialized_collection_name(
            _RETRIEVAL_UNITS_COLLECTION,
            build_id=build_id,
        )
        resolutions_collection_name = _materialized_collection_name(
            _CITATION_RESOLUTIONS_COLLECTION,
            build_id=build_id,
        )

        retrieval_collection = self._runtime.collection(retrieval_collection_name)
        if retrieval_units:
            retrieval_collection.insert_many(retrieval_units)

        resolutions_collection = self._runtime.collection(resolutions_collection_name)
        if citation_resolutions:
            resolutions_collection.insert_many(citation_resolutions)

        _ensure_materialized_indexes(
            self._runtime,
            retrieval_units_collection=retrieval_collection_name,
            citation_resolutions_collection=resolutions_collection_name,
        )

        index_runs_collection = self._runtime.collection(
            _RETRIEVAL_INDEX_RUNS_COLLECTION
        )
        index_runs_collection.insert_one(
            {
                "build_id": build_id,
                "built_at": built_at,
                "source_ingest_run_id": (
                    str(latest_successful_ingest.get("run_id"))
                    if latest_successful_ingest
                    else None
                ),
                "retrieval_units_collection": retrieval_collection_name,
                "citation_resolutions_collection": resolutions_collection_name,
                "source_ingest_finished_at": (
                    _as_optional_iso(latest_successful_ingest.get("finished_at"))
                    if latest_successful_ingest
                    else None
                ),
                "documents_count": len(documents),
                "units_count": len(retrieval_units),
                "citation_resolutions_count": len(citation_resolutions),
                "status": "completed",
            }
        )
        return RetrievalIndexBuildReport(
            built_at=built_at,
            source_ingest_run_id=(
                str(latest_successful_ingest.get("run_id"))
                if latest_successful_ingest
                else None
            ),
            units_count=len(retrieval_units),
            citation_resolutions_count=len(citation_resolutions),
            documents_count=len(documents),
        )


class MongoLegalCorpusTool:
    """Read-only legal corpus adapter over Mongo-derived retrieval units."""

    def __init__(
        self,
        *,
        mongo_config: MongoConfig | None = None,
        runtime: _MongoRuntimeProtocol | None = None,
        auto_materialize: bool = True,
    ) -> None:
        self._owns_runtime = runtime is None
        self._materialization_warning: str | None = None
        if runtime is None:
            mongo_runtime = MongoRuntime(mongo_config or MongoConfig())
            mongo_runtime.connect()
            self._runtime: _MongoRuntimeProtocol = mongo_runtime
        else:
            self._runtime = runtime
        if auto_materialize:
            self.ensure_materialized_index()

    def ensure_materialized_index(self) -> RetrievalIndexBuildReport | None:
        existing_index_runs = self._runtime.load_collection(
            _RETRIEVAL_INDEX_RUNS_COLLECTION,
            projection={"_id": 0},
        )
        latest_index_run = _latest_retrieval_index_run(existing_index_runs)
        existing_units = self._load_materialized_collection(
            _RETRIEVAL_UNITS_COLLECTION,
            index_run=latest_index_run,
            projection={"_id": 0, "unit_id": 1},
        )
        ingest_runs = self._runtime.load_collection(
            _INGEST_RUNS_COLLECTION,
            projection={"_id": 0},
        )
        latest_ingest = _latest_successful_ingest_run(ingest_runs)
        if existing_units and _is_index_fresh(latest_ingest, latest_index_run):
            self._materialization_warning = None
            return None
        materializer = MongoLegalCorpusMaterializer(runtime=self._runtime)
        try:
            report = materializer.rebuild()
        except Exception as error:
            if existing_units and latest_index_run is not None:
                self._materialization_warning = (
                    "Materialized retrieval rebuild failed; continuing with the "
                    f"last completed build. Details: {error}"
                )
                return None
            raise
        self._materialization_warning = None
        return report

    def search(self, request: SearchRequest) -> dict[str, Any]:
        started_at = time.perf_counter()
        query = str(request["query"]).strip()
        scope = str(request["scope"])
        requested_return_level = str(request["return_level"])
        top_k = max(int(request.get("top_k") or 5), 1)

        index_context = self._index_context()
        documents = self._documents_by_uid()
        document_sources = self._document_sources_by_doc_uid()
        units = self._load_active_retrieval_units()
        resolutions = self._load_active_citation_resolutions()
        query_terms = _query_terms(
            query=query,
            expansions=request.get("query_expansions") or [],
        )
        constraint_state = _evaluate_search_constraints(request)
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        as_of_date = _parse_date(request.get("as_of_date"))

        if not query_terms:
            effective_return_level = _effective_return_level(
                requested_return_level=requested_return_level,
                results=[],
            )
            payload = {
                "results": [],
                "result_count": 0,
                "total_matches": 0,
                "query": query,
                "scope": scope,
                "return_level": requested_return_level,
                "effective_return_level": effective_return_level,
                "applied_filters": constraint_state["applied_filters"],
                "ignored_filters": constraint_state["ignored_filters"],
                "unsupported_filters": constraint_state["unsupported_filters"],
                "diagnostics": _build_search_diagnostics(
                    backend="mongo",
                    query_terms=query_terms,
                    total_matches=0,
                    result_count=0,
                    effective_return_level=effective_return_level,
                    index_context=index_context,
                    limitations=["query: empty query string returns no results."],
                    historical_version_not_found=[],
                    filter_semantics=constraint_state["filter_semantics"],
                    include_history_status=constraint_state["include_history_status"],
                    filter_aliases=constraint_state["filter_aliases"],
                    returned_result_levels=[],
                ),
            }
            payload["audit"] = _build_tool_audit_payload(
                tool_name="search",
                request=request,
                started_at=started_at,
                results=payload["results"],
                warnings=_audit_warnings_from_payload(payload),
                query_hash=query_hash,
            )
            return payload

        selected_versions, historical_missing = _select_versions_for_search(
            documents=documents,
            document_sources=document_sources,
            filters=constraint_state["filter_constraints"],
            as_of_date=as_of_date,
            include_history=constraint_state["include_history_applied"],
        )
        historical_missing = [
            doc_uid
            for doc_uid in historical_missing
            if doc_uid in documents
            and _scope_matches(
                unit={"document_kind": documents[doc_uid].get("document_kind")},
                scope=scope,
            )
            and documents[doc_uid].get("operational_status") == "operational"
            and bool(documents[doc_uid].get("is_indexable"))
        ]

        candidates: list[_SearchCandidate] = []
        for unit in units:
            if not _scope_matches(unit=unit, scope=scope):
                continue
            if not _unit_matches_constraints(
                unit=unit,
                constraints=constraint_state["filter_constraints"],
            ):
                continue
            if not _unit_matches_constraints(
                unit=unit,
                constraints=constraint_state["locator_constraints"],
            ):
                continue
            if not _is_operational_search_candidate(unit):
                continue

            version_selection = selected_versions.get(str(unit.get("doc_uid")))
            if version_selection is not None and version_selection.source_hash:
                if str(unit.get("source_hash") or "") != version_selection.source_hash:
                    continue
            elif as_of_date is not None:
                continue

            candidate = _score_unit(unit=unit, query_terms=query_terms)
            if candidate is None:
                continue
            candidates.append(candidate)

        if bool(request.get("expand_citations")):
            candidates = _expand_candidates_one_hop(
                candidates=candidates,
                units=units,
                resolutions=resolutions,
                top_k=top_k,
            )

        deduped = _dedupe_candidates(
            candidates=candidates,
            include_history=constraint_state["include_history_applied"],
        )
        limited = _interleave_mixed_candidates(
            candidates=deduped,
            scope=scope,
            top_k=top_k,
        )
        results = _build_search_results(
            candidates=limited,
            requested_return_level=requested_return_level,
            documents=documents,
            selected_versions=selected_versions,
        )
        effective_return_level = _effective_return_level(
            requested_return_level=requested_return_level,
            results=results,
        )
        returned_result_levels = _returned_result_levels(results)

        payload = {
            "results": results,
            "result_count": len(results),
            "total_matches": len(deduped),
            "query": query,
            "scope": scope,
            "return_level": requested_return_level,
            "effective_return_level": effective_return_level,
            "applied_filters": constraint_state["applied_filters"],
            "ignored_filters": constraint_state["ignored_filters"],
            "unsupported_filters": constraint_state["unsupported_filters"],
            "diagnostics": _build_search_diagnostics(
                backend="mongo",
                query_terms=query_terms,
                total_matches=len(deduped),
                result_count=len(results),
                effective_return_level=effective_return_level,
                index_context=index_context,
                limitations=constraint_state["limitations"],
                historical_version_not_found=historical_missing,
                filter_semantics=constraint_state["filter_semantics"],
                include_history_status=constraint_state["include_history_status"],
                filter_aliases=constraint_state["filter_aliases"],
                returned_result_levels=returned_result_levels,
            ),
        }
        payload["audit"] = _build_tool_audit_payload(
            tool_name="search",
            request=request,
            started_at=started_at,
            results=payload["results"],
            warnings=_audit_warnings_from_payload(payload),
            query_hash=query_hash,
        )
        return payload

    def fetch_fragments(self, request: FetchFragmentsRequest) -> dict[str, Any]:
        started_at = time.perf_counter()
        refs = request["refs"]
        include_neighbors = bool(request.get("include_neighbors", False))
        neighbor_window = max(int(request.get("neighbor_window") or 1), 0)
        max_chars = max(int(request.get("max_chars_per_fragment") or 800), 1)

        units = self._load_active_retrieval_units()
        units_by_key = _index_units_by_key(units)
        documents = self._documents_by_uid()
        fragments: list[dict[str, Any]] = []
        diagnostics: list[str] = []

        for ref in refs:
            unit = _resolve_unit_from_ref(ref=ref, units_by_key=units_by_key)
            if unit is None:
                diagnostics.append(
                    f"Fragment not found for ref: {json.dumps(ref, ensure_ascii=False)}"
                )
                continue
            neighbors = _neighbor_units(
                unit=unit,
                units=units,
                window=neighbor_window if include_neighbors else 0,
            )
            fragment_text = "\n".join(
                _trim_excerpt(str(item.get("text") or ""), max_chars=max_chars)
                for item in neighbors
                if str(item.get("text") or "").strip()
            ).strip()
            if not fragment_text:
                diagnostics.append(
                    f"Fragment text is empty for unit_id={unit.get('unit_id')}"
                )
                continue
            quote_checksum = hashlib.sha256(fragment_text.encode("utf-8")).hexdigest()
            source_hash = str(unit.get("source_hash") or "")
            doc_uid = str(unit.get("doc_uid") or "")
            document = documents.get(doc_uid, {})
            locator = dict(unit.get("locator") or {})
            if not locator:
                locator = {
                    "unit_id": unit.get("unit_id"),
                    "node_id": unit.get("node_id"),
                    "page_start": unit.get("page_start"),
                    "page_end": unit.get("page_end"),
                }
            fragments.append(
                {
                    "machine_ref": ref,
                    "doc_uid": doc_uid,
                    "source_hash": source_hash,
                    "text": fragment_text,
                    "title_path": list(unit.get("title_path") or []),
                    "page_start": unit.get("page_start"),
                    "page_end": unit.get("page_end"),
                    "page_range": _page_range(
                        unit.get("page_start"),
                        unit.get("page_end"),
                    ),
                    "node_id": unit.get("node_id"),
                    "unit_id": unit.get("unit_id"),
                    "locator": locator,
                    "locator_precision": unit.get("locator_precision")
                    or "retrieval_unit_locator",
                    "page_truth_status": unit.get("page_truth_status")
                    or "materialized",
                    "display_citation": _display_citation(document, unit),
                    "source_label": _source_label(document, unit),
                    "document_kind": unit.get("document_kind"),
                    "deep_link": _deep_link(document, unit),
                    "citation": {
                        "display_citation": _display_citation(document, unit),
                        "deep_link": _deep_link(document, unit),
                        "locator_kind": "materialized_locator",
                        "page_truth_status": unit.get("page_truth_status")
                        or "materialized",
                    },
                    "quote_checksum": quote_checksum,
                    "diagnostics": {
                        "backend": "mongo",
                        "text_source": unit.get("text_source") or "retrieval_units",
                        "fallback_used": bool(unit.get("fallback_used", False)),
                        "page_truth_status": unit.get("page_truth_status")
                        or "materialized",
                        "locator_precision": unit.get("locator_precision")
                        or "retrieval_unit_locator",
                    },
                }
            )

        payload = {
            "fragments": fragments,
            "ref_count": len(refs),
            "diagnostics": {
                "backend": "mongo",
                "fragment_source": "retrieval_units",
                "warnings": diagnostics,
                "fallback_fragment_count": sum(
                    1
                    for item in fragments
                    if bool(item.get("diagnostics", {}).get("fallback_used"))
                ),
            },
        }
        payload["audit"] = _build_tool_audit_payload(
            tool_name="fetch_fragments",
            request=request,
            started_at=started_at,
            results=payload["fragments"],
            warnings=_audit_warnings_from_payload(payload),
        )
        return payload

    def expand_related(self, request: ExpandRelatedRequest) -> dict[str, Any]:
        started_at = time.perf_counter()
        refs = request["refs"]
        relation_types = request["relation_types"]
        top_k = max(int(request.get("top_k") or 5), 1)
        documents = self._documents_by_uid()
        resolutions = self._load_active_citation_resolutions()
        units = self._load_active_retrieval_units()

        base_doc_uids = {
            str(ref.get("doc_uid") or "") for ref in refs if ref.get("doc_uid")
        }
        results: list[dict[str, Any]] = []
        explanations: list[dict[str, Any]] = []
        warnings: list[str] = []

        for relation_type in relation_types:
            if relation_type in {"cites", "cited_by"}:
                matches = _expand_via_resolution_layer(
                    relation_type=relation_type,
                    base_doc_uids=base_doc_uids,
                    resolutions=resolutions,
                    documents=documents,
                    units=units,
                )
                explanations.append(
                    {
                        "relation_type": relation_type,
                        "resolver": "citation_resolutions",
                        "match_count": len(matches),
                    }
                )
                results.extend(matches)
                continue
            if relation_type == "same_case":
                matches = _expand_same_case(
                    base_doc_uids=base_doc_uids,
                    documents=documents,
                    units=units,
                )
                explanations.append(
                    {
                        "relation_type": relation_type,
                        "resolver": "same_case_group_id",
                        "match_count": len(matches),
                    }
                )
                results.extend(matches)
                continue
            if relation_type == "supersedes":
                matches = _expand_supersedes(
                    base_doc_uids=base_doc_uids,
                    documents=documents,
                    units=units,
                )
                explanations.append(
                    {
                        "relation_type": relation_type,
                        "resolver": "superseded_by",
                        "match_count": len(matches),
                    }
                )
                results.extend(matches)
                continue
            if relation_type == "related_provision":
                matches = _expand_related_provisions(
                    base_doc_uids=base_doc_uids,
                    documents=documents,
                    units=units,
                )
                explanations.append(
                    {
                        "relation_type": relation_type,
                        "resolver": "related_provisions",
                        "match_count": len(matches),
                    }
                )
                results.extend(matches)
                continue
            warnings.append(
                f"Unsupported relation_type for mongo backend: {relation_type}"
            )

        deduped = _dedupe_related_results(results)[:top_k]
        payload = {
            "results": deduped,
            "expanded_from": refs,
            "relation_types": relation_types,
            "status": "ok",
            "why_relevant": "Related authority candidates resolved via materialized relations.",
            "explanation": {
                "backend": "mongo",
                "supported": True,
                "relation_resolvers": explanations,
                "used_resolution_layer": True,
            },
        }
        payload["audit"] = _build_tool_audit_payload(
            tool_name="expand_related",
            request=request,
            started_at=started_at,
            results=payload["results"],
            warnings=warnings,
        )
        return payload

    def get_provenance(self, request: ProvenanceRequest) -> dict[str, Any]:
        started_at = time.perf_counter()
        ref = request["ref"]
        include_artifacts = bool(request.get("include_artifacts", False))
        debug = bool(request.get("debug", False))

        documents = self._documents_by_uid()
        document_sources = self._document_sources_by_doc_uid()
        doc_uid = str(ref.get("doc_uid") or "")
        if not doc_uid:
            raise KeyError("machine_ref.doc_uid is required")
        document = documents.get(doc_uid)
        if document is None:
            raise KeyError(f"Unknown doc_uid in Mongo legal corpus: {doc_uid}")

        requested_source_hash = str(ref.get("source_hash") or "")
        source = _resolve_provenance_source(
            document=document,
            document_sources=document_sources.get(doc_uid, []),
            source_hash=requested_source_hash,
        )
        source_hash = str(
            source.get("source_hash") or document.get("current_source_hash") or ""
        )
        artifact_manifest = _artifact_manifest(source)
        integrity_status = str(source.get("integrity_status") or "unknown")
        payload: dict[str, Any] = {
            "doc_uid": doc_uid,
            "source_hash": source_hash,
            "source_url": document.get("source_url"),
            "final_url": source.get("final_url") or document.get("source_url"),
            "normalized_source_url": source.get("final_url")
            or document.get("normalized_source_url")
            or normalize_url(document.get("source_url")),
            "license_tag": document.get("license_tag"),
            "source_label": _source_label(document, None),
            "document_kind": document.get("document_kind"),
            "deep_link": _deep_link(document, None),
            "provenance_status": "ok"
            if integrity_status in {"ok", "manifest_only"}
            else "incomplete",
            "has_history": len(document_sources.get(doc_uid, [])) > 1,
            "artifact_uri": source.get("storage_uri_normalized")
            or source.get("raw_object_path"),
            "normalized_artifact_hint": artifact_manifest.get("normalized_nodes_uri")
            or artifact_manifest.get("normalized_pages_uri")
            or source.get("storage_uri_normalized"),
            "current_version": {
                "status": document.get("current_status") or "current",
                "has_history": len(document_sources.get(doc_uid, [])) > 1,
                "version_date": _as_optional_iso(source.get("version_date")),
                "effective_from": _as_optional_iso(source.get("effective_from")),
                "effective_to": _as_optional_iso(source.get("effective_to")),
                "is_current_source": bool(source.get("is_current_source")),
                "version_kind": source.get("version_kind") or "current",
            },
            "artifact_integrity": {
                "status": integrity_status,
                "storage_backend": source.get("storage_backend") or "unknown",
                "availability_flags": artifact_manifest.get("availability_flags") or {},
            },
            "integrity_status": integrity_status,
            "storage_backend": source.get("storage_backend") or "unknown",
            "storage_uri_normalized": source.get("storage_uri_normalized")
            or source.get("raw_object_path"),
            "artifact_manifest": artifact_manifest,
            "version": {
                "effective_from": _as_optional_iso(source.get("effective_from")),
                "effective_to": _as_optional_iso(source.get("effective_to")),
                "version_date": _as_optional_iso(source.get("version_date")),
                "version_kind": source.get("version_kind") or "current",
                "is_current_source": bool(source.get("is_current_source")),
            },
        }
        if include_artifacts:
            payload["raw_object_path"] = source.get("raw_object_path")
            payload["response_meta_path"] = source.get("response_meta_path")
        if debug:
            payload["debug"] = {
                "backend": "mongo",
                "requested_ref": ref,
                "document_status": document.get("status"),
                "operational_status": document.get("operational_status"),
            }
        payload["audit"] = _build_tool_audit_payload(
            tool_name="get_provenance",
            request=request,
            started_at=started_at,
            results=[{"machine_ref": ref}],
            warnings=[],
        )
        return payload

    def _load_active_retrieval_units(self) -> list[dict[str, Any]]:
        return self._load_materialized_collection(
            _RETRIEVAL_UNITS_COLLECTION,
            index_run=self._active_index_run(),
            projection={"_id": 0},
        )

    def _load_active_citation_resolutions(self) -> list[dict[str, Any]]:
        return self._load_materialized_collection(
            _CITATION_RESOLUTIONS_COLLECTION,
            index_run=self._active_index_run(),
            projection={"_id": 0},
        )

    def _load_materialized_collection(
        self,
        collection_name: str,
        *,
        index_run: Mapping[str, Any] | None,
        projection: dict[str, int] | None,
    ) -> list[dict[str, Any]]:
        active_collection = _materialized_collection_for_index_run(
            collection_name=collection_name,
            index_run=index_run,
        )
        return self._runtime.load_collection(
            active_collection,
            projection=projection,
        )

    def _active_index_run(self) -> dict[str, Any] | None:
        return _latest_retrieval_index_run(
            self._runtime.load_collection(
                _RETRIEVAL_INDEX_RUNS_COLLECTION,
                projection={"_id": 0},
            )
        )

    def _documents_by_uid(self) -> dict[str, dict[str, Any]]:
        documents = self._runtime.load_collection(
            _DOCUMENTS_COLLECTION, projection={"_id": 0}
        )
        return {
            str(document.get("doc_uid")): _normalized_document(document)
            for document in documents
            if document.get("doc_uid")
        }

    def _document_sources_by_doc_uid(self) -> dict[str, list[dict[str, Any]]]:
        documents = self._runtime.load_collection(
            _DOCUMENTS_COLLECTION, projection={"_id": 0}
        )
        document_sources = self._runtime.load_collection(
            _DOCUMENT_SOURCES_COLLECTION,
            projection={"_id": 0},
        )
        current_sources = build_current_source_index(documents, document_sources)
        grouped: dict[str, list[dict[str, Any]]] = {}
        for source in document_sources:
            doc_uid = str(source.get("doc_uid") or "")
            if not doc_uid:
                continue
            grouped.setdefault(doc_uid, []).append(
                _normalized_document_source(
                    document=next(
                        (
                            item
                            for item in documents
                            if str(item.get("doc_uid") or "") == doc_uid
                        ),
                        {},
                    ),
                    source=source,
                    current_source=current_sources.get(doc_uid),
                )
            )
        for sources in grouped.values():
            sources.sort(key=_document_source_sort_key, reverse=True)
        return grouped

    def _index_context(self) -> dict[str, Any]:
        ingest_runs = self._runtime.load_collection(
            _INGEST_RUNS_COLLECTION,
            projection={"_id": 0},
        )
        index_runs = self._runtime.load_collection(
            _RETRIEVAL_INDEX_RUNS_COLLECTION,
            projection={"_id": 0},
        )
        latest_ingest = _latest_successful_ingest_run(ingest_runs)
        latest_index = _latest_retrieval_index_run(index_runs)
        freshness_status = (
            "fresh" if _is_index_fresh(latest_ingest, latest_index) else "stale"
        )
        warnings = (
            []
            if freshness_status == "fresh"
            else ["Retrieval index is older than the latest successful ingest_run."]
        )
        if self._materialization_warning:
            warnings.append(self._materialization_warning)
        return {
            "index_freshness_status": freshness_status,
            "latest_successful_ingest_run_id": (
                str(latest_ingest.get("run_id")) if latest_ingest else None
            ),
            "retrieval_index_ingest_run_id": (
                str(latest_index.get("source_ingest_run_id"))
                if latest_index and latest_index.get("source_ingest_run_id")
                else None
            ),
            "index_built_at": (
                _as_optional_iso(latest_index.get("built_at")) if latest_index else None
            ),
            "warnings": warnings,
        }


def build_mongo_runtime(
    *,
    mongo_uri: str,
    mongo_db_name: str,
) -> MongoRuntime:
    runtime = MongoRuntime(MongoConfig(uri=mongo_uri, db_name=mongo_db_name))
    runtime.connect()
    return runtime


def _build_retrieval_units(
    *,
    documents: list[dict[str, Any]],
    document_sources: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    docs_by_uid = {
        str(document.get("doc_uid")): _normalized_document(document)
        for document in documents
        if document.get("doc_uid")
    }
    current_sources = build_current_source_index(documents, document_sources)
    sources_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    sources_by_doc_uid: dict[str, list[dict[str, Any]]] = {}
    for source in document_sources:
        doc_uid = str(source.get("doc_uid") or "")
        source_hash = str(source.get("source_hash") or "")
        if not doc_uid or not source_hash:
            continue
        normalized = _normalized_document_source(
            document=docs_by_uid.get(doc_uid, {}),
            source=source,
            current_source=current_sources.get(doc_uid),
        )
        sources_by_key[(doc_uid, source_hash)] = normalized
        sources_by_doc_uid.setdefault(doc_uid, []).append(normalized)

    units: list[dict[str, Any]] = []
    for document in docs_by_uid.values():
        doc_uid = str(document.get("doc_uid") or "")
        source_candidates = sources_by_doc_uid.get(doc_uid, [])
        grouped_nodes = [
            node
            for node in nodes
            if str(node.get("doc_uid") or "") == doc_uid
            and str(node.get("text") or "").strip()
        ]
        grouped_pages = [
            page
            for page in pages
            if str(page.get("doc_uid") or "") == doc_uid
            and str(page.get("text") or "").strip()
        ]
        if grouped_nodes:
            for node in grouped_nodes:
                source_hash = _resolve_source_hash(
                    document=document,
                    source_hash=str(node.get("source_hash") or ""),
                )
                source = sources_by_key.get((doc_uid, source_hash), {})
                units.append(
                    _build_unit_from_node(
                        document=document,
                        source=source,
                        node=node,
                        source_hash=source_hash,
                    )
                )
            continue
        if grouped_pages:
            for page in grouped_pages:
                source_hash = _resolve_source_hash(
                    document=document,
                    source_hash=str(page.get("source_hash") or ""),
                )
                source = sources_by_key.get((doc_uid, source_hash), {})
                units.append(
                    _build_unit_from_page(
                        document=document,
                        source=source,
                        page=page,
                        source_hash=source_hash,
                    )
                )
            continue

        fallback_source = source_candidates[0] if source_candidates else {}
        fallback_text = str(document.get("_source_text_blob") or "").strip()
        if not fallback_text:
            continue
        source_hash = _resolve_source_hash(
            document=document,
            source_hash=str(fallback_source.get("source_hash") or ""),
        )
        units.append(
            _build_fallback_document_unit(
                document=document,
                source=fallback_source,
                source_hash=source_hash,
                text=fallback_text,
            )
        )
    return units


def _build_citation_resolutions(
    *,
    citations: list[dict[str, Any]],
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    external_id_map: dict[str, list[dict[str, Any]]] = {}
    for document in documents:
        external_candidates = {
            str(document.get("external_id") or "").strip(),
            str(document.get("act_id") or "").strip(),
        }
        for candidate in external_candidates:
            if not candidate:
                continue
            external_id_map.setdefault(candidate, []).append(
                _normalized_document(document)
            )

    resolutions: list[dict[str, Any]] = []
    for citation in citations:
        citation_uid = str(
            citation.get("citation_uid")
            or citation.get("_id")
            or f"citation:{len(resolutions)}"
        )
        target_external_id = str(
            citation.get("target_external_id")
            or citation.get("target", {}).get("external_id")
            or citation.get("external_id")
            or ""
        ).strip()
        matches = external_id_map.get(target_external_id, [])
        resolution_status = "unresolved"
        target_doc_uid = None
        target_canonical_doc_uid = None
        confidence = 0.0
        if len(matches) == 1:
            match = matches[0]
            target_doc_uid = str(match.get("doc_uid"))
            target_canonical_doc_uid = str(
                match.get("canonical_doc_uid") or match.get("doc_uid")
            )
            resolution_status = "resolved"
            confidence = 1.0
        elif len(matches) > 1:
            resolution_status = "ambiguous"
            confidence = 0.5

        resolutions.append(
            {
                "citation_uid": citation_uid,
                "from_doc_uid": citation.get("from_doc_uid") or citation.get("doc_uid"),
                "from_source_hash": citation.get("from_source_hash")
                or citation.get("source_hash"),
                "from_node_id": citation.get("from_node_id") or citation.get("node_id"),
                "target_external_id": target_external_id or None,
                "target_doc_uid": target_doc_uid,
                "target_canonical_doc_uid": target_canonical_doc_uid,
                "target_node_id": citation.get("target_node_id"),
                "resolver_version": "mongo_materializer_v1",
                "resolution_status": resolution_status,
                "confidence": confidence,
                "resolved_at": _utc_now_iso(),
            }
        )
    return resolutions


def _dedupe_retrieval_units(
    units: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for unit in units:
        normalized = dict(unit)
        key = (
            str(normalized.get("doc_uid") or ""),
            str(normalized.get("source_hash") or ""),
            str(normalized.get("unit_id") or ""),
        )
        existing = deduped.get(key)
        if existing is None or _prefer_retrieval_unit_candidate(
            candidate=normalized,
            existing=existing,
        ):
            deduped[key] = normalized
    return list(deduped.values())


def _prefer_retrieval_unit_candidate(
    *,
    candidate: Mapping[str, Any],
    existing: Mapping[str, Any],
) -> bool:
    candidate_score = (
        1 if not bool(candidate.get("fallback_used")) else 0,
        len(str(candidate.get("text") or "")),
        int(candidate.get("order_index") or 0),
    )
    existing_score = (
        1 if not bool(existing.get("fallback_used")) else 0,
        len(str(existing.get("text") or "")),
        int(existing.get("order_index") or 0),
    )
    return candidate_score > existing_score


def _normalized_document(document: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(document)
    payload["doc_uid"] = str(document.get("doc_uid") or "")
    payload["canonical_doc_uid"] = str(
        document.get("canonical_doc_uid") or document.get("doc_uid") or ""
    )
    payload["document_kind"] = _normalized_document_kind(document)
    payload["operational_status"] = _document_operational_status(document)
    payload["is_indexable"] = _document_is_indexable(
        document, payload["operational_status"]
    )
    payload["authority_weight"] = _authority_weight(document)
    payload["display_citation"] = _document_display_citation(document)
    payload["source_url"] = document.get("source_url") or _first_value(
        document.get("source_urls")
    )
    payload["normalized_source_url"] = document.get(
        "normalized_source_url"
    ) or normalize_url(payload["source_url"])
    return payload


def _normalized_document_source(
    *,
    document: Mapping[str, Any],
    source: Mapping[str, Any],
    current_source: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(source)
    payload["doc_uid"] = str(source.get("doc_uid") or document.get("doc_uid") or "")
    payload["source_hash"] = str(source.get("source_hash") or "")
    payload["storage_backend"] = _storage_backend(source)
    payload["storage_uri_normalized"] = str(
        source.get("storage_uri_normalized")
        or source.get("raw_object_path")
        or source.get("storage_uri")
        or ""
    )
    payload["artifact_manifest"] = _artifact_manifest(source)
    payload["integrity_status"] = str(
        source.get("integrity_status")
        or ("ok" if payload["artifact_manifest"] else "missing_artifact")
    )
    payload["is_current_source"] = bool(
        source.get("is_current_source")
        or (
            current_source is not None
            and str(current_source.get("source_hash") or "") == payload["source_hash"]
        )
    )
    payload["effective_from"] = _as_optional_iso(
        source.get("effective_from") or document.get("effective_from")
    )
    payload["effective_to"] = _as_optional_iso(
        source.get("effective_to") or document.get("effective_to")
    )
    payload["version_date"] = _as_optional_iso(
        source.get("version_date") or document.get("version_date")
    )
    payload["version_kind"] = str(source.get("version_kind") or "current")
    return payload


def _build_unit_from_node(
    *,
    document: Mapping[str, Any],
    source: Mapping[str, Any],
    node: Mapping[str, Any],
    source_hash: str,
) -> dict[str, Any]:
    text = str(node.get("text") or "").strip()
    title_path = [str(item) for item in node.get("title_path") or []]
    page_start = _to_optional_int(node.get("page_start"))
    page_end = _to_optional_int(node.get("page_end")) or page_start
    node_id = str(node.get("node_id") or "")
    unit_id = f"unit:{document.get('doc_uid')}:{source_hash}:{node_id or 'node'}"
    return _base_unit_payload(
        document=document,
        source=source,
        source_hash=source_hash,
        unit_id=unit_id,
        unit_type=_semantic_role(
            node_id=node_id, semantic_role=node.get("semantic_role")
        ),
        node_id=node_id or None,
        title=str(
            node.get("title")
            or document.get("title_short")
            or document.get("canonical_title")
            or ""
        ),
        title_path=title_path,
        text=text,
        page_start=page_start,
        page_end=page_end,
        locator=node.get("locator")
        or {
            "node_id": node_id or None,
            "page_start": page_start,
            "page_end": page_end,
        },
        locator_precision="node_materialized",
        page_truth_status="materialized",
        order_index=_to_optional_int(node.get("order_index")) or 0,
        fallback_used=False,
        text_source="nodes",
    )


def _build_unit_from_page(
    *,
    document: Mapping[str, Any],
    source: Mapping[str, Any],
    page: Mapping[str, Any],
    source_hash: str,
) -> dict[str, Any]:
    page_no = _to_optional_int(page.get("page_no")) or 1
    text = str(page.get("text") or "").strip()
    unit_id = f"unit:{document.get('doc_uid')}:{source_hash}:page:{page_no}"
    return _base_unit_payload(
        document=document,
        source=source,
        source_hash=source_hash,
        unit_id=unit_id,
        unit_type="page_chunk",
        node_id=None,
        title=str(document.get("title_short") or document.get("canonical_title") or ""),
        title_path=[str(document.get("canonical_title") or "")],
        text=text,
        page_start=page_no,
        page_end=page_no,
        locator={"page": page_no},
        locator_precision="page_materialized",
        page_truth_status="materialized",
        order_index=page_no,
        fallback_used=False,
        text_source="pages",
    )


def _build_fallback_document_unit(
    *,
    document: Mapping[str, Any],
    source: Mapping[str, Any],
    source_hash: str,
    text: str,
) -> dict[str, Any]:
    unit_id = f"unit:{document.get('doc_uid')}:{source_hash}:fallback"
    return _base_unit_payload(
        document=document,
        source=source,
        source_hash=source_hash,
        unit_id=unit_id,
        unit_type="document_chunk",
        node_id=None,
        title=str(document.get("title_short") or document.get("canonical_title") or ""),
        title_path=[str(document.get("canonical_title") or "")],
        text=text,
        page_start=None,
        page_end=None,
        locator={"source": "document_blob"},
        locator_precision="document_blob",
        page_truth_status="not_available",
        order_index=0,
        fallback_used=True,
        text_source="document_blob",
    )


def _base_unit_payload(
    *,
    document: Mapping[str, Any],
    source: Mapping[str, Any],
    source_hash: str,
    unit_id: str,
    unit_type: str,
    node_id: str | None,
    title: str,
    title_path: list[str],
    text: str,
    page_start: int | None,
    page_end: int | None,
    locator: Mapping[str, Any] | None,
    locator_precision: str,
    page_truth_status: str,
    order_index: int,
    fallback_used: bool,
    text_source: str,
) -> dict[str, Any]:
    document_kind = _normalized_document_kind(document)
    return {
        "unit_id": unit_id,
        "doc_uid": document.get("doc_uid"),
        "source_hash": source_hash,
        "canonical_doc_uid": document.get("canonical_doc_uid")
        or document.get("doc_uid"),
        "duplicate_owner_doc_uid": document.get("duplicate_owner_doc_uid"),
        "same_case_group_id": document.get("same_case_group_id"),
        "document_kind": document_kind,
        "legal_role": document.get("legal_role"),
        "act_id": document.get("act_id"),
        "unit_type": unit_type,
        "node_id": node_id,
        "title": title,
        "title_path": title_path,
        "text": text,
        "text_norm": _normalize_text(text),
        "page_start": page_start,
        "page_end": page_end,
        "locator": dict(locator or {}),
        "locator_precision": locator_precision,
        "page_truth_status": page_truth_status,
        "issue_tags": list(document.get("issue_tags") or []),
        "facts_tags": list(document.get("facts_tags") or []),
        "related_provisions": list(document.get("related_provisions") or []),
        "court_level": document.get("court_level"),
        "judgment_date": document.get("judgment_date"),
        "current_status": document.get("current_status"),
        "operational_status": document.get("operational_status")
        or _document_operational_status(document),
        "is_indexable": _document_is_indexable(
            document,
            document.get("operational_status")
            or _document_operational_status(document),
        ),
        "display_citation": _document_display_citation(document),
        "authority_weight": _authority_weight(document),
        "effective_from": source.get("effective_from")
        or document.get("effective_from"),
        "effective_to": source.get("effective_to") or document.get("effective_to"),
        "version_date": source.get("version_date") or document.get("version_date"),
        "embedding_ref": None,
        "court_name": document.get("court_name"),
        "act_short_name": document.get("act_short_name"),
        "summary_1line": document.get("summary_1line"),
        "holding_1line": document.get("holding_1line"),
        "source_label": _source_label(document, None),
        "deep_link": _deep_link(document, None),
        "source_tier": document.get("source_tier"),
        "jurisdiction": document.get("jurisdiction"),
        "language": document.get("language"),
        "title_short": document.get("title_short"),
        "version_kind": source.get("version_kind") or "current",
        "is_current_source": bool(source.get("is_current_source")),
        "storage_backend": source.get("storage_backend"),
        "storage_uri_normalized": source.get("storage_uri_normalized"),
        "artifact_manifest": source.get("artifact_manifest") or {},
        "integrity_status": source.get("integrity_status") or "unknown",
        "order_index": order_index,
        "fallback_used": fallback_used,
        "text_source": text_source,
    }


def _evaluate_search_constraints(request: SearchRequest) -> dict[str, Any]:
    filter_constraints: dict[str, Any] = {}
    locator_constraints: dict[str, Any] = {}
    applied_filters = {"filters": {}, "locator": {}, "options": {}}
    ignored_filters = {"filters": {}, "locator": {}, "options": {}}
    unsupported_filters = {"filters": {}, "locator": {}, "options": {}}
    limitations: list[str] = []
    filter_semantics: dict[str, str] = {}
    filter_aliases: dict[str, str] = {}

    raw_filters = request.get("filters") or {}

    for key, value in raw_filters.items():
        if _is_blank_value(value):
            ignored_filters["filters"][key] = {
                "value": value,
                "reason": "Empty filter value was ignored.",
            }
            continue
        if key == "status":
            if not _is_blank_value(raw_filters.get("current_status")):
                ignored_filters["filters"]["status"] = {
                    "value": value,
                    "reason": (
                        "Ignored because current_status filter was provided explicitly."
                    ),
                }
                limitations.append(
                    "filters.status: ignored because current_status takes precedence."
                )
                continue
            filter_constraints["current_status"] = value
            applied_filters["filters"]["status"] = {
                "value": value,
                "alias_to": "current_status",
            }
            filter_aliases["status"] = "current_status"
            continue
        if key in _SUPPORTED_FILTER_KEYS:
            filter_constraints[key] = value
            applied_filters["filters"][key] = value
            if key in _TOKEN_FILTER_KEYS:
                filter_semantics[key] = "case_insensitive_exact_token_membership"
            elif key == "judgment_date":
                filter_semantics[key] = "iso_date_exact_match"
            continue
        reason = f"Unsupported filter key for mongo backend: {key}"
        unsupported_filters["filters"][key] = {"value": value, "reason": reason}
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
        reason = f"Unsupported locator key for mongo backend: {key}"
        unsupported_filters["locator"][key] = {"value": value, "reason": reason}
        limitations.append(f"locator.{key}: {reason}")

    applied_filters["options"]["return_level"] = request["return_level"]
    if request.get("as_of_date"):
        applied_filters["options"]["as_of_date"] = request["as_of_date"]
    include_history_requested = _coerce_bool(
        request.get("include_history"),
        default=False,
    )
    include_history_status = "disabled"
    current_only_explicit = None
    if "current_only" in raw_filters:
        current_only_explicit = _coerce_bool(raw_filters.get("current_only"), default=True)
    if "include_history" in request:
        if include_history_requested and request.get("as_of_date"):
            include_history_status = "ignored_as_of_date"
            ignored_filters["options"]["include_history"] = {
                "value": request.get("include_history"),
                "reason": "Ignored because as_of_date selects a single version.",
            }
            limitations.append(
                "include_history: ignored because as_of_date selects a single version."
            )
        elif include_history_requested and current_only_explicit is True:
            include_history_status = "ignored_current_only"
            ignored_filters["options"]["include_history"] = {
                "value": request.get("include_history"),
                "reason": "Ignored because current_only=true restricts search to the current source hash.",
            }
            limitations.append(
                "include_history: ignored because current_only=true is stricter."
            )
        else:
            include_history_status = (
                "all_versions" if include_history_requested else "disabled"
            )
            applied_filters["options"]["include_history"] = {
                "value": include_history_requested,
                "mode": include_history_status,
            }
    elif include_history_requested:
        include_history_status = "all_versions"
    if "expand_citations" in request:
        applied_filters["options"]["expand_citations"] = bool(
            request.get("expand_citations")
        )

    return {
        "filter_constraints": filter_constraints,
        "locator_constraints": locator_constraints,
        "applied_filters": applied_filters,
        "ignored_filters": ignored_filters,
        "unsupported_filters": unsupported_filters,
        "limitations": limitations,
        "filter_semantics": filter_semantics,
        "filter_aliases": filter_aliases,
        "include_history_applied": include_history_status == "all_versions",
        "include_history_status": include_history_status,
    }


def _select_versions_for_search(
    *,
    documents: Mapping[str, Mapping[str, Any]],
    document_sources: Mapping[str, list[dict[str, Any]]],
    filters: Mapping[str, Any],
    as_of_date: date | None,
    include_history: bool,
) -> tuple[dict[str, _DocumentVersionSelection], list[str]]:
    current_only = _coerce_bool(
        filters.get("current_only"),
        default=as_of_date is None and not include_history,
    )
    selections: dict[str, _DocumentVersionSelection] = {}
    historical_missing: list[str] = []

    for doc_uid, document in documents.items():
        sources = document_sources.get(doc_uid, [])
        if current_only:
            source_hash = str(
                document.get("current_source_hash")
                or _first_non_blank(source.get("source_hash") for source in sources)
                or ""
            )
            selections[doc_uid] = _DocumentVersionSelection(
                source_hash=source_hash or None,
                version_status="current",
                current_only=True,
                historical_version_found=source_hash != "",
                effective_from=None,
                effective_to=None,
                version_date=None,
            )
            continue

        if include_history and as_of_date is None:
            selections[doc_uid] = _DocumentVersionSelection(
                source_hash=None,
                version_status="history_included",
                current_only=False,
                historical_version_found=True,
                effective_from=None,
                effective_to=None,
                version_date=None,
            )
            continue

        if as_of_date is None:
            selections[doc_uid] = _DocumentVersionSelection(
                source_hash=str(document.get("current_source_hash") or "") or None,
                version_status="current",
                current_only=False,
                historical_version_found=True,
                effective_from=None,
                effective_to=None,
                version_date=None,
            )
            continue

        matched_source = _source_for_as_of_date(sources=sources, as_of_date=as_of_date)
        if matched_source is None:
            historical_missing.append(doc_uid)
            selections[doc_uid] = _DocumentVersionSelection(
                source_hash=None,
                version_status="historical_version_not_found",
                current_only=False,
                historical_version_found=False,
                effective_from=None,
                effective_to=None,
                version_date=None,
            )
            continue

        selections[doc_uid] = _DocumentVersionSelection(
            source_hash=str(matched_source.get("source_hash") or "") or None,
            version_status="historical",
            current_only=False,
            historical_version_found=True,
            effective_from=_as_optional_iso(matched_source.get("effective_from")),
            effective_to=_as_optional_iso(matched_source.get("effective_to")),
            version_date=_as_optional_iso(matched_source.get("version_date")),
        )

    return selections, historical_missing


def _score_unit(
    *,
    unit: Mapping[str, Any],
    query_terms: Sequence[str],
) -> _SearchCandidate | None:
    search_fields = {
        "text": _normalize_text(unit.get("text")),
        "title": _normalize_text(unit.get("title")),
        "title_path": _normalize_text(
            " ".join(str(item) for item in unit.get("title_path") or [])
        ),
        "issue_tags": _normalize_text(
            " ".join(str(item) for item in unit.get("issue_tags") or [])
        ),
        "facts_tags": _normalize_text(
            " ".join(str(item) for item in unit.get("facts_tags") or [])
        ),
        "related_provisions": _normalize_text(
            " ".join(str(item) for item in unit.get("related_provisions") or [])
        ),
        "summary": _normalize_text(unit.get("summary_1line")),
        "holding": _normalize_text(unit.get("holding_1line")),
        "display_citation": _normalize_text(unit.get("display_citation")),
    }
    matched_terms: list[str] = []
    matched_fields: list[str] = []
    field_hits: dict[str, int] = {}
    total_score = 0.0

    for term in query_terms:
        term_hit = False
        for field_name, haystack in search_fields.items():
            if not haystack or term not in haystack:
                continue
            field_hits[field_name] = field_hits.get(field_name, 0) + 1
            if field_name not in matched_fields:
                matched_fields.append(field_name)
            term_hit = True
            if field_name == "text":
                total_score += 3.0
            elif field_name in {"title", "display_citation"}:
                total_score += 2.0
            else:
                total_score += 1.0
        if term_hit:
            matched_terms.append(term)

    if not matched_terms:
        return None

    total_score += float(unit.get("authority_weight") or 0) / 100.0
    if str(unit.get("document_kind") or "").upper() in ACT_KINDS:
        total_score += 0.25
    return _SearchCandidate(
        unit=dict(unit),
        score=total_score,
        matched_terms=tuple(matched_terms),
        matched_fields=tuple(matched_fields),
        score_breakdown={
            "matched_terms": len(matched_terms),
            "matched_fields": list(matched_fields),
            "field_hits": field_hits,
            "authority_weight": unit.get("authority_weight"),
        },
    )


def _dedupe_candidates(
    candidates: Sequence[_SearchCandidate],
    *,
    include_history: bool = False,
) -> list[_SearchCandidate]:
    ordered = sorted(
        candidates,
        key=lambda item: (
            -item.score,
            str(item.unit.get("doc_uid") or ""),
            str(item.unit.get("unit_id") or ""),
        ),
    )
    grouped: dict[str, _SearchCandidate] = {}
    for candidate in ordered:
        dedupe_key = _dedupe_key(candidate.unit, include_history=include_history)
        if dedupe_key not in grouped:
            grouped[dedupe_key] = candidate
    return list(grouped.values())


def _candidate_to_search_result(
    *,
    candidate: _SearchCandidate,
    requested_return_level: str,
    result_level: str,
    effective_return_level: str,
    documents: Mapping[str, Mapping[str, Any]],
    version_selection: _DocumentVersionSelection | None,
) -> dict[str, Any]:
    unit = candidate.unit
    document = documents.get(str(unit.get("doc_uid") or ""), {})
    preview = _snippet(
        text=str(unit.get("text") or ""),
        query_terms=candidate.matched_terms,
    )
    machine_ref = {
        "doc_uid": unit.get("doc_uid"),
        "source_hash": unit.get("source_hash"),
        "unit_id": unit.get("unit_id"),
        "node_id": unit.get("node_id"),
        "page_range": _page_range(unit.get("page_start"), unit.get("page_end")),
    }
    base_payload = {
        "result_level": result_level,
        "preview": preview,
        "machine_ref": machine_ref,
        "display_citation": _display_citation(document, unit),
        "score": candidate.score,
        "score_breakdown": candidate.score_breakdown,
        "why_relevant": _why_relevant(
            matched_terms=candidate.matched_terms,
            matched_fields=candidate.matched_fields,
            version_selection=version_selection,
        ),
        "source_label": _source_label(document, unit),
        "document_kind": unit.get("document_kind"),
        "act_short_name": document.get("act_short_name"),
        "court_name": document.get("court_name"),
        "judgment_date": document.get("judgment_date"),
        "version_date": unit.get("version_date"),
        "deep_link": _deep_link(document, unit),
        "doc_uid": unit.get("doc_uid"),
        "source_hash": unit.get("source_hash"),
        "canonical_doc_uid": unit.get("canonical_doc_uid"),
        "matched_fields": list(candidate.matched_fields),
        "provenance_status": (
            "ok"
            if unit.get("integrity_status") in {"ok", "manifest_only"}
            else "incomplete"
        ),
        "metadata": {
            "requested_return_level": requested_return_level,
            "effective_return_level": effective_return_level,
            "result_level": result_level,
            "document_kind": unit.get("document_kind"),
            "legal_role": unit.get("legal_role"),
            "current_status": unit.get("current_status"),
            "operational_status": unit.get("operational_status"),
            "is_indexable": unit.get("is_indexable"),
            "authority_weight": unit.get("authority_weight"),
            "current_only": version_selection.current_only
            if version_selection
            else True,
            "version_status": (
                version_selection.version_status if version_selection else "current"
            ),
            "version_date": unit.get("version_date"),
            "effective_from": unit.get("effective_from"),
            "effective_to": unit.get("effective_to"),
            "anchor_unit_id": unit.get("unit_id"),
            "anchor_node_id": unit.get("node_id"),
            "anchor_page_range": _page_range(
                unit.get("page_start"), unit.get("page_end")
            ),
        },
        "diagnostics": {
            "backend": "mongo",
            "result_level": result_level,
            "locator_precision": unit.get("locator_precision")
            or "retrieval_unit_locator",
            "page_truth_status": unit.get("page_truth_status") or "materialized",
            "integrity_status": unit.get("integrity_status"),
            "machine_ref_kind": (
                "document_anchor" if result_level == "document" else "fragment"
            ),
        },
    }
    if result_level == "fragment":
        base_payload["node_id"] = unit.get("node_id")
        base_payload["unit_id"] = unit.get("unit_id")
        base_payload["page_range"] = _page_range(
            unit.get("page_start"), unit.get("page_end")
        )
    return base_payload


def _build_search_results(
    *,
    candidates: Sequence[_SearchCandidate],
    requested_return_level: str,
    documents: Mapping[str, Mapping[str, Any]],
    selected_versions: Mapping[str, _DocumentVersionSelection],
) -> list[dict[str, Any]]:
    normalized_return_level = _normalize_return_level(requested_return_level)
    if normalized_return_level == "mixed":
        result_levels = _mixed_result_levels(len(candidates))
    else:
        result_levels = [normalized_return_level] * len(candidates)

    results: list[dict[str, Any]] = []
    effective_return_level = _effective_return_level_from_levels(
        requested_return_level=requested_return_level,
        result_levels=result_levels,
    )
    for candidate, result_level in zip(candidates, result_levels, strict=False):
        results.append(
            _candidate_to_search_result(
                candidate=candidate,
                requested_return_level=requested_return_level,
                result_level=result_level,
                effective_return_level=effective_return_level,
                documents=documents,
                version_selection=selected_versions.get(
                    str(candidate.unit.get("doc_uid"))
                ),
            )
        )
    return results


def _mixed_result_levels(candidate_count: int) -> list[str]:
    if candidate_count <= 0:
        return []
    if candidate_count == 1:
        return ["document"]
    return [
        "document" if index % 2 == 0 else "fragment"
        for index in range(candidate_count)
    ]


def _normalize_return_level(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"document", "fragment", "mixed"}:
        return normalized
    return "fragment"


def _effective_return_level(
    *,
    requested_return_level: str,
    results: Sequence[Mapping[str, Any]],
) -> str:
    result_levels = [
        str(result.get("result_level") or "").strip().lower()
        for result in results
        if str(result.get("result_level") or "").strip()
    ]
    return _effective_return_level_from_levels(
        requested_return_level=requested_return_level,
        result_levels=result_levels,
    )


def _effective_return_level_from_levels(
    *,
    requested_return_level: str,
    result_levels: Sequence[str],
) -> str:
    normalized_request = _normalize_return_level(requested_return_level)
    if normalized_request != "mixed":
        return normalized_request
    level_set = {level for level in result_levels if level in {"document", "fragment"}}
    if level_set == {"document", "fragment"}:
        return "mixed"
    if level_set == {"fragment"}:
        return "fragment"
    if level_set == {"document"}:
        return "document"
    return "mixed"


def _returned_result_levels(results: Sequence[Mapping[str, Any]]) -> list[str]:
    ordered: list[str] = []
    for result in results:
        level = str(result.get("result_level") or "").strip()
        if level and level not in ordered:
            ordered.append(level)
    return ordered


def _expand_candidates_one_hop(
    *,
    candidates: Sequence[_SearchCandidate],
    units: Sequence[dict[str, Any]],
    resolutions: Sequence[dict[str, Any]],
    top_k: int,
) -> list[_SearchCandidate]:
    candidate_doc_uids = {
        str(candidate.unit.get("doc_uid") or "") for candidate in candidates
    }
    units_by_doc_uid: dict[str, list[dict[str, Any]]] = {}
    for unit in units:
        doc_uid = str(unit.get("doc_uid") or "")
        if not doc_uid:
            continue
        units_by_doc_uid.setdefault(doc_uid, []).append(unit)

    expanded = list(candidates)
    for resolution in resolutions:
        from_doc_uid = str(resolution.get("from_doc_uid") or "")
        target_doc_uid = str(resolution.get("target_doc_uid") or "")
        if resolution.get("resolution_status") != "resolved":
            continue
        if (
            from_doc_uid not in candidate_doc_uids
            or target_doc_uid in candidate_doc_uids
        ):
            continue
        related_units = units_by_doc_uid.get(target_doc_uid, [])
        if not related_units:
            continue
        best_unit = sorted(
            related_units,
            key=lambda item: (
                -float(item.get("authority_weight") or 0),
                str(item.get("unit_id") or ""),
            ),
        )[0]
        expanded.append(
            _SearchCandidate(
                unit=best_unit,
                score=0.75,
                matched_terms=("expanded_citation",),
                matched_fields=("citation_resolution",),
                score_breakdown={
                    "matched_terms": 1,
                    "matched_fields": ["citation_resolution"],
                    "field_hits": {"citation_resolution": 1},
                    "authority_weight": best_unit.get("authority_weight"),
                },
            )
        )
        if len(expanded) >= len(candidates) + top_k:
            break
    return expanded


def _interleave_mixed_candidates(
    *,
    candidates: Sequence[_SearchCandidate],
    scope: str,
    top_k: int,
) -> list[_SearchCandidate]:
    ordered = sorted(
        candidates,
        key=lambda item: (
            -item.score,
            str(item.unit.get("doc_uid") or ""),
            str(item.unit.get("unit_id") or ""),
        ),
    )
    if scope != "mixed":
        return ordered[:top_k]

    acts = [
        item
        for item in ordered
        if str(item.unit.get("document_kind") or "").upper() in ACT_KINDS
    ]
    case_law = [
        item
        for item in ordered
        if str(item.unit.get("document_kind") or "").upper() in _CASELAW_KINDS
    ]
    selected: list[_SearchCandidate] = []
    if acts:
        selected.append(acts.pop(0))
    if case_law and len(selected) < top_k:
        selected.append(case_law.pop(0))

    seen = {
        (str(item.unit.get("doc_uid") or ""), str(item.unit.get("unit_id") or ""))
        for item in selected
    }
    for candidate in ordered:
        key = (
            str(candidate.unit.get("doc_uid") or ""),
            str(candidate.unit.get("unit_id") or ""),
        )
        if key in seen:
            continue
        selected.append(candidate)
        seen.add(key)
        if len(selected) >= top_k:
            break
    return selected[:top_k]


def _build_search_diagnostics(
    *,
    backend: str,
    query_terms: Sequence[str],
    total_matches: int,
    result_count: int,
    effective_return_level: str,
    index_context: Mapping[str, Any],
    limitations: Sequence[str],
    historical_version_not_found: Sequence[str],
    filter_semantics: Mapping[str, Any],
    include_history_status: str,
    filter_aliases: Mapping[str, str],
    returned_result_levels: Sequence[str],
) -> dict[str, Any]:
    warnings = list(index_context.get("warnings") or [])
    if historical_version_not_found:
        warnings.append(
            "Historical version not found for: "
            + ", ".join(sorted(historical_version_not_found))
        )
    return {
        "backend": backend,
        "query_terms": list(query_terms),
        "effective_return_level": effective_return_level,
        "total_matches": total_matches,
        "result_count": result_count,
        "filter_semantics": dict(filter_semantics),
        "filter_aliases": dict(filter_aliases),
        "include_history_status": include_history_status,
        "returned_result_levels": list(returned_result_levels),
        "limitations": list(limitations),
        "historical_version_not_found": sorted(historical_version_not_found),
        "index_freshness_status": index_context.get("index_freshness_status"),
        "latest_successful_ingest_run_id": index_context.get(
            "latest_successful_ingest_run_id"
        ),
        "retrieval_index_ingest_run_id": index_context.get(
            "retrieval_index_ingest_run_id"
        ),
        "index_built_at": index_context.get("index_built_at"),
        "warnings": warnings,
    }


def _index_units_by_key(
    units: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    indexed: dict[tuple[str, str, str], dict[str, Any]] = {}
    for unit in units:
        key = (
            str(unit.get("doc_uid") or ""),
            str(unit.get("source_hash") or ""),
            str(unit.get("unit_id") or ""),
        )
        indexed[key] = dict(unit)
    return indexed


def _resolve_unit_from_ref(
    *,
    ref: Mapping[str, Any],
    units_by_key: Mapping[tuple[str, str, str], dict[str, Any]],
) -> dict[str, Any] | None:
    doc_uid = str(ref.get("doc_uid") or "")
    source_hash = str(ref.get("source_hash") or "")
    unit_id = str(ref.get("unit_id") or "")
    if doc_uid and source_hash and unit_id:
        return units_by_key.get((doc_uid, source_hash, unit_id))
    for key, unit in units_by_key.items():
        if doc_uid and key[0] != doc_uid:
            continue
        if unit_id and key[2] != unit_id:
            continue
        if source_hash and key[1] != source_hash:
            continue
        return unit
    return None


def _neighbor_units(
    *,
    unit: Mapping[str, Any],
    units: Sequence[Mapping[str, Any]],
    window: int,
) -> list[dict[str, Any]]:
    if window <= 0:
        return [dict(unit)]
    same_doc = [
        dict(item)
        for item in units
        if str(item.get("doc_uid") or "") == str(unit.get("doc_uid") or "")
        and str(item.get("source_hash") or "") == str(unit.get("source_hash") or "")
    ]
    same_doc.sort(
        key=lambda item: (
            int(item.get("order_index") or 0),
            str(item.get("unit_id") or ""),
        )
    )
    index = 0
    for idx, item in enumerate(same_doc):
        if str(item.get("unit_id") or "") == str(unit.get("unit_id") or ""):
            index = idx
            break
    start = max(index - window, 0)
    end = min(index + window + 1, len(same_doc))
    return same_doc[start:end]


def _expand_via_resolution_layer(
    *,
    relation_type: str,
    base_doc_uids: set[str],
    resolutions: Sequence[Mapping[str, Any]],
    documents: Mapping[str, Mapping[str, Any]],
    units: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    units_by_doc_uid: dict[str, dict[str, Any]] = {}
    for unit in units:
        doc_uid = str(unit.get("doc_uid") or "")
        if not doc_uid:
            continue
        existing = units_by_doc_uid.get(doc_uid)
        candidate = dict(unit)
        if existing is None or float(candidate.get("authority_weight") or 0) > float(
            existing.get("authority_weight") or 0
        ):
            units_by_doc_uid[doc_uid] = candidate

    for resolution in resolutions:
        if resolution.get("resolution_status") != "resolved":
            continue
        from_doc_uid = str(resolution.get("from_doc_uid") or "")
        target_doc_uid = str(resolution.get("target_doc_uid") or "")
        if relation_type == "cites" and from_doc_uid not in base_doc_uids:
            continue
        if relation_type == "cited_by" and target_doc_uid not in base_doc_uids:
            continue
        related_doc_uid = target_doc_uid if relation_type == "cites" else from_doc_uid
        document = documents.get(related_doc_uid)
        unit = units_by_doc_uid.get(related_doc_uid)
        if document is None or unit is None:
            continue
        results.append(
            {
                "relation_type": relation_type,
                "doc_uid": related_doc_uid,
                "canonical_doc_uid": document.get("canonical_doc_uid"),
                "display_citation": _display_citation(document, unit),
                "machine_ref": {
                    "doc_uid": related_doc_uid,
                    "source_hash": unit.get("source_hash"),
                    "unit_id": unit.get("unit_id"),
                    "node_id": unit.get("node_id"),
                    "page_range": _page_range(
                        unit.get("page_start"), unit.get("page_end")
                    ),
                },
                "why_relevant": f"{relation_type} resolved via target_external_id mapping.",
            }
        )
    return results


def _expand_same_case(
    *,
    base_doc_uids: set[str],
    documents: Mapping[str, Mapping[str, Any]],
    units: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    group_ids = {
        str(documents[doc_uid].get("same_case_group_id") or "")
        for doc_uid in base_doc_uids
        if doc_uid in documents and documents[doc_uid].get("same_case_group_id")
    }
    units_by_doc_uid = {
        str(unit.get("doc_uid") or ""): dict(unit)
        for unit in units
        if unit.get("doc_uid")
    }
    results: list[dict[str, Any]] = []
    for document in documents.values():
        doc_uid = str(document.get("doc_uid") or "")
        if doc_uid in base_doc_uids:
            continue
        if str(document.get("same_case_group_id") or "") not in group_ids:
            continue
        unit = units_by_doc_uid.get(doc_uid)
        if unit is None:
            continue
        results.append(
            {
                "relation_type": "same_case",
                "doc_uid": doc_uid,
                "canonical_doc_uid": document.get("canonical_doc_uid"),
                "display_citation": _display_citation(document, unit),
                "machine_ref": {
                    "doc_uid": doc_uid,
                    "source_hash": unit.get("source_hash"),
                    "unit_id": unit.get("unit_id"),
                    "node_id": unit.get("node_id"),
                    "page_range": _page_range(
                        unit.get("page_start"), unit.get("page_end")
                    ),
                },
                "why_relevant": "Same case group candidate.",
            }
        )
    return results


def _expand_supersedes(
    *,
    base_doc_uids: set[str],
    documents: Mapping[str, Mapping[str, Any]],
    units: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    units_by_doc_uid = {
        str(unit.get("doc_uid") or ""): dict(unit)
        for unit in units
        if unit.get("doc_uid")
    }
    targets = {
        str(documents[doc_uid].get("superseded_by") or "")
        for doc_uid in base_doc_uids
        if doc_uid in documents and documents[doc_uid].get("superseded_by")
    }
    results: list[dict[str, Any]] = []
    for doc_uid in targets:
        if not doc_uid or doc_uid not in documents:
            continue
        unit = units_by_doc_uid.get(doc_uid)
        if unit is None:
            continue
        document = documents[doc_uid]
        results.append(
            {
                "relation_type": "supersedes",
                "doc_uid": doc_uid,
                "canonical_doc_uid": document.get("canonical_doc_uid"),
                "display_citation": _display_citation(document, unit),
                "machine_ref": {
                    "doc_uid": doc_uid,
                    "source_hash": unit.get("source_hash"),
                    "unit_id": unit.get("unit_id"),
                    "node_id": unit.get("node_id"),
                    "page_range": _page_range(
                        unit.get("page_start"), unit.get("page_end")
                    ),
                },
                "why_relevant": "Supersession edge from document metadata.",
            }
        )
    return results


def _expand_related_provisions(
    *,
    base_doc_uids: set[str],
    documents: Mapping[str, Mapping[str, Any]],
    units: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    related_terms: set[str] = set()
    for doc_uid in base_doc_uids:
        document = documents.get(doc_uid)
        if document is None:
            continue
        related_terms.update(
            str(item) for item in document.get("related_provisions") or []
        )
    if not related_terms:
        return []

    units_by_doc_uid = {
        str(unit.get("doc_uid") or ""): dict(unit)
        for unit in units
        if unit.get("doc_uid")
    }
    results: list[dict[str, Any]] = []
    for document in documents.values():
        doc_uid = str(document.get("doc_uid") or "")
        if doc_uid in base_doc_uids:
            continue
        document_terms = {
            str(item) for item in document.get("related_provisions") or []
        }
        if not document_terms.intersection(related_terms):
            continue
        unit = units_by_doc_uid.get(doc_uid)
        if unit is None:
            continue
        results.append(
            {
                "relation_type": "related_provision",
                "doc_uid": doc_uid,
                "canonical_doc_uid": document.get("canonical_doc_uid"),
                "display_citation": _display_citation(document, unit),
                "machine_ref": {
                    "doc_uid": doc_uid,
                    "source_hash": unit.get("source_hash"),
                    "unit_id": unit.get("unit_id"),
                    "node_id": unit.get("node_id"),
                    "page_range": _page_range(
                        unit.get("page_start"), unit.get("page_end")
                    ),
                },
                "why_relevant": "Shared related_provisions tag.",
            }
        )
    return results


def _dedupe_related_results(results: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for item in results:
        key = (str(item.get("relation_type") or ""), str(item.get("doc_uid") or ""))
        if key not in deduped:
            deduped[key] = item
    return list(deduped.values())


def _resolve_provenance_source(
    *,
    document: Mapping[str, Any],
    document_sources: Sequence[Mapping[str, Any]],
    source_hash: str,
) -> dict[str, Any]:
    if source_hash:
        for source in document_sources:
            if str(source.get("source_hash") or "") == source_hash:
                return dict(source)
    for source in document_sources:
        if bool(source.get("is_current_source")):
            return dict(source)
    current_source_hash = str(document.get("current_source_hash") or "")
    for source in document_sources:
        if str(source.get("source_hash") or "") == current_source_hash:
            return dict(source)
    if document_sources:
        return dict(document_sources[0])
    return {}


def _artifact_manifest(source: Mapping[str, Any]) -> dict[str, Any]:
    existing = source.get("artifact_manifest")
    if isinstance(existing, dict) and existing:
        return dict(existing)
    raw_uri = source.get("raw_object_path") or source.get("storage_uri")
    response_meta_uri = source.get("response_meta_path")
    normalized_pages_uri = source.get("normalized_pages_uri")
    normalized_nodes_uri = source.get("normalized_nodes_uri")
    availability_flags = {
        "raw_bin": bool(raw_uri),
        "response_meta": bool(response_meta_uri),
        "normalized_pages": bool(normalized_pages_uri),
        "normalized_nodes": bool(normalized_nodes_uri),
    }
    return {
        "raw_bin_uri": raw_uri,
        "response_meta_uri": response_meta_uri,
        "normalized_pages_uri": normalized_pages_uri,
        "normalized_nodes_uri": normalized_nodes_uri,
        "availability_flags": availability_flags,
    }


def _ensure_materialized_indexes(
    runtime: _MongoRuntimeProtocol,
    *,
    retrieval_units_collection: str = _RETRIEVAL_UNITS_COLLECTION,
    citation_resolutions_collection: str = _CITATION_RESOLUTIONS_COLLECTION,
) -> None:
    _safe_create_index(
        runtime.collection(retrieval_units_collection),
        [("doc_uid", 1), ("source_hash", 1), ("unit_id", 1)],
        unique=True,
    )
    _safe_create_index(
        runtime.collection(retrieval_units_collection),
        [("document_kind", 1), ("operational_status", 1), ("is_indexable", 1)],
    )
    _safe_create_index(
        runtime.collection(retrieval_units_collection),
        [("same_case_group_id", 1)],
    )
    _safe_create_index(
        runtime.collection(retrieval_units_collection),
        [("act_id", 1), ("effective_from", 1), ("effective_to", 1)],
    )
    _safe_create_index(
        runtime.collection(retrieval_units_collection),
        [("court_level", 1), ("judgment_date", 1)],
    )
    _safe_create_index(
        runtime.collection(citation_resolutions_collection),
        [("from_doc_uid", 1), ("from_node_id", 1)],
    )
    _safe_create_index(
        runtime.collection(citation_resolutions_collection),
        [("target_external_id", 1)],
    )
    _safe_create_index(
        runtime.collection(citation_resolutions_collection),
        [("target_doc_uid", 1)],
    )
    _safe_create_index(
        runtime.collection(citation_resolutions_collection),
        [("target_canonical_doc_uid", 1)],
    )


def _safe_create_index(
    collection: _CollectionProtocol,
    keys: list[tuple[str, int]],
    **kwargs: Any,
) -> None:
    create_index = getattr(collection, "create_index", None)
    if callable(create_index):
        create_index(keys, **kwargs)


def _is_index_fresh(
    latest_ingest: Mapping[str, Any] | None,
    latest_index: Mapping[str, Any] | None,
) -> bool:
    if latest_index is None:
        return False
    if latest_ingest is None:
        return True
    return str(latest_index.get("source_ingest_run_id") or "") == str(
        latest_ingest.get("run_id") or ""
    )


def _latest_successful_ingest_run(
    ingest_runs: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    successful = [
        dict(run)
        for run in ingest_runs
        if str(run.get("status") or "").lower() in {"completed", "success", "succeeded"}
    ]
    if not successful:
        return None
    successful.sort(
        key=lambda item: (
            _sort_timestamp(item.get("finished_at")),
            _sort_timestamp(item.get("updated_at")),
            str(item.get("run_id") or ""),
        ),
        reverse=True,
    )
    return successful[0]


def _latest_retrieval_index_run(
    index_runs: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    rows = [
        dict(row)
        for row in index_runs
        if row and str(row.get("status") or "completed").lower() == "completed"
    ]
    if not rows:
        return None
    rows.sort(
        key=lambda item: (
            _sort_timestamp(item.get("built_at")),
            str(item.get("build_id") or ""),
        ),
        reverse=True,
    )
    return rows[0]


def _materialized_collection_name(base_name: str, *, build_id: str) -> str:
    suffix = hashlib.sha256(build_id.encode("utf-8")).hexdigest()[:12]
    return f"{base_name}__{suffix}"


def _materialized_collection_for_index_run(
    *,
    collection_name: str,
    index_run: Mapping[str, Any] | None,
) -> str:
    if index_run is None:
        return collection_name
    if collection_name == _RETRIEVAL_UNITS_COLLECTION:
        active = str(index_run.get("retrieval_units_collection") or "").strip()
        return active or collection_name
    if collection_name == _CITATION_RESOLUTIONS_COLLECTION:
        active = str(index_run.get("citation_resolutions_collection") or "").strip()
        return active or collection_name
    return collection_name


def _request_hash(request: Mapping[str, Any]) -> str:
    serialized = json.dumps(
        request,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _build_tool_audit_payload(
    *,
    tool_name: str,
    request: Mapping[str, Any],
    started_at: float,
    results: Sequence[Mapping[str, Any]],
    warnings: Sequence[str],
    query_hash: str | None = None,
) -> dict[str, Any]:
    request_hash = _request_hash(request)
    returned_refs = _extract_returned_refs(results)
    return {
        "request_id": f"legal_corpus:{tool_name}:{request_hash[:16]}",
        "tool_call_id": f"{tool_name}:{request_hash[:16]}",
        "request_hash": request_hash,
        "query_hash": query_hash,
        "latency_ms": max(int((time.perf_counter() - started_at) * 1000), 0),
        "returned_refs": returned_refs,
        "returned_ref_count": len(returned_refs),
        "warnings": list(warnings),
    }


def _extract_returned_refs(
    results: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for item in results:
        machine_ref = item.get("machine_ref")
        if not isinstance(machine_ref, Mapping):
            continue
        refs.append(dict(machine_ref))
    return refs


def _audit_warnings_from_payload(payload: Mapping[str, Any]) -> list[str]:
    diagnostics = payload.get("diagnostics")
    if not isinstance(diagnostics, Mapping):
        return []
    warnings = diagnostics.get("warnings")
    if not isinstance(warnings, Sequence) or isinstance(warnings, (str, bytes)):
        return []
    return [str(item) for item in warnings]


def _sort_timestamp(value: Any) -> str:
    return _as_optional_iso(value) or ""


def _normalized_document_kind(document: Mapping[str, Any]) -> str:
    raw = str(document.get("document_kind") or document.get("doc_type") or "").upper()
    if raw in ACT_KINDS:
        return raw
    if raw in _CASELAW_KINDS:
        return raw
    return raw or "DOCUMENT"


def _document_operational_status(document: Mapping[str, Any]) -> str:
    existing = str(document.get("operational_status") or "").strip()
    if existing:
        return existing
    status = str(document.get("status") or "active").lower()
    legal_role = str(document.get("legal_role") or "")
    if status == "alias":
        return "alias"
    if status == "excluded":
        if legal_role == "INVENTORY_ONLY":
            if "broken" in str(document.get("exclusion_reason") or "").lower():
                return "broken"
            return "traceability"
        return "excluded"
    if status in {"broken", "error"}:
        return "broken"
    return "operational"


def _document_is_indexable(
    document: Mapping[str, Any],
    operational_status: str,
) -> bool:
    existing = document.get("is_indexable")
    if isinstance(existing, bool):
        return existing
    return operational_status == "operational"


def _authority_weight(document: Mapping[str, Any]) -> int:
    value = document.get("authority_weight")
    if isinstance(value, int):
        return value
    document_kind = _normalized_document_kind(document)
    source_tier = str(document.get("source_tier") or "")
    legal_role = str(document.get("legal_role") or "")
    if document_kind in ACT_KINDS:
        return 100
    if source_tier == "official":
        return 95
    if source_tier == "saos":
        return 85
    if legal_role == "SECONDARY_SOURCE":
        return 55
    return 70


def _document_display_citation(document: Mapping[str, Any]) -> str:
    explicit = str(document.get("display_citation") or "").strip()
    if explicit:
        return explicit
    act_short_name = str(document.get("act_short_name") or "").strip()
    if act_short_name:
        return f"{act_short_name} [{document.get('doc_uid')}]"
    case_signature = str(document.get("case_signature") or "").strip()
    court_name = str(document.get("court_name") or "").strip()
    if case_signature and court_name:
        return f"{court_name}, {case_signature}"
    title_short = str(document.get("title_short") or "").strip()
    if title_short:
        return f"{title_short} [{document.get('doc_uid')}]"
    canonical_title = str(
        document.get("canonical_title") or document.get("title") or ""
    ).strip()
    if canonical_title:
        return canonical_title
    return str(document.get("doc_uid") or "")


def _semantic_role(*, node_id: str, semantic_role: Any) -> str:
    if semantic_role:
        return str(semantic_role)
    lowered = node_id.lower()
    if lowered.startswith("art:"):
        return "article"
    if lowered.startswith("sec:") or lowered.startswith("section:"):
        return "section"
    if lowered.startswith("holding"):
        return "holding"
    return "reasoning"


def _source_label(document: Mapping[str, Any], unit: Mapping[str, Any] | None) -> str:
    explicit = str(
        (unit or {}).get("source_label") or document.get("source_label") or ""
    ).strip()
    if explicit:
        return explicit
    act_short_name = str(document.get("act_short_name") or "").strip()
    if act_short_name:
        return act_short_name
    court_name = str(document.get("court_name") or "").strip()
    if court_name:
        return court_name
    return str(document.get("doc_uid") or "")


def _display_citation(
    document: Mapping[str, Any],
    unit: Mapping[str, Any] | None,
) -> str:
    explicit = str(
        (unit or {}).get("display_citation") or document.get("display_citation") or ""
    ).strip()
    if explicit:
        return explicit
    return _document_display_citation(document)


def _deep_link(document: Mapping[str, Any], unit: Mapping[str, Any] | None) -> str:
    candidate = str(
        (unit or {}).get("deep_link")
        or document.get("source_url")
        or document.get("normalized_source_url")
        or ""
    ).strip()
    if candidate:
        return candidate
    return f"mongo://legal_corpus/{document.get('doc_uid')}"


def _query_terms(*, query: str, expansions: Sequence[str]) -> list[str]:
    tokens: list[str] = []
    for value in (query, *expansions):
        for token in re.split(r"\s+", str(value).casefold()):
            cleaned = token.strip()
            if cleaned and cleaned not in tokens:
                tokens.append(cleaned)
    return tokens


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def _normalize_filter_token(value: Any) -> str:
    return _normalize_text(value)


def _snippet(*, text: str, query_terms: Sequence[str]) -> str:
    normalized = text.strip()
    if not normalized:
        return ""
    lowered = normalized.casefold()
    start = 0
    for term in query_terms:
        position = lowered.find(term)
        if position >= 0:
            start = max(position - (_MAX_PREVIEW_CHARS // 2), 0)
            break
    end = min(start + _MAX_PREVIEW_CHARS, len(normalized))
    snippet = normalized[start:end].strip()
    if start > 0:
        snippet = f"...{snippet}"
    if end < len(normalized):
        snippet = f"{snippet}..."
    return snippet


def _trim_excerpt(text: str, *, max_chars: int) -> str:
    normalized = text.strip()
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[: max_chars - 1].rstrip()}…"


def _why_relevant(
    *,
    matched_terms: Sequence[str],
    matched_fields: Sequence[str],
    version_selection: _DocumentVersionSelection | None,
) -> str:
    parts = [
        f"Matched terms: {', '.join(matched_terms)}.",
        f"Matched fields: {', '.join(matched_fields)}.",
    ]
    if version_selection and not version_selection.current_only:
        parts.append(f"Version mode: {version_selection.version_status}.")
    return " ".join(parts)


def _page_range(page_start: Any, page_end: Any) -> list[int] | None:
    start = _to_optional_int(page_start)
    end = _to_optional_int(page_end)
    if start is None and end is None:
        return None
    if start is None:
        start = end
    if end is None:
        end = start
    return [start or 0, end or 0]


def _resolve_source_hash(*, document: Mapping[str, Any], source_hash: str) -> str:
    if source_hash:
        return source_hash
    return str(document.get("current_source_hash") or "")


def _storage_backend(source: Mapping[str, Any]) -> str:
    explicit = str(source.get("storage_backend") or "").strip()
    if explicit:
        return explicit
    uri = str(source.get("raw_object_path") or source.get("storage_uri") or "")
    if not uri:
        return "unknown"
    if uri.startswith(("s3://", "gs://")):
        return uri.split("://", 1)[0]
    return "file"


def _document_source_sort_key(source: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        _as_optional_iso(source.get("effective_from")) or "",
        _as_optional_iso(source.get("version_date")) or "",
        str(source.get("source_hash") or ""),
    )


def _source_for_as_of_date(
    *,
    sources: Sequence[Mapping[str, Any]],
    as_of_date: date,
) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for source in sources:
        effective_from = _parse_date(source.get("effective_from"))
        effective_to = _parse_date(source.get("effective_to"))
        version_date = _parse_date(source.get("version_date"))
        if effective_from and as_of_date < effective_from:
            continue
        if effective_to and as_of_date > effective_to:
            continue
        candidates.append(
            {
                **dict(source),
                "_effective_from": effective_from,
                "_effective_to": effective_to,
                "_version_date": version_date,
            }
        )
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            item["_effective_from"] or date.min,
            item["_version_date"] or date.min,
            str(item.get("source_hash") or ""),
        ),
        reverse=True,
    )
    return candidates[0]


def _dedupe_key(unit: Mapping[str, Any], *, include_history: bool = False) -> str:
    for key in ("same_case_group_id", "duplicate_owner_doc_uid"):
        value = str(unit.get(key) or "").strip()
        if value:
            return value
    base_key = ""
    for key in ("canonical_doc_uid", "doc_uid"):
        value = str(unit.get(key) or "").strip()
        if value:
            base_key = value
            break
    if not base_key:
        base_key = str(unit.get("unit_id") or "")
    if include_history:
        source_hash = str(unit.get("source_hash") or "").strip()
        if source_hash:
            return f"{base_key}::{source_hash}"
    return base_key


def _unit_matches_constraints(
    *,
    unit: Mapping[str, Any],
    constraints: Mapping[str, Any],
) -> bool:
    for key, value in constraints.items():
        if key == "current_only":
            continue
        if key in _TOKEN_FILTER_KEYS:
            if not _matches_token_membership(unit.get(key), value):
                return False
            continue
        if key == "judgment_date":
            if not _matches_exact_date(unit.get(key), value):
                return False
            continue
        unit_value = unit.get(key)
        if isinstance(unit_value, list):
            if isinstance(value, list):
                if not any(str(item) in unit_value for item in value):
                    return False
                continue
            if value not in unit_value:
                return False
            continue
        if str(unit_value) != str(value):
            return False
    return True


def _matches_token_membership(unit_value: Any, expected: Any) -> bool:
    unit_tokens = {
        _normalize_filter_token(item)
        for item in (unit_value if isinstance(unit_value, list) else [unit_value])
        if not _is_blank_value(item)
    }
    expected_tokens = {
        _normalize_filter_token(item)
        for item in (expected if isinstance(expected, list) else [expected])
        if not _is_blank_value(item)
    }
    if not unit_tokens or not expected_tokens:
        return False
    return bool(unit_tokens & expected_tokens)


def _matches_exact_date(unit_value: Any, expected: Any) -> bool:
    unit_date = _parse_date(unit_value)
    expected_date = _parse_date(expected)
    if unit_date is not None and expected_date is not None:
        return unit_date == expected_date
    return str(unit_value or "").strip()[:10] == str(expected or "").strip()[:10]


def _is_operational_search_candidate(unit: Mapping[str, Any]) -> bool:
    return (
        bool(unit.get("is_indexable"))
        and str(unit.get("operational_status") or "") == "operational"
    )


def _scope_matches(*, unit: Mapping[str, Any], scope: str) -> bool:
    if scope == "mixed":
        return True
    kind = str(unit.get("document_kind") or "").upper()
    if scope == "acts":
        return kind in ACT_KINDS
    if scope == "case_law":
        return kind in _CASELAW_KINDS
    return False


def _to_optional_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_optional_iso(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.isoformat()
    return str(value)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _utc_now_build_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _first_value(value: Any) -> str | None:
    if isinstance(value, list):
        for item in value:
            if item:
                return str(item)
    return None


def _first_non_blank(values: Iterable[Any]) -> str | None:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return None


def _is_blank_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) == 0
    return False


def _coerce_bool(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    return default
