"""OpenAI Responses integration for the NormaDepo pipeline."""

from __future__ import annotations

import signal
import json
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic
from typing import Any, Iterator, Protocol, TypeVar

from openai import APIStatusError, APITimeoutError, OpenAI, RateLimitError
from pydantic import BaseModel

TextFormatT = TypeVar("TextFormatT", bound=BaseModel)


class LlmCallError(RuntimeError):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


@dataclass(frozen=True, slots=True)
class StructuredLlmRequest:
    stage: str
    system_prompt: str
    input_payload: dict[str, Any]
    output_schema: dict[str, Any]
    output_model: type[TextFormatT]
    metadata: dict[str, str]
    provider: str
    api: str
    model_id: str
    reasoning_effort: str
    text_verbosity: str
    truncation: str
    store: bool
    max_output_tokens: int
    prompt_pack_id: str
    prompt_pack_version: str
    prompt_profile: str
    prompt_hash: str
    request_hash: str


@dataclass(frozen=True, slots=True)
class StructuredLlmUsage:
    input_tokens: int | None
    output_tokens: int | None
    reasoning_tokens: int | None


@dataclass(frozen=True, slots=True)
class StructuredLlmResponse:
    response_id: str
    output_payload: dict[str, Any]
    raw_json: str
    status: str
    completed_at: datetime | None
    duration_ms: int
    usage: StructuredLlmUsage


class AnnotationLlmClient(Protocol):
    def run(self, request: StructuredLlmRequest) -> StructuredLlmResponse:
        """Execute a structured OpenAI Responses API call."""


class _ResponsesServiceProtocol(Protocol):
    def parse(self, **kwargs: Any) -> Any:
        """Execute a parsed Responses API call."""


class OpenAIResponsesAnnotationLlmClient:
    def __init__(
        self,
        *,
        responses_service: _ResponsesServiceProtocol | None = None,
        timeout_seconds: int = 120,
    ) -> None:
        self._responses_service = responses_service
        self._timeout_seconds = timeout_seconds
        self._openai_client: OpenAI | None = None

    def run(self, request: StructuredLlmRequest) -> StructuredLlmResponse:
        started = monotonic()
        request_kwargs: dict[str, Any] = {
            "model": request.model_id,
            "instructions": request.system_prompt,
            "input": _serialize_input_payload(request.input_payload),
            "text_format": request.output_model,
            "text": {"verbosity": request.text_verbosity},
            "max_output_tokens": request.max_output_tokens,
            "metadata": request.metadata,
            "store": request.store,
            "truncation": request.truncation,
        }
        reasoning = _build_reasoning_payload(request.reasoning_effort)
        if reasoning is not None:
            request_kwargs["reasoning"] = reasoning
        try:
            with _request_timeout_guard(self._timeout_seconds):
                response = self._service().parse(**request_kwargs)
        except RateLimitError as error:
            raise LlmCallError(code="llm_rate_limit", message=str(error)) from error
        except APITimeoutError as error:
            raise LlmCallError(code="llm_timeout", message=str(error)) from error
        except TimeoutError as error:
            raise LlmCallError(code="llm_timeout", message=str(error)) from error
        except APIStatusError as error:
            raise LlmCallError(
                code="llm_http_error",
                message=str(error),
                details=_build_api_status_error_details(error),
            ) from error
        except Exception as error:  # pragma: no cover - defensive mapping
            raise LlmCallError(code="llm_http_error", message=str(error)) from error

        if getattr(response, "error", None) is not None:
            raise LlmCallError(
                code="llm_http_error",
                message=str(getattr(response.error, "message", response.error)),
                details=_build_response_error_details(response),
            )
        if _has_refusal(response):
            raise LlmCallError(code="llm_refusal", message="Model returned a refusal.")
        if getattr(response, "status", None) == "incomplete":
            raise LlmCallError(
                code="llm_incomplete",
                message="Responses API returned an incomplete result.",
                details=_build_incomplete_error_details(response),
            )

        parsed_payload = getattr(response, "output_parsed", None)
        if parsed_payload is None:
            raise LlmCallError(
                code="llm_schema_validation_error",
                message="Structured output was not returned by the model.",
            )

        output_payload = parsed_payload.model_dump(mode="json")
        raw_json = json.dumps(output_payload, ensure_ascii=False, sort_keys=True)
        duration_ms = int((monotonic() - started) * 1000)
        return StructuredLlmResponse(
            response_id=str(getattr(response, "id", "")),
            output_payload=output_payload,
            raw_json=raw_json,
            status=str(getattr(response, "status", "completed")),
            completed_at=_coerce_datetime(getattr(response, "completed_at", None)),
            duration_ms=duration_ms,
            usage=_extract_usage(getattr(response, "usage", None)),
        )

    def _service(self) -> _ResponsesServiceProtocol:
        if self._responses_service is None:
            if self._openai_client is None:
                self._openai_client = OpenAI(timeout=self._timeout_seconds)
            self._responses_service = self._openai_client.responses
        return self._responses_service


def _serialize_input_payload(input_payload: dict[str, Any]) -> str:
    return json.dumps(
        input_payload,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )


def _build_reasoning_payload(reasoning_effort: str) -> dict[str, str] | None:
    if reasoning_effort == "auto":
        return None
    return {"effort": reasoning_effort}


def _build_incomplete_error_details(response: Any) -> dict[str, Any]:
    usage = _extract_usage(getattr(response, "usage", None))
    incomplete_details = getattr(response, "incomplete_details", None)
    return {
        "response_id": str(getattr(response, "id", "")),
        "status": str(getattr(response, "status", "")),
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "reasoning_tokens": usage.reasoning_tokens,
        },
        "incomplete_details": {
            "reason": getattr(incomplete_details, "reason", None),
        },
    }


def _build_api_status_error_details(error: APIStatusError) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status_code": getattr(error, "status_code", None),
    }
    response = getattr(error, "response", None)
    if response is not None:
        payload["response_id"] = getattr(response, "id", None)
    body = getattr(error, "body", None)
    if isinstance(body, dict):
        error_body = body.get("error")
        if isinstance(error_body, dict):
            payload["provider_error"] = {
                "type": error_body.get("type"),
                "code": error_body.get("code"),
                "message": error_body.get("message"),
            }
    return payload


def _build_response_error_details(response: Any) -> dict[str, Any]:
    error_payload = getattr(response, "error", None)
    if error_payload is None:
        return {}
    return {
        "response_id": str(getattr(response, "id", "")),
        "status": str(getattr(response, "status", "")),
        "provider_error": {
            "type": getattr(error_payload, "type", None),
            "code": getattr(error_payload, "code", None),
            "message": getattr(error_payload, "message", None),
        },
    }


def _extract_usage(usage: Any) -> StructuredLlmUsage:
    if usage is None:
        return StructuredLlmUsage(
            input_tokens=None,
            output_tokens=None,
            reasoning_tokens=None,
        )
    output_tokens_details = getattr(usage, "output_tokens_details", None)
    reasoning_tokens = None
    if output_tokens_details is not None:
        reasoning_tokens = getattr(output_tokens_details, "reasoning_tokens", None)
    return StructuredLlmUsage(
        input_tokens=getattr(usage, "input_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None),
        reasoning_tokens=reasoning_tokens,
    )


def _coerce_datetime(raw_value: Any) -> datetime | None:
    if raw_value is None:
        return None
    if isinstance(raw_value, datetime):
        return raw_value.astimezone(timezone.utc)
    if isinstance(raw_value, (int, float)):
        return datetime.fromtimestamp(raw_value, tz=timezone.utc)
    return None


def _has_refusal(response: Any) -> bool:
    for output in getattr(response, "output", []):
        if getattr(output, "type", None) != "message":
            continue
        for content in getattr(output, "content", []):
            if getattr(content, "type", None) == "refusal":
                return True
    return False


@contextmanager
def _request_timeout_guard(timeout_seconds: int) -> Iterator[None]:
    if (
        timeout_seconds <= 0
        or threading.current_thread() is not threading.main_thread()
        or not hasattr(signal, "SIGALRM")
    ):
        yield
        return

    def _raise_timeout(_signum: int, _frame: Any) -> None:
        raise TimeoutError(
            f"OpenAI Responses request exceeded {timeout_seconds} seconds."
        )

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, float(timeout_seconds))
    signal.signal(signal.SIGALRM, _raise_timeout)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer != (0.0, 0.0):
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)
