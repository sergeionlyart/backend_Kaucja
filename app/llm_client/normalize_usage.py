from __future__ import annotations

from typing import Any


def normalize_openai_usage(usage: dict[str, Any] | None) -> dict[str, int | None]:
    usage_data = usage or {}

    prompt_tokens = _to_int(
        usage_data.get("prompt_tokens")
        or usage_data.get("input_tokens")
        or usage_data.get("inputTokens")
    )
    completion_tokens = _to_int(
        usage_data.get("completion_tokens")
        or usage_data.get("output_tokens")
        or usage_data.get("outputTokens")
    )
    total_tokens = _to_int(
        usage_data.get("total_tokens")
        or usage_data.get("totalTokens")
        or _sum_tokens(prompt_tokens, completion_tokens)
    )

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "thoughts_tokens": None,
    }


def normalize_gemini_usage(usage: dict[str, Any] | None) -> dict[str, int | None]:
    usage_data = usage or {}

    prompt_tokens = _to_int(
        usage_data.get("promptTokenCount") or usage_data.get("prompt_tokens")
    )
    completion_tokens = _to_int(
        usage_data.get("candidatesTokenCount") or usage_data.get("completion_tokens")
    )
    total_tokens = _to_int(
        usage_data.get("totalTokenCount")
        or usage_data.get("total_tokens")
        or _sum_tokens(prompt_tokens, completion_tokens)
    )
    thoughts_tokens = _to_int(
        usage_data.get("thoughtsTokenCount") or usage_data.get("thoughts_tokens")
    )

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "thoughts_tokens": thoughts_tokens,
    }


def _sum_tokens(prompt_tokens: int | None, completion_tokens: int | None) -> int | None:
    if prompt_tokens is None and completion_tokens is None:
        return None

    return int((prompt_tokens or 0) + (completion_tokens or 0))


def _to_int(value: Any) -> int | None:
    if value is None:
        return None

    return int(value)
