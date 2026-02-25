from __future__ import annotations

import json
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


def _now_factory(values: list[datetime]):
    sequence = iter(values)

    def _now() -> datetime:
        return next(sequence)

    return _now


def test_live_smoke_non_strict_skipped_is_allowed(tmp_path: Path) -> None:
    output_path = tmp_path / "live_smoke.json"
    report = run_live_smoke(
        strict=False,
        settings=_settings(),
        output_path=output_path,
        provider_probes=[
            _probe(name="openai", status="pass", latency_ms=1.2),
            _probe(
                name="google",
                status="skipped",
                error_code="MISSING_API_KEY",
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
    assert report["strict_mode"] is False
    providers = report["providers"]
    assert isinstance(providers, list)
    assert providers[1]["status"] == "skipped"
    assert output_path.is_file()

    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded["started_at"] == "2026-02-25T18:00:00+00:00"
    assert loaded["finished_at"] == "2026-02-25T18:00:01+00:00"


def test_live_smoke_strict_skipped_causes_fail() -> None:
    report = run_live_smoke(
        strict=True,
        settings=_settings(),
        provider_probes=[
            _probe(name="openai", status="pass", latency_ms=1.0),
            _probe(
                name="google",
                status="skipped",
                error_code="MISSING_API_KEY",
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
    assert report["strict_mode"] is True
    summary = report["summary"]
    assert isinstance(summary, dict)
    assert summary["strict_skipped_violation"] is True


def test_live_smoke_fail_aggregation() -> None:
    report = run_live_smoke(
        strict=False,
        settings=_settings(),
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
    providers = report["providers"]
    assert isinstance(providers, list)
    assert providers[1]["error_code"] == "LLM_API_ERROR"


def test_live_smoke_report_contains_required_provider_fields() -> None:
    report = run_live_smoke(
        strict=False,
        settings=_settings(),
        provider_probes=[
            _probe(name="openai", status="pass", latency_ms=1.12345),
            _probe(name="google", status="pass", latency_ms=2.23456),
            _probe(name="mistral_ocr", status="pass", latency_ms=3.34567),
        ],
        now_fn=_now_factory(
            [
                datetime(2026, 2, 25, 18, 3, 0, tzinfo=timezone.utc),
                datetime(2026, 2, 25, 18, 3, 1, tzinfo=timezone.utc),
            ]
        ),
    )

    assert set(report.keys()) >= {
        "started_at",
        "finished_at",
        "overall_status",
        "providers",
    }
    providers = report["providers"]
    assert isinstance(providers, list)
    assert len(providers) == 3
    for provider in providers:
        assert set(provider.keys()) == {
            "name",
            "status",
            "latency_ms",
            "error_code",
            "error_message",
        }


def test_live_smoke_cli_exit_code_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_run_live_smoke(**kwargs: object) -> dict[str, object]:
        del kwargs
        return {
            "started_at": "2026-02-25T00:00:00+00:00",
            "finished_at": "2026-02-25T00:00:01+00:00",
            "overall_status": "pass",
            "providers": [],
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
        }

    monkeypatch.setattr(live_smoke_module, "run_live_smoke", _fake_run_live_smoke)
    exit_code = main(["--strict"])
    assert exit_code == 1
