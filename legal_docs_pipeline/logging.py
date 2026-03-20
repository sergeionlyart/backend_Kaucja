"""Structured logging for the NormaDepo pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

_LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
}


@dataclass(frozen=True, slots=True)
class PipelineLogEvent:
    run_id: str
    stage: str
    event: str
    level: str
    message: str
    doc_id: str | None = None
    error: dict[str, Any] | None = None
    details: dict[str, Any] = field(default_factory=dict)


class PipelineLogger(Protocol):
    log_path: Path

    def log(self, event: PipelineLogEvent) -> None:
        """Write structured pipeline event."""


class JsonlPipelineLogger:
    def __init__(
        self,
        *,
        run_id: str,
        log_dir: Path | str = Path("logs"),
        log_level: str = "INFO",
    ) -> None:
        self.log_path = Path(log_dir).resolve() / f"{run_id}.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_level = _normalize_log_level(log_level)

    def log(self, event: PipelineLogEvent) -> None:
        if _LOG_LEVELS[_normalize_log_level(event.level)] < _LOG_LEVELS[self._log_level]:
            return
        payload = {
            "timestamp": _utc_now().isoformat(),
            "level": event.level,
            "run_id": event.run_id,
            "doc_id": event.doc_id,
            "stage": event.stage,
            "event": event.event,
            "message": event.message,
            "error": event.error,
            "details": event.details,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _normalize_log_level(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in _LOG_LEVELS:
        raise ValueError(f"Unsupported log level: {value}")
    return normalized
