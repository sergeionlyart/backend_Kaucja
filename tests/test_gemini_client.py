from __future__ import annotations

from typing import Any
from unittest.mock import patch

from app.llm_client.gemini_client import GeminiLLMClient


class FakeGenerateService:
    def __init__(self, output_text: str = '{"answer": 1}') -> None:
        self.calls: list[dict[str, Any]] = []
        self.output_text = output_text

    def generate_content(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": self.output_text}],
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
    with patch("app.config.settings.get_settings") as mock_settings:
        mock_settings.return_value.providers_config = {
            "llm_providers": {
                "google": {
                    "models": {"gemini-3.1-pro-preview": {"supports_thinking": False}}
                }
            }
        }
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
    with patch("app.config.settings.get_settings") as mock_settings:
        mock_settings.return_value.providers_config = {
            "llm_providers": {
                "google": {
                    "models": {"gemini-2.0-flash-thinking": {"supports_thinking": True}}
                }
            }
        }
        payload = GeminiLLMClient.build_request_payload(
            system_prompt="sys",
            user_content="user",
            json_schema={"type": "object"},
            model="gemini-2.0-flash-thinking",
            params={"gemini_thinking_level": "high"},
        )
    assert payload["config"]["thinking_config"] == {"thinking_level": "high"}


def test_gemini_payload_builder_omits_thinking_config_for_unsupported_models() -> None:
    with patch("app.config.settings.get_settings") as mock_settings:
        mock_settings.return_value.providers_config = {
            "llm_providers": {
                "google": {"models": {"gemini-2.5-flash": {"supports_thinking": False}}}
            }
        }
        payload = GeminiLLMClient.build_request_payload(
            system_prompt="sys",
            user_content="user",
            json_schema={"type": "object"},
            model="gemini-2.5-flash",
            params={"gemini_thinking_level": "high"},
        )
    assert "thinking_config" not in payload["config"]


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


def test_gemini_generate_text_returns_plain_text_without_json_parsing() -> None:
    service = FakeGenerateService(output_text="Plain text legal brief")
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

    with patch("app.config.settings.get_settings") as mock_settings:
        mock_settings.return_value.providers_config = {
            "llm_providers": {
                "google": {
                    "models": {"gemini-3.1-pro-preview": {"supports_thinking": False}}
                }
            }
        }
        result = client.generate_text(
            system_prompt="sys",
            user_content="user",
            model="gemini-3.1-pro-preview",
            params={"gemini_thinking_level": "auto"},
            run_meta={},
        )

    assert result.raw_text == "Plain text legal brief"
    assert result.parsed_json is None
    assert len(service.calls) == 1
    assert "response_mime_type" not in service.calls[0]["config"]
