from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agentic.scenario2_verifier import (
    build_scenario2_review_payload,
    build_scenario2_verifier_gate_payload,
    normalize_scenario2_verifier_policy,
)
from app.pipeline.scenario_router import SCENARIO_1_ID, SCENARIO_2_ID
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
    scenario_id = _manifest_scenario_id(manifest=manifest)

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
    scenario2_payload, scenario2_warning = _load_scenario2_snapshot(
        manifest=manifest,
        artifacts_root=artifacts_root,
        scenario_id=scenario_id,
    )
    if scenario2_warning is not None:
        warnings.append(scenario2_warning)

    review_status = _snapshot_review_status(
        scenario_id=scenario_id,
        manifest=manifest,
        scenario2_payload=scenario2_payload,
    )

    return {
        "run_id": run.run_id,
        "exists": True,
        "scenario_id": scenario_id,
        "review_status": review_status,
        "run": _run_identity(run),
        "artifacts_root_path": artifacts_root,
        "checklist": checklist,
        "critical_gaps_summary": critical_gaps_summary,
        "next_questions_to_user": next_questions_to_user,
        "scenario2": scenario2_payload,
        "metrics": _metrics_payload(run=run, manifest=manifest),
        "warnings": sorted(set(warnings)),
    }


def build_run_diff(
    *,
    snapshot_a: dict[str, Any],
    snapshot_b: dict[str, Any],
) -> dict[str, Any]:
    comparison_mode = _comparison_mode(snapshot_a=snapshot_a, snapshot_b=snapshot_b)
    if comparison_mode == "scenario1_pair":
        rows, counts = _scenario1_checklist_diff(
            snapshot_a=snapshot_a,
            snapshot_b=snapshot_b,
        )
        critical_gaps_diff = _compare_string_lists(
            left=snapshot_a.get("critical_gaps_summary"),
            right=snapshot_b.get("critical_gaps_summary"),
        )
        next_questions_diff = _compare_string_lists(
            left=snapshot_a.get("next_questions_to_user"),
            right=snapshot_b.get("next_questions_to_user"),
        )
        scenario2_diff: dict[str, Any] | None = None
    elif comparison_mode == "scenario2_pair":
        rows = []
        counts = _empty_summary_counts()
        critical_gaps_diff = _empty_string_list_diff()
        next_questions_diff = _empty_string_list_diff()
        scenario2_diff = _compare_scenario2_payloads(
            payload_a=snapshot_a.get("scenario2"),
            payload_b=snapshot_b.get("scenario2"),
        )
    else:
        rows = []
        counts = _empty_summary_counts()
        critical_gaps_diff = _empty_string_list_diff()
        next_questions_diff = _empty_string_list_diff()
        scenario2_diff = None

    metadata = {
        "provider_changed": _meta_value(snapshot_a, "provider")
        != _meta_value(snapshot_b, "provider"),
        "model_changed": _meta_value(snapshot_a, "model")
        != _meta_value(snapshot_b, "model"),
        "prompt_version_changed": _meta_value(snapshot_a, "prompt_version")
        != _meta_value(snapshot_b, "prompt_version"),
        "scenario_changed": _snapshot_scenario_id(snapshot_a)
        != _snapshot_scenario_id(snapshot_b),
        "review_status_changed": _snapshot_review_status_value(snapshot_a)
        != _snapshot_review_status_value(snapshot_b),
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
            "scenario_id": _snapshot_scenario_id(snapshot_a),
            "review_status": _snapshot_review_status_value(snapshot_a),
        },
        "run_b": {
            "run_id": snapshot_b.get("run_id"),
            "exists": bool(snapshot_b.get("exists")),
            "run": (
                snapshot_b.get("run") if isinstance(snapshot_b.get("run"), dict) else {}
            ),
            "artifacts_root_path": str(snapshot_b.get("artifacts_root_path") or ""),
            "warnings": _to_string_list(snapshot_b.get("warnings")),
            "scenario_id": _snapshot_scenario_id(snapshot_b),
            "review_status": _snapshot_review_status_value(snapshot_b),
        },
        "metadata": metadata,
        "scenario_comparison": {
            "mode": comparison_mode,
            "scenario_id_a": _snapshot_scenario_id(snapshot_a),
            "scenario_id_b": _snapshot_scenario_id(snapshot_b),
            "checklist_applicable": comparison_mode == "scenario1_pair",
            "compatible": comparison_mode != "mixed",
        },
        "scenario2_diff": scenario2_diff,
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
        "scenario_id": "",
        "run": {},
        "artifacts_root_path": "",
        "review_status": "not_applicable",
        "checklist": [],
        "critical_gaps_summary": [],
        "next_questions_to_user": [],
        "scenario2": None,
        "metrics": {"timings": {}, "usage": {}, "usage_normalized": {}, "cost": {}},
        "warnings": [reason],
    }


def _scenario1_checklist_diff(
    *,
    snapshot_a: dict[str, Any],
    snapshot_b: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    checklist_a = _checklist_map(snapshot_a.get("checklist"))
    checklist_b = _checklist_map(snapshot_b.get("checklist"))
    item_ids = sorted(set(checklist_a.keys()) | set(checklist_b.keys()))

    rows: list[dict[str, Any]] = []
    counts = _empty_summary_counts()

    for item_id in item_ids:
        item_a = checklist_a.get(item_id)
        item_b = checklist_b.get(item_id)
        row = _compare_checklist_item(item_id=item_id, item_a=item_a, item_b=item_b)
        rows.append(row)
        change = str(row.get("change") or "")
        if change in counts:
            counts[change] += 1

    return rows, counts


def _comparison_mode(*, snapshot_a: dict[str, Any], snapshot_b: dict[str, Any]) -> str:
    if not bool(snapshot_a.get("exists")) or not bool(snapshot_b.get("exists")):
        return "scenario1_pair"

    scenario_id_a = _snapshot_scenario_id(snapshot_a)
    scenario_id_b = _snapshot_scenario_id(snapshot_b)
    if scenario_id_a == SCENARIO_2_ID and scenario_id_b == SCENARIO_2_ID:
        return "scenario2_pair"
    if scenario_id_a != scenario_id_b:
        return "mixed"
    return "scenario1_pair"


def _snapshot_scenario_id(snapshot: dict[str, Any]) -> str:
    scenario_id = str(snapshot.get("scenario_id") or "").strip()
    if scenario_id == SCENARIO_2_ID:
        return SCENARIO_2_ID
    return SCENARIO_1_ID


def _empty_summary_counts() -> dict[str, int]:
    return {
        "improved": 0,
        "regressed": 0,
        "unchanged": 0,
        "added": 0,
        "removed": 0,
    }


def _empty_string_list_diff() -> dict[str, list[str]]:
    return {"only_in_a": [], "only_in_b": [], "common": []}


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


def _load_scenario2_snapshot(
    *,
    manifest: dict[str, Any] | None,
    artifacts_root: str,
    scenario_id: str,
) -> tuple[dict[str, Any] | None, str | None]:
    if scenario_id != SCENARIO_2_ID:
        return None, None

    trace_path = _scenario2_trace_path(manifest=manifest, artifacts_root=artifacts_root)
    if trace_path is None:
        return _scenario2_snapshot_from_trace(trace_payload=None, manifest=manifest), (
            "Scenario 2 trace path is not configured."
        )

    trace_payload, error = safe_read_json(trace_path)
    if error is not None:
        return _scenario2_snapshot_from_trace(trace_payload=None, manifest=manifest), (
            error
        )
    if not isinstance(trace_payload, dict):
        return _scenario2_snapshot_from_trace(trace_payload=None, manifest=manifest), (
            "Scenario 2 trace payload is not a JSON object."
        )
    return _scenario2_snapshot_from_trace(
        trace_payload=trace_payload, manifest=manifest
    ), None


def _scenario2_trace_path(
    *,
    manifest: dict[str, Any] | None,
    artifacts_root: str,
) -> Path | None:
    if isinstance(manifest, dict):
        artifacts = manifest.get("artifacts")
        if isinstance(artifacts, dict):
            llm = artifacts.get("llm")
            if isinstance(llm, dict):
                trace_path = llm.get("trace_path")
                if isinstance(trace_path, str) and trace_path.strip():
                    return Path(trace_path)

    if not artifacts_root:
        return None
    return Path(artifacts_root) / "llm" / "scenario2_trace.json"


def _scenario2_snapshot_from_trace(
    *,
    trace_payload: dict[str, Any] | None,
    manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    diagnostics = (
        trace_payload.get("diagnostics")
        if isinstance(trace_payload, dict)
        and isinstance(trace_payload.get("diagnostics"), dict)
        else {}
    )
    return {
        "runner_mode": _string_value(
            _trace_or_manifest_runner_mode(
                trace_payload=trace_payload, manifest=manifest
            )
        ),
        "review_status": _scenario2_review_status(
            manifest=manifest,
            diagnostics=diagnostics,
        ),
        "verifier_policy": _scenario2_verifier_policy(
            manifest=manifest,
            diagnostics=diagnostics,
        ),
        "verifier_gate_status": _scenario2_verifier_gate_status(
            manifest=manifest,
            diagnostics=diagnostics,
            llm_executed=_trace_or_manifest_llm_executed(
                trace_payload=trace_payload,
                manifest=manifest,
            ),
        ),
        "llm_executed": _trace_or_manifest_llm_executed(
            trace_payload=trace_payload,
            manifest=manifest,
        ),
        "fragment_grounding_status": _string_value(
            diagnostics.get("fragment_grounding_status")
        ),
        "citation_binding_status": _string_value(
            diagnostics.get("citation_binding_status")
        ),
        "verifier_status": _scenario2_verifier_status(
            diagnostics=diagnostics,
            llm_executed=_trace_or_manifest_llm_executed(
                trace_payload=trace_payload,
                manifest=manifest,
            ),
        ),
        "citation_format_status": _scenario2_citation_format_status(
            diagnostics=diagnostics,
            llm_executed=_trace_or_manifest_llm_executed(
                trace_payload=trace_payload,
                manifest=manifest,
            ),
        ),
        "fetch_fragments_called": _bool_or_none(
            diagnostics.get("fetch_fragments_called")
        ),
        "fetch_fragments_returned_usable_fragments": _bool_or_none(
            diagnostics.get("fetch_fragments_returned_usable_fragments")
        ),
        "repair_turn_used": _bool_or_none(diagnostics.get("repair_turn_used")),
        "tool_round_count": _int_or_zero(
            (
                trace_payload.get("tool_round_count")
                if isinstance(trace_payload, dict)
                else diagnostics.get("tool_round_count")
            )
        ),
        "fetched_fragment_citations": _to_string_list(
            diagnostics.get("fetched_fragment_citations")
        ),
        "fetched_fragment_doc_uids": _to_string_list(
            diagnostics.get("fetched_fragment_doc_uids")
        ),
        "fetched_fragment_source_hashes": _to_string_list(
            diagnostics.get("fetched_fragment_source_hashes")
        ),
        "fetched_fragment_quote_checksums": _scenario2_quote_checksums(
            diagnostics=diagnostics
        ),
        "missing_sections": _to_string_list(diagnostics.get("missing_sections")),
        "legal_citation_count": _int_or_zero(diagnostics.get("legal_citation_count")),
        "user_doc_citation_count": _int_or_zero(
            diagnostics.get("user_doc_citation_count")
        ),
        "citations_in_analysis_sections": _bool_or_none(
            diagnostics.get("citations_in_analysis_sections")
        ),
        "sources_section_present": _bool_or_none(
            diagnostics.get("sources_section_present")
        ),
        "fetched_sources_referenced": _bool_or_none(
            diagnostics.get("fetched_sources_referenced")
        ),
    }


def _trace_or_manifest_runner_mode(
    *,
    trace_payload: dict[str, Any] | None,
    manifest: dict[str, Any] | None,
) -> str:
    if isinstance(trace_payload, dict):
        value = trace_payload.get("runner_mode")
        if isinstance(value, str) and value.strip():
            return value
    llm = _manifest_llm_artifacts(manifest=manifest)
    return str(llm.get("runner_mode") or "")


def _trace_or_manifest_llm_executed(
    *,
    trace_payload: dict[str, Any] | None,
    manifest: dict[str, Any] | None,
) -> bool | None:
    if isinstance(trace_payload, dict):
        value = trace_payload.get("llm_executed")
        if isinstance(value, bool):
            return value
    llm = _manifest_llm_artifacts(manifest=manifest)
    value = llm.get("llm_executed")
    if isinstance(value, bool):
        return value
    return None


def _manifest_llm_artifacts(*, manifest: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        return {}
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return {}
    llm = artifacts.get("llm")
    if not isinstance(llm, dict):
        return {}
    return llm


def _manifest_scenario_id(*, manifest: dict[str, Any] | None) -> str:
    if not isinstance(manifest, dict):
        return SCENARIO_1_ID
    inputs = manifest.get("inputs")
    if not isinstance(inputs, dict):
        return SCENARIO_1_ID
    scenario_id = str(inputs.get("scenario_id") or "").strip()
    if scenario_id == SCENARIO_2_ID:
        return SCENARIO_2_ID
    return SCENARIO_1_ID


def _snapshot_review_status(
    *,
    scenario_id: str,
    manifest: dict[str, Any] | None,
    scenario2_payload: dict[str, Any] | None,
) -> str:
    if scenario_id != SCENARIO_2_ID:
        return "not_applicable"

    direct = _manifest_review_status(manifest=manifest)
    if direct:
        return direct

    if isinstance(scenario2_payload, dict):
        direct = _string_value(scenario2_payload.get("review_status"))
        if direct:
            return direct
    return "not_applicable"


def _snapshot_review_status_value(snapshot: dict[str, Any]) -> str:
    value = _string_value(snapshot.get("review_status"))
    if value:
        return value
    return "not_applicable"


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


def _compare_scenario2_payloads(
    *,
    payload_a: Any,
    payload_b: Any,
) -> dict[str, Any]:
    normalized_a = payload_a if isinstance(payload_a, dict) else {}
    normalized_b = payload_b if isinstance(payload_b, dict) else {}

    tool_round_a = _int_or_zero(normalized_a.get("tool_round_count"))
    tool_round_b = _int_or_zero(normalized_b.get("tool_round_count"))

    return {
        "review_status": _compare_scalar(
            normalized_a.get("review_status"),
            normalized_b.get("review_status"),
        ),
        "verifier_policy": _compare_scalar(
            normalized_a.get("verifier_policy"),
            normalized_b.get("verifier_policy"),
        ),
        "verifier_gate_status": _compare_scalar(
            normalized_a.get("verifier_gate_status"),
            normalized_b.get("verifier_gate_status"),
        ),
        "runner_mode": _compare_scalar(
            normalized_a.get("runner_mode"),
            normalized_b.get("runner_mode"),
        ),
        "llm_executed": _compare_scalar(
            _bool_or_none(normalized_a.get("llm_executed")),
            _bool_or_none(normalized_b.get("llm_executed")),
        ),
        "fragment_grounding_status": _compare_scalar(
            normalized_a.get("fragment_grounding_status"),
            normalized_b.get("fragment_grounding_status"),
        ),
        "citation_binding_status": _compare_scalar(
            normalized_a.get("citation_binding_status"),
            normalized_b.get("citation_binding_status"),
        ),
        "verifier_status": _compare_scalar(
            normalized_a.get("verifier_status"),
            normalized_b.get("verifier_status"),
        ),
        "citation_format_status": _compare_scalar(
            normalized_a.get("citation_format_status"),
            normalized_b.get("citation_format_status"),
        ),
        "fetch_fragments_called": _compare_scalar(
            _bool_or_none(normalized_a.get("fetch_fragments_called")),
            _bool_or_none(normalized_b.get("fetch_fragments_called")),
        ),
        "fetch_fragments_returned_usable_fragments": _compare_scalar(
            _bool_or_none(
                normalized_a.get("fetch_fragments_returned_usable_fragments")
            ),
            _bool_or_none(
                normalized_b.get("fetch_fragments_returned_usable_fragments")
            ),
        ),
        "repair_turn_used": _compare_scalar(
            _bool_or_none(normalized_a.get("repair_turn_used")),
            _bool_or_none(normalized_b.get("repair_turn_used")),
        ),
        "sources_section_present": _compare_scalar(
            _bool_or_none(normalized_a.get("sources_section_present")),
            _bool_or_none(normalized_b.get("sources_section_present")),
        ),
        "fetched_sources_referenced": _compare_scalar(
            _bool_or_none(normalized_a.get("fetched_sources_referenced")),
            _bool_or_none(normalized_b.get("fetched_sources_referenced")),
        ),
        "legal_citation_count": _compare_scalar(
            _int_or_zero(normalized_a.get("legal_citation_count")),
            _int_or_zero(normalized_b.get("legal_citation_count")),
        ),
        "user_doc_citation_count": _compare_scalar(
            _int_or_zero(normalized_a.get("user_doc_citation_count")),
            _int_or_zero(normalized_b.get("user_doc_citation_count")),
        ),
        "citations_in_analysis_sections": _compare_scalar(
            _bool_or_none(normalized_a.get("citations_in_analysis_sections")),
            _bool_or_none(normalized_b.get("citations_in_analysis_sections")),
        ),
        "tool_round_count": {
            "value_a": tool_round_a,
            "value_b": tool_round_b,
            "delta_b_minus_a": tool_round_b - tool_round_a,
            "changed": tool_round_a != tool_round_b,
        },
        "missing_sections": _compare_string_lists(
            left=normalized_a.get("missing_sections"),
            right=normalized_b.get("missing_sections"),
        ),
        "fetched_fragment_citations": _compare_string_lists(
            left=normalized_a.get("fetched_fragment_citations"),
            right=normalized_b.get("fetched_fragment_citations"),
        ),
        "fetched_fragment_doc_uids": _compare_string_lists(
            left=normalized_a.get("fetched_fragment_doc_uids"),
            right=normalized_b.get("fetched_fragment_doc_uids"),
        ),
        "fetched_fragment_source_hashes": _compare_string_lists(
            left=normalized_a.get("fetched_fragment_source_hashes"),
            right=normalized_b.get("fetched_fragment_source_hashes"),
        ),
        "fetched_fragment_quote_checksums": _compare_string_lists(
            left=normalized_a.get("fetched_fragment_quote_checksums"),
            right=normalized_b.get("fetched_fragment_quote_checksums"),
        ),
    }


def _scenario2_quote_checksums(*, diagnostics: dict[str, Any]) -> list[str]:
    direct = _to_string_list(diagnostics.get("fetched_fragment_quote_checksums"))
    if direct:
        return direct

    ledger = diagnostics.get("fetched_fragment_ledger")
    if not isinstance(ledger, list):
        return []

    checksums: list[str] = []
    for item in ledger:
        if not isinstance(item, dict):
            continue
        value = _string_value(item.get("quote_checksum"))
        if value:
            checksums.append(value)
    return sorted(set(checksums))


def _scenario2_verifier_status(
    *,
    diagnostics: dict[str, Any],
    llm_executed: bool | None,
) -> str:
    direct = _string_value(diagnostics.get("verifier_status"))
    if direct:
        return direct
    if llm_executed is False:
        return "not_applicable"
    return ""


def _manifest_review_status(*, manifest: dict[str, Any] | None) -> str:
    if not isinstance(manifest, dict):
        return ""

    review = manifest.get("review")
    if isinstance(review, dict):
        value = _string_value(review.get("status"))
        if value:
            return value

    return _string_value(manifest.get("review_status"))


def _scenario2_review_status(
    *,
    manifest: dict[str, Any] | None,
    diagnostics: dict[str, Any],
) -> str:
    direct = _manifest_review_status(manifest=manifest)
    if direct:
        return direct

    derived = build_scenario2_review_payload(
        verifier_status=_string_value(diagnostics.get("verifier_status")),
        verifier_warnings=_to_string_list(diagnostics.get("verifier_warnings")),
    )
    return _string_value(derived.get("status"))


def _scenario2_verifier_policy(
    *,
    manifest: dict[str, Any] | None,
    diagnostics: dict[str, Any],
) -> str:
    direct = _manifest_verifier_policy(manifest=manifest)
    if direct:
        return direct

    direct = _string_value(diagnostics.get("verifier_policy"))
    if direct:
        return normalize_scenario2_verifier_policy(direct)
    return normalize_scenario2_verifier_policy("informational")


def _scenario2_verifier_gate_status(
    *,
    manifest: dict[str, Any] | None,
    diagnostics: dict[str, Any],
    llm_executed: bool | None,
) -> str:
    direct = _manifest_verifier_gate_status(manifest=manifest)
    if direct:
        return direct

    direct = _string_value(diagnostics.get("verifier_gate_status"))
    if direct:
        return direct

    derived = build_scenario2_verifier_gate_payload(
        verifier_policy=_scenario2_verifier_policy(
            manifest=manifest,
            diagnostics=diagnostics,
        ),
        verifier_status=_string_value(diagnostics.get("verifier_status")),
        llm_executed=llm_executed,
        verifier_warnings=_to_string_list(diagnostics.get("verifier_warnings")),
    )
    return _string_value(derived.get("status"))


def _manifest_verifier_policy(*, manifest: dict[str, Any] | None) -> str:
    if not isinstance(manifest, dict):
        return ""
    value = _string_value(manifest.get("verifier_policy"))
    if value:
        return normalize_scenario2_verifier_policy(value)
    return ""


def _manifest_verifier_gate_status(*, manifest: dict[str, Any] | None) -> str:
    if not isinstance(manifest, dict):
        return ""

    verifier_gate = manifest.get("verifier_gate")
    if isinstance(verifier_gate, dict):
        value = _string_value(verifier_gate.get("status"))
        if value:
            return value

    return _string_value(manifest.get("verifier_gate_status"))


def _scenario2_citation_format_status(
    *,
    diagnostics: dict[str, Any],
    llm_executed: bool | None,
) -> str:
    direct = _string_value(diagnostics.get("citation_format_status"))
    if direct:
        return direct
    if llm_executed is False:
        return "not_applicable"
    return ""


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


def _compare_scalar(value_a: Any, value_b: Any) -> dict[str, Any]:
    return {
        "value_a": value_a,
        "value_b": value_b,
        "changed": value_a != value_b,
    }


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _int_or_zero(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
