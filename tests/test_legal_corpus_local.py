from __future__ import annotations

from pathlib import Path

from app.agentic.legal_corpus_local import LocalLegalCorpusTool
from app.ops.legal_collection import FetchResponse, build_local_collection


def _build_collection_root(tmp_path: Path) -> Path:
    input_path = tmp_path / "sources.md"
    input_path.write_text(
        "\n".join(
            [
                "Acts",
                "1. https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.txt",
                "Case law",
                "2. https://www.saos.org.pl/judgments/171957",
            ]
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "legal_collection"
    text_payloads = {
        "https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.txt": (
            "Art. 6. The party alleging damage must prove the damage."
        ),
        "https://www.saos.org.pl/judgments/171957": (
            "Judgment 171957. Deposit should be returned unless the landlord "
            "proves concrete damage and amount."
        ),
    }

    def fetcher(url: str, timeout_seconds: float) -> FetchResponse:
        del timeout_seconds
        body = text_payloads[url].encode("utf-8")
        return FetchResponse(
            url=url,
            status_code=200,
            headers={"Content-Type": "text/plain; charset=utf-8"},
            body=body,
        )

    build_local_collection(
        input_path=input_path,
        output_dir=output_dir,
        fetcher=fetcher,
    )
    return output_dir


def test_local_legal_corpus_search_reports_limitations_and_rich_fields(
    tmp_path: Path,
) -> None:
    tool = LocalLegalCorpusTool(root=_build_collection_root(tmp_path))

    result = tool.search(
        {
            "query": "deposit damage proof",
            "query_expansions": ["landlord"],
            "scope": "mixed",
            "return_level": "document",
            "as_of_date": "2024-01-01",
            "include_history": True,
            "expand_citations": True,
            "filters": {
                "jurisdiction": "PL",
                "issue_tags": ["deposit"],
                "court_level": "appeal",
            },
            "top_k": 5,
        }
    )

    assert result["result_count"] == 2
    assert result["effective_return_level"] == "fragment"
    assert result["applied_filters"]["filters"]["jurisdiction"] == "PL"
    assert result["applied_filters"]["options"]["query_expansions"] == ["landlord"]
    assert result["ignored_filters"]["options"]["return_level"]["value"] == "document"
    assert "issue_tags" in result["unsupported_filters"]["filters"]
    assert "court_level" in result["unsupported_filters"]["filters"]
    assert "as_of_date" in result["unsupported_filters"]["options"]
    assert "include_history" in result["unsupported_filters"]["options"]
    assert "expand_citations" in result["unsupported_filters"]["options"]

    by_doc_uid = {item["doc_uid"]: item for item in result["results"]}
    act_result = by_doc_uid["eli_pl:DU/2001/733"]
    judgment_result = by_doc_uid["saos_pl:171957"]

    assert act_result["act_short_name"] == "Dz.U. 2001 poz. 733"
    assert act_result["source_label"] == "Dz.U. 2001 poz. 733"
    assert act_result["document_kind"] == "act"
    assert act_result["page_range"] is None
    assert act_result["unit_id"].startswith("fragment:")
    assert act_result["node_id"].startswith("offset:")

    assert judgment_result["document_kind"] == "judgment"
    assert judgment_result["court_name"] is None
    assert judgment_result["deep_link"] == "https://www.saos.org.pl/judgments/171957"
    assert "text" in judgment_result["matched_fields"]
    assert judgment_result["source_hash"]


def test_local_legal_corpus_search_supports_document_kind_and_locator_filters(
    tmp_path: Path,
) -> None:
    tool = LocalLegalCorpusTool(root=_build_collection_root(tmp_path))

    result = tool.search(
        {
            "query": "deposit damage",
            "scope": "mixed",
            "return_level": "fragment",
            "filters": {"document_kind": "judgment"},
            "locator": {"source_system": "saos_pl", "case_signature": "I ACa 1/24"},
            "top_k": 5,
        }
    )

    assert result["result_count"] == 1
    assert result["results"][0]["doc_uid"] == "saos_pl:171957"
    assert result["applied_filters"]["filters"]["document_kind"] == "judgment"
    assert result["applied_filters"]["locator"]["source_system"] == "saos_pl"
    assert "case_signature" in result["unsupported_filters"]["locator"]


def test_local_legal_corpus_fetch_fragments_marks_raw_text_fallback_truthfully(
    tmp_path: Path,
) -> None:
    tool = LocalLegalCorpusTool(root=_build_collection_root(tmp_path))
    search_result = tool.search(
        {
            "query": "landlord damage",
            "scope": "mixed",
            "return_level": "fragment",
            "top_k": 1,
        }
    )
    machine_ref = search_result["results"][0]["machine_ref"]

    fragments = tool.fetch_fragments(
        {
            "refs": [machine_ref],
            "include_neighbors": True,
            "neighbor_window": 1,
            "max_chars_per_fragment": 300,
        }
    )

    assert fragments["ref_count"] == 1
    fragment = fragments["fragments"][0]
    assert fragment["text"]
    assert fragment["page_start"] is None
    assert fragment["page_end"] is None
    assert fragment["page_range"] is None
    assert fragment["locator"]["precision"] == "char_offsets_only"
    assert fragment["citation"]["page_truth_status"] == "not_available_local"
    assert fragment["diagnostics"]["fallback_used"] is True
    assert fragment["diagnostics"]["text_source"] == "raw_object_text"
    assert fragment["quote_checksum"]


def test_local_legal_corpus_provenance_exposes_integrity_and_version_limits(
    tmp_path: Path,
) -> None:
    tool = LocalLegalCorpusTool(root=_build_collection_root(tmp_path))
    search_result = tool.search(
        {
            "query": "damage",
            "scope": "mixed",
            "return_level": "fragment",
            "top_k": 1,
        }
    )
    machine_ref = search_result["results"][0]["machine_ref"]

    provenance = tool.get_provenance(
        {"ref": machine_ref, "include_artifacts": True, "debug": True}
    )

    assert provenance["provenance_status"] == "ok"
    assert provenance["has_history"] is False
    assert provenance["integrity_status"] == "ok"
    assert provenance["artifact_integrity"]["status"] == "ok"
    assert provenance["artifact_uri"].startswith("docs/")
    assert provenance["current_version"]["status"] == "current_snapshot_only_local"
    assert provenance["current_version"]["version_date"] is None
    assert provenance["raw_object_path"]
    assert provenance["response_meta_path"]
    assert provenance["debug"]["backend"] == "local"


def test_local_legal_corpus_expand_related_returns_structured_explanation(
    tmp_path: Path,
) -> None:
    tool = LocalLegalCorpusTool(root=_build_collection_root(tmp_path))
    result = tool.expand_related(
        {
            "refs": [{"doc_uid": "saos_pl:171957"}],
            "relation_types": ["cites", "same_case"],
        }
    )

    assert result["results"] == []
    assert result["status"] == "not_available_local"
    assert result["explanation"]["backend"] == "local"
    assert result["explanation"]["supported"] is False
    assert result["explanation"]["requested_relation_types"] == [
        "cites",
        "same_case",
    ]
