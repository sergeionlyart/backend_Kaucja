from __future__ import annotations

import json
import time
from typing import Any, Protocol

from app.llm_client.base import LLMResult
from app.llm_client.cost import estimate_llm_cost
from app.llm_client.normalize_usage import normalize_openai_usage


class OpenAIResponsesService(Protocol):
    def create(self, **kwargs: Any) -> Any: ...


class OpenAILLMClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        responses_service: OpenAIResponsesService | None = None,
        pricing_config: dict[str, Any] | None = None,
    ) -> None:
        self._api_key = api_key
        self._responses_service = responses_service
        self._pricing_config = pricing_config or {}

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_content: str,
        json_schema: dict[str, Any],
        model: str,
        params: dict[str, Any],
        run_meta: dict[str, Any],
    ) -> LLMResult:
        service = self._resolve_service()
        payload = self.build_request_payload(
            system_prompt=system_prompt,
            user_content=user_content,
            json_schema=json_schema,
            model=model,
            params=params,
            run_meta=run_meta,
        )

        start_time = time.perf_counter()
        response = service.create(**payload)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        response_payload = _to_dict(response)
        raw_text = _extract_openai_output_text(
            response=response, payload=response_payload
        )
        parsed_json = json.loads(raw_text)

        usage_raw = _extract_usage(response=response, payload=response_payload)
        usage_normalized = normalize_openai_usage(usage_raw)
        cost = estimate_llm_cost(
            pricing_config=self._pricing_config,
            provider="openai",
            model=model,
            usage_normalized=usage_normalized,
        )

        return LLMResult(
            raw_text=raw_text,
            parsed_json=parsed_json,
            raw_response=response_payload,
            usage_raw=usage_raw,
            usage_normalized=usage_normalized,
            cost=cost,
            timings={"t_llm_total_ms": elapsed_ms},
        )

    @staticmethod
    def build_request_payload(
        *,
        system_prompt: str,
        user_content: str,
        json_schema: dict[str, Any],
        model: str,
        params: dict[str, Any],
        run_meta: dict[str, Any],
    ) -> dict[str, Any]:
        schema_name = str(run_meta.get("schema_name") or "kaucja_gap_analysis")
        payload: dict[str, Any] = {
            "model": model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_content}],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": json_schema,
                    "strict": True,
                }
            },
            "tools": [],
            "tool_choice": "none",
        }

        reasoning_effort = str(
            params.get("openai_reasoning_effort")
            or params.get("reasoning_effort")
            or "auto"
        )
        if reasoning_effort in {"low", "medium", "high"}:
            payload["reasoning"] = {"effort": reasoning_effort}

        temperature = params.get("temperature")
        if temperature is not None:
            payload["temperature"] = temperature

        max_output_tokens = params.get("max_output_tokens")
        if max_output_tokens is not None:
            payload["max_output_tokens"] = int(max_output_tokens)

        return payload

    def _resolve_service(self) -> OpenAIResponsesService:
        if self._responses_service is not None:
            return self._responses_service

        if self._api_key is None:
            raise ValueError("OpenAI API key is required when service is not injected")

        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError("openai package is not installed") from error

        client = OpenAI(api_key=self._api_key)
        self._responses_service = client.responses
        return self._responses_service


def _extract_usage(*, response: Any, payload: dict[str, Any]) -> dict[str, Any]:
    usage = payload.get("usage")
    if isinstance(usage, dict):
        return usage

    response_usage = getattr(response, "usage", None)
    if response_usage is None:
        return {}

    return _to_dict(response_usage)


def _extract_openai_output_text(*, response: Any, payload: dict[str, Any]) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    payload_text = payload.get("output_text")
    if isinstance(payload_text, str) and payload_text.strip():
        return payload_text

    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for content_item in content:
                if not isinstance(content_item, dict):
                    continue
                text = content_item.get("text")
                if isinstance(text, str) and text.strip():
                    return text

    raise ValueError("OpenAI response does not contain output text")


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, dict):
            return dumped

    return {}
