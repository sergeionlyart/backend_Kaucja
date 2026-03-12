from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.agentic.case_workspace_store import MongoCaseWorkspaceStore
from app.agentic.legal_corpus_contract import LegalCorpusTool
from app.agentic.legal_corpus_local import LocalLegalCorpusTool
from app.agentic.legal_corpus_mongo import MongoLegalCorpusTool, build_mongo_runtime
from app.agentic.openai_scenario2_runner import OpenAIScenario2Runner
from app.agentic.scenario2_runner import Scenario2Runner, StubScenario2Runner
from app.config.settings import Settings
from app.llm_client.openai_client import OpenAIResponsesService
from app.pipeline.scenario_router import (
    SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    normalize_scenario2_runner_mode,
)

_SCENARIO2_LEGAL_CORPUS_BACKEND_LOCAL = "local"
_SCENARIO2_LEGAL_CORPUS_BACKEND_MONGO = "mongo"


@dataclass(frozen=True, slots=True)
class Scenario2RuntimeComponents:
    runner_mode: str
    runner: Scenario2Runner
    legal_corpus_tool: LegalCorpusTool | None
    case_workspace_store: Any | None = None
    bootstrap_error: str | None = None


def build_scenario2_runtime(
    *,
    settings: Settings,
    responses_service: OpenAIResponsesService | None = None,
    mongo_runtime_factory: Callable[[Settings], Any] | None = None,
) -> Scenario2RuntimeComponents:
    runner_mode = normalize_scenario2_runner_mode(settings.scenario2_runner_mode)
    if runner_mode != SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP:
        return Scenario2RuntimeComponents(
            runner_mode=runner_mode,
            runner=StubScenario2Runner(),
            legal_corpus_tool=None,
        )

    backend = str(settings.scenario2_legal_corpus_backend or "").strip().lower()
    if backend == _SCENARIO2_LEGAL_CORPUS_BACKEND_LOCAL:
        return _build_local_runtime(
            runner_mode=runner_mode,
            settings=settings,
            responses_service=responses_service,
        )
    if backend == _SCENARIO2_LEGAL_CORPUS_BACKEND_MONGO:
        return _build_mongo_runtime(
            runner_mode=runner_mode,
            settings=settings,
            responses_service=responses_service,
            mongo_runtime_factory=mongo_runtime_factory,
        )
    return Scenario2RuntimeComponents(
        runner_mode=runner_mode,
        runner=StubScenario2Runner(),
        legal_corpus_tool=None,
        bootstrap_error=(
            "Scenario 2 legal corpus backend is unsupported: "
            f"{settings.scenario2_legal_corpus_backend}"
        ),
    )


def _build_local_runtime(
    *,
    runner_mode: str,
    settings: Settings,
    responses_service: OpenAIResponsesService | None,
) -> Scenario2RuntimeComponents:
    try:
        legal_corpus_tool = LocalLegalCorpusTool(
            root=settings.resolved_scenario2_legal_corpus_local_root
        )
    except Exception as error:  # noqa: BLE001
        return Scenario2RuntimeComponents(
            runner_mode=runner_mode,
            runner=StubScenario2Runner(),
            legal_corpus_tool=None,
            bootstrap_error=str(error),
        )

    service_error: str | None = None
    service: OpenAIResponsesService | None = responses_service
    if service is None:
        try:
            service = build_openai_responses_service(api_key=settings.openai_api_key)
        except Exception as error:  # noqa: BLE001
            service_error = str(error)

    if service_error is not None:
        return Scenario2RuntimeComponents(
            runner_mode=runner_mode,
            runner=StubScenario2Runner(),
            legal_corpus_tool=legal_corpus_tool,
            bootstrap_error=service_error,
        )

    return Scenario2RuntimeComponents(
        runner_mode=runner_mode,
        runner=OpenAIScenario2Runner(responses_service=service),
        legal_corpus_tool=legal_corpus_tool,
    )


def _build_mongo_runtime(
    *,
    runner_mode: str,
    settings: Settings,
    responses_service: OpenAIResponsesService | None,
    mongo_runtime_factory: Callable[[Settings], Any] | None,
) -> Scenario2RuntimeComponents:
    try:
        runtime = (
            mongo_runtime_factory(settings)
            if mongo_runtime_factory is not None
            else build_mongo_runtime(
                mongo_uri=settings.scenario2_legal_corpus_mongo_uri,
                mongo_db_name=settings.scenario2_legal_corpus_mongo_db,
            )
        )
        legal_corpus_tool = MongoLegalCorpusTool(
            runtime=runtime,
            auto_materialize=settings.scenario2_legal_corpus_mongo_auto_materialize,
        )
        case_workspace_store = MongoCaseWorkspaceStore(runtime=runtime)
    except Exception as error:  # noqa: BLE001
        return Scenario2RuntimeComponents(
            runner_mode=runner_mode,
            runner=StubScenario2Runner(),
            legal_corpus_tool=None,
            case_workspace_store=None,
            bootstrap_error=str(error),
        )

    service_error: str | None = None
    service: OpenAIResponsesService | None = responses_service
    if service is None:
        try:
            service = build_openai_responses_service(api_key=settings.openai_api_key)
        except Exception as error:  # noqa: BLE001
            service_error = str(error)

    if service_error is not None:
        return Scenario2RuntimeComponents(
            runner_mode=runner_mode,
            runner=StubScenario2Runner(),
            legal_corpus_tool=legal_corpus_tool,
            case_workspace_store=case_workspace_store,
            bootstrap_error=service_error,
        )

    return Scenario2RuntimeComponents(
        runner_mode=runner_mode,
        runner=OpenAIScenario2Runner(responses_service=service),
        legal_corpus_tool=legal_corpus_tool,
        case_workspace_store=case_workspace_store,
    )


def build_openai_responses_service(
    *,
    api_key: str | None,
) -> OpenAIResponsesService:
    if api_key is None or not api_key.strip():
        raise RuntimeError(
            "Scenario 2 OpenAI runtime is not configured: OPENAI_API_KEY is missing."
        )

    try:
        from openai import OpenAI
    except ImportError as error:
        raise RuntimeError(
            "Scenario 2 OpenAI runtime is not configured: openai package "
            "is not installed."
        ) from error

    client = OpenAI(api_key=api_key)
    return client.responses
