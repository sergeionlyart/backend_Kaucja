"""Thin OpenAI Batch transport helpers for annotate_original."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Protocol

from openai import OpenAI

from .llm import StructuredLlmRequest, StructuredLlmResponse, StructuredLlmUsage
from .schemas import AnalysisAnnotationOutput

_BATCH_ENDPOINT = "/v1/responses"
_BATCH_COMPLETION_WINDOW = "24h"


@dataclass(frozen=True, slots=True)
class BatchJobSnapshot:
    job_id: str
    status: str
    input_file_id: str | None
    output_file_id: str | None
    error_file_id: str | None
    submitted_at: datetime | None
    completed_at: datetime | None
    raw_payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class BatchResultItem:
    custom_id: str
    status: str
    response: StructuredLlmResponse | None
    error_payload: dict[str, Any] | None
    raw_payload: dict[str, Any]


class BatchClient(Protocol):
    def create_job(
        self,
        *,
        jsonl_items: list[dict[str, Any]],
        metadata: dict[str, str],
    ) -> BatchJobSnapshot:
        """Submit a batch job."""

    def retrieve_job(self, job_id: str) -> BatchJobSnapshot:
        """Return the latest provider-side batch state."""

    def download_results(self, *, output_file_id: str | None) -> list[BatchResultItem]:
        """Download and parse successful response lines."""

    def download_errors(self, *, error_file_id: str | None) -> list[BatchResultItem]:
        """Download and parse failed response lines."""


def build_batch_custom_id(*, doc_id: str, stage: str, request_hash: str) -> str:
    return f"{doc_id}::{stage}::{request_hash}"


def serialize_analysis_request_record(request: StructuredLlmRequest) -> dict[str, Any]:
    return {
        "stage": request.stage,
        "system_prompt": request.system_prompt,
        "input_payload": request.input_payload,
        "output_schema": request.output_schema,
        "metadata": request.metadata,
        "provider": request.provider,
        "api": request.api,
        "model_id": request.model_id,
        "reasoning_effort": request.reasoning_effort,
        "text_verbosity": request.text_verbosity,
        "truncation": request.truncation,
        "store": request.store,
        "max_output_tokens": request.max_output_tokens,
        "prompt_pack_id": request.prompt_pack_id,
        "prompt_pack_version": request.prompt_pack_version,
        "prompt_profile": request.prompt_profile,
        "prompt_hash": request.prompt_hash,
        "request_hash": request.request_hash,
    }


def deserialize_analysis_request_record(record: dict[str, Any]) -> StructuredLlmRequest:
    return StructuredLlmRequest(
        stage=str(record["stage"]),
        system_prompt=str(record["system_prompt"]),
        input_payload=dict(record["input_payload"]),
        output_schema=dict(record["output_schema"]),
        output_model=AnalysisAnnotationOutput,
        metadata={str(key): str(value) for key, value in dict(record["metadata"]).items()},
        provider=str(record["provider"]),
        api=str(record["api"]),
        model_id=str(record["model_id"]),
        reasoning_effort=str(record["reasoning_effort"]),
        text_verbosity=str(record["text_verbosity"]),
        truncation=str(record["truncation"]),
        store=bool(record["store"]),
        max_output_tokens=int(record["max_output_tokens"]),
        prompt_pack_id=str(record["prompt_pack_id"]),
        prompt_pack_version=str(record["prompt_pack_version"]),
        prompt_profile=str(record["prompt_profile"]),
        prompt_hash=str(record["prompt_hash"]),
        request_hash=str(record["request_hash"]),
    )


def build_batch_jsonl_item(request: StructuredLlmRequest) -> dict[str, Any]:
    custom_id = build_batch_custom_id(
        doc_id=str(request.metadata["doc_id"]),
        stage=request.stage,
        request_hash=request.request_hash,
    )
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": _BATCH_ENDPOINT,
        "body": _build_responses_request_body(request),
    }


def parse_batch_output_line(line: str) -> BatchResultItem:
    payload = json.loads(line)
    custom_id = str(payload["custom_id"])
    response_payload = payload.get("response")
    error_payload = payload.get("error")
    if not isinstance(response_payload, dict):
        return BatchResultItem(
            custom_id=custom_id,
            status="failed",
            response=None,
            error_payload=error_payload if isinstance(error_payload, dict) else payload,
            raw_payload=payload,
        )
    body = response_payload.get("body")
    if not isinstance(body, dict):
        return BatchResultItem(
            custom_id=custom_id,
            status="failed",
            response=None,
            error_payload={"message": "Batch response body is missing.", "payload": payload},
            raw_payload=payload,
        )
    try:
        output_payload = _extract_structured_output_payload(body)
        response = StructuredLlmResponse(
            response_id=str(body.get("id", "")),
            output_payload=output_payload,
            raw_json=json.dumps(output_payload, ensure_ascii=False, sort_keys=True),
            status=str(body.get("status", "completed")),
            completed_at=_coerce_datetime(body.get("completed_at")),
            duration_ms=0,
            usage=_extract_usage_from_response_body(body),
        )
        return BatchResultItem(
            custom_id=custom_id,
            status="completed",
            response=response,
            error_payload=None,
            raw_payload=payload,
        )
    except Exception as error:
        return BatchResultItem(
            custom_id=custom_id,
            status="failed",
            response=None,
            error_payload={
                "code": "batch_output_parse_error",
                "message": str(error),
            },
            raw_payload=payload,
        )


class OpenAIResponsesBatchClient:
    def __init__(
        self,
        *,
        client: OpenAI | None = None,
        timeout_seconds: int = 600,
    ) -> None:
        self._client = client or OpenAI(timeout=timeout_seconds)

    def create_job(
        self,
        *,
        jsonl_items: list[dict[str, Any]],
        metadata: dict[str, str],
    ) -> BatchJobSnapshot:
        if not jsonl_items:
            raise ValueError("jsonl_items must not be empty.")
        payload = "\n".join(
            json.dumps(item, ensure_ascii=False, separators=(",", ":"))
            for item in jsonl_items
        )
        with NamedTemporaryFile("w+b", suffix=".jsonl") as handle:
            handle.write(payload.encode("utf-8"))
            handle.flush()
            handle.seek(0)
            input_file = self._client.files.create(file=Path(handle.name), purpose="batch")
        batch = self._client.batches.create(
            input_file_id=str(getattr(input_file, "id", "")),
            endpoint=_BATCH_ENDPOINT,
            completion_window=_BATCH_COMPLETION_WINDOW,
            metadata=metadata,
        )
        return _coerce_batch_job_snapshot(batch)

    def retrieve_job(self, job_id: str) -> BatchJobSnapshot:
        batch = self._client.batches.retrieve(job_id)
        return _coerce_batch_job_snapshot(batch)

    def download_results(self, *, output_file_id: str | None) -> list[BatchResultItem]:
        if not output_file_id:
            return []
        content = _read_file_content(self._client, output_file_id)
        return [
            parse_batch_output_line(line)
            for line in content.splitlines()
            if line.strip()
        ]

    def download_errors(self, *, error_file_id: str | None) -> list[BatchResultItem]:
        if not error_file_id:
            return []
        content = _read_file_content(self._client, error_file_id)
        return [
            parse_batch_output_line(line)
            for line in content.splitlines()
            if line.strip()
        ]


def _build_responses_request_body(request: StructuredLlmRequest) -> dict[str, Any]:
    return {
        "model": request.model_id,
        "instructions": request.system_prompt,
        "input": json.dumps(
            request.input_payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
        "text": {
            "verbosity": request.text_verbosity,
            "format": {
                "type": "json_schema",
                "name": request.stage,
                "strict": True,
                "schema": request.output_schema,
            },
        },
        "reasoning": {"effort": request.reasoning_effort},
        "max_output_tokens": request.max_output_tokens,
        "metadata": request.metadata,
        "store": request.store,
        "truncation": request.truncation,
    }


def _extract_structured_output_payload(body: dict[str, Any]) -> dict[str, Any]:
    output_parsed = body.get("output_parsed")
    if isinstance(output_parsed, dict):
        return output_parsed
    for output in body.get("output", []):
        if not isinstance(output, dict):
            continue
        for content in output.get("content", []):
            if not isinstance(content, dict):
                continue
            text_value = content.get("text")
            if isinstance(text_value, str) and text_value.strip():
                return json.loads(text_value)
    output_text = body.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return json.loads(output_text)
    raise ValueError("Structured JSON payload was not found in batch response body.")


def _extract_usage_from_response_body(body: dict[str, Any]) -> StructuredLlmUsage:
    usage = body.get("usage")
    if not isinstance(usage, dict):
        return StructuredLlmUsage(
            input_tokens=None,
            output_tokens=None,
            reasoning_tokens=None,
        )
    output_details = usage.get("output_tokens_details")
    reasoning_tokens = None
    if isinstance(output_details, dict):
        raw_reasoning = output_details.get("reasoning_tokens")
        if isinstance(raw_reasoning, int):
            reasoning_tokens = raw_reasoning
    return StructuredLlmUsage(
        input_tokens=usage.get("input_tokens")
        if isinstance(usage.get("input_tokens"), int)
        else None,
        output_tokens=usage.get("output_tokens")
        if isinstance(usage.get("output_tokens"), int)
        else None,
        reasoning_tokens=reasoning_tokens,
    )


def _coerce_batch_job_snapshot(batch: Any) -> BatchJobSnapshot:
    raw_payload = json.loads(batch.model_dump_json())
    return BatchJobSnapshot(
        job_id=str(getattr(batch, "id", "")),
        status=str(getattr(batch, "status", "")),
        input_file_id=_coerce_optional_str(getattr(batch, "input_file_id", None)),
        output_file_id=_coerce_optional_str(getattr(batch, "output_file_id", None)),
        error_file_id=_coerce_optional_str(getattr(batch, "error_file_id", None)),
        submitted_at=_coerce_datetime(getattr(batch, "in_progress_at", None))
        or _coerce_datetime(getattr(batch, "created_at", None)),
        completed_at=_coerce_datetime(getattr(batch, "completed_at", None)),
        raw_payload=raw_payload,
    )


def _coerce_datetime(raw_value: Any) -> datetime | None:
    if raw_value is None:
        return None
    if isinstance(raw_value, datetime):
        return raw_value.astimezone(timezone.utc)
    if isinstance(raw_value, (int, float)):
        return datetime.fromtimestamp(raw_value, tz=timezone.utc)
    return None


def _coerce_optional_str(raw_value: Any) -> str | None:
    if raw_value is None:
        return None
    value = str(raw_value)
    return value if value else None


def _read_file_content(client: OpenAI, file_id: str) -> str:
    content = client.files.content(file_id)
    text_value = getattr(content, "text", None)
    if isinstance(text_value, str):
        return text_value
    read_method = getattr(content, "read", None)
    if callable(read_method):
        raw_value = read_method()
        if isinstance(raw_value, bytes):
            return raw_value.decode("utf-8")
        if isinstance(raw_value, str):
            return raw_value
    if isinstance(content, bytes):
        return content.decode("utf-8")
    if isinstance(content, io.BytesIO):
        return content.getvalue().decode("utf-8")
    raise TypeError(f"Unsupported OpenAI file content payload for {file_id}.")
