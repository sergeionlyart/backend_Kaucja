from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RunStatus = Literal["created", "running", "completed", "failed"]
OCRStatus = Literal["pending", "ok", "failed"]


@dataclass(frozen=True, slots=True)
class SessionRecord:
    session_id: str
    created_at: str


@dataclass(frozen=True, slots=True)
class RunRecord:
    run_id: str
    session_id: str
    created_at: str
    provider: str
    model: str
    prompt_name: str
    prompt_version: str
    schema_version: str
    status: RunStatus
    artifacts_root_path: str
    openai_reasoning_effort: str | None = None
    gemini_thinking_level: str | None = None
    error_code: str | None = None
    error_message: str | None = None
