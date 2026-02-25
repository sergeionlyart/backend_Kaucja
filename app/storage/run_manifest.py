from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MANIFEST_FILE_NAME = "run.json"


def init_run_manifest(
    *,
    artifacts_root_path: Path | str,
    session_id: str,
    run_id: str,
    inputs: dict[str, Any],
    artifacts: dict[str, Any],
    status: str = "running",
) -> Path:
    timestamp = _utc_now()
    manifest = {
        "session_id": session_id,
        "run_id": run_id,
        "status": status,
        "inputs": inputs,
        "stages": {
            "init": {"status": "completed", "updated_at": timestamp},
            "ocr": {"status": "pending", "updated_at": timestamp},
            "llm": {"status": "pending", "updated_at": timestamp},
            "finalize": {"status": "pending", "updated_at": timestamp},
        },
        "artifacts": artifacts,
        "metrics": {
            "timings": {},
            "usage": {},
            "usage_normalized": {},
            "cost": {},
        },
        "validation": {"valid": None, "errors": []},
        "error_code": None,
        "error_message": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    path = get_manifest_path(artifacts_root_path)
    _write_json(path, manifest)
    return path


def update_run_manifest(
    *,
    artifacts_root_path: Path | str,
    updates: dict[str, Any],
) -> dict[str, Any]:
    path = get_manifest_path(artifacts_root_path)
    current = read_run_manifest(artifacts_root_path=artifacts_root_path)
    merged = _deep_merge(current, updates)
    merged["updated_at"] = _utc_now()
    _write_json(path, merged)
    return merged


def read_run_manifest(*, artifacts_root_path: Path | str) -> dict[str, Any]:
    path = get_manifest_path(artifacts_root_path)
    if not path.exists():
        return {}

    raw = path.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"Manifest root must be an object: {path}")

    return parsed


def get_manifest_path(artifacts_root_path: Path | str) -> Path:
    return Path(artifacts_root_path) / MANIFEST_FILE_NAME


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = dict(base)
    for key, value in updates.items():
        existing = result.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            result[key] = _deep_merge(existing, value)
        else:
            result[key] = value
    return result


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
