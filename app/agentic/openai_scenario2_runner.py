from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.agentic.legal_corpus_contract import LegalCorpusTool
from app.agentic.scenario2_runner import (
    Scenario2RunConfig,
    Scenario2RunResult,
    Scenario2RunnerError,
)
from app.agentic.scenario2_verifier import verify_scenario2_response
from app.llm_client.openai_client import OpenAIResponsesService


_KNOWN_TOOL_NAMES = {"search", "fetch_fragments", "expand_related", "get_provenance"}
_MAX_FETCHED_FRAGMENT_EXCERPT_CHARS = 280
_FRAGMENT_GROUNDING_REPAIR_MESSAGE = (
    "Grounding guard: you already used legal_corpus retrieval tools. "
    "Do not provide a final answer yet. Call fetch_fragments for the exact "
    "authorities or fragments you rely on, then continue with the final answer."
)

_TOOL_SCHEMA: dict[str, dict[str, Any]] = {
    "search": {
        "query": {"type": "string"},
        "query_language": {"type": "string"},
        "query_expansions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "scope": {"type": "string", "enum": ["acts", "case_law", "mixed"]},
        "return_level": {
            "type": "string",
            "enum": ["document", "fragment", "mixed"],
        },
        "as_of_date": {"type": "string"},
        "include_history": {"type": "boolean"},
        "expand_citations": {"type": "boolean"},
        "top_k": {"type": "integer"},
        "locator": {"type": "object"},
        "filters": {"type": "object"},
    },
    "fetch_fragments": {
        "refs": {"type": "array", "items": {"type": "object"}},
        "include_neighbors": {"type": "boolean"},
        "neighbor_window": {"type": "integer"},
        "max_chars_per_fragment": {"type": "integer"},
    },
    "expand_related": {
        "refs": {"type": "array", "items": {"type": "object"}},
        "relation_types": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "cites",
                    "cited_by",
                    "same_case",
                    "supersedes",
                    "related_provision",
                ],
            },
        },
        "top_k": {"type": "integer"},
    },
    "get_provenance": {
        "ref": {"type": "object"},
        "include_artifacts": {"type": "boolean"},
        "debug": {"type": "boolean"},
    },
}

_REQUIRED_TOOL_FIELDS = {
    "search": {"query", "scope", "return_level"},
    "fetch_fragments": {"refs"},
    "expand_related": {"refs", "relation_types"},
    "get_provenance": {"ref"},
}


@dataclass(frozen=True, slots=True)
class _FetchedFragmentLedgerEntry:
    ref: dict[str, Any]
    doc_uid: str | None
    source_hash: str | None
    display_citation: str | None
    text_excerpt: str | None
    locator: dict[str, Any] | None
    locator_precision: str | None
    page_truth_status: str | None
    quote_checksum: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ref": self.ref,
            "doc_uid": self.doc_uid,
            "source_hash": self.source_hash,
            "display_citation": self.display_citation,
            "text_excerpt": self.text_excerpt,
            "locator": self.locator,
            "locator_precision": self.locator_precision,
            "page_truth_status": self.page_truth_status,
            "quote_checksum": self.quote_checksum,
        }


@dataclass(slots=True)
class _ToolUsageState:
    search: int = 0
    fetch_fragments: int = 0
    expand_related: int = 0
    get_provenance: int = 0
    usable_fetch_fragments_count: int = 0
    repair_turn_used: bool = False
    fetched_fragment_ledger: list[_FetchedFragmentLedgerEntry] = field(
        default_factory=list
    )

    def register_attempt(self, tool_name: str) -> None:
        if tool_name == "search":
            self.search += 1
            return
        if tool_name == "fetch_fragments":
            self.fetch_fragments += 1
            return
        if tool_name == "expand_related":
            self.expand_related += 1
            return
        if tool_name == "get_provenance":
            self.get_provenance += 1
            return
        raise RuntimeError(f"Unsupported legal corpus tool: {tool_name}")

    def register_fetched_fragments(self, tool_output: dict[str, Any]) -> int:
        usable_entries = _extract_usable_fragment_entries(tool_output)
        if not usable_entries:
            return 0

        self.usable_fetch_fragments_count += 1
        for entry in usable_entries:
            if not any(
                existing.as_dict() == entry.as_dict()
                for existing in self.fetched_fragment_ledger
            ):
                self.fetched_fragment_ledger.append(entry)
        return len(usable_entries)

    @property
    def total_tool_calls(self) -> int:
        return (
            self.search
            + self.fetch_fragments
            + self.expand_related
            + self.get_provenance
        )

    @property
    def retrieval_used(self) -> bool:
        return self.total_tool_calls > 0

    @property
    def successful_fetch_fragments(self) -> bool:
        return self.usable_fetch_fragments_count > 0

    @property
    def fetch_fragments_called(self) -> bool:
        return self.fetch_fragments > 0

    @property
    def fetch_fragments_returned_usable_fragments(self) -> bool:
        return self.usable_fetch_fragments_count > 0

    def as_dict(self) -> dict[str, int]:
        return {
            "search": self.search,
            "fetch_fragments": self.fetch_fragments,
            "expand_related": self.expand_related,
            "get_provenance": self.get_provenance,
        }

    def fetched_fragment_refs(self) -> list[dict[str, Any]]:
        return [entry.ref for entry in self.fetched_fragment_ledger]

    def fetched_fragment_doc_uids(self) -> list[str]:
        return [
            entry.doc_uid
            for entry in self.fetched_fragment_ledger
            if entry.doc_uid is not None
        ]

    def fetched_fragment_source_hashes(self) -> list[str]:
        return [
            entry.source_hash
            for entry in self.fetched_fragment_ledger
            if entry.source_hash is not None
        ]

    def fetched_fragment_citations(self) -> list[str]:
        return [
            entry.display_citation
            for entry in self.fetched_fragment_ledger
            if entry.display_citation is not None
        ]

    def fetched_fragment_quote_checksums(self) -> list[str]:
        return [
            entry.quote_checksum
            for entry in self.fetched_fragment_ledger
            if entry.quote_checksum is not None
        ]

    def fetched_fragment_ledger_payload(self) -> list[dict[str, Any]]:
        return [entry.as_dict() for entry in self.fetched_fragment_ledger]


class OpenAIScenario2Runner:
    """OpenAI-based runner for Scenario 2 with bounded tool loop."""

    def __init__(
        self,
        *,
        responses_service: OpenAIResponsesService | None = None,
        max_tool_rounds: int = 60,
        search_budget_limit: int = 40,
    ) -> None:
        if max_tool_rounds < 1:
            raise ValueError("max_tool_rounds must be >= 1")
        if search_budget_limit < 1:
            raise ValueError("search_budget_limit must be >= 1")
        self._responses_service = responses_service
        self._max_tool_rounds = max_tool_rounds
        self._search_budget_limit = search_budget_limit

    def run(
        self,
        *,
        packed_documents: str,
        config: Scenario2RunConfig,
        system_prompt_path: str,
        legal_corpus_tool: LegalCorpusTool | None = None,
    ) -> Scenario2RunResult:
        system_prompt = self._load_system_prompt(system_prompt_path)
        steps: list[str] = ["scenario2_openai_start"]
        tool_trace: list[dict[str, Any]] = []
        service = self._resolve_service()
        tool_usage_state = _ToolUsageState()
        threading_trace: list[dict[str, Any]] = []

        conversation_input = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": system_prompt,
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": packed_documents,
                    }
                ],
            },
        ]
        pending_input = list(conversation_input)
        previous_response_id: str | None = None

        tool_round_count = 0

        while True:
            payload = self._build_request_payload(
                model=config.model,
                input_payload=pending_input,
                previous_response_id=previous_response_id,
            )
            request_debug = _build_request_debug_entry(
                request_index=len(threading_trace) + 1,
                payload=payload,
            )
            steps.append("openai_request")
            try:
                response = service.create(**payload)
                parsed = self._parse_response(response)
            except Scenario2RunnerError:
                raise
            except Exception as error:
                request_debug["error"] = str(error)
                threading_trace.append(request_debug)
                self._raise_runner_error(
                    message=str(error),
                    model=config.model,
                    system_prompt_path=system_prompt_path,
                    steps=steps,
                    tool_trace=tool_trace,
                    tool_round_count=tool_round_count,
                    tool_usage_state=tool_usage_state,
                    threading_trace=threading_trace,
                )
            parsed_response_id = _as_optional_str(parsed.get("response_id"))
            request_debug["response_id"] = parsed_response_id
            request_debug["parsed_tool_calls"] = _summarize_tool_calls(
                parsed["tool_calls"]
            )
            request_debug["final_text_present"] = bool(
                _as_optional_str(parsed.get("final_text"))
            )
            request_debug["response_raw_item_count"] = parsed.get(
                "response_raw_item_count"
            )
            threading_trace.append(request_debug)
            if parsed_response_id is not None:
                previous_response_id = parsed_response_id
            tool_calls = parsed["tool_calls"]

            if tool_calls:
                if tool_round_count + len(tool_calls) > self._max_tool_rounds:
                    self._raise_runner_error(
                        message=(
                            "OpenAI tool round limit exceeded for Scenario 2 "
                            f"(limit={self._max_tool_rounds})"
                        ),
                        model=config.model,
                        system_prompt_path=system_prompt_path,
                        steps=steps,
                        tool_trace=tool_trace,
                        tool_round_count=tool_round_count,
                        tool_usage_state=tool_usage_state,
                        parsed=parsed,
                        threading_trace=threading_trace,
                    )

                call_payloads = self._execute_tool_calls(
                    calls=tool_calls,
                    legal_corpus_tool=legal_corpus_tool,
                    tool_usage_state=tool_usage_state,
                    model=config.model,
                    system_prompt_path=system_prompt_path,
                    tool_round_count=tool_round_count,
                    base_steps=steps,
                    base_tool_trace=tool_trace,
                    parsed=parsed,
                    previous_response_id=previous_response_id,
                    threading_trace=threading_trace,
                )
                tool_trace.extend(call_payloads["tool_trace"])
                tool_round_count += len(tool_calls)
                steps.extend(call_payloads["steps"])
                if previous_response_id is None:
                    conversation_input.extend(call_payloads["messages"])
                    pending_input = list(conversation_input)
                else:
                    pending_input = call_payloads["messages"]
                continue

            final_text = parsed.get("final_text")
            if final_text is not None:
                if not final_text.strip():
                    self._raise_runner_error(
                        message="OpenAI returned empty final text",
                        model=config.model,
                        system_prompt_path=system_prompt_path,
                        steps=steps,
                        tool_trace=tool_trace,
                        tool_round_count=tool_round_count,
                        tool_usage_state=tool_usage_state,
                        parsed=parsed,
                        threading_trace=threading_trace,
                    )
                if _requires_fragment_grounding(tool_usage_state):
                    if not tool_usage_state.repair_turn_used:
                        tool_usage_state.repair_turn_used = True
                        steps.append("fragment_grounding_repair_requested")
                        repair_messages = self._build_grounding_repair_messages()
                        if previous_response_id is None:
                            conversation_input.extend(repair_messages)
                            pending_input = list(conversation_input)
                        else:
                            pending_input = repair_messages
                        continue
                    self._raise_runner_error(
                        message=(
                            "Scenario 2 final answer is not source-grounded: "
                            "retrieval tools were used without usable "
                            "fetch_fragments results"
                        ),
                        model=config.model,
                        system_prompt_path=system_prompt_path,
                        steps=steps,
                        tool_trace=tool_trace,
                        tool_round_count=tool_round_count,
                        tool_usage_state=tool_usage_state,
                        parsed=parsed,
                        final_text=final_text.strip(),
                        threading_trace=threading_trace,
                    )
                return Scenario2RunResult(
                    final_text=final_text.strip(),
                    response_mode="plain_text",
                    tool_trace=tool_trace,
                    steps=steps + ["openai_final_response"],
                    diagnostics=self._build_diagnostics(
                        final_text=final_text.strip(),
                        model=config.model,
                        system_prompt_path=system_prompt_path,
                        parsed=parsed,
                        tool_round_count=tool_round_count,
                        tool_usage_state=tool_usage_state,
                        threading_trace=threading_trace,
                    ),
                    model=config.model,
                    tool_round_count=tool_round_count,
                )

            if not tool_calls:
                self._raise_runner_error(
                    message="OpenAI returned no final text and no tool calls",
                    model=config.model,
                    system_prompt_path=system_prompt_path,
                    steps=steps,
                    tool_trace=tool_trace,
                    tool_round_count=tool_round_count,
                    tool_usage_state=tool_usage_state,
                    parsed=parsed,
                    threading_trace=threading_trace,
                )

    def _resolve_service(self) -> OpenAIResponsesService:
        if self._responses_service is None:
            raise RuntimeError(
                "OpenAI responses service must be injected for Scenario2 runner."
            )
        return self._responses_service

    def _load_system_prompt(self, system_prompt_path: str) -> str:
        prompt_path = Path(system_prompt_path)
        if not prompt_path.is_absolute():
            prompt_path = prompt_path.resolve()

        if not prompt_path.is_file():
            raise FileNotFoundError(f"System prompt source missing: {prompt_path}")

        return prompt_path.read_text(encoding="utf-8")

    def _build_request_payload(
        self,
        *,
        model: str,
        input_payload: list[dict[str, Any]],
        previous_response_id: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "model": model,
            "input": input_payload,
            "tools": _build_tool_schemas(),
            "tool_choice": "auto",
        }
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
        return payload

    def _build_diagnostics(
        self,
        *,
        final_text: str = "",
        model: str,
        system_prompt_path: str,
        parsed: dict[str, Any] | None,
        tool_round_count: int,
        tool_usage_state: _ToolUsageState,
        threading_trace: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        parsed_payload = parsed or {}
        verification = verify_scenario2_response(
            final_text=final_text,
            fetched_fragment_ledger=tool_usage_state.fetched_fragment_ledger_payload(),
            retrieval_used=tool_usage_state.retrieval_used,
        )
        return {
            "model": model,
            "prompt_source_path": str(Path(system_prompt_path)),
            "response_raw_item_count": parsed_payload.get("response_raw_item_count"),
            "tool_calls": parsed_payload.get("tool_call_count"),
            "tool_round_count": tool_round_count,
            "tool_round_limit": self._max_tool_rounds,
            "max_tool_rounds": self._max_tool_rounds,
            "search_budget_limit": self._search_budget_limit,
            "search_budget_used": tool_usage_state.search,
            "tool_usage_counts": tool_usage_state.as_dict(),
            "fetch_fragments_called": tool_usage_state.fetch_fragments_called,
            "fetch_fragments_returned_usable_fragments": (
                tool_usage_state.fetch_fragments_returned_usable_fragments
            ),
            "fragment_grounding_status": _fragment_grounding_status(
                tool_usage_state=tool_usage_state
            ),
            "successful_fetch_fragments": tool_usage_state.successful_fetch_fragments,
            "repair_turn_used": tool_usage_state.repair_turn_used,
            "fetched_fragment_ledger": tool_usage_state.fetched_fragment_ledger_payload(),
            "fetched_fragment_refs": tool_usage_state.fetched_fragment_refs(),
            "fetched_fragment_doc_uids": tool_usage_state.fetched_fragment_doc_uids(),
            "fetched_fragment_source_hashes": tool_usage_state.fetched_fragment_source_hashes(),
            "fetched_fragment_citations": tool_usage_state.fetched_fragment_citations(),
            "fetched_fragment_quote_checksums": (
                tool_usage_state.fetched_fragment_quote_checksums()
            ),
            "citation_binding_status": _citation_binding_status(
                tool_usage_state=tool_usage_state
            ),
            "verifier_status": verification.status,
            "missing_sections": list(verification.missing_sections),
            "sources_section_present": verification.sources_section_present,
            "fetched_sources_referenced": verification.fetched_sources_referenced,
            "verifier_warnings": list(verification.warnings),
            "citation_format_status": verification.citation_format_status,
            "legal_citation_count": verification.legal_citation_count,
            "user_doc_citation_count": verification.user_doc_citation_count,
            "citations_in_analysis_sections": (
                verification.citations_in_analysis_sections
            ),
            "malformed_citation_warnings": list(
                verification.malformed_citation_warnings
            ),
            "openai_threading_trace": list(threading_trace or []),
        }

    def _raise_runner_error(
        self,
        *,
        message: str,
        model: str,
        system_prompt_path: str,
        steps: list[str],
        tool_trace: list[dict[str, Any]],
        tool_round_count: int,
        tool_usage_state: _ToolUsageState,
        parsed: dict[str, Any] | None = None,
        final_text: str = "",
        threading_trace: list[dict[str, Any]] | None = None,
    ) -> None:
        raise Scenario2RunnerError(
            message,
            final_text=final_text,
            tool_trace=list(tool_trace),
            steps=list(steps),
            diagnostics=self._build_diagnostics(
                model=model,
                system_prompt_path=system_prompt_path,
                parsed=parsed,
                tool_round_count=tool_round_count,
                tool_usage_state=tool_usage_state,
                final_text=final_text,
                threading_trace=threading_trace,
            ),
            model=model,
            tool_round_count=tool_round_count,
        )

    def _build_grounding_repair_messages(self) -> list[dict[str, Any]]:
        return [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": _FRAGMENT_GROUNDING_REPAIR_MESSAGE,
                    }
                ],
            }
        ]

    def _parse_response(self, response: Any) -> dict[str, Any]:
        payload = _to_payload(response)
        output = payload.get("output", [])
        if not isinstance(output, list):
            raise RuntimeError("OpenAI response payload missing output list")

        final_text = None
        tool_calls: list[dict[str, Any]] = []
        for item in output:
            if not isinstance(item, dict):
                continue

            item_type = str(item.get("type") or "")
            if item_type in {"message", "assistant"}:
                text = _extract_output_text(item)
                if text:
                    final_text = text
                nested_calls = _extract_tool_calls_from_content(item.get("content"))
                for call in nested_calls:
                    tool_calls.append(call)
                continue

            if item_type in {"function_call", "tool_call"}:
                normalized = _normalize_tool_call(item)
                if normalized is not None:
                    tool_calls.append(normalized)
                continue

            content_calls = _extract_tool_calls_from_content(item.get("content"))
            for call in content_calls:
                tool_calls.append(call)

        return {
            "final_text": final_text,
            "tool_calls": tool_calls,
            "tool_call_count": len(tool_calls),
            "response_raw_item_count": len(output),
            "response_id": _response_id(payload=payload, response=response),
        }

    def _execute_tool_calls(
        self,
        *,
        calls: list[dict[str, Any]],
        legal_corpus_tool: LegalCorpusTool | None,
        tool_usage_state: _ToolUsageState,
        model: str,
        system_prompt_path: str,
        tool_round_count: int,
        base_steps: list[str],
        base_tool_trace: list[dict[str, Any]],
        parsed: dict[str, Any] | None,
        previous_response_id: str | None,
        threading_trace: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if legal_corpus_tool is None:
            self._raise_runner_error(
                message="Legal corpus tool adapter is not configured",
                model=model,
                system_prompt_path=system_prompt_path,
                steps=base_steps,
                tool_trace=base_tool_trace,
                tool_round_count=tool_round_count,
                tool_usage_state=tool_usage_state,
                parsed=parsed,
                threading_trace=threading_trace,
            )

        tool_trace: list[dict[str, Any]] = []
        history_messages: list[dict[str, Any]] = []
        steps: list[str] = []

        for call in calls:
            name = call.get("name")
            arguments = call.get("arguments")
            call_id = call.get("call_id") or call.get("id")
            if not isinstance(name, str):
                tool_trace.append(
                    _build_failed_tool_trace_entry(
                        tool_name="unknown",
                        request_args=arguments,
                        error_message="Tool call is missing a name",
                    )
                )
                steps.append("tool_error:unknown")
                self._raise_runner_error(
                    message="Tool call is missing a name",
                    model=model,
                    system_prompt_path=system_prompt_path,
                    steps=base_steps + steps,
                    tool_trace=base_tool_trace + tool_trace,
                    tool_round_count=tool_round_count + len(tool_trace),
                    tool_usage_state=tool_usage_state,
                    parsed=parsed,
                    threading_trace=threading_trace,
                )

            normalized_name = _normalize_tool_name(name)
            if normalized_name is None:
                tool_trace.append(
                    _build_failed_tool_trace_entry(
                        tool_name=name,
                        request_args=arguments,
                        error_message=f"Unknown legal corpus tool: {name}",
                    )
                )
                steps.append("tool_error:unknown")
                self._raise_runner_error(
                    message=f"Unknown legal corpus tool: {name}",
                    model=model,
                    system_prompt_path=system_prompt_path,
                    steps=base_steps + steps,
                    tool_trace=base_tool_trace + tool_trace,
                    tool_round_count=tool_round_count + len(tool_trace),
                    tool_usage_state=tool_usage_state,
                    parsed=parsed,
                    threading_trace=threading_trace,
                )

            if not isinstance(arguments, dict):
                tool_trace.append(
                    _build_failed_tool_trace_entry(
                        tool_name=normalized_name,
                        request_args=arguments,
                        error_message=f"Tool arguments must be an object: {name}",
                    )
                )
                steps.append(f"tool_error:{normalized_name}")
                self._raise_runner_error(
                    message=f"Tool arguments must be an object: {name}",
                    model=model,
                    system_prompt_path=system_prompt_path,
                    steps=base_steps + steps,
                    tool_trace=base_tool_trace + tool_trace,
                    tool_round_count=tool_round_count + len(tool_trace),
                    tool_usage_state=tool_usage_state,
                    parsed=parsed,
                    threading_trace=threading_trace,
                )
            normalized_arguments, request_aliases_applied = _normalize_tool_request(
                normalized_name, arguments
            )
            try:
                _validate_tool_request(normalized_name, normalized_arguments)
            except RuntimeError as error:
                tool_trace.append(
                    _build_failed_tool_trace_entry(
                        tool_name=normalized_name,
                        request_args=normalized_arguments,
                        error_message=str(error),
                        request_aliases_applied=request_aliases_applied,
                        request_args_raw=arguments,
                    )
                )
                steps.append(f"tool_error:{normalized_name}")
                self._raise_runner_error(
                    message=str(error),
                    model=model,
                    system_prompt_path=system_prompt_path,
                    steps=base_steps + steps,
                    tool_trace=base_tool_trace + tool_trace,
                    tool_round_count=tool_round_count + len(tool_trace),
                    tool_usage_state=tool_usage_state,
                    parsed=parsed,
                    threading_trace=threading_trace,
                )
            if normalized_name == "search":
                self._ensure_search_budget(
                    search_budget_used=tool_usage_state.search,
                    search_budget_limit=self._search_budget_limit,
                    model=model,
                    system_prompt_path=system_prompt_path,
                    base_steps=base_steps,
                    steps=steps,
                    base_tool_trace=base_tool_trace,
                    tool_trace=tool_trace,
                    tool_round_count=tool_round_count,
                    tool_usage_state=tool_usage_state,
                    parsed=parsed,
                    threading_trace=threading_trace,
                    normalized_arguments=normalized_arguments,
                    request_aliases_applied=request_aliases_applied,
                    request_args_raw=arguments,
                )
            tool_usage_state.register_attempt(normalized_name)

            try:
                tool_result = self._dispatch_tool(
                    tool=legal_corpus_tool,
                    tool_name=normalized_name,
                    request=normalized_arguments,
                )
            except Exception as error:
                message = str(error)
                steps.append(f"tool_error:{normalized_name}")
                tool_trace.append(
                    _build_failed_tool_trace_entry(
                        tool_name=normalized_name,
                        request_args=normalized_arguments,
                        error_message=message,
                        request_aliases_applied=request_aliases_applied,
                        request_args_raw=arguments,
                    )
                )
                self._raise_runner_error(
                    message=f"legal_corpus.{normalized_name} failed: {message}",
                    model=model,
                    system_prompt_path=system_prompt_path,
                    steps=base_steps + steps,
                    tool_trace=base_tool_trace + tool_trace,
                    tool_round_count=tool_round_count + len(tool_trace),
                    tool_usage_state=tool_usage_state,
                    parsed=parsed,
                    threading_trace=threading_trace,
                )

            normalized_output = _normalize_tool_output(tool_result)
            if normalized_name == "fetch_fragments":
                tool_usage_state.register_fetched_fragments(normalized_output)
            serialized = json.dumps(normalized_output, ensure_ascii=False)
            tool_trace.append(
                {
                    "tool": normalized_name,
                    "status": "ok",
                    "request_args": normalized_arguments,
                    "request_arg_count": len(normalized_arguments),
                    "request_aliases_applied": dict(request_aliases_applied),
                    "response_summary": _tool_result_summary(normalized_output),
                    "response_size_bytes": len(serialized.encode("utf-8")),
                    "audit": normalized_output.get("audit", {}),
                    "openai_call_id": _as_optional_str(call_id),
                    "openai_item_id": _as_optional_str(call.get("id")),
                    "openai_previous_response_id": _as_optional_str(
                        previous_response_id
                    ),
                    "openai_source_response_id": _as_optional_str(
                        parsed.get("response_id") if parsed else None
                    ),
                }
            )
            if normalized_arguments != arguments:
                tool_trace[-1]["request_args_raw"] = dict(arguments)
            steps.append(f"tool_call:{normalized_name}")
            history_messages.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": serialized,
                }
            )

        return {
            "tool_trace": tool_trace,
            "messages": history_messages,
            "steps": steps,
        }

    def _ensure_search_budget(
        self,
        *,
        search_budget_used: int,
        search_budget_limit: int,
        model: str,
        system_prompt_path: str,
        base_steps: list[str],
        steps: list[str],
        base_tool_trace: list[dict[str, Any]],
        tool_trace: list[dict[str, Any]],
        tool_round_count: int,
        tool_usage_state: _ToolUsageState,
        parsed: dict[str, Any] | None,
        threading_trace: list[dict[str, Any]],
        normalized_arguments: dict[str, Any],
        request_aliases_applied: dict[str, str],
        request_args_raw: dict[str, Any],
    ) -> None:
        if search_budget_used < search_budget_limit:
            return

        tool_trace.append(
            _build_failed_tool_trace_entry(
                tool_name="search",
                request_args=normalized_arguments,
                error_message=(
                    "OpenAI search budget exceeded for Scenario 2 "
                    f"(limit={search_budget_limit})"
                ),
                request_aliases_applied=request_aliases_applied,
                request_args_raw=request_args_raw,
            )
        )
        steps.append("tool_error:search")
        self._raise_runner_error(
            message=(
                "OpenAI search budget exceeded for Scenario 2 "
                f"(limit={search_budget_limit})"
            ),
            model=model,
            system_prompt_path=system_prompt_path,
            steps=base_steps + steps,
            tool_trace=base_tool_trace + tool_trace,
            tool_round_count=tool_round_count + len(tool_trace),
            tool_usage_state=tool_usage_state,
            parsed=parsed,
            threading_trace=threading_trace,
        )

    def _dispatch_tool(
        self,
        *,
        tool: LegalCorpusTool,
        tool_name: str,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        if tool_name == "search":
            return tool.search(request=request)
        if tool_name == "fetch_fragments":
            return tool.fetch_fragments(request=request)
        if tool_name == "expand_related":
            return tool.expand_related(request=request)
        if tool_name == "get_provenance":
            return tool.get_provenance(request=request)
        raise RuntimeError(f"Unsupported legal corpus tool: {tool_name}")


def _build_tool_schemas() -> list[dict[str, Any]]:
    tool_schemas: list[dict[str, Any]] = []
    for name in sorted(_KNOWN_TOOL_NAMES):
        schema = _TOOL_SCHEMA[name]
        required = sorted(_REQUIRED_TOOL_FIELDS[name])
        tool_schemas.append(
            {
                "type": "function",
                "name": name,
                "description": f"legal_corpus.{name}",
                "parameters": {
                    "type": "object",
                    "properties": schema,
                    "required": required,
                    "additionalProperties": True,
                },
            }
        )

    return tool_schemas


def _normalize_tool_name(name: str) -> str | None:
    if name in _KNOWN_TOOL_NAMES:
        return name
    if "." in name:
        tail = name.rsplit(".", 1)[-1]
        if tail in _KNOWN_TOOL_NAMES:
            return tail
    return None


def _validate_tool_request(tool_name: str, request: dict[str, Any]) -> None:
    required = _REQUIRED_TOOL_FIELDS.get(tool_name, set())
    missing = sorted(required - set(request))
    if missing:
        raise RuntimeError(
            f"Tool request missing required fields for {tool_name}: {', '.join(missing)}"
        )


def _normalize_tool_request(
    tool_name: str,
    request: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    normalized_request = dict(request)
    aliases_applied: dict[str, str] = {}

    if tool_name == "fetch_fragments":
        machine_ref = normalized_request.get("machine_ref")
        if "refs" not in normalized_request and machine_ref is not None:
            normalized_request.pop("machine_ref", None)
            normalized_request["refs"] = [machine_ref]
            aliases_applied["machine_ref"] = "refs"
        if "refs" not in normalized_request and "machine_refs" in normalized_request:
            normalized_request["refs"] = normalized_request.pop("machine_refs")
            aliases_applied["machine_refs"] = "refs"
        if "refs" not in normalized_request and "references" in normalized_request:
            normalized_request["refs"] = normalized_request.pop("references")
            aliases_applied["references"] = "refs"

    return normalized_request, aliases_applied


def _normalize_tool_output(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return response
    return {"result": response}


def _tool_result_summary(response: dict[str, Any]) -> str:
    if not response:
        return "empty"
    summary = str(response)
    return summary[:250]


def _build_failed_tool_trace_entry(
    *,
    tool_name: str,
    request_args: Any,
    error_message: str,
    request_aliases_applied: dict[str, str] | None = None,
    request_args_raw: Any | None = None,
) -> dict[str, Any]:
    entry = {
        "tool": tool_name,
        "status": "failed",
        "request_args": request_args,
        "error": error_message,
        "response_summary": "",
        "response_size_bytes": 0,
    }
    if request_aliases_applied:
        entry["request_aliases_applied"] = dict(request_aliases_applied)
    if request_args_raw is not None and request_args_raw != request_args:
        entry["request_args_raw"] = request_args_raw
    return entry


def _requires_fragment_grounding(tool_usage_state: _ToolUsageState) -> bool:
    return (
        tool_usage_state.retrieval_used
        and not tool_usage_state.successful_fetch_fragments
    )


def _fragment_grounding_status(*, tool_usage_state: _ToolUsageState) -> str:
    return _citation_binding_status(tool_usage_state=tool_usage_state)


def _citation_binding_status(*, tool_usage_state: _ToolUsageState) -> str:
    if not tool_usage_state.retrieval_used:
        return "not_applicable"
    if tool_usage_state.successful_fetch_fragments:
        return "fragments_fetched"
    if tool_usage_state.fetch_fragments_called:
        return "empty_fragments"
    return "missing_fragments"


def _extract_usable_fragment_entries(
    tool_output: dict[str, Any],
) -> list[_FetchedFragmentLedgerEntry]:
    fragments = tool_output.get("fragments")
    if not isinstance(fragments, list):
        return []

    usable_entries: list[_FetchedFragmentLedgerEntry] = []
    for fragment in fragments:
        if not isinstance(fragment, dict):
            continue
        entry = _FetchedFragmentLedgerEntry(
            ref=_extract_fragment_ref(fragment),
            doc_uid=_extract_fragment_doc_uid(fragment),
            source_hash=_extract_fragment_source_hash(fragment),
            display_citation=_extract_fragment_display_citation(fragment),
            text_excerpt=_extract_fragment_excerpt(fragment),
            locator=_extract_fragment_locator(fragment),
            locator_precision=_extract_fragment_locator_precision(fragment),
            page_truth_status=_extract_fragment_page_truth_status(fragment),
            quote_checksum=_extract_fragment_quote_checksum(fragment),
        )
        if _is_usable_fragment_entry(entry):
            usable_entries.append(entry)
    return usable_entries


def _is_usable_fragment_entry(entry: _FetchedFragmentLedgerEntry) -> bool:
    if entry.ref:
        return True
    if entry.doc_uid is not None:
        return True
    if entry.source_hash is not None:
        return True
    return False


def _extract_fragment_ref(fragment: dict[str, Any]) -> dict[str, Any]:
    machine_ref = fragment.get("machine_ref")
    if isinstance(machine_ref, dict):
        return machine_ref
    return {}


def _extract_fragment_doc_uid(fragment: dict[str, Any]) -> str | None:
    direct = _as_optional_str(fragment.get("doc_uid"))
    if direct is not None:
        return direct
    machine_ref = fragment.get("machine_ref")
    if isinstance(machine_ref, dict):
        return _as_optional_str(machine_ref.get("doc_uid"))
    return None


def _extract_fragment_source_hash(fragment: dict[str, Any]) -> str | None:
    direct = _as_optional_str(fragment.get("source_hash"))
    if direct is not None:
        return direct
    machine_ref = fragment.get("machine_ref")
    if isinstance(machine_ref, dict):
        return _as_optional_str(machine_ref.get("source_hash"))
    return None


def _extract_fragment_display_citation(fragment: dict[str, Any]) -> str | None:
    direct = _as_optional_str(fragment.get("display_citation"))
    if direct is not None:
        return direct
    citation = fragment.get("citation")
    if isinstance(citation, dict):
        nested = _as_optional_str(citation.get("display_citation"))
        if nested is not None:
            return nested
    return _as_optional_str(fragment.get("source_label"))


def _extract_fragment_excerpt(fragment: dict[str, Any]) -> str | None:
    direct = _as_optional_str(fragment.get("text_excerpt"))
    if direct is not None:
        return _truncate_excerpt(direct)

    text = _as_optional_str(fragment.get("text"))
    if text is not None:
        return _truncate_excerpt(text)
    return None


def _truncate_excerpt(value: str) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= _MAX_FETCHED_FRAGMENT_EXCERPT_CHARS:
        return normalized

    limit = _MAX_FETCHED_FRAGMENT_EXCERPT_CHARS - 3
    return normalized[:limit].rstrip() + "..."


def _extract_fragment_locator(fragment: dict[str, Any]) -> dict[str, Any] | None:
    locator = fragment.get("locator")
    if isinstance(locator, dict):
        return dict(locator)

    machine_ref = fragment.get("machine_ref")
    if isinstance(machine_ref, dict):
        nested_locator = machine_ref.get("locator")
        if isinstance(nested_locator, dict):
            return dict(nested_locator)
    return None


def _extract_fragment_locator_precision(fragment: dict[str, Any]) -> str | None:
    direct = _as_optional_str(fragment.get("locator_precision"))
    if direct is not None:
        return direct

    diagnostics = fragment.get("diagnostics")
    if isinstance(diagnostics, dict):
        nested = _as_optional_str(diagnostics.get("locator_precision"))
        if nested is not None:
            return nested
    return None


def _extract_fragment_page_truth_status(fragment: dict[str, Any]) -> str | None:
    direct = _as_optional_str(fragment.get("page_truth_status"))
    if direct is not None:
        return direct

    citation = fragment.get("citation")
    if isinstance(citation, dict):
        nested = _as_optional_str(citation.get("page_truth_status"))
        if nested is not None:
            return nested

    diagnostics = fragment.get("diagnostics")
    if isinstance(diagnostics, dict):
        nested = _as_optional_str(diagnostics.get("page_truth_status"))
        if nested is not None:
            return nested
    return None


def _extract_fragment_quote_checksum(fragment: dict[str, Any]) -> str | None:
    return _as_optional_str(fragment.get("quote_checksum"))


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _extract_output_text(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None

    content = value.get("content")
    if isinstance(content, list):
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                return text
            nested_text = item.get("input_text")
            if isinstance(nested_text, str) and nested_text.strip():
                return nested_text
            if isinstance(item.get("content"), list):
                nested = _extract_output_text(item)
                if nested:
                    return nested

    text = value.get("text")
    if isinstance(text, str) and text.strip():
        return text
    return None


def _extract_tool_calls_from_content(content: Any) -> list[dict[str, Any]]:
    if not isinstance(content, list):
        return []

    calls: list[dict[str, Any]] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type") or "")
        if item_type not in {"function_call", "tool_call"}:
            continue
        normalized = _normalize_tool_call(item)
        if normalized is not None:
            calls.append(normalized)
    return calls


def _normalize_tool_call(item: dict[str, Any]) -> dict[str, Any] | None:
    name = item.get("name")
    if not isinstance(name, str):
        return None

    arguments_raw = item.get("arguments", {})
    if isinstance(arguments_raw, str):
        try:
            arguments = json.loads(arguments_raw)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Invalid JSON arguments for tool call {name}: {error}"
            ) from error
    elif isinstance(arguments_raw, dict):
        arguments = arguments_raw
    else:
        raise RuntimeError(
            f"Unsupported tool arguments type for {name}: {type(arguments_raw)}"
        )

    return {
        "name": name,
        "arguments": arguments,
        "id": item.get("id"),
        "call_id": item.get("call_id"),
    }


def _to_payload(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return response

    payload = getattr(response, "model_dump", None)
    if callable(payload):
        as_dict = payload()
        if isinstance(as_dict, dict):
            return as_dict

    return {}


def _response_id(*, payload: dict[str, Any], response: Any) -> str | None:
    direct = _as_optional_str(payload.get("id"))
    if direct is not None:
        return direct
    return _as_optional_str(getattr(response, "id", None))


def _build_request_debug_entry(
    *,
    request_index: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "request_index": request_index,
        "previous_response_id": _as_optional_str(payload.get("previous_response_id")),
        "input_items": _sanitize_input_payload(payload.get("input")),
    }


def _sanitize_input_payload(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    sanitized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue

        item_type = _as_optional_str(item.get("type"))
        if item_type == "function_call_output":
            output_text = str(item.get("output") or "")
            sanitized.append(
                {
                    "type": "function_call_output",
                    "call_id": _as_optional_str(item.get("call_id")),
                    "output_size_bytes": len(output_text.encode("utf-8")),
                    "output_sha256": hashlib.sha256(
                        output_text.encode("utf-8")
                    ).hexdigest(),
                }
            )
            continue

        role = _as_optional_str(item.get("role"))
        content = item.get("content")
        content_types: list[str] = []
        content_text_chars = 0
        if isinstance(content, list):
            for content_item in content:
                if not isinstance(content_item, dict):
                    continue
                content_type = _as_optional_str(content_item.get("type"))
                if content_type is not None:
                    content_types.append(content_type)
                text_value = _as_optional_str(content_item.get("text"))
                if text_value is None:
                    text_value = _as_optional_str(content_item.get("input_text"))
                if text_value is not None:
                    content_text_chars += len(text_value)

        sanitized.append(
            {
                "role": role,
                "content_types": content_types,
                "content_text_chars": content_text_chars,
            }
        )

    return sanitized


def _summarize_tool_calls(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "name": _as_optional_str(call.get("name")),
            "id": _as_optional_str(call.get("id")),
            "call_id": _as_optional_str(call.get("call_id")),
        }
        for call in calls
    ]
