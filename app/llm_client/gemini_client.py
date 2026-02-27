from __future__ import annotations

import json
import time
from typing import Any, Protocol

from app.llm_client.base import LLMResult
from app.llm_client.cost import estimate_llm_cost
from app.llm_client.normalize_usage import normalize_gemini_usage


class GeminiGenerateService(Protocol):
    def generate_content(self, **kwargs: Any) -> Any: ...


class GeminiLLMClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        generate_service: GeminiGenerateService | None = None,
        pricing_config: dict[str, Any] | None = None,
    ) -> None:
        self._api_key = api_key
        self._generate_service = generate_service
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
        del run_meta
        service = self._resolve_service()
        payload = self.build_request_payload(
            system_prompt=system_prompt,
            user_content=user_content,
            json_schema=json_schema,
            model=model,
            params=params,
        )

        start_time = time.perf_counter()
        response = service.generate_content(**payload)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        response_payload = _to_dict(response)
        raw_text = _extract_gemini_output_text(
            response=response, payload=response_payload
        )
        parsed_json = json.loads(raw_text)

        usage_raw = _extract_usage(response=response, payload=response_payload)
        usage_normalized = normalize_gemini_usage(usage_raw)
        cost = estimate_llm_cost(
            pricing_config=self._pricing_config,
            provider="google",
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
    ) -> dict[str, Any]:
        config: dict[str, Any] = {
            "system_instruction": system_prompt,
            "response_mime_type": "application/json",
            "response_json_schema": json_schema,
        }

        thinking_level = str(
            params.get("gemini_thinking_level")
            or params.get("thinking_level")
            or "auto"
        )
        mapped_level = _map_thinking_level(thinking_level)
        if mapped_level is not None:
            config["thinking_config"] = {"thinking_level": mapped_level}

        temperature = params.get("temperature")
        if temperature is not None:
            config["temperature"] = temperature

        max_output_tokens = params.get("max_output_tokens")
        if max_output_tokens is not None:
            config["max_output_tokens"] = int(max_output_tokens)

        return {
            "model": model,
            "contents": [{"role": "user", "parts": [{"text": user_content}]}],
            "config": config,
        }

    def _resolve_service(self) -> GeminiGenerateService:
        if self._generate_service is not None:
            return self._generate_service

        if self._api_key is None:
            raise ValueError("Google API key is required when service is not injected")

        try:
            from google import genai
        except ImportError as error:
            raise RuntimeError("google-genai package is not installed") from error

        # Keep a persistent client reference to prevent socket closures.
        # See Iteration 24 live_smoke bug.
        client = getattr(self, "_genai_client", None)
        if client is None:
            client = genai.Client(api_key=self._api_key)
            self._genai_client = client

        self._generate_service = client.models
        return self._generate_service


def _map_thinking_level(value: str) -> str | None:
    normalized = value.strip().lower()
    if normalized == "auto":
        return None
    if normalized not in {"low", "medium", "high"}:
        return None
    return normalized


def _extract_usage(*, response: Any, payload: dict[str, Any]) -> dict[str, Any]:
    usage = payload.get("usage_metadata")
    if isinstance(usage, dict):
        return usage

    usage_camel = payload.get("usageMetadata")
    if isinstance(usage_camel, dict):
        return usage_camel

    response_usage = getattr(response, "usage_metadata", None)
    if response_usage is not None:
        return _to_dict(response_usage)

    return {}


def _extract_gemini_output_text(*, response: Any, payload: dict[str, Any]) -> str:
    direct_text = getattr(response, "text", None)
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text

    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content")
            if not isinstance(content, dict):
                continue
            parts = content.get("parts")
            if not isinstance(parts, list):
                continue
            for part in parts:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    return text

    raise ValueError("Gemini response does not contain text output")


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, dict):
            return dumped

    return {}
