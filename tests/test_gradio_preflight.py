from __future__ import annotations

from app.config.settings import Settings
from app.pipeline.scenario_router import (
    SCENARIO_2_ID,
    SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    SCENARIO2_RUNNER_MODE_STUB,
)
from app.ui.gradio_app import (
    _make_preflight_checker,
    _preflight_providers_for_selection,
    _scenario2_openai_mode_readiness_error,
)


class DummyOrchestrator:
    def __init__(
        self,
        *,
        scenario2_runner_mode: str,
        scenario2_runner: object | None = None,
        legal_corpus_tool: object | None = None,
        scenario2_bootstrap_error: str | None = None,
    ) -> None:
        self.scenario2_runner_mode = scenario2_runner_mode
        self.scenario2_runner = scenario2_runner
        self.legal_corpus_tool = legal_corpus_tool
        self.scenario2_bootstrap_error = scenario2_bootstrap_error


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


def test_preflight_providers_for_scenario_2_depend_on_runner_mode() -> None:
    settings = Settings(_env_file=None, scenario2_runner_mode=SCENARIO2_RUNNER_MODE_STUB)

    stub_providers = _preflight_providers_for_selection(
        orchestrator=DummyOrchestrator(
            scenario2_runner_mode=SCENARIO2_RUNNER_MODE_STUB
        ),
        settings=settings,
        scenario_id=SCENARIO_2_ID,
        effective_provider="openai",
    )
    openai_providers = _preflight_providers_for_selection(
        orchestrator=DummyOrchestrator(
            scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
            scenario2_runner=object(),
            legal_corpus_tool=object(),
        ),
        settings=settings,
        scenario_id=SCENARIO_2_ID,
        effective_provider="openai",
    )

    assert stub_providers == ["mistral"]
    assert openai_providers == ["mistral", "openai"]


def test_scenario2_openai_mode_readiness_requires_real_runner_and_tool() -> None:
    bootstrap_error = _scenario2_openai_mode_readiness_error(
        orchestrator=DummyOrchestrator(
            scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
            scenario2_bootstrap_error="local corpus root is invalid",
        )
    )
    runner_error = _scenario2_openai_mode_readiness_error(
        orchestrator=DummyOrchestrator(
            scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP
        )
    )
    tool_error = _scenario2_openai_mode_readiness_error(
        orchestrator=DummyOrchestrator(
            scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
            scenario2_runner=object(),
        )
    )
    ready_error = _scenario2_openai_mode_readiness_error(
        orchestrator=DummyOrchestrator(
            scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
            scenario2_runner=object(),
            legal_corpus_tool=object(),
        )
    )

    assert bootstrap_error is not None
    assert "local corpus root is invalid" in bootstrap_error
    assert runner_error is not None
    assert "real Scenario2 runner injection" in runner_error
    assert tool_error is not None
    assert "legal_corpus_tool adapter" in tool_error
    assert ready_error is None
