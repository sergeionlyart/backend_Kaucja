from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol

from app.agentic.legal_corpus_contract import LegalCorpusTool


@dataclass(frozen=True, slots=True)
class Scenario2RunConfig:
    """Runtime configuration used by Scenario 2 runner."""

    provider: str
    model: str
    prompt_name: str
    prompt_version: str
    prompt_source_path: str
    placeholder_text: str


@dataclass(frozen=True, slots=True)
class Scenario2RunResult:
    """Runtime output contract for Scenario 2 runner."""

    final_text: str
    response_mode: Literal["plain_text"]
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    model: str | None = None
    tool_round_count: int = 0


class Scenario2RunnerError(RuntimeError):
    """Scenario 2 runtime error that preserves partial execution context."""

    def __init__(
        self,
        message: str,
        *,
        final_text: str = "",
        tool_trace: list[dict[str, Any]] | None = None,
        steps: list[str] | None = None,
        diagnostics: dict[str, Any] | None = None,
        model: str | None = None,
        tool_round_count: int = 0,
    ) -> None:
        super().__init__(message)
        self.final_text = final_text
        self.tool_trace = list(tool_trace or [])
        self.steps = list(steps or [])
        self.diagnostics = dict(diagnostics or {})
        self.model = model
        self.tool_round_count = tool_round_count

    def to_run_result(self) -> Scenario2RunResult:
        return Scenario2RunResult(
            final_text=self.final_text,
            response_mode="plain_text",
            tool_trace=list(self.tool_trace),
            steps=list(self.steps),
            diagnostics=dict(self.diagnostics),
            model=self.model,
            tool_round_count=self.tool_round_count,
        )


class Scenario2Runner(Protocol):
    """Contract for Scenario 2 execution path."""

    def run(
        self,
        *,
        packed_documents: str,
        config: Scenario2RunConfig,
        system_prompt_path: str,
        legal_corpus_tool: LegalCorpusTool | None = None,
    ) -> Scenario2RunResult: ...


class StubScenario2Runner:
    """Default Scenario 2 runner implementation with deterministic plain-text output."""

    def run(
        self,
        *,
        packed_documents: str,
        config: Scenario2RunConfig,
        system_prompt_path: str,
        legal_corpus_tool: LegalCorpusTool | None = None,
    ) -> Scenario2RunResult:
        del legal_corpus_tool
        prompt_path = Path(system_prompt_path)
        if not prompt_path.is_absolute():
            prompt_path = prompt_path.resolve()

        if not prompt_path.is_file():
            raise FileNotFoundError(
                f"System prompt path must point to an existing file: {prompt_path}"
            )

        prompt_bytes = prompt_path.read_bytes()
        prompt_size_bytes = len(prompt_bytes)
        prompt_sha256 = hashlib.sha256(prompt_bytes).hexdigest()
        return Scenario2RunResult(
            final_text=config.placeholder_text,
            response_mode="plain_text",
            tool_trace=[
                {
                    "tool": "scenario2_stub",
                    "status": "ok",
                    "resolved_prompt_path": str(prompt_path),
                    "document_chars": len(packed_documents),
                    "prompt_sha256": prompt_sha256,
                }
            ],
            steps=["ocr_complete", "scenario2_stub_response"],
            diagnostics={
                "provider": config.provider,
                "model": config.model,
                "prompt_name": config.prompt_name,
                "prompt_version": config.prompt_version,
                "prompt_source_path": config.prompt_source_path,
                "resolved_prompt_path": str(prompt_path),
                "prompt_exists": True,
                "prompt_size_bytes": prompt_size_bytes,
                "run_mode": "placeholder",
            },
            model=config.model,
            tool_round_count=0,
        )
