from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.storage.repo import StorageRepo
from app.ui.run_comparison import build_run_diff, build_run_snapshot, compare_runs


def _item(
    *,
    item_id: str,
    status: str,
    confidence: str,
    findings_quote: str,
    ask: str,
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "importance": "critical",
        "status": status,
        "confidence": confidence,
        "findings": [
            {
                "doc_id": "0000001",
                "quote": findings_quote,
                "why_this_quote_matters": "evidence",
            }
        ],
        "request_from_user": {
            "type": "upload_document",
            "ask": ask,
            "examples": ["example"],
        },
    }


def _payload(
    *, checklist: list[dict[str, Any]], gaps: list[str], questions: list[str]
) -> dict[str, Any]:
    return {
        "checklist": checklist,
        "critical_gaps_summary": gaps,
        "next_questions_to_user": questions,
    }


def test_build_run_diff_is_deterministic_and_counts_changes() -> None:
    snapshot_a = {
        "run_id": "run-a",
        "exists": True,
        "run": {
            "provider": "openai",
            "model": "gpt-5.1",
            "prompt_version": "v001",
        },
        "artifacts_root_path": "/tmp/run-a",
        "checklist": [
            _item(
                item_id="CONTRACT_EXISTS",
                status="confirmed",
                confidence="high",
                findings_quote="quote-a1",
                ask="",
            ),
            _item(
                item_id="KAUCJA_PAYMENT_PROOF",
                status="missing",
                confidence="low",
                findings_quote="quote-a2",
                ask="Upload transfer receipt",
            ),
        ],
        "critical_gaps_summary": ["gap-1", "gap-2"],
        "next_questions_to_user": ["q1", "q2"],
        "metrics": {
            "timings": {"t_total_ms": 100.0},
            "usage": {},
            "usage_normalized": {"total_tokens": 100},
            "cost": {"total_cost_usd": 0.2},
        },
        "warnings": [],
    }

    snapshot_b = {
        "run_id": "run-b",
        "exists": True,
        "run": {
            "provider": "google",
            "model": "gemini-3.1-pro-preview",
            "prompt_version": "v002",
        },
        "artifacts_root_path": "/tmp/run-b",
        "checklist": [
            _item(
                item_id="CONTRACT_EXISTS",
                status="confirmed",
                confidence="high",
                findings_quote="quote-b1",
                ask="",
            ),
            _item(
                item_id="KAUCJA_PAYMENT_PROOF",
                status="confirmed",
                confidence="medium",
                findings_quote="quote-b2",
                ask="",
            ),
            _item(
                item_id="MOVE_IN_PROTOCOL",
                status="missing",
                confidence="low",
                findings_quote="quote-b3",
                ask="Upload protocol",
            ),
        ],
        "critical_gaps_summary": ["gap-2", "gap-3"],
        "next_questions_to_user": ["q2", "q3"],
        "metrics": {
            "timings": {"t_total_ms": 80.0},
            "usage": {},
            "usage_normalized": {"total_tokens": 140},
            "cost": {"total_cost_usd": 0.25},
        },
        "warnings": [],
    }

    diff = build_run_diff(snapshot_a=snapshot_a, snapshot_b=snapshot_b)

    assert [row["item_id"] for row in diff["checklist_diff"]] == [
        "CONTRACT_EXISTS",
        "KAUCJA_PAYMENT_PROOF",
        "MOVE_IN_PROTOCOL",
    ]
    assert diff["summary_counts"] == {
        "improved": 1,
        "regressed": 0,
        "unchanged": 1,
        "added": 1,
        "removed": 0,
    }
    assert diff["metadata"]["provider_changed"] is True
    assert diff["metadata"]["prompt_version_changed"] is True
    assert diff["critical_gaps_diff"]["only_in_a"] == ["gap-1"]
    assert diff["critical_gaps_diff"]["only_in_b"] == ["gap-3"]

    metric_delta = {
        row["key"]: row["delta_b_minus_a"] for row in diff["metrics_diff"]["delta"]
    }
    assert metric_delta["usage_normalized.total_tokens"] == 40.0
    assert metric_delta["cost.total_cost_usd"] == 0.05


def test_compare_runs_handles_missing_run_without_crash(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-1")
    run = repo.create_run(
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        schema_version="v001",
        status="completed",
    )

    diff = compare_runs(repo=repo, run_id_a=run.run_id, run_id_b="missing-run")

    assert diff["run_a"]["exists"] is True
    assert diff["run_b"]["exists"] is False
    assert any("not found" in warning for warning in diff["run_b"]["warnings"])


def test_build_run_snapshot_fallback_for_missing_artifacts_and_metrics(
    tmp_path: Path,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-fallback")
    run = repo.create_run(
        session_id=session.session_id,
        provider="google",
        model="gemini-3.1-flash-preview",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v003",
        schema_version="v003",
        status="failed",
    )
    repo.update_run_metrics(
        run_id=run.run_id,
        timings_json={"t_total_ms": 120.0},
        usage_json={"input_tokens": 11},
        usage_normalized_json={"total_tokens": 20},
        cost_json={"total_cost_usd": 0.12},
    )

    snapshot = build_run_snapshot(repo=repo, run_id=run.run_id)

    assert snapshot["exists"] is True
    assert snapshot["run"]["provider"] == "google"
    assert snapshot["run"]["prompt_version"] == "v003"
    assert snapshot["checklist"] == []
    assert snapshot["metrics"]["usage_normalized"]["total_tokens"] == 20
    assert snapshot["warnings"]


def test_compare_runs_handles_different_provider_and_prompt_with_missing_llm_artifacts(
    tmp_path: Path,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-diff")

    run_a = repo.create_run(
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        schema_version="v001",
        status="completed",
    )
    run_b = repo.create_run(
        session_id=session.session_id,
        provider="google",
        model="gemini-3.1-pro-preview",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v002",
        schema_version="v002",
        status="completed",
    )

    diff = compare_runs(repo=repo, run_id_a=run_a.run_id, run_id_b=run_b.run_id)

    assert diff["metadata"]["provider_changed"] is True
    assert diff["metadata"]["model_changed"] is True
    assert diff["metadata"]["prompt_version_changed"] is True
    assert isinstance(diff["checklist_diff"], list)
    assert isinstance(json.dumps(diff, ensure_ascii=False), str)
