from __future__ import annotations

from app.llm_client.cost import estimate_llm_cost
from app.llm_client.normalize_usage import (
    normalize_gemini_usage,
    normalize_openai_usage,
)


def test_normalize_openai_usage() -> None:
    normalized = normalize_openai_usage(
        {
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        }
    )

    assert normalized == {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
        "thoughts_tokens": None,
    }


def test_normalize_gemini_usage() -> None:
    normalized = normalize_gemini_usage(
        {
            "promptTokenCount": 12,
            "candidatesTokenCount": 7,
            "totalTokenCount": 19,
            "thoughtsTokenCount": 3,
        }
    )

    assert normalized == {
        "prompt_tokens": 12,
        "completion_tokens": 7,
        "total_tokens": 19,
        "thoughts_tokens": 3,
    }


def test_estimate_llm_cost() -> None:
    cost = estimate_llm_cost(
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
        provider="openai",
        model="gpt-5.1",
        usage_normalized={
            "prompt_tokens": 1_000,
            "completion_tokens": 2_000,
            "total_tokens": 3_000,
            "thoughts_tokens": None,
        },
    )

    assert cost["currency"] == "USD"
    assert cost["llm_cost_usd"] == 0.02125
