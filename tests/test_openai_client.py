from __future__ import annotations

from typing import Any

from app.llm_client.openai_client import OpenAILLMClient


class FakeResponsesService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "output": [
                {
                    "content": [
                        {"type": "output_text", "text": '{"result": "ok"}'},
                    ]
                }
            ],
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
            },
        }


def test_openai_payload_builder_auto_reasoning_omits_reasoning_field() -> None:
    payload = OpenAILLMClient.build_request_payload(
        system_prompt="sys",
        user_content="user",
        json_schema={"type": "object"},
        model="gpt-5.1",
        params={"openai_reasoning_effort": "auto"},
        run_meta={"schema_name": "schema-v1"},
    )

    assert payload["text"]["format"]["strict"] is True
    assert payload["tools"] == []
    assert payload["tool_choice"] == "none"
    assert "reasoning" not in payload


def test_openai_payload_builder_low_reasoning_includes_reasoning_field() -> None:
    payload = OpenAILLMClient.build_request_payload(
        system_prompt="sys",
        user_content="user",
        json_schema={"type": "object"},
        model="gpt-5.1",
        params={"openai_reasoning_effort": "low"},
        run_meta={"schema_name": "schema-v1"},
    )

    assert payload["reasoning"] == {"effort": "low"}


def test_openai_generate_json_normalizes_usage_and_cost() -> None:
    fake_service = FakeResponsesService()
    client = OpenAILLMClient(
        responses_service=fake_service,
        pricing_config={
            "currency": "USD",
            "updated_at": "2026-02-25",
            "llm": {
                "openai": {
                    "models": {
                        "gpt-5.1": {
                            "input": 1.25,
                            "output": 10.0,
                        }
                    }
                }
            },
        },
    )

    result = client.generate_json(
        system_prompt="sys",
        user_content="user",
        json_schema={"type": "object"},
        model="gpt-5.1",
        params={"openai_reasoning_effort": "auto"},
        run_meta={"schema_name": "schema-v1"},
    )

    assert result.parsed_json == {"result": "ok"}
    assert result.usage_normalized["prompt_tokens"] == 100
    assert result.usage_normalized["completion_tokens"] == 50
    assert result.usage_normalized["total_tokens"] == 150
    assert result.cost["llm_cost_usd"] > 0
    assert len(fake_service.calls) == 1
