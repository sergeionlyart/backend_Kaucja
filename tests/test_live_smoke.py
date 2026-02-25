from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

import app.ops.live_smoke as live_smoke_module
from app.config.settings import Settings
from app.ops.live_smoke import ProviderSmokeResult, main, run_live_smoke


def _settings() -> Settings:
    return Settings(_env_file=None)


def _probe(
    *,
    name: str,
    status: str,
    latency_ms: float | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
):
    def _inner(_: Settings) -> ProviderSmokeResult:
        return ProviderSmokeResult(
            name=name,
            status=status,  # type: ignore[arg-type]
            latency_ms=latency_ms,
            error_code=error_code,
            error_message=error_message,
        )

    _inner.provider_name = name  # type: ignore[attr-defined]
    return _inner


def _slow_probe(*, name: str, sleep_seconds: float):
    def _inner(_: Settings) -> ProviderSmokeResult:
        time.sleep(sleep_seconds)
        return ProviderSmokeResult(
            name=name,
            status="pass",
            latency_ms=1.0,
            error_code=None,
            error_message=None,
        )

    _inner.provider_name = name  # type: ignore[attr-defined]
    return _inner


def _now_factory(values: list[datetime]):
    sequence = iter(values)

    def _now() -> datetime:
        return next(sequence)

    return _now


def test_live_smoke_non_strict_skipped_non_required_is_allowed(tmp_path: Path) -> None:
    output_path = tmp_path / "live_smoke.json"
    report = run_live_smoke(
        strict=False,
        settings=_settings(),
        output_path=output_path,
        required_providers=["openai"],
        provider_timeout_seconds=5.0,
        provider_probes=[
            _probe(name="openai", status="pass", latency_ms=1.2),
            _probe(
                name="google",
                status="skipped",
                error_code="LIVE_SMOKE_MISSING_API_KEY",
                error_message="not configured",
            ),
            _probe(name="mistral_ocr", status="pass", latency_ms=2.3),
        ],
        now_fn=_now_factory(
            [
                datetime(2026, 2, 25, 18, 0, 0, tzinfo=timezone.utc),
                datetime(2026, 2, 25, 18, 0, 1, tzinfo=timezone.utc),
            ]
        ),
    )

    assert report["overall_status"] == "pass"
    assert report["required_providers"] == ["openai"]
    assert report["required_failures"] == []
    assert report["required_skipped"] == []
    assert output_path.is_file()

    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded["started_at"] == "2026-02-25T18:00:00+00:00"
    assert loaded["finished_at"] == "2026-02-25T18:00:01+00:00"


def test_live_smoke_required_skipped_fails_even_non_strict() -> None:
    report = run_live_smoke(
        strict=False,
        settings=_settings(),
        required_providers=["openai", "google"],
        provider_timeout_seconds=5.0,
        provider_probes=[
            _probe(name="openai", status="pass", latency_ms=1.0),
            _probe(
                name="google",
                status="skipped",
                error_code="LIVE_SMOKE_MISSING_API_KEY",
                error_message="not configured",
            ),
            _probe(name="mistral_ocr", status="pass", latency_ms=1.5),
        ],
        now_fn=_now_factory(
            [
                datetime(2026, 2, 25, 18, 1, 0, tzinfo=timezone.utc),
                datetime(2026, 2, 25, 18, 1, 2, tzinfo=timezone.utc),
            ]
        ),
    )

    assert report["overall_status"] == "fail"
    assert report["required_skipped"] == ["google"]
    assert report["required_failures"] == []


def test_live_smoke_required_failures_are_reported() -> None:
    report = run_live_smoke(
        strict=False,
        settings=_settings(),
        required_providers=["openai", "google", "mistral_ocr"],
        provider_timeout_seconds=5.0,
        provider_probes=[
            _probe(name="openai", status="pass", latency_ms=1.0),
            _probe(
                name="google",
                status="fail",
                latency_ms=2.0,
                error_code="LLM_API_ERROR",
                error_message="failure",
            ),
            _probe(name="mistral_ocr", status="pass", latency_ms=1.5),
        ],
        now_fn=_now_factory(
            [
                datetime(2026, 2, 25, 18, 2, 0, tzinfo=timezone.utc),
                datetime(2026, 2, 25, 18, 2, 1, tzinfo=timezone.utc),
            ]
        ),
    )

    assert report["overall_status"] == "fail"
    assert report["required_failures"] == ["google"]
    providers = report["providers"]
    assert isinstance(providers, list)
    assert providers[1]["error_code"] == "LLM_API_ERROR"


def test_live_smoke_timeout_marks_provider_failed() -> None:
    report = run_live_smoke(
        strict=False,
        settings=_settings(),
        required_providers=["openai"],
        provider_timeout_seconds=0.01,
        provider_probes=[
            _slow_probe(name="openai", sleep_seconds=0.2),
            _probe(name="google", status="pass", latency_ms=1.0),
            _probe(name="mistral_ocr", status="pass", latency_ms=1.0),
        ],
        now_fn=_now_factory(
            [
                datetime(2026, 2, 25, 18, 3, 0, tzinfo=timezone.utc),
                datetime(2026, 2, 25, 18, 3, 1, tzinfo=timezone.utc),
            ]
        ),
    )

    assert report["overall_status"] == "fail"
    providers = report["providers"]
    assert isinstance(providers, list)
    assert providers[0]["status"] == "fail"
    assert providers[0]["error_code"] == "LIVE_SMOKE_TIMEOUT"


def test_live_smoke_report_contains_policy_fields() -> None:
    report = run_live_smoke(
        strict=True,
        settings=_settings(),
        required_providers=["openai", "google"],
        provider_timeout_seconds=7.5,
        provider_probes=[
            _probe(name="openai", status="pass", latency_ms=1.12345),
            _probe(name="google", status="pass", latency_ms=2.23456),
            _probe(name="mistral_ocr", status="pass", latency_ms=3.34567),
        ],
        now_fn=_now_factory(
            [
                datetime(2026, 2, 25, 18, 4, 0, tzinfo=timezone.utc),
                datetime(2026, 2, 25, 18, 4, 1, tzinfo=timezone.utc),
            ]
        ),
    )

    assert set(report.keys()) >= {
        "started_at",
        "finished_at",
        "overall_status",
        "providers",
        "required_providers",
        "required_failures",
        "required_skipped",
        "provider_timeout_seconds",
    }
    assert report["required_providers"] == ["openai", "google"]
    assert report["provider_timeout_seconds"] == 7.5


def test_live_smoke_cli_exit_code_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_run_live_smoke(**kwargs: object) -> dict[str, object]:
        del kwargs
        return {
            "started_at": "2026-02-25T00:00:00+00:00",
            "finished_at": "2026-02-25T00:00:01+00:00",
            "overall_status": "pass",
            "providers": [],
            "required_providers": [],
            "required_failures": [],
            "required_skipped": [],
        }

    monkeypatch.setattr(live_smoke_module, "run_live_smoke", _fake_run_live_smoke)
    exit_code = main([])
    assert exit_code == 0


def test_live_smoke_cli_exit_code_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_run_live_smoke(**kwargs: object) -> dict[str, object]:
        del kwargs
        return {
            "started_at": "2026-02-25T00:00:00+00:00",
            "finished_at": "2026-02-25T00:00:01+00:00",
            "overall_status": "fail",
            "providers": [],
            "required_providers": ["openai"],
            "required_failures": ["openai"],
            "required_skipped": [],
        }

    monkeypatch.setattr(live_smoke_module, "run_live_smoke", _fake_run_live_smoke)
    exit_code = main(
        [
            "--strict",
            "--required-providers",
            "openai,google",
            "--provider-timeout-seconds",
            "15",
        ]
    )
    assert exit_code == 1


def test_live_smoke_cli_uses_settings_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_run_live_smoke(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "started_at": "2026-02-25T00:00:00+00:00",
            "finished_at": "2026-02-25T00:00:01+00:00",
            "overall_status": "pass",
            "providers": [],
            "required_providers": [],
            "required_failures": [],
            "required_skipped": [],
        }

    class _StubSettings:
        live_smoke_required_providers = "openai,mistral_ocr"
        live_smoke_provider_timeout_seconds = 12.5

    monkeypatch.setattr(live_smoke_module, "run_live_smoke", _fake_run_live_smoke)
    monkeypatch.setattr(live_smoke_module, "get_settings", lambda: _StubSettings())

    exit_code = main([])
    assert exit_code == 0
    assert captured["required_providers"] == ["openai", "mistral_ocr"]
    assert captured["provider_timeout_seconds"] == 12.5
