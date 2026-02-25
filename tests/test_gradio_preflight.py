from __future__ import annotations

from app.config.settings import Settings
from app.ui.gradio_app import _make_preflight_checker


def test_make_preflight_checker_bypasses_checks_in_e2e_mode(monkeypatch) -> None:
    monkeypatch.setenv("E2E_MODE", "true")
    settings = Settings(_env_file=None)

    checker = _make_preflight_checker(settings)

    assert checker("openai") is None
    assert checker("google") is None


def test_make_preflight_checker_requires_mistral_key_outside_e2e() -> None:
    settings = Settings(
        _env_file=None,
        e2e_mode=False,
        mistral_api_key="",
    )

    checker = _make_preflight_checker(settings)

    assert checker("openai") == (
        "Runtime preflight failed: MISTRAL_API_KEY is not configured."
    )
