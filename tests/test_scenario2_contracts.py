from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.agentic.legal_corpus_contract import (
    ExpandRelatedRequest,
    FetchFragmentsRequest,
    ProvenanceRequest,
    SearchRequest,
)
from app.agentic.scenario2_runner import Scenario2RunConfig, StubScenario2Runner
from app.pipeline.scenario_router import (
    SCENARIO_2_PROMPT_SOURCE_PATH,
    resolve_scenario_prompt_source_path,
)


def test_legal_corpus_request_shapes_cover_expected_fields() -> None:
    expected_search_required = {"query", "scope", "return_level"}
    expected_search_optional = {
        "query_language",
        "query_expansions",
        "as_of_date",
        "include_history",
        "expand_citations",
        "top_k",
        "locator",
        "filters",
    }
    expected_fetch_fragments_required = {"refs"}
    expected_fetch_fragments_optional = {
        "include_neighbors",
        "neighbor_window",
        "max_chars_per_fragment",
    }
    expected_expand_related_required = {"refs", "relation_types"}
    expected_expand_related_optional = {"top_k"}
    expected_provenance_required = {"ref"}
    expected_provenance_optional = {"include_artifacts", "debug"}

    search: SearchRequest = {
        "query": "warranty term",
        "scope": "mixed",
        "return_level": "fragment",
        "filters": {"jurisdiction": "pl"},
        "top_k": 5,
    }
    fetch: FetchFragmentsRequest = {
        "refs": [{"doc_uid": "doc-1"}],
        "include_neighbors": True,
        "neighbor_window": 1,
    }
    expand: ExpandRelatedRequest = {
        "refs": [{"doc_uid": "doc-1"}],
        "relation_types": ["cites", "cited_by"],
        "top_k": 3,
    }
    provenance: ProvenanceRequest = {"ref": {"doc_uid": "doc-1"}}

    assert set(search.keys()).issubset(
        expected_search_required | expected_search_optional
    )
    assert expected_search_required.issubset(search.keys())
    assert expected_fetch_fragments_required.issubset(fetch.keys())
    assert expected_fetch_fragments_optional.issuperset(fetch.keys() - expected_fetch_fragments_required)
    assert expected_expand_related_required.issubset(expand.keys())
    assert expected_expand_related_optional.issuperset(expand.keys() - expected_expand_related_required)
    assert expected_provenance_required.issubset(provenance.keys())
    assert expected_provenance_optional.issuperset(provenance.keys() - expected_provenance_required)

    assert search["query"] == "warranty term"
    assert search["scope"] == "mixed"
    assert search["return_level"] == "fragment"
    assert search["top_k"] == 5
    assert fetch["refs"] == [{"doc_uid": "doc-1"}]
    assert expand["relation_types"] == ["cites", "cited_by"]
    assert expand["top_k"] == 3
    assert provenance["ref"] == {"doc_uid": "doc-1"}


def test_stub_scenario2_runner_returns_plain_text_result_and_trace(tmp_path: Path) -> None:
    prompt_file = tmp_path / "agent_prompt_V1.1.md"
    prompt_file.write_text("scenario2 prompt", encoding="utf-8")
    prompt_fingerprint = hashlib.sha256(b"scenario2 prompt").hexdigest()

    result = StubScenario2Runner().run(
        packed_documents="A\nB\n",
        config=Scenario2RunConfig(
            provider="openai",
            model="gpt-5.4",
            prompt_name="agent_prompt_foundation",
            prompt_version="v1.1",
            prompt_source_path=str(prompt_file),
            placeholder_text="Scenario 2 foundation is active.",
        ),
        system_prompt_path=str(prompt_file),
        legal_corpus_tool=None,
    )

    assert result.response_mode == "plain_text"
    assert result.final_text == "Scenario 2 foundation is active."
    assert result.tool_trace
    assert result.steps
    assert result.diagnostics["provider"] == "openai"
    assert result.diagnostics["resolved_prompt_path"] == str(prompt_file.resolve())
    assert result.diagnostics["prompt_exists"] is True
    assert result.diagnostics["prompt_size_bytes"] == len("scenario2 prompt".encode("utf-8"))
    assert result.tool_trace[0]["prompt_sha256"] == prompt_fingerprint


def test_stub_scenario2_runner_errors_if_prompt_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="System prompt path must point"):
        StubScenario2Runner().run(
            packed_documents="docs",
            config=Scenario2RunConfig(
                provider="openai",
                model="gpt-5.4",
                prompt_name="agent_prompt_foundation",
                prompt_version="v1.1",
                prompt_source_path=str(tmp_path / "missing.md"),
                placeholder_text="Scenario 2 foundation is active.",
            ),
            system_prompt_path=str(tmp_path / "missing.md"),
            legal_corpus_tool=None,
        )


def test_scenario2_prompt_path_resolver_returns_existing_file(tmp_path: Path) -> None:
    prompt_source = tmp_path / "app" / "prompts" / "agent_prompt_V1.1.md"
    prompt_source.parent.mkdir(parents=True)
    prompt_source.write_text("foundation prompt", encoding="utf-8")

    resolved = resolve_scenario_prompt_source_path(
        SCENARIO_2_PROMPT_SOURCE_PATH,
        prompt_root=tmp_path,
    )

    assert Path(resolved).is_file()
