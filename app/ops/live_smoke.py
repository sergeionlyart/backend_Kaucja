from __future__ import annotations

import argparse
import base64
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable
from typing import Literal

from app.config.settings import Settings, get_settings
from app.llm_client.gemini_client import GeminiLLMClient
from app.llm_client.openai_client import OpenAILLMClient
from app.ocr_client.mistral_ocr import MistralOCRClient
from app.ocr_client.types import OCROptions
from app.utils.error_taxonomy import (
    build_error_details,
    classify_llm_api_error,
    classify_ocr_error,
)

ProviderStatus = Literal["pass", "fail", "skipped"]

_SMOKE_RESPONSE_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "pong": {"type": "string"},
    },
    "required": ["pong"],
    "additionalProperties": False,
}
_SMOKE_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQ"
    "AAAAASUVORK5CYII="
)


@dataclass(frozen=True, slots=True)
class ProviderSmokeResult:
    name: str
    status: ProviderStatus
    latency_ms: float | None
    error_code: str | None
    error_message: str | None


ProviderProbe = Callable[[Settings], ProviderSmokeResult]


def run_live_smoke(
    *,
    strict: bool,
    settings: Settings | None = None,
    output_path: Path | str | None = None,
    provider_probes: list[ProviderProbe] | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> dict[str, object]:
    active_settings = settings or get_settings()
    probes = provider_probes or _default_provider_probes()
    time_provider = now_fn or _utc_now

    started_at = time_provider().isoformat()
    provider_results: list[ProviderSmokeResult] = []
    for probe in probes:
        provider_name = _probe_provider_name(probe)
        try:
            provider_results.append(probe(active_settings))
        except Exception as error:  # noqa: BLE001
            provider_results.append(
                ProviderSmokeResult(
                    name=provider_name,
                    status="fail",
                    latency_ms=None,
                    error_code="UNKNOWN_ERROR",
                    error_message=build_error_details(error),
                )
            )

    finished_at = time_provider().isoformat()
    report = _build_report(
        started_at=started_at,
        finished_at=finished_at,
        strict=strict,
        providers=provider_results,
    )

    if output_path is not None:
        report_path = Path(output_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(_json_report_text(report), encoding="utf-8")

    return report


def _build_report(
    *,
    started_at: str,
    finished_at: str,
    strict: bool,
    providers: list[ProviderSmokeResult],
) -> dict[str, object]:
    pass_count = sum(1 for provider in providers if provider.status == "pass")
    fail_count = sum(1 for provider in providers if provider.status == "fail")
    skipped_count = sum(1 for provider in providers if provider.status == "skipped")
    strict_skipped_violation = strict and skipped_count > 0

    overall_status = "pass"
    if fail_count > 0 or strict_skipped_violation:
        overall_status = "fail"

    return {
        "finished_at": finished_at,
        "overall_status": overall_status,
        "providers": [_provider_to_dict(provider) for provider in providers],
        "started_at": started_at,
        "strict_mode": strict,
        "summary": {
            "fail": fail_count,
            "pass": pass_count,
            "skipped": skipped_count,
            "strict_skipped_violation": strict_skipped_violation,
        },
    }


def _provider_to_dict(provider: ProviderSmokeResult) -> dict[str, object]:
    latency: float | None = None
    if provider.latency_ms is not None:
        latency = round(provider.latency_ms, 3)

    return {
        "error_code": provider.error_code,
        "error_message": provider.error_message,
        "latency_ms": latency,
        "name": provider.name,
        "status": provider.status,
    }


def _probe_openai(settings: Settings) -> ProviderSmokeResult:
    provider_name = "openai"
    start = time.perf_counter()

    if not settings.openai_api_key:
        return _skipped_result(
            name=provider_name,
            error_code="MISSING_API_KEY",
            error_message="OPENAI_API_KEY is not configured.",
        )

    try:
        model_name = _resolve_llm_model(
            settings=settings,
            provider_name=provider_name,
            fallback_model="gpt-5.1",
        )
        client = OpenAILLMClient(
            api_key=settings.openai_api_key,
            pricing_config=settings.pricing_config,
        )
        result = client.generate_json(
            system_prompt=(
                "You are smoke-test assistant. Return JSON object with pong string."
            ),
            user_content='Return {"pong":"ok"}.',
            json_schema=_SMOKE_RESPONSE_SCHEMA,
            model=model_name,
            params={"openai_reasoning_effort": "low", "max_output_tokens": 32},
            run_meta={"schema_name": "live_provider_smoke_openai"},
        )
        if not isinstance(result.parsed_json.get("pong"), str):
            raise ValueError("OpenAI structured output missing string field 'pong'.")
    except Exception as error:  # noqa: BLE001
        if _is_sdk_missing_error(error):
            return _skipped_result(
                name=provider_name,
                error_code="SDK_NOT_INSTALLED",
                error_message=str(error),
            )
        return _failed_result(
            name=provider_name,
            start_time=start,
            error_code=classify_llm_api_error(error),
            error_message=build_error_details(error),
        )

    return _passed_result(name=provider_name, start_time=start)


_probe_openai.provider_name = "openai"  # type: ignore[attr-defined]


def _probe_gemini(settings: Settings) -> ProviderSmokeResult:
    provider_name = "google"
    start = time.perf_counter()

    if not settings.google_api_key:
        return _skipped_result(
            name=provider_name,
            error_code="MISSING_API_KEY",
            error_message="GOOGLE_API_KEY is not configured.",
        )

    try:
        model_name = _resolve_llm_model(
            settings=settings,
            provider_name=provider_name,
            fallback_model="gemini-3.1-pro-preview",
        )
        client = GeminiLLMClient(
            api_key=settings.google_api_key,
            pricing_config=settings.pricing_config,
        )
        result = client.generate_json(
            system_prompt=(
                "You are smoke-test assistant. Return JSON object with pong string."
            ),
            user_content='Return {"pong":"ok"}.',
            json_schema=_SMOKE_RESPONSE_SCHEMA,
            model=model_name,
            params={"gemini_thinking_level": "low", "max_output_tokens": 32},
            run_meta={"schema_name": "live_provider_smoke_google"},
        )
        if not isinstance(result.parsed_json.get("pong"), str):
            raise ValueError("Gemini structured output missing string field 'pong'.")
    except Exception as error:  # noqa: BLE001
        if _is_sdk_missing_error(error):
            return _skipped_result(
                name=provider_name,
                error_code="SDK_NOT_INSTALLED",
                error_message=str(error),
            )
        return _failed_result(
            name=provider_name,
            start_time=start,
            error_code=classify_llm_api_error(error),
            error_message=build_error_details(error),
        )

    return _passed_result(name=provider_name, start_time=start)


_probe_gemini.provider_name = "google"  # type: ignore[attr-defined]


def _probe_mistral_ocr(settings: Settings) -> ProviderSmokeResult:
    provider_name = "mistral_ocr"
    start = time.perf_counter()

    if not settings.mistral_api_key:
        return _skipped_result(
            name=provider_name,
            error_code="MISSING_API_KEY",
            error_message="MISTRAL_API_KEY is not configured.",
        )

    try:
        model_name = _resolve_ocr_model(settings=settings)
        client = MistralOCRClient(api_key=settings.mistral_api_key)
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            input_path = temp_root / "smoke.png"
            input_path.write_bytes(base64.b64decode(_SMOKE_PNG_BASE64))
            output_dir = temp_root / "ocr_output"

            result = client.process_document(
                input_path=input_path,
                doc_id="smoke-doc",
                options=OCROptions(
                    model=model_name,
                    table_format="none",
                    include_image_base64=False,
                ),
                output_dir=output_dir,
            )
            if result.pages_count < 1:
                raise ValueError("Mistral OCR returned zero pages in smoke run.")
    except Exception as error:  # noqa: BLE001
        if _is_sdk_missing_error(error):
            return _skipped_result(
                name=provider_name,
                error_code="SDK_NOT_INSTALLED",
                error_message=str(error),
            )
        return _failed_result(
            name=provider_name,
            start_time=start,
            error_code=classify_ocr_error(error),
            error_message=build_error_details(error),
        )

    return _passed_result(name=provider_name, start_time=start)


_probe_mistral_ocr.provider_name = "mistral_ocr"  # type: ignore[attr-defined]


def _default_provider_probes() -> list[ProviderProbe]:
    return [_probe_openai, _probe_gemini, _probe_mistral_ocr]


def _resolve_llm_model(
    *,
    settings: Settings,
    provider_name: str,
    fallback_model: str,
) -> str:
    providers_config = settings.providers_config
    llm_providers = providers_config.get("llm_providers")
    if not isinstance(llm_providers, dict):
        return fallback_model

    provider_payload = llm_providers.get(provider_name)
    if not isinstance(provider_payload, dict):
        return fallback_model

    models_payload = provider_payload.get("models")
    if not isinstance(models_payload, dict) or not models_payload:
        return fallback_model

    if fallback_model in models_payload:
        model_payload = models_payload[fallback_model]
        if isinstance(model_payload, dict):
            model_id = str(model_payload.get("id") or "").strip()
            if model_id:
                return model_id
        return fallback_model

    first_model_name = sorted(models_payload.keys())[0]
    first_model_payload = models_payload[first_model_name]
    if isinstance(first_model_payload, dict):
        model_id = str(first_model_payload.get("id") or "").strip()
        if model_id:
            return model_id
    return str(first_model_name)


def _resolve_ocr_model(*, settings: Settings) -> str:
    providers_config = settings.providers_config
    ocr_providers = providers_config.get("ocr_providers")
    if not isinstance(ocr_providers, dict):
        return settings.default_ocr_model

    provider_payload = ocr_providers.get("mistral")
    if not isinstance(provider_payload, dict):
        return settings.default_ocr_model

    models_payload = provider_payload.get("models")
    if not isinstance(models_payload, dict) or not models_payload:
        return settings.default_ocr_model

    if settings.default_ocr_model in models_payload:
        model_payload = models_payload[settings.default_ocr_model]
        if isinstance(model_payload, dict):
            model_id = str(model_payload.get("id") or "").strip()
            if model_id:
                return model_id
        return settings.default_ocr_model

    first_model_name = sorted(models_payload.keys())[0]
    first_model_payload = models_payload[first_model_name]
    if isinstance(first_model_payload, dict):
        model_id = str(first_model_payload.get("id") or "").strip()
        if model_id:
            return model_id
    return str(first_model_name)


def _passed_result(*, name: str, start_time: float) -> ProviderSmokeResult:
    return ProviderSmokeResult(
        name=name,
        status="pass",
        latency_ms=(time.perf_counter() - start_time) * 1000,
        error_code=None,
        error_message=None,
    )


def _failed_result(
    *,
    name: str,
    start_time: float,
    error_code: str,
    error_message: str,
) -> ProviderSmokeResult:
    return ProviderSmokeResult(
        name=name,
        status="fail",
        latency_ms=(time.perf_counter() - start_time) * 1000,
        error_code=error_code,
        error_message=error_message,
    )


def _skipped_result(
    *,
    name: str,
    error_code: str,
    error_message: str,
) -> ProviderSmokeResult:
    return ProviderSmokeResult(
        name=name,
        status="skipped",
        latency_ms=None,
        error_code=error_code,
        error_message=error_message,
    )


def _is_sdk_missing_error(error: Exception) -> bool:
    if not isinstance(error, RuntimeError):
        return False
    return "package is not installed" in str(error)


def _probe_provider_name(probe: ProviderProbe) -> str:
    provider_name = getattr(probe, "provider_name", None)
    if isinstance(provider_name, str) and provider_name:
        return provider_name
    return getattr(probe, "__name__", "unknown_provider")


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _json_report_text(report: dict[str, object]) -> str:
    return f"{json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run live provider contract smoke diagnostics."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat skipped providers as operational failure.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write deterministic JSON report to given path.",
    )
    args = parser.parse_args(argv)

    report = run_live_smoke(
        strict=bool(args.strict),
        output_path=(Path(args.output) if args.output else None),
    )
    print(_json_report_text(report), end="")
    return 0 if report["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
