"""Cost and token estimation helpers for direct and batch dispatch paths."""

from __future__ import annotations

import json
import math
from typing import Any

from .llm import StructuredLlmRequest, StructuredLlmResponse


def estimate_request_input_tokens(request: StructuredLlmRequest) -> int:
    payload = {
        "system_prompt": request.system_prompt,
        "input_payload": request.input_payload,
        "output_schema": request.output_schema,
    }
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _estimate_tokens_for_text(serialized)


def estimate_request_output_tokens(request: StructuredLlmRequest) -> int:
    return request.max_output_tokens


def estimate_stage_cost(
    *,
    request: StructuredLlmRequest,
    response: StructuredLlmResponse | None = None,
    input_cost_per_1k_tokens_usd: float | None = None,
    output_cost_per_1k_tokens_usd: float | None = None,
) -> dict[str, Any]:
    input_tokens = (
        response.usage.input_tokens
        if response is not None and response.usage.input_tokens is not None
        else estimate_request_input_tokens(request)
    )
    output_tokens = (
        response.usage.output_tokens
        if response is not None and response.usage.output_tokens is not None
        else estimate_request_output_tokens(request)
    )
    payload: dict[str, Any] = {
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
    }
    if (
        input_cost_per_1k_tokens_usd is None
        or output_cost_per_1k_tokens_usd is None
    ):
        payload["estimated_cost_usd"] = None
        return payload
    payload["estimated_cost_usd"] = round(
        (input_tokens / 1000.0) * input_cost_per_1k_tokens_usd
        + (output_tokens / 1000.0) * output_cost_per_1k_tokens_usd,
        6,
    )
    return payload


def _estimate_tokens_for_text(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))
