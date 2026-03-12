from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from app.agentic.openai_scenario2_runner import (
    OpenAIScenario2Runner,
    _citation_binding_status,
    _fragment_grounding_status,
    _ToolUsageState,
)
from app.agentic.scenario2_runner import (
    Scenario2RunConfig,
    Scenario2RunnerError,
)


_FRAGMENT_REF = {
    "doc_uid": "doc-1",
    "source_hash": "sha256:doc-1",
    "unit_id": "fragment:0:32",
    "locator": {"start_char": 0, "end_char": 32},
}


class FakeResponsesService:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(copy.deepcopy(kwargs))
        if not self.responses:
            raise AssertionError("No more mock responses")
        return self.responses.pop(0)


class FakeSDKResponse:
    def __init__(self, *, response_id: str, output: list[dict[str, Any]]) -> None:
        self.id = response_id
        self._payload = {"output": output}

    def model_dump(self) -> dict[str, Any]:
        return copy.deepcopy(self._payload)


class RecordingLegalCorpusTool:
    def __init__(self) -> None:
        self.search_calls: list[dict[str, Any]] = []
        self.fetch_fragments_calls: list[dict[str, Any]] = []
        self.expand_related_calls: list[dict[str, Any]] = []
        self.get_provenance_calls: list[dict[str, Any]] = []

    def search(self, request: dict[str, Any]) -> dict[str, Any]:
        self.search_calls.append(request)
        return {"results": [{"machine_ref": dict(_FRAGMENT_REF)}]}

    def fetch_fragments(self, request: dict[str, Any]) -> dict[str, Any]:
        self.fetch_fragments_calls.append(request)
        return {
            "fragments": [
                {
                    "machine_ref": dict(_FRAGMENT_REF),
                    "doc_uid": "doc-1",
                    "source_hash": "sha256:doc-1",
                    "display_citation": "Doc 1 fragment",
                    "text": "Exact supporting fragment.",
                    "locator": {"start_char": 0, "end_char": 32},
                    "locator_precision": "char_offsets_only",
                    "page_truth_status": "not_available_local",
                    "quote_checksum": "sha256:fragment",
                }
            ]
        }

    def expand_related(self, request: dict[str, Any]) -> dict[str, Any]:
        self.expand_related_calls.append(request)
        return {"related": ["related"]}

    def get_provenance(self, request: dict[str, Any]) -> dict[str, Any]:
        self.get_provenance_calls.append(request)
        return {"provenance": ["prov"]}


class EmptyFragmentsLegalCorpusTool(RecordingLegalCorpusTool):
    def fetch_fragments(self, request: dict[str, Any]) -> dict[str, Any]:
        self.fetch_fragments_calls.append(request)
        return {"fragments": []}


class UnusableFragmentsLegalCorpusTool(RecordingLegalCorpusTool):
    def fetch_fragments(self, request: dict[str, Any]) -> dict[str, Any]:
        self.fetch_fragments_calls.append(request)
        return {
            "fragments": [
                {
                    "text": "Preview without stable provenance handle.",
                }
            ]
        }


class LongExcerptLegalCorpusTool(RecordingLegalCorpusTool):
    def fetch_fragments(self, request: dict[str, Any]) -> dict[str, Any]:
        self.fetch_fragments_calls.append(request)
        return {
            "fragments": [
                {
                    "machine_ref": dict(_FRAGMENT_REF),
                    "doc_uid": "doc-1",
                    "source_hash": "sha256:doc-1",
                    "display_citation": "Doc 1 fragment",
                    "text": "A" * 600,
                    "locator": {"start_char": 0, "end_char": 600},
                    "locator_precision": "char_offsets_only",
                    "page_truth_status": "not_available_local",
                    "quote_checksum": "sha256:long-fragment",
                }
            ]
        }


def _scenario2_config(*, prompt_path: str) -> Scenario2RunConfig:
    return Scenario2RunConfig(
        provider="openai",
        model="gpt-5.4",
        prompt_name="agent_prompt_foundation",
        prompt_version="v1.1",
        prompt_source_path=prompt_path,
        placeholder_text="placeholder",
    )


def _output_text_response(text: str) -> dict[str, Any]:
    return {
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": text},
                ],
            }
        ]
    }


def _structured_scenario2_answer(
    *,
    include_sources_section: bool = True,
    include_fetched_source_reference: bool = True,
    include_legal_citations_in_analysis: bool = True,
    include_user_doc_citations: bool = True,
    include_legal_citations_only_in_sources: bool = False,
) -> str:
    user_doc_citation = (
        "[Документ пользователя: договор аренды, п. 3]"
        if include_user_doc_citations
        else "Подтвержден факт внесения депозита."
    )
    legal_citation_line = (
        "[Норма: KC, art. 6] [Практика: SA Warszawa, 2024, № I ACa 123/24]"
    )
    applicable_norms = "Применимы общие нормы о возврате депозита."
    analysis_text = "Удержание требует документального подтверждения."
    if include_legal_citations_in_analysis:
        applicable_norms = f"{applicable_norms} {legal_citation_line}"
        analysis_text = f"{analysis_text} {legal_citation_line}"

    sections = [
        "1. Краткий вывод\nПозиция арендатора выглядит частично подтвержденной.",
        f"2. Что подтверждено документами\n{user_doc_citation}",
        "3. Что спорно или не доказано\nРазмер ущерба подтвержден не полностью.",
        f"4. Применимые нормы и практика\n{applicable_norms}",
        f"5. Анализ по вопросам\n{analysis_text}",
        "6. Что делать дальше\nЗапросить расчет удержаний и подтверждающие документы.",
    ]
    if include_sources_section:
        source_line = (
            "Doc 1 fragment"
            if include_fetched_source_reference
            else "Общие ссылки на материалы дела."
        )
        if include_legal_citations_only_in_sources:
            source_line = f"{source_line} {legal_citation_line}".strip()
        sections.append(f"7. Источники\n{source_line}")
    return "\n\n".join(sections)


def test_openai_scenario2_runner_builds_initial_request_payload(tmp_path: Path) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt for scenario2", encoding="utf-8")
    responses_service = FakeResponsesService(
        responses=[_output_text_response("final answer")]
    )
    runner = OpenAIScenario2Runner(
        responses_service=responses_service,
        max_tool_rounds=2,
    )

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=None,
    )

    assert result.final_text == "final answer"
    assert result.diagnostics["tool_usage_counts"] == {
        "search": 0,
        "fetch_fragments": 0,
        "expand_related": 0,
        "get_provenance": 0,
    }
    assert result.diagnostics["search_budget_limit"] == 40
    assert result.diagnostics["search_budget_used"] == 0
    assert result.diagnostics["tool_round_limit"] == 2
    assert result.diagnostics["fetch_fragments_called"] is False
    assert result.diagnostics["fetch_fragments_returned_usable_fragments"] is False
    assert result.diagnostics["fragment_grounding_status"] == "not_applicable"
    assert result.diagnostics["citation_binding_status"] == "not_applicable"
    assert result.diagnostics["successful_fetch_fragments"] is False
    assert result.diagnostics["fetched_fragment_ledger"] == []
    assert result.diagnostics["fetched_fragment_refs"] == []
    assert result.diagnostics["fetched_fragment_doc_uids"] == []
    assert result.diagnostics["fetched_fragment_source_hashes"] == []
    assert result.diagnostics["fetched_fragment_quote_checksums"] == []
    assert result.diagnostics["repair_turn_used"] is False
    assert result.diagnostics["citation_format_status"] == "not_applicable"
    assert result.diagnostics["legal_citation_count"] == 0
    assert result.diagnostics["user_doc_citation_count"] == 0
    assert result.diagnostics["citations_in_analysis_sections"] is None
    assert result.diagnostics["malformed_citation_warnings"] == []
    assert len(responses_service.calls) == 1
    call = responses_service.calls[0]
    assert call["model"] == "gpt-5.4"
    assert call["tool_choice"] == "auto"
    tools = call["tools"]
    assert {entry["name"] for entry in tools} == {
        "search",
        "fetch_fragments",
        "expand_related",
        "get_provenance",
    }


def test_openai_scenario2_runner_enforces_search_budget_limit(tmp_path: Path) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt for search budget", encoding="utf-8")

    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "komunalne",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
        ]
    )
    runner = OpenAIScenario2Runner(
        responses_service=service,
        max_tool_rounds=10,
        search_budget_limit=1,
    )

    with pytest.raises(Scenario2RunnerError) as exc_info:
        runner.run(
            packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
            config=_scenario2_config(prompt_path=str(prompt_path)),
            system_prompt_path=str(prompt_path),
            legal_corpus_tool=RecordingLegalCorpusTool(),
        )

    error = exc_info.value
    assert "search budget exceeded" in str(error)
    partial = error.to_run_result()
    assert partial.diagnostics["search_budget_limit"] == 1
    assert partial.diagnostics["search_budget_used"] == 1
    assert partial.diagnostics["tool_round_limit"] == 10
    assert partial.diagnostics["tool_usage_counts"]["search"] == 1
    assert partial.tool_trace[-1]["tool"] == "search"
    assert partial.tool_trace[-1]["status"] == "failed"


def test_openai_scenario2_runner_bounded_tool_rounds(tmp_path: Path) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Scenario2 bounded tool round prompt", encoding="utf-8")

    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {"type": "function_call", "name": "search", "arguments": "{}"},
                    {
                        "type": "function_call",
                        "name": "get_provenance",
                        "arguments": "{}",
                    },
                ]
            }
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=1)

    with pytest.raises(Scenario2RunnerError, match="tool round limit exceeded") as exc:
        runner.run(
            packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
            config=_scenario2_config(prompt_path=str(prompt_path)),
            system_prompt_path=str(prompt_path),
            legal_corpus_tool=None,
        )

    partial = exc.value.to_run_result()
    assert partial.steps == ["scenario2_openai_start", "openai_request"]
    assert partial.diagnostics["tool_calls"] == 2
    assert partial.tool_round_count == 0


def test_openai_scenario2_runner_unknown_tool_is_rejected(tmp_path: Path) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")

    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "legal_corpus.unknown",
                        "arguments": "{}",
                    }
                ]
            }
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service)

    with pytest.raises(Scenario2RunnerError, match="Unknown legal corpus tool") as exc:
        runner.run(
            packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
            config=_scenario2_config(prompt_path=str(prompt_path)),
            system_prompt_path=str(prompt_path),
            legal_corpus_tool=RecordingLegalCorpusTool(),
        )

    partial = exc.value.to_run_result()
    assert partial.steps[-1] == "tool_error:unknown"
    assert partial.tool_trace[0]["tool"] == "legal_corpus.unknown"
    assert partial.tool_trace[0]["status"] == "failed"


def test_openai_scenario2_runner_reports_empty_fragments_status() -> None:
    tool_usage_state = _ToolUsageState()

    tool_usage_state.register_attempt("search")
    tool_usage_state.register_attempt("fetch_fragments")
    tool_usage_state.register_fetched_fragments({"fragments": [{}]})

    assert tool_usage_state.fetch_fragments_called is True
    assert tool_usage_state.fetch_fragments_returned_usable_fragments is False
    assert _fragment_grounding_status(tool_usage_state=tool_usage_state) == (
        "empty_fragments"
    )
    assert _citation_binding_status(tool_usage_state=tool_usage_state) == (
        "empty_fragments"
    )


def test_openai_scenario2_runner_requires_fetch_fragments_before_final_answer(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    search_call = {
        "type": "function_call",
        "name": "search",
        "arguments": json.dumps(
            {
                "query": "warranty",
                "scope": "mixed",
                "return_level": "fragment",
            }
        ),
    }
    service = FakeResponsesService(
        responses=[
            {"output": [search_call]},
            _output_text_response("ungrounded final response"),
            _output_text_response("still ungrounded final response"),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)
    legal_tool = RecordingLegalCorpusTool()

    with pytest.raises(Scenario2RunnerError, match="not source-grounded") as exc:
        runner.run(
            packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
            config=_scenario2_config(prompt_path=str(prompt_path)),
            system_prompt_path=str(prompt_path),
            legal_corpus_tool=legal_tool,
        )

    partial = exc.value.to_run_result()
    assert legal_tool.search_calls == [
        {
            "query": "warranty",
            "scope": "mixed",
            "return_level": "fragment",
        }
    ]
    assert legal_tool.fetch_fragments_calls == []
    assert partial.final_text == "still ungrounded final response"
    assert partial.tool_trace[0]["tool"] == "search"
    assert partial.diagnostics["tool_usage_counts"] == {
        "search": 1,
        "fetch_fragments": 0,
        "expand_related": 0,
        "get_provenance": 0,
    }
    assert partial.diagnostics["fragment_grounding_status"] == "missing_fragments"
    assert partial.diagnostics["repair_turn_used"] is True
    assert len(service.calls) == 3
    repair_input = service.calls[2]["input"]
    assert any(
        "Grounding guard:" in item["content"][0]["text"]
        for item in repair_input
        if item.get("role") == "system"
    )


def test_openai_scenario2_runner_empty_fetch_fragments_refs_do_not_ground(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "warranty",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"refs": []}),
                    }
                ]
            },
            _output_text_response("ungrounded final response"),
            _output_text_response("still ungrounded final response"),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=4)
    legal_tool = EmptyFragmentsLegalCorpusTool()

    with pytest.raises(Scenario2RunnerError, match="not source-grounded") as exc:
        runner.run(
            packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
            config=_scenario2_config(prompt_path=str(prompt_path)),
            system_prompt_path=str(prompt_path),
            legal_corpus_tool=legal_tool,
        )

    partial = exc.value.to_run_result()
    assert legal_tool.fetch_fragments_calls == [{"refs": []}]
    assert partial.diagnostics["fragment_grounding_status"] == "empty_fragments"
    assert partial.diagnostics["citation_binding_status"] == "empty_fragments"
    assert partial.diagnostics["fetch_fragments_called"] is True
    assert partial.diagnostics["fetch_fragments_returned_usable_fragments"] is False
    assert partial.diagnostics["repair_turn_used"] is True
    assert [item["tool"] for item in partial.tool_trace] == [
        "search",
        "fetch_fragments",
    ]
    assert len(service.calls) == 4


def test_openai_scenario2_runner_empty_fragment_payload_does_not_ground(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "warranty",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"refs": [dict(_FRAGMENT_REF)]}),
                    }
                ]
            },
            _output_text_response("ungrounded final response"),
            _output_text_response("still ungrounded final response"),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=4)
    legal_tool = UnusableFragmentsLegalCorpusTool()

    with pytest.raises(Scenario2RunnerError, match="not source-grounded") as exc:
        runner.run(
            packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
            config=_scenario2_config(prompt_path=str(prompt_path)),
            system_prompt_path=str(prompt_path),
            legal_corpus_tool=legal_tool,
        )

    partial = exc.value.to_run_result()
    assert legal_tool.fetch_fragments_calls == [{"refs": [dict(_FRAGMENT_REF)]}]
    assert partial.diagnostics["fragment_grounding_status"] == "empty_fragments"
    assert partial.diagnostics["citation_binding_status"] == "empty_fragments"
    assert partial.diagnostics["fetch_fragments_called"] is True
    assert partial.diagnostics["fetch_fragments_returned_usable_fragments"] is False
    assert len(service.calls) == 4


def test_openai_scenario2_runner_succeeds_after_search_fetch_fragments_then_final(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "warranty",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"refs": [dict(_FRAGMENT_REF)]}),
                    }
                ]
            },
            _output_text_response("final response"),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)
    legal_tool = RecordingLegalCorpusTool()

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=legal_tool,
    )

    assert result.final_text == "final response"
    assert result.tool_round_count == 2
    assert result.response_mode == "plain_text"
    assert len(result.tool_trace) == 2
    assert result.tool_trace[0]["tool"] == "search"
    assert result.tool_trace[1]["tool"] == "fetch_fragments"
    assert result.tool_trace[1]["status"] == "ok"
    assert result.diagnostics["tool_round_count"] == 2
    assert result.diagnostics["model"] == "gpt-5.4"
    assert result.diagnostics["tool_usage_counts"] == {
        "search": 1,
        "fetch_fragments": 1,
        "expand_related": 0,
        "get_provenance": 0,
    }
    assert result.diagnostics["fetch_fragments_called"] is True
    assert result.diagnostics["fetch_fragments_returned_usable_fragments"] is True
    assert result.diagnostics["fragment_grounding_status"] == "fragments_fetched"
    assert result.diagnostics["citation_binding_status"] == "fragments_fetched"
    assert result.diagnostics["successful_fetch_fragments"] is True
    assert result.diagnostics["repair_turn_used"] is False
    assert result.diagnostics["fetched_fragment_ledger"] == [
        {
            "ref": dict(_FRAGMENT_REF),
            "doc_uid": "doc-1",
            "source_hash": "sha256:doc-1",
            "display_citation": "Doc 1 fragment",
            "text_excerpt": "Exact supporting fragment.",
            "locator": {"start_char": 0, "end_char": 32},
            "locator_precision": "char_offsets_only",
            "page_truth_status": "not_available_local",
            "quote_checksum": "sha256:fragment",
        }
    ]
    assert result.diagnostics["fetched_fragment_refs"] == [dict(_FRAGMENT_REF)]
    assert result.diagnostics["fetched_fragment_doc_uids"] == ["doc-1"]
    assert result.diagnostics["fetched_fragment_source_hashes"] == ["sha256:doc-1"]
    assert result.diagnostics["fetched_fragment_citations"] == ["Doc 1 fragment"]
    assert result.diagnostics["fetched_fragment_quote_checksums"] == ["sha256:fragment"]
    assert result.diagnostics["verifier_status"] == "passed"
    assert result.diagnostics["missing_sections"] == []
    assert result.diagnostics["sources_section_present"] is None
    assert result.diagnostics["fetched_sources_referenced"] is False
    assert result.diagnostics["citation_format_status"] == "not_applicable"
    assert result.diagnostics["legal_citation_count"] == 0
    assert result.diagnostics["user_doc_citation_count"] == 0
    assert result.diagnostics["citations_in_analysis_sections"] is None
    assert legal_tool.search_calls == [
        {
            "query": "warranty",
            "scope": "mixed",
            "return_level": "fragment",
        }
    ]
    assert legal_tool.fetch_fragments_calls == [{"refs": [dict(_FRAGMENT_REF)]}]


def test_openai_scenario2_runner_normalizes_fetch_fragments_references_alias(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "warranty",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"references": [dict(_FRAGMENT_REF)]}),
                    }
                ]
            },
            _output_text_response("final response"),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)
    legal_tool = RecordingLegalCorpusTool()

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=legal_tool,
    )

    assert result.final_text == "final response"
    assert legal_tool.fetch_fragments_calls == [{"refs": [dict(_FRAGMENT_REF)]}]
    assert result.tool_trace[1]["tool"] == "fetch_fragments"
    assert result.tool_trace[1]["request_args"] == {"refs": [dict(_FRAGMENT_REF)]}
    assert result.tool_trace[1]["request_args_raw"] == {
        "references": [dict(_FRAGMENT_REF)]
    }
    assert result.tool_trace[1]["request_aliases_applied"] == {"references": "refs"}


def test_openai_scenario2_runner_normalizes_fetch_fragments_machine_refs_alias(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "warranty",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps(
                            {"machine_refs": [dict(_FRAGMENT_REF)]}
                        ),
                    }
                ]
            },
            _output_text_response("final response"),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)
    legal_tool = RecordingLegalCorpusTool()

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=legal_tool,
    )

    assert result.final_text == "final response"
    assert legal_tool.fetch_fragments_calls == [{"refs": [dict(_FRAGMENT_REF)]}]
    assert result.tool_trace[1]["request_args"] == {"refs": [dict(_FRAGMENT_REF)]}
    assert result.tool_trace[1]["request_args_raw"] == {
        "machine_refs": [dict(_FRAGMENT_REF)]
    }
    assert result.tool_trace[1]["request_aliases_applied"] == {"machine_refs": "refs"}


def test_openai_scenario2_runner_normalizes_fetch_fragments_machine_ref_alias(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "warranty",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"machine_ref": dict(_FRAGMENT_REF)}),
                    }
                ]
            },
            _output_text_response("final response"),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)
    legal_tool = RecordingLegalCorpusTool()

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=legal_tool,
    )

    assert result.final_text == "final response"
    assert legal_tool.fetch_fragments_calls == [{"refs": [dict(_FRAGMENT_REF)]}]
    assert result.tool_trace[1]["request_args"] == {"refs": [dict(_FRAGMENT_REF)]}
    assert result.tool_trace[1]["request_args_raw"] == {
        "machine_ref": dict(_FRAGMENT_REF)
    }
    assert result.tool_trace[1]["request_aliases_applied"] == {"machine_ref": "refs"}


def test_openai_scenario2_runner_empty_fetch_fragments_request_still_fails(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "warranty",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({}),
                    }
                ]
            },
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)

    with pytest.raises(
        Scenario2RunnerError,
        match="Tool request missing required fields for fetch_fragments: refs",
    ) as exc:
        runner.run(
            packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
            config=_scenario2_config(prompt_path=str(prompt_path)),
            system_prompt_path=str(prompt_path),
            legal_corpus_tool=RecordingLegalCorpusTool(),
        )

    partial = exc.value.to_run_result()
    assert partial.tool_trace[-1]["tool"] == "fetch_fragments"
    assert partial.tool_trace[-1]["status"] == "failed"
    assert "request_aliases_applied" not in partial.tool_trace[-1]


def test_openai_scenario2_runner_second_round_uses_valid_function_call_output_payload(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "id": "resp_search_1",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_item_search_1",
                        "call_id": "fc_call_search_1",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "warranty",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ],
            },
            {
                "id": "resp_fetch_1",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_item_fetch_1",
                        "call_id": "fc_call_fetch_1",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"refs": [dict(_FRAGMENT_REF)]}),
                    }
                ],
            },
            _output_text_response("final response"),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=RecordingLegalCorpusTool(),
    )

    assert result.final_text == "final response"
    assert len(service.calls) == 3
    second_round_input = service.calls[1]["input"]
    assert service.calls[1]["previous_response_id"] == "resp_search_1"
    assert second_round_input == [
        {
            "type": "function_call_output",
            "call_id": "fc_call_search_1",
            "output": json.dumps(
                {"results": [{"machine_ref": dict(_FRAGMENT_REF)}]},
                ensure_ascii=False,
            ),
        }
    ]
    third_round_input = service.calls[2]["input"]
    assert service.calls[2]["previous_response_id"] == "resp_fetch_1"
    assert third_round_input == [
        {
            "type": "function_call_output",
            "call_id": "fc_call_fetch_1",
            "output": json.dumps(
                {
                    "fragments": [
                        {
                            "machine_ref": dict(_FRAGMENT_REF),
                            "doc_uid": "doc-1",
                            "source_hash": "sha256:doc-1",
                            "display_citation": "Doc 1 fragment",
                            "text": "Exact supporting fragment.",
                            "locator": {"start_char": 0, "end_char": 32},
                            "locator_precision": "char_offsets_only",
                            "page_truth_status": "not_available_local",
                            "quote_checksum": "sha256:fragment",
                        }
                    ]
                },
                ensure_ascii=False,
            ),
        }
    ]
    assert all("tool_name" not in item for item in second_round_input)


def test_openai_scenario2_runner_uses_sdk_response_id_for_live_threading(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            FakeSDKResponse(
                response_id="resp_sdk_search_1",
                output=[
                    {
                        "type": "function_call",
                        "id": "fc_item_search_sdk",
                        "call_id": "fc_call_search_sdk",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "warranty",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ],
            ),
            FakeSDKResponse(
                response_id="resp_sdk_fetch_1",
                output=[
                    {
                        "type": "function_call",
                        "id": "fc_item_fetch_sdk",
                        "call_id": "fc_call_fetch_sdk",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"refs": [dict(_FRAGMENT_REF)]}),
                    }
                ],
            ),
            FakeSDKResponse(
                response_id="resp_sdk_final_1",
                output=[
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "final response"}],
                    }
                ],
            ),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=RecordingLegalCorpusTool(),
    )

    assert result.final_text == "final response"
    assert service.calls[1]["previous_response_id"] == "resp_sdk_search_1"
    assert service.calls[1]["input"] == [
        {
            "type": "function_call_output",
            "call_id": "fc_call_search_sdk",
            "output": json.dumps(
                {"results": [{"machine_ref": dict(_FRAGMENT_REF)}]},
                ensure_ascii=False,
            ),
        }
    ]
    assert service.calls[2]["previous_response_id"] == "resp_sdk_fetch_1"
    threading_trace = result.diagnostics["openai_threading_trace"]
    assert threading_trace[0]["response_id"] == "resp_sdk_search_1"
    assert threading_trace[0]["parsed_tool_calls"] == [
        {
            "name": "search",
            "id": "fc_item_search_sdk",
            "call_id": "fc_call_search_sdk",
        }
    ]
    assert threading_trace[1]["previous_response_id"] == "resp_sdk_search_1"
    assert threading_trace[1]["input_items"] == [
        {
            "type": "function_call_output",
            "call_id": "fc_call_search_sdk",
            "output_size_bytes": len(
                json.dumps(
                    {"results": [{"machine_ref": dict(_FRAGMENT_REF)}]},
                    ensure_ascii=False,
                ).encode("utf-8")
            ),
            "output_sha256": threading_trace[1]["input_items"][0]["output_sha256"],
        }
    ]
    assert result.tool_trace[0]["openai_call_id"] == "fc_call_search_sdk"
    assert result.tool_trace[0]["openai_source_response_id"] == "resp_sdk_search_1"
    assert result.tool_trace[1]["openai_call_id"] == "fc_call_fetch_sdk"
    assert result.tool_trace[1]["openai_previous_response_id"] == "resp_sdk_fetch_1"


def test_openai_scenario2_runner_uses_one_shot_repair_then_accepts_grounded_final(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja damage",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            _output_text_response("premature final answer"),
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"refs": [dict(_FRAGMENT_REF)]}),
                    }
                ]
            },
            _output_text_response("grounded final answer"),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)
    legal_tool = RecordingLegalCorpusTool()

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=legal_tool,
    )

    assert result.final_text == "grounded final answer"
    assert result.diagnostics["fetch_fragments_called"] is True
    assert result.diagnostics["fetch_fragments_returned_usable_fragments"] is True
    assert result.diagnostics["fragment_grounding_status"] == "fragments_fetched"
    assert result.diagnostics["citation_binding_status"] == "fragments_fetched"
    assert result.diagnostics["successful_fetch_fragments"] is True
    assert result.diagnostics["repair_turn_used"] is True
    assert result.diagnostics["fetched_fragment_doc_uids"] == ["doc-1"]
    assert result.diagnostics["fetched_fragment_source_hashes"] == ["sha256:doc-1"]
    assert result.diagnostics["fetched_fragment_citations"] == ["Doc 1 fragment"]
    assert result.diagnostics["fetched_fragment_quote_checksums"] == ["sha256:fragment"]
    assert "fragment_grounding_repair_requested" in result.steps
    repair_input = service.calls[2]["input"]
    assert any(
        "Grounding guard:" in item["content"][0]["text"]
        for item in repair_input
        if item.get("role") == "system"
    )


def test_openai_scenario2_runner_verifier_passes_for_structured_answer_with_sources(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"refs": [dict(_FRAGMENT_REF)]}),
                    }
                ]
            },
            _output_text_response(
                _structured_scenario2_answer(
                    include_sources_section=True,
                    include_fetched_source_reference=True,
                )
            ),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=RecordingLegalCorpusTool(),
    )

    assert result.diagnostics["verifier_status"] == "passed"
    assert result.diagnostics["missing_sections"] == []
    assert result.diagnostics["sources_section_present"] is None
    assert result.diagnostics["fetched_sources_referenced"] is True
    assert result.diagnostics["verifier_warnings"] == []
    assert result.diagnostics["citation_format_status"] == "not_applicable"
    assert result.diagnostics["legal_citation_count"] == 4
    assert result.diagnostics["user_doc_citation_count"] == 1
    assert result.diagnostics["citations_in_analysis_sections"] is None
    assert result.diagnostics["malformed_citation_warnings"] == []


def test_openai_scenario2_runner_verifier_warns_when_sources_section_missing(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"refs": [dict(_FRAGMENT_REF)]}),
                    }
                ]
            },
            _output_text_response(
                _structured_scenario2_answer(include_sources_section=False)
            ),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=RecordingLegalCorpusTool(),
    )

    assert result.diagnostics["verifier_status"] == "passed"
    assert result.diagnostics["missing_sections"] == []
    assert result.diagnostics["sources_section_present"] is None
    assert result.diagnostics["fetched_sources_referenced"] is False
    assert result.diagnostics["citation_format_status"] == "not_applicable"
    assert result.diagnostics["legal_citation_count"] == 4
    assert result.diagnostics["user_doc_citation_count"] == 1
    assert result.diagnostics["citations_in_analysis_sections"] is None
    assert result.diagnostics["verifier_warnings"] == []


def test_openai_scenario2_runner_verifier_warns_when_legal_citations_are_missing(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"refs": [dict(_FRAGMENT_REF)]}),
                    }
                ]
            },
            _output_text_response(
                _structured_scenario2_answer(
                    include_sources_section=True,
                    include_fetched_source_reference=False,
                    include_legal_citations_in_analysis=False,
                )
            ),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=RecordingLegalCorpusTool(),
    )

    assert result.diagnostics["verifier_status"] == "passed"
    assert result.diagnostics["citation_format_status"] == "not_applicable"
    assert result.diagnostics["sources_section_present"] is None
    assert result.diagnostics["fetched_sources_referenced"] is False
    assert result.diagnostics["verifier_warnings"] == []
    assert result.diagnostics["legal_citation_count"] == 0
    assert result.diagnostics["user_doc_citation_count"] == 1
    assert result.diagnostics["citations_in_analysis_sections"] is None


def test_openai_scenario2_runner_verifier_warns_when_inline_legal_citations_only_in_sources(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"refs": [dict(_FRAGMENT_REF)]}),
                    }
                ]
            },
            _output_text_response(
                _structured_scenario2_answer(
                    include_sources_section=True,
                    include_fetched_source_reference=True,
                    include_legal_citations_in_analysis=False,
                    include_legal_citations_only_in_sources=True,
                )
            ),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=RecordingLegalCorpusTool(),
    )

    assert result.diagnostics["verifier_status"] == "passed"
    assert result.diagnostics["citation_format_status"] == "not_applicable"
    assert result.diagnostics["sources_section_present"] is None
    assert result.diagnostics["fetched_sources_referenced"] is True
    assert result.diagnostics["legal_citation_count"] == 2
    assert result.diagnostics["user_doc_citation_count"] == 1
    assert result.diagnostics["citations_in_analysis_sections"] is None
    assert result.diagnostics["verifier_warnings"] == []


def test_openai_scenario2_runner_limits_fetched_fragment_excerpt_length(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent_prompt_V1.1.md"
    prompt_path.write_text("Prompt", encoding="utf-8")
    service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps({"refs": [dict(_FRAGMENT_REF)]}),
                    }
                ]
            },
            _output_text_response("grounded final response"),
        ]
    )
    runner = OpenAIScenario2Runner(responses_service=service, max_tool_rounds=3)
    legal_tool = LongExcerptLegalCorpusTool()

    result = runner.run(
        packed_documents="<BEGIN_DOCUMENTS>mock</END_DOCUMENTS>",
        config=_scenario2_config(prompt_path=str(prompt_path)),
        system_prompt_path=str(prompt_path),
        legal_corpus_tool=legal_tool,
    )

    excerpt = result.diagnostics["fetched_fragment_ledger"][0]["text_excerpt"]
    assert len(excerpt) < 600
    assert excerpt.endswith("...")
    assert result.diagnostics["fetched_fragment_quote_checksums"] == [
        "sha256:long-fragment"
    ]
