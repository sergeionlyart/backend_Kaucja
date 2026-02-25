from __future__ import annotations

from typing import Any

from app.llm_client.gemini_client import GeminiLLMClient


class FakeGenerateService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate_content(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": '{"answer": 1}'}],
                    }
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 80,
                "candidatesTokenCount": 20,
                "totalTokenCount": 100,
                "thoughtsTokenCount": 5,
            },
        }


def test_gemini_payload_builder_enforces_json_schema_output() -> None:
    payload = GeminiLLMClient.build_request_payload(
        system_prompt="sys",
        user_content="user",
        json_schema={"type": "object"},
        model="gemini-3.1-pro-preview",
        params={"gemini_thinking_level": "auto"},
    )

    config = payload["config"]
    assert config["response_mime_type"] == "application/json"
    assert "response_json_schema" in config
    assert "thinking_config" not in config


def test_gemini_payload_builder_maps_thinking_level() -> None:
    payload = GeminiLLMClient.build_request_payload(
        system_prompt="sys",
        user_content="user",
        json_schema={"type": "object"},
        model="gemini-3.1-pro-preview",
        params={"gemini_thinking_level": "high"},
    )

    assert payload["config"]["thinking_config"] == {"thinking_level": "high"}


def test_gemini_generate_json_normalizes_usage_and_cost() -> None:
    service = FakeGenerateService()
    client = GeminiLLMClient(
        generate_service=service,
        pricing_config={
            "currency": "USD",
            "updated_at": "2026-02-25",
            "llm": {
                "google": {
                    "models": {
                        "gemini-3.1-pro-preview": {
                            "input": 2.0,
                            "output": 12.0,
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
        model="gemini-3.1-pro-preview",
        params={"gemini_thinking_level": "low"},
        run_meta={},
    )

    assert result.parsed_json == {"answer": 1}
    assert result.usage_normalized["prompt_tokens"] == 80
    assert result.usage_normalized["completion_tokens"] == 20
    assert result.usage_normalized["total_tokens"] == 100
    assert result.usage_normalized["thoughts_tokens"] == 5
    assert result.cost["llm_cost_usd"] > 0
    assert len(service.calls) == 1
