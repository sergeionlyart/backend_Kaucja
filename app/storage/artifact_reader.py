from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def safe_read_text(path: Path | str) -> tuple[str | None, str | None]:
    file_path = Path(path)
    if not file_path.exists():
        return None, f"File not found: {file_path}"
    if not file_path.is_file():
        return None, f"Path is not a file: {file_path}"

    try:
        return file_path.read_text(encoding="utf-8"), None
    except OSError as error:
        return None, f"Failed to read file {file_path}: {error}"


def safe_read_json(
    path: Path | str,
) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
    text, error = safe_read_text(path)
    if error is not None:
        return None, error

    try:
        return json.loads(text or ""), None
    except json.JSONDecodeError as decode_error:
        return None, f"Invalid JSON in {Path(path)}: {decode_error}"


def safe_load_run_manifest(
    artifacts_root_path: Path | str,
) -> tuple[dict[str, Any] | None, str | None]:
    payload, error = safe_read_json(Path(artifacts_root_path) / "run.json")
    if error is not None:
        return None, error
    if not isinstance(payload, dict):
        return None, "Invalid run manifest format: expected JSON object."
    return payload, None


def safe_load_llm_raw_text(
    artifacts_root_path: Path | str,
) -> tuple[str | None, str | None]:
    return safe_read_text(Path(artifacts_root_path) / "llm" / "response_raw.txt")


def safe_load_llm_parsed_json(
    artifacts_root_path: Path | str,
) -> tuple[dict[str, Any] | None, str | None]:
    payload, error = safe_read_json(
        Path(artifacts_root_path) / "llm" / "response_parsed.json"
    )
    if error is not None:
        return None, error
    if not isinstance(payload, dict):
        return None, "Invalid parsed LLM response format: expected JSON object."
    return payload, None


def safe_load_llm_validation_json(
    artifacts_root_path: Path | str,
) -> tuple[dict[str, Any] | None, str | None]:
    payload, error = safe_read_json(
        Path(artifacts_root_path) / "llm" / "validation.json"
    )
    if error is not None:
        return None, error
    if not isinstance(payload, dict):
        return None, "Invalid validation artifact format: expected JSON object."
    return payload, None


def safe_load_combined_markdown(
    ocr_artifacts_path: Path | str,
) -> tuple[str | None, str | None]:
    return safe_read_text(Path(ocr_artifacts_path) / "combined.md")
