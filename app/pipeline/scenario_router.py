from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCENARIO_1_ID = "scenario_1"
SCENARIO_2_ID = "scenario_2"

SCENARIO_ID_1_LABEL = "Scenario 1"
SCENARIO_ID_2_LABEL = "Scenario 2"
SCENARIO_2_PROVIDER = "openai"
SCENARIO_2_MODEL = "gpt-5.4"
SCENARIO_2_PROMPT_NAME = "agent_prompt_foundation"
SCENARIO_2_PROMPT_VERSION = "v1.1"
SCENARIO_2_PROMPT_SOURCE_PATH = "app/prompts/agent_prompt_V1.1.md"
SCENARIO2_RUNNER_MODE_STUB = "stub"
SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP = "openai_tool_loop"
SCENARIO_2_VALIDATION_STATUS = "not_applicable"
SCENARIO_2_VALIDATION_MESSAGE = (
    "Validation is not applied to plain-text Scenario 2 responses."
)
SCENARIO2_CONFIG_ERROR = "SCENARIO2_CONFIG_ERROR"
SCENARIO2_RUNTIME_ERROR = "SCENARIO2_RUNTIME_ERROR"
SCENARIO2_TRACE_PERSIST_ERROR = "SCENARIO2_TRACE_PERSIST_ERROR"

SCENARIO_2_PLACEHOLDER = (
    "Scenario 2 foundation is active. OCR completed successfully. "
    "Agent/legal_corpus stage is not enabled in this iteration."
)


def resolve_scenario_prompt_source_path(
    prompt_source_path: str, *, prompt_root: Path | None = None
) -> str:
    """Resolve a scenario prompt path to an existing file path."""
    cleaned = (prompt_source_path or "").strip()
    if not cleaned:
        raise ValueError("Scenario prompt source path must be set.")

    requested = Path(cleaned)
    candidates: list[Path] = []

    if requested.is_absolute():
        candidates.append(requested)
    else:
        if prompt_root is not None:
            candidates.append(Path(prompt_root) / requested)
        candidates.append(Path.cwd() / requested)
        project_root = Path(__file__).resolve().parents[2]
        candidates.append(project_root / requested)

    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            return str(resolved)

    checked = ", ".join(str(candidate.resolve()) for candidate in candidates)
    raise FileNotFoundError(
        f"Scenario prompt source not found: {cleaned}. Checked: {checked}"
    )


@dataclass(frozen=True, slots=True)
class ScenarioConfig:
    scenario_id: str
    provider: str
    model: str
    prompt_name: str
    prompt_version: str
    prompt_source_path: str
    llm_stage_enabled: bool
    scenario_placeholder: str | None = None


def scenario_choices() -> list[tuple[str, str]]:
    return [(SCENARIO_ID_1_LABEL, SCENARIO_1_ID), (SCENARIO_ID_2_LABEL, SCENARIO_2_ID)]


def resolve_scenario_config(
    *,
    scenario_id: str,
    requested_provider: str,
    requested_model: str,
    requested_prompt_name: str,
    requested_prompt_version: str,
) -> ScenarioConfig:
    normalized = (scenario_id or "").strip()
    if normalized == SCENARIO_2_ID:
        return ScenarioConfig(
            scenario_id=SCENARIO_2_ID,
            provider=SCENARIO_2_PROVIDER,
            model=SCENARIO_2_MODEL,
            prompt_name=SCENARIO_2_PROMPT_NAME,
            prompt_version=SCENARIO_2_PROMPT_VERSION,
            prompt_source_path=SCENARIO_2_PROMPT_SOURCE_PATH,
            llm_stage_enabled=False,
            scenario_placeholder=SCENARIO_2_PLACEHOLDER,
        )

    return ScenarioConfig(
        scenario_id=SCENARIO_1_ID,
        provider=requested_provider,
        model=requested_model,
        prompt_name=requested_prompt_name,
        prompt_version=requested_prompt_version,
        prompt_source_path="",
        llm_stage_enabled=True,
    )


def normalize_scenario2_runner_mode(runner_mode: str | None) -> str:
    """Normalize runner mode and fallback to the safe default."""
    if (runner_mode or "").strip() == SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP:
        return SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP
    return SCENARIO2_RUNNER_MODE_STUB


def is_openai_tool_loop_mode(runner_mode: str | None) -> bool:
    return normalize_scenario2_runner_mode(runner_mode=runner_mode) == (
        SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP
    )
