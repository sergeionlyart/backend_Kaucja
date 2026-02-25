from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class LLMResult:
    raw_text: str
    parsed_json: dict[str, Any]
    raw_response: dict[str, Any]
    usage_raw: dict[str, Any]
    usage_normalized: dict[str, int | None]
    cost: dict[str, Any]
    timings: dict[str, float]


class LLMClient(Protocol):
    def generate_json(
        self,
        *,
        system_prompt: str,
        user_content: str,
        json_schema: dict[str, Any],
        model: str,
        params: dict[str, Any],
        run_meta: dict[str, Any],
    ) -> LLMResult: ...
