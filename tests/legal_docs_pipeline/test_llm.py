from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any

import pytest

from legal_docs_pipeline.llm import (
    LlmCallError,
    OpenAIResponsesAnnotationLlmClient,
    StructuredLlmRequest,
)
from legal_docs_pipeline.schemas import AnalysisAnnotationOutput


class FakeUsage:
    def __init__(self) -> None:
        self.input_tokens = 100
        self.output_tokens = 200
        self.output_tokens_details = type(
            "Details",
            (),
            {"reasoning_tokens": 50},
        )()


class FakeParsedResponse:
    def __init__(self) -> None:
        self.id = "resp_123"
        self.status = "completed"
        self.completed_at = datetime(2026, 3, 16, 12, 0, 0, tzinfo=timezone.utc)
        self.output_parsed = AnalysisAnnotationOutput.model_validate(
            {
                "semantic": {
                    "document_type_code": "pl_statute",
                    "authority_level": "primary",
                    "relevance": "core",
                    "usually_supports": "depends",
                    "topic_codes": ["deposit_legal_basis"],
                    "use_for_tasks_codes": ["claim"],
                },
                "annotation_original": {
                    "language_code": "pl",
                    "document_type_label": "ustawa",
                    "summary": "Określa podstawę prawną kaucji.",
                    "practical_value": ["Pozwala ustalić punkt wyjścia dla roszczenia."],
                    "best_use_scenarios": ["Pozew o zwrot kaucji."],
                    "use_for_tasks_labels": ["pozew"],
                    "read_first": ["Art. 6."],
                    "limitations": ["Wymaga uzupełnienia orzecznictwem."],
                    "tags": ["kaucja", "ustawa"],
                },
            }
        )
        self.output: list[Any] = []
        self.error = None
        self.usage = FakeUsage()


class FakeResponsesService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def parse(self, **kwargs: Any) -> FakeParsedResponse:
        self.calls.append(kwargs)
        return FakeParsedResponse()


class FakeOpenAIClient:
    def __init__(self, timeout: int, service: FakeResponsesService) -> None:
        self.timeout = timeout
        self.responses = service


class SlowResponsesService:
    def parse(self, **kwargs: Any) -> FakeParsedResponse:
        time.sleep(2)
        return FakeParsedResponse()


def test_openai_responses_client_uses_spec_compatible_request() -> None:
    service = FakeResponsesService()
    client = OpenAIResponsesAnnotationLlmClient(responses_service=service)

    response = client.run(
        StructuredLlmRequest(
            stage="annotate_original",
            system_prompt="system prompt",
            input_payload={"doc_id": "doc.md"},
            output_schema={"type": "object"},
            output_model=AnalysisAnnotationOutput,
            metadata={
                "run_id": "run-1",
                "doc_id": "doc.md",
                "prompt_pack_version": "2026-03-16",
                "prompt_profile": "addon_normative",
            },
            provider="openai",
            api="responses",
            model_id="gpt-5.4",
            reasoning_effort="xhigh",
            text_verbosity="low",
            truncation="disabled",
            store=False,
            max_output_tokens=32000,
            prompt_pack_id="kaucja-prompt-pack",
            prompt_pack_version="2026-03-16",
            prompt_profile="addon_normative",
            prompt_hash="prompt-hash",
            request_hash="request-hash",
        )
    )

    assert response.response_id == "resp_123"
    assert response.usage.reasoning_tokens == 50
    assert response.output_payload["semantic"]["document_type_code"] == "pl_statute"

    call = service.calls[0]
    assert call["model"] == "gpt-5.4"
    assert call["reasoning"] == {"effort": "xhigh"}
    assert call["text"] == {"verbosity": "low"}
    assert call["store"] is False
    assert call["truncation"] == "disabled"
    assert "temperature" not in call
    assert "top_p" not in call
    assert "top_logprobs" not in call


def test_openai_responses_client_uses_configured_timeout(monkeypatch) -> None:
    service = FakeResponsesService()
    captured: dict[str, Any] = {}

    def fake_openai(*, timeout: int) -> FakeOpenAIClient:
        captured["timeout"] = timeout
        return FakeOpenAIClient(timeout=timeout, service=service)

    monkeypatch.setattr("legal_docs_pipeline.llm.OpenAI", fake_openai)
    client = OpenAIResponsesAnnotationLlmClient(timeout_seconds=77)

    client.run(
        StructuredLlmRequest(
            stage="annotate_original",
            system_prompt="system prompt",
            input_payload={"doc_id": "doc.md"},
            output_schema={"type": "object"},
            output_model=AnalysisAnnotationOutput,
            metadata={
                "run_id": "run-1",
                "doc_id": "doc.md",
                "prompt_pack_version": "2026-03-16",
                "prompt_profile": "addon_normative",
            },
            provider="openai",
            api="responses",
            model_id="gpt-5.4",
            reasoning_effort="xhigh",
            text_verbosity="low",
            truncation="disabled",
            store=False,
            max_output_tokens=32000,
            prompt_pack_id="kaucja-prompt-pack",
            prompt_pack_version="2026-03-16",
            prompt_profile="addon_normative",
            prompt_hash="prompt-hash",
            request_hash="request-hash",
        )
    )

    assert captured["timeout"] == 77
    assert service.calls


def test_openai_responses_client_interrupts_hanging_request() -> None:
    client = OpenAIResponsesAnnotationLlmClient(
        responses_service=SlowResponsesService(),
        timeout_seconds=1,
    )

    with pytest.raises(LlmCallError) as error:
        client.run(
            StructuredLlmRequest(
                stage="annotate_original",
                system_prompt="system prompt",
                input_payload={"doc_id": "doc.md"},
                output_schema={"type": "object"},
                output_model=AnalysisAnnotationOutput,
                metadata={
                    "run_id": "run-1",
                    "doc_id": "doc.md",
                    "prompt_pack_version": "2026-03-16",
                    "prompt_profile": "addon_normative",
                },
                provider="openai",
                api="responses",
                model_id="gpt-5.4",
                reasoning_effort="xhigh",
                text_verbosity="low",
                truncation="disabled",
                store=False,
                max_output_tokens=32000,
                prompt_pack_id="kaucja-prompt-pack",
                prompt_pack_version="2026-03-16",
                prompt_profile="addon_normative",
                prompt_hash="prompt-hash",
                request_hash="request-hash",
            )
        )

    assert error.value.code == "llm_timeout"
