from __future__ import annotations

from typing import Any

import app.agentic.legal_corpus_mongo as legal_corpus_mongo
from app.agentic.legal_corpus_mongo import (
    MongoLegalCorpusMaterializer,
    MongoLegalCorpusTool,
)
from tests.fake_mongo_runtime import build_legal_corpus_runtime


_QUERY = "niewozwrot kaucji uszkodzenia komunalne po wyjezdzie"


def test_materializer_builds_retrieval_units_and_citation_resolutions() -> None:
    runtime = build_legal_corpus_runtime()

    report = MongoLegalCorpusMaterializer(runtime=runtime).rebuild()

    index_run = runtime.load_collection("retrieval_index_runs")[0]
    retrieval_units = runtime.load_collection(index_run["retrieval_units_collection"])
    citation_resolutions = runtime.load_collection(
        index_run["citation_resolutions_collection"]
    )
    assert report.units_count == len(retrieval_units)
    assert report.citation_resolutions_count == len(citation_resolutions)
    assert retrieval_units
    assert {
        "unit_id",
        "doc_uid",
        "source_hash",
        "effective_from",
        "effective_to",
    } <= set(retrieval_units[0])
    resolution = citation_resolutions[0]
    assert resolution["target_external_id"] == "eli:DU/2001/733"
    assert resolution["target_doc_uid"] == "eli_pl:DU/2001/733"
    assert resolution["resolution_status"] == "resolved"
    assert index_run["status"] == "completed"
    assert index_run["retrieval_units_collection"].startswith("retrieval_units__")
    assert index_run["citation_resolutions_collection"].startswith(
        "citation_resolutions__"
    )


def test_materializer_dedupes_duplicate_retrieval_units_before_unique_index() -> None:
    runtime = build_legal_corpus_runtime()
    duplicate_node = dict(runtime.load_collection("nodes")[0])
    runtime.collection("nodes").insert_one(duplicate_node)

    report = MongoLegalCorpusMaterializer(runtime=runtime).rebuild()

    index_run = runtime.load_collection("retrieval_index_runs")[0]
    retrieval_units = runtime.load_collection(index_run["retrieval_units_collection"])
    unique_keys = {
        (row["doc_uid"], row["source_hash"], row["unit_id"])
        for row in retrieval_units
    }
    assert report.units_count == len(retrieval_units)
    assert len(unique_keys) == len(retrieval_units)


def test_search_returns_operational_current_results_without_same_case_duplicates() -> (
    None
):
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)

    payload = tool.search(
        {
            "query": _QUERY,
            "scope": "mixed",
            "return_level": "fragment",
            "top_k": 5,
            "filters": {"current_only": True},
        }
    )

    assert payload["result_count"] >= 2
    returned_doc_uids = [result["doc_uid"] for result in payload["results"]]
    assert "eli_pl:DU/2001/733" in returned_doc_uids
    assert "saos_pl:171957" in returned_doc_uids
    assert "courts_pl:urlsha:mirror-171957" not in returned_doc_uids
    assert "curia_eu:urlsha:broken" not in returned_doc_uids
    act_result = next(
        result
        for result in payload["results"]
        if result["doc_uid"] == "eli_pl:DU/2001/733"
    )
    assert act_result["source_hash"] == "sha256:act-current"
    assert act_result["result_level"] == "fragment"
    assert act_result["metadata"]["effective_return_level"] == "fragment"
    assert payload["diagnostics"]["index_freshness_status"] == "fresh"


def test_search_return_level_document_returns_document_level_results() -> None:
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)

    payload = tool.search(
        {
            "query": _QUERY,
            "scope": "mixed",
            "return_level": "document",
            "top_k": 5,
            "filters": {"current_only": True},
        }
    )

    assert payload["effective_return_level"] == "document"
    assert payload["diagnostics"]["returned_result_levels"] == ["document"]
    assert payload["result_count"] >= 2
    first_result = payload["results"][0]
    assert first_result["result_level"] == "document"
    assert first_result["metadata"]["result_level"] == "document"
    assert first_result["metadata"]["effective_return_level"] == "document"
    assert first_result["machine_ref"]["doc_uid"] == first_result["doc_uid"]
    assert first_result["machine_ref"]["source_hash"] == first_result["source_hash"]
    assert first_result["metadata"]["anchor_unit_id"]
    assert "unit_id" not in first_result
    assert "page_range" not in first_result


def test_search_return_level_mixed_returns_document_and_fragment_results() -> None:
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)

    payload = tool.search(
        {
            "query": _QUERY,
            "scope": "mixed",
            "return_level": "mixed",
            "top_k": 4,
            "filters": {"current_only": True},
        }
    )

    result_levels = [result["result_level"] for result in payload["results"]]
    assert payload["effective_return_level"] == "mixed"
    assert payload["diagnostics"]["returned_result_levels"] == ["document", "fragment"]
    assert result_levels[:2] == ["document", "fragment"]
    assert "document" in result_levels
    assert "fragment" in result_levels
    doc_uids = [result["doc_uid"] for result in payload["results"]]
    assert len(doc_uids) == len(set(doc_uids))


def test_search_supports_as_of_date_and_reports_missing_historical_version() -> None:
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)

    historical_payload = tool.search(
        {
            "query": _QUERY,
            "scope": "acts",
            "return_level": "fragment",
            "top_k": 3,
            "as_of_date": "2024-06-01",
        }
    )
    assert historical_payload["result_count"] == 1
    assert historical_payload["results"][0]["source_hash"] == "sha256:act-historical"

    missing_payload = tool.search(
        {
            "query": _QUERY,
            "scope": "acts",
            "return_level": "fragment",
            "top_k": 3,
            "as_of_date": "1990-01-01",
        }
    )
    assert missing_payload["result_count"] == 0
    assert missing_payload["diagnostics"]["historical_version_not_found"] == [
        "eli_pl:DU/2001/733"
    ]


def test_search_supports_issue_tags_and_facts_tags_filters() -> None:
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)

    issue_payload = tool.search(
        {
            "query": _QUERY,
            "scope": "mixed",
            "return_level": "fragment",
            "top_k": 5,
            "filters": {"issue_tags": "deposit_return"},
        }
    )
    issue_doc_uids = {result["doc_uid"] for result in issue_payload["results"]}
    assert "eli_pl:DU/2001/733" in issue_doc_uids
    assert "saos_pl:171957" in issue_doc_uids
    assert "issue_tags" not in issue_payload["unsupported_filters"]["filters"]
    assert (
        issue_payload["diagnostics"]["filter_semantics"]["issue_tags"]
        == "case_insensitive_exact_token_membership"
    )

    facts_payload = tool.search(
        {
            "query": _QUERY,
            "scope": "case_law",
            "return_level": "fragment",
            "top_k": 5,
            "filters": {"facts_tags": ["utilities_after_move_out"]},
        }
    )
    assert facts_payload["result_count"] == 1
    assert facts_payload["results"][0]["doc_uid"] == "saos_pl:171957"
    assert "facts_tags" not in facts_payload["unsupported_filters"]["filters"]


def test_search_supports_related_provisions_and_judgment_date_filters() -> None:
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)

    provisions_payload = tool.search(
        {
            "query": _QUERY,
            "scope": "mixed",
            "return_level": "fragment",
            "top_k": 5,
            "filters": {
                "related_provisions": [
                    "ART. 6 UST. 4 USTAWY O OCHRONIE PRAW LOKATOROW"
                ]
            },
        }
    )
    provision_doc_uids = {result["doc_uid"] for result in provisions_payload["results"]}
    assert "eli_pl:DU/2001/733" in provision_doc_uids
    assert "saos_pl:171957" in provision_doc_uids
    assert "related_provisions" not in provisions_payload["unsupported_filters"][
        "filters"
    ]

    judgment_payload = tool.search(
        {
            "query": _QUERY,
            "scope": "case_law",
            "return_level": "fragment",
            "top_k": 5,
            "filters": {"judgment_date": "2015-05-13T00:00:00Z"},
        }
    )
    assert judgment_payload["result_count"] == 1
    assert judgment_payload["results"][0]["doc_uid"] == "saos_pl:171957"
    assert "judgment_date" not in judgment_payload["unsupported_filters"]["filters"]
    assert (
        judgment_payload["diagnostics"]["filter_semantics"]["judgment_date"]
        == "iso_date_exact_match"
    )


def test_search_supports_status_alias_to_current_status() -> None:
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)

    alias_payload = tool.search(
        {
            "query": _QUERY,
            "scope": "acts",
            "return_level": "fragment",
            "top_k": 5,
            "filters": {"status": "current"},
        }
    )
    canonical_payload = tool.search(
        {
            "query": _QUERY,
            "scope": "acts",
            "return_level": "fragment",
            "top_k": 5,
            "filters": {"current_status": "current"},
        }
    )

    assert [result["doc_uid"] for result in alias_payload["results"]] == [
        result["doc_uid"] for result in canonical_payload["results"]
    ]
    assert alias_payload["applied_filters"]["filters"]["status"] == {
        "value": "current",
        "alias_to": "current_status",
    }
    assert alias_payload["diagnostics"]["filter_aliases"]["status"] == "current_status"
    assert "status" not in alias_payload["unsupported_filters"]["filters"]


def test_search_include_history_returns_all_versions_and_reports_mode() -> None:
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)

    payload = tool.search(
        {
            "query": _QUERY,
            "scope": "acts",
            "return_level": "fragment",
            "top_k": 5,
            "include_history": True,
        }
    )

    source_hashes = {result["source_hash"] for result in payload["results"]}
    assert source_hashes == {"sha256:act-current", "sha256:act-historical"}
    assert payload["result_count"] == 2
    assert payload["diagnostics"]["include_history_status"] == "all_versions"
    assert payload["applied_filters"]["options"]["include_history"] == {
        "value": True,
        "mode": "all_versions",
    }


def test_fetch_fragments_expand_related_and_get_provenance_use_materialized_layer() -> (
    None
):
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)
    search_payload = tool.search(
        {
            "query": _QUERY,
            "scope": "case_law",
            "return_level": "fragment",
            "top_k": 2,
            "filters": {"current_only": True},
        }
    )
    machine_ref = search_payload["results"][0]["machine_ref"]

    fragments = tool.fetch_fragments(
        {
            "refs": [machine_ref],
            "include_neighbors": False,
            "neighbor_window": 0,
            "max_chars_per_fragment": 400,
        }
    )
    fragment = fragments["fragments"][0]
    assert "udowodnienia" in fragment["text"]
    assert fragment["locator"]
    assert fragment["page_start"] == 2
    assert fragment["quote_checksum"]

    related = tool.expand_related(
        {
            "refs": [machine_ref],
            "relation_types": ["cites", "same_case"],
            "top_k": 5,
        }
    )
    relation_doc_uids = {result["doc_uid"] for result in related["results"]}
    assert "eli_pl:DU/2001/733" in relation_doc_uids
    assert "courts_pl:urlsha:mirror-171957" in relation_doc_uids
    assert related["explanation"]["used_resolution_layer"] is True

    provenance = tool.get_provenance({"ref": machine_ref, "include_artifacts": True})
    assert provenance["storage_backend"] == "file"
    assert provenance["artifact_manifest"]["raw_bin_uri"]
    assert provenance["integrity_status"] == "ok"
    assert provenance["raw_object_path"]


def test_mongo_tool_responses_include_deterministic_audit_trail() -> None:
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)

    search_payload = tool.search(
        {
            "query": _QUERY,
            "scope": "mixed",
            "return_level": "fragment",
            "top_k": 3,
        }
    )
    machine_ref = search_payload["results"][0]["machine_ref"]
    fragments_payload = tool.fetch_fragments(
        {
            "refs": [machine_ref],
            "include_neighbors": False,
            "neighbor_window": 0,
            "max_chars_per_fragment": 400,
        }
    )
    related_payload = tool.expand_related(
        {
            "refs": [machine_ref],
            "relation_types": ["cites", "unsupported_edge"],
            "top_k": 5,
        }
    )
    provenance_payload = tool.get_provenance(
        {"ref": machine_ref, "include_artifacts": True}
    )

    for payload in (
        search_payload,
        fragments_payload,
        related_payload,
        provenance_payload,
    ):
        audit = payload["audit"]
        assert audit["request_id"]
        assert audit["tool_call_id"]
        assert audit["request_hash"]
        assert isinstance(audit["latency_ms"], int)
        assert isinstance(audit["returned_refs"], list)
        assert audit["returned_ref_count"] == len(audit["returned_refs"])
        assert isinstance(audit["warnings"], list)

    assert search_payload["audit"]["query_hash"]
    assert search_payload["audit"]["returned_ref_count"] == len(
        search_payload["results"]
    )
    assert fragments_payload["audit"]["returned_ref_count"] == len(
        fragments_payload["fragments"]
    )
    assert related_payload["audit"]["warnings"] == [
        "Unsupported relation_type for mongo backend: unsupported_edge"
    ]
    assert provenance_payload["audit"]["returned_refs"] == [machine_ref]


def test_search_reports_stale_index_when_ingest_advances_after_materialization() -> (
    None
):
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)
    runtime.collection("ingest_runs").insert_one(
        {
            "run_id": "ingest-003",
            "status": "completed",
            "finished_at": "2026-03-12T00:00:00+00:00",
            "updated_at": "2026-03-12T00:00:00+00:00",
        }
    )

    payload = tool.search(
        {
            "query": _QUERY,
            "scope": "mixed",
            "return_level": "fragment",
            "top_k": 5,
        }
    )

    assert payload["diagnostics"]["index_freshness_status"] == "stale"
    assert payload["diagnostics"]["retrieval_index_ingest_run_id"] == "ingest-002"
    assert payload["diagnostics"]["latest_successful_ingest_run_id"] == "ingest-003"
    assert payload["diagnostics"]["warnings"]


def test_failed_rebuild_keeps_last_completed_materialized_index(
    monkeypatch: Any,
) -> None:
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)
    initial_index_run = runtime.load_collection("retrieval_index_runs")[0]
    runtime.collection("ingest_runs").insert_one(
        {
            "run_id": "ingest-003",
            "status": "completed",
            "finished_at": "2026-03-12T00:00:00+00:00",
            "updated_at": "2026-03-12T00:00:00+00:00",
        }
    )
    monkeypatch.setattr(
        legal_corpus_mongo,
        "_utc_now_iso",
        lambda: "2026-03-12T00:00:01+00:00",
    )

    original_collection = runtime.collection

    def failing_collection(name: str) -> Any:
        collection = original_collection(name)
        if name.startswith("retrieval_units__") and name != initial_index_run.get(
            "retrieval_units_collection"
        ):
            original_insert_many = collection.insert_many

            def fail_insert(rows: list[dict[str, Any]]) -> None:
                raise RuntimeError("simulated rebuild failure")

            collection.insert_many = fail_insert  # type: ignore[method-assign]
            collection._original_insert_many = original_insert_many  # type: ignore[attr-defined]
        return collection

    monkeypatch.setattr(
        type(runtime), "collection", lambda self, name: failing_collection(name)
    )

    report = tool.ensure_materialized_index()
    assert report is None

    payload = tool.search(
        {
            "query": _QUERY,
            "scope": "mixed",
            "return_level": "fragment",
            "top_k": 3,
        }
    )

    assert payload["result_count"] >= 2
    assert any(
        "Materialized retrieval rebuild failed" in warning
        for warning in payload["diagnostics"]["warnings"]
    )
    index_runs = runtime.load_collection("retrieval_index_runs")
    assert len(index_runs) == 1
    assert index_runs[0]["build_id"] == initial_index_run["build_id"]


def test_successful_rebuild_refreshes_index_freshness_after_new_ingest() -> None:
    runtime = build_legal_corpus_runtime()
    tool = MongoLegalCorpusTool(runtime=runtime, auto_materialize=True)
    runtime.collection("ingest_runs").insert_one(
        {
            "run_id": "ingest-003",
            "status": "completed",
            "finished_at": "2026-03-12T00:00:00+00:00",
            "updated_at": "2026-03-12T00:00:00+00:00",
        }
    )

    report = tool.ensure_materialized_index()

    assert report is not None
    payload = tool.search(
        {
            "query": _QUERY,
            "scope": "mixed",
            "return_level": "fragment",
            "top_k": 3,
        }
    )

    assert payload["result_count"] >= 2
    assert payload["diagnostics"]["index_freshness_status"] == "fresh"
    assert payload["diagnostics"]["latest_successful_ingest_run_id"] == "ingest-003"
    assert payload["diagnostics"]["retrieval_index_ingest_run_id"] == "ingest-003"
