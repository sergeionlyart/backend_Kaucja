from __future__ import annotations

import json
from typing import Any

from app.storage.artifact_reader import (
    safe_load_llm_parsed_json,
    safe_load_llm_raw_text,
    safe_load_run_manifest,
    safe_read_json,
)
from app.storage.models import RunRecord
from app.storage.repo import StorageRepo

_STATUS_RANK = {
    "missing": 0,
    "conflict": 1,
    "ambiguous": 2,
    "confirmed": 3,
}


def compare_runs(
    *,
    repo: StorageRepo,
    run_id_a: str,
    run_id_b: str,
) -> dict[str, Any]:
    snapshot_a = build_run_snapshot(repo=repo, run_id=run_id_a)
    snapshot_b = build_run_snapshot(repo=repo, run_id=run_id_b)
    return build_run_diff(snapshot_a=snapshot_a, snapshot_b=snapshot_b)


def build_run_snapshot(*, repo: StorageRepo, run_id: str) -> dict[str, Any]:
    target_run_id = run_id.strip()
    if not target_run_id:
        return _missing_snapshot(run_id=run_id, reason="run_id is empty")

    bundle = repo.get_run_bundle(target_run_id)
    if bundle is None:
        return _missing_snapshot(
            run_id=target_run_id,
            reason=f"run_id={target_run_id} not found",
        )

    run = bundle.run
    artifacts_root = run.artifacts_root_path
    warnings: list[str] = []

    manifest, manifest_error = safe_load_run_manifest(artifacts_root)
    if manifest_error is not None:
        warnings.append(manifest_error)

    parsed_json, parsed_warning = _load_parsed_json(
        bundle=bundle,
        artifacts_root=artifacts_root,
    )
    if parsed_warning is not None:
        warnings.append(parsed_warning)

    checklist = _checklist(parsed_json)
    critical_gaps_summary = _to_string_list(
        parsed_json.get("critical_gaps_summary") if parsed_json else None
    )
    next_questions_to_user = _to_string_list(
        parsed_json.get("next_questions_to_user") if parsed_json else None
    )

    return {
        "run_id": run.run_id,
        "exists": True,
        "run": _run_identity(run),
        "artifacts_root_path": artifacts_root,
        "checklist": checklist,
        "critical_gaps_summary": critical_gaps_summary,
        "next_questions_to_user": next_questions_to_user,
        "metrics": _metrics_payload(run=run, manifest=manifest),
        "warnings": sorted(set(warnings)),
    }


def build_run_diff(
    *,
    snapshot_a: dict[str, Any],
    snapshot_b: dict[str, Any],
) -> dict[str, Any]:
    checklist_a = _checklist_map(snapshot_a.get("checklist"))
    checklist_b = _checklist_map(snapshot_b.get("checklist"))
    item_ids = sorted(set(checklist_a.keys()) | set(checklist_b.keys()))

    rows: list[dict[str, Any]] = []
    counts = {
        "improved": 0,
        "regressed": 0,
        "unchanged": 0,
        "added": 0,
        "removed": 0,
    }

    for item_id in item_ids:
        item_a = checklist_a.get(item_id)
        item_b = checklist_b.get(item_id)
        row = _compare_checklist_item(item_id=item_id, item_a=item_a, item_b=item_b)
        rows.append(row)
        change = str(row.get("change") or "")
        if change in counts:
            counts[change] += 1

    critical_gaps_diff = _compare_string_lists(
        left=snapshot_a.get("critical_gaps_summary"),
        right=snapshot_b.get("critical_gaps_summary"),
    )
    next_questions_diff = _compare_string_lists(
        left=snapshot_a.get("next_questions_to_user"),
        right=snapshot_b.get("next_questions_to_user"),
    )

    metadata = {
        "provider_changed": _meta_value(snapshot_a, "provider")
        != _meta_value(snapshot_b, "provider"),
        "model_changed": _meta_value(snapshot_a, "model")
        != _meta_value(snapshot_b, "model"),
        "prompt_version_changed": _meta_value(snapshot_a, "prompt_version")
        != _meta_value(snapshot_b, "prompt_version"),
    }

    metrics_diff = _compare_metrics(
        metrics_a=snapshot_a.get("metrics"),
        metrics_b=snapshot_b.get("metrics"),
    )

    warnings_a = [
        f"run_a: {warning}" for warning in _to_string_list(snapshot_a.get("warnings"))
    ]
    warnings_b = [
        f"run_b: {warning}" for warning in _to_string_list(snapshot_b.get("warnings"))
    ]
    combined_warnings = sorted(set(warnings_a + warnings_b))

    return {
        "run_a": {
            "run_id": snapshot_a.get("run_id"),
            "exists": bool(snapshot_a.get("exists")),
            "run": (
                snapshot_a.get("run") if isinstance(snapshot_a.get("run"), dict) else {}
            ),
            "artifacts_root_path": str(snapshot_a.get("artifacts_root_path") or ""),
            "warnings": _to_string_list(snapshot_a.get("warnings")),
        },
        "run_b": {
            "run_id": snapshot_b.get("run_id"),
            "exists": bool(snapshot_b.get("exists")),
            "run": (
                snapshot_b.get("run") if isinstance(snapshot_b.get("run"), dict) else {}
            ),
            "artifacts_root_path": str(snapshot_b.get("artifacts_root_path") or ""),
            "warnings": _to_string_list(snapshot_b.get("warnings")),
        },
        "metadata": metadata,
        "checklist_diff": rows,
        "critical_gaps_diff": critical_gaps_diff,
        "next_questions_diff": next_questions_diff,
        "metrics_diff": metrics_diff,
        "summary_counts": counts,
        "warnings": combined_warnings,
    }


def _missing_snapshot(*, run_id: str, reason: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "exists": False,
        "run": {},
        "artifacts_root_path": "",
        "checklist": [],
        "critical_gaps_summary": [],
        "next_questions_to_user": [],
        "metrics": {"timings": {}, "usage": {}, "usage_normalized": {}, "cost": {}},
        "warnings": [reason],
    }


def _run_identity(run: RunRecord) -> dict[str, Any]:
    return {
        "session_id": run.session_id,
        "provider": run.provider,
        "model": run.model,
        "prompt_name": run.prompt_name,
        "prompt_version": run.prompt_version,
        "status": run.status,
        "created_at": run.created_at,
    }


def _load_parsed_json(
    *,
    bundle: Any,
    artifacts_root: str,
) -> tuple[dict[str, Any] | None, str | None]:
    warnings: list[str] = []

    if bundle.llm_output is not None:
        payload, error = safe_read_json(bundle.llm_output.response_json_path)
        if error is None and isinstance(payload, dict):
            return payload, None
        if error is not None:
            warnings.append(error)
        else:
            warnings.append("Invalid parsed LLM response format: expected JSON object.")

    payload, error = safe_load_llm_parsed_json(artifacts_root)
    if error is None and isinstance(payload, dict):
        return payload, None
    if error is not None:
        warnings.append(error)

    raw_text, raw_error = safe_load_llm_raw_text(artifacts_root)
    if raw_error is None and raw_text is not None:
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as decode_error:
            warnings.append(f"Invalid JSON in raw response: {decode_error}")
        else:
            if isinstance(parsed, dict):
                return parsed, None
            warnings.append("Raw response JSON is not an object.")
    elif raw_error is not None:
        warnings.append(raw_error)

    if warnings:
        return None, "; ".join(sorted(set(warnings)))
    return None, "LLM artifacts unavailable."


def _metrics_payload(
    *,
    run: RunRecord,
    manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    metrics = {
        "timings": run.timings_json or {},
        "usage": run.usage_json or {},
        "usage_normalized": run.usage_normalized_json or {},
        "cost": run.cost_json or {},
    }

    if isinstance(manifest, dict):
        manifest_metrics = manifest.get("metrics")
        if isinstance(manifest_metrics, dict):
            metrics = {
                "timings": _dict_or_empty(
                    manifest_metrics.get("timings"),
                    metrics["timings"],
                ),
                "usage": _dict_or_empty(
                    manifest_metrics.get("usage"), metrics["usage"]
                ),
                "usage_normalized": _dict_or_empty(
                    manifest_metrics.get("usage_normalized"),
                    metrics["usage_normalized"],
                ),
                "cost": _dict_or_empty(manifest_metrics.get("cost"), metrics["cost"]),
            }

    return metrics


def _checklist(value: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return []
    checklist = value.get("checklist")
    if not isinstance(checklist, list):
        return []
    return [item for item in checklist if isinstance(item, dict)]


def _checklist_map(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        return {}

    mapped: dict[str, dict[str, Any]] = {}
    for item in value:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("item_id") or "").strip()
        if not item_id:
            continue
        mapped[item_id] = item
    return mapped


def _compare_checklist_item(
    *,
    item_id: str,
    item_a: dict[str, Any] | None,
    item_b: dict[str, Any] | None,
) -> dict[str, Any]:
    if item_a is None and item_b is None:
        return {
            "item_id": item_id,
            "status_a": "",
            "status_b": "",
            "confidence_a": "",
            "confidence_b": "",
            "findings_changed": False,
            "request_changed": False,
            "change": "unchanged",
        }

    if item_a is None:
        return {
            "item_id": item_id,
            "status_a": "",
            "status_b": str(item_b.get("status") or ""),
            "confidence_a": "",
            "confidence_b": str(item_b.get("confidence") or ""),
            "findings_changed": True,
            "request_changed": True,
            "change": "added",
        }

    if item_b is None:
        return {
            "item_id": item_id,
            "status_a": str(item_a.get("status") or ""),
            "status_b": "",
            "confidence_a": str(item_a.get("confidence") or ""),
            "confidence_b": "",
            "findings_changed": True,
            "request_changed": True,
            "change": "removed",
        }

    status_a = str(item_a.get("status") or "")
    status_b = str(item_b.get("status") or "")
    findings_changed = _stable_json(item_a.get("findings")) != _stable_json(
        item_b.get("findings")
    )
    request_changed = _stable_json(item_a.get("request_from_user")) != _stable_json(
        item_b.get("request_from_user")
    )

    return {
        "item_id": item_id,
        "status_a": status_a,
        "status_b": status_b,
        "confidence_a": str(item_a.get("confidence") or ""),
        "confidence_b": str(item_b.get("confidence") or ""),
        "findings_changed": findings_changed,
        "request_changed": request_changed,
        "change": _status_change(status_a=status_a, status_b=status_b),
    }


def _status_change(*, status_a: str, status_b: str) -> str:
    if status_a == status_b:
        return "unchanged"

    rank_a = _STATUS_RANK.get(status_a)
    rank_b = _STATUS_RANK.get(status_b)
    if rank_a is None or rank_b is None:
        return "unchanged"
    if rank_b > rank_a:
        return "improved"
    return "regressed"


def _compare_string_lists(*, left: Any, right: Any) -> dict[str, list[str]]:
    left_set = set(_to_string_list(left))
    right_set = set(_to_string_list(right))
    return {
        "only_in_a": sorted(left_set - right_set),
        "only_in_b": sorted(right_set - left_set),
        "common": sorted(left_set & right_set),
    }


def _compare_metrics(*, metrics_a: Any, metrics_b: Any) -> dict[str, Any]:
    normalized_a = _normalize_metrics(metrics_a)
    normalized_b = _normalize_metrics(metrics_b)

    flattened_a: dict[str, float] = {}
    flattened_b: dict[str, float] = {}
    _flatten_numeric(prefix="", payload=normalized_a, output=flattened_a)
    _flatten_numeric(prefix="", payload=normalized_b, output=flattened_b)

    keys = sorted(set(flattened_a.keys()) | set(flattened_b.keys()))
    delta_rows: list[dict[str, Any]] = []
    for key in keys:
        value_a = flattened_a.get(key)
        value_b = flattened_b.get(key)
        delta = None
        if value_a is not None and value_b is not None:
            delta = round(value_b - value_a, 6)
        delta_rows.append(
            {
                "key": key,
                "value_a": value_a,
                "value_b": value_b,
                "delta_b_minus_a": delta,
            }
        )

    return {
        "run_a": normalized_a,
        "run_b": normalized_b,
        "delta": delta_rows,
    }


def _normalize_metrics(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {"timings": {}, "usage": {}, "usage_normalized": {}, "cost": {}}

    return {
        "timings": _dict_or_empty(value.get("timings"), {}),
        "usage": _dict_or_empty(value.get("usage"), {}),
        "usage_normalized": _dict_or_empty(value.get("usage_normalized"), {}),
        "cost": _dict_or_empty(value.get("cost"), {}),
    }


def _flatten_numeric(*, prefix: str, payload: Any, output: dict[str, float]) -> None:
    if not isinstance(payload, dict):
        return

    for key in sorted(payload.keys()):
        value = payload[key]
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            _flatten_numeric(prefix=full_key, payload=value, output=output)
            continue

        parsed = _to_float_or_none(value)
        if parsed is not None:
            output[full_key] = parsed


def _to_float_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _dict_or_empty(value: Any, fallback: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return fallback


def _meta_value(snapshot: dict[str, Any], key: str) -> str:
    run_meta = snapshot.get("run")
    if not isinstance(run_meta, dict):
        return ""
    return str(run_meta.get(key) or "")


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _to_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
