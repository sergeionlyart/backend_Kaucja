from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agentic.scenario2_verifier import (
    build_scenario2_review_payload,
    build_scenario2_verifier_gate_payload,
)
from app.pipeline.scenario_router import (
    SCENARIO_1_ID,
    SCENARIO_2_ID,
    SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
)
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


def _seed_scenario1_run(
    *,
    repo: StorageRepo,
    session_id: str,
    run_id_suffix: str,
    payload: dict[str, Any],
) -> str:
    run = repo.create_run(
        session_id=session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version=f"v{run_id_suffix}",
        schema_version=f"v{run_id_suffix}",
        status="completed",
    )
    root = Path(run.artifacts_root_path)
    llm_dir = root / "llm"
    llm_dir.mkdir(parents=True, exist_ok=True)
    parsed_path = llm_dir / "response_parsed.json"
    parsed_path.write_text(json.dumps(payload), encoding="utf-8")
    (llm_dir / "response_raw.txt").write_text(json.dumps(payload), encoding="utf-8")
    (root / "run.json").write_text(
        json.dumps(
            {
                "run_id": run.run_id,
                "status": "completed",
                "inputs": {
                    "scenario_id": SCENARIO_1_ID,
                    "provider": run.provider,
                    "model": run.model,
                    "prompt_name": run.prompt_name,
                    "prompt_version": run.prompt_version,
                },
                "artifacts": {"llm": {}},
                "metrics": {
                    "timings": {"t_total_ms": 100.0},
                    "usage": {},
                    "usage_normalized": {"total_tokens": 100},
                    "cost": {"total_cost_usd": 0.1},
                },
                "validation": {"valid": True, "errors": []},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    repo.upsert_llm_output(
        run_id=run.run_id,
        response_json_path=str(parsed_path),
        response_valid=True,
        schema_validation_errors_path=None,
    )
    repo.update_run_metrics(
        run_id=run.run_id,
        timings_json={"t_total_ms": 100.0},
        usage_json={},
        usage_normalized_json={"total_tokens": 100},
        cost_json={"total_cost_usd": 0.1},
    )
    repo.update_run_status(run_id=run.run_id, status="completed")
    return run.run_id


def _seed_scenario2_run(
    *,
    repo: StorageRepo,
    session_id: str,
    prompt_version: str,
    status: str,
    fragment_grounding_status: str,
    citation_binding_status: str,
    fetch_fragments_called: bool,
    fetch_fragments_returned_usable_fragments: bool,
    repair_turn_used: bool,
    tool_round_count: int,
    fetched_fragment_citations: list[str],
    fetched_fragment_doc_uids: list[str],
    fetched_fragment_source_hashes: list[str],
    llm_executed: bool,
    fetched_fragment_quote_checksums: list[str] | None = None,
    verifier_status: str = "not_applicable",
    citation_format_status: str = "not_applicable",
    legal_citation_count: int = 0,
    user_doc_citation_count: int = 0,
    citations_in_analysis_sections: bool | None = None,
    missing_sections: list[str] | None = None,
    sources_section_present: bool | None = None,
    fetched_sources_referenced: bool | None = None,
    review_status: str | None = None,
    verifier_policy: str = "informational",
    verifier_gate_status: str | None = None,
) -> str:
    run = repo.create_run(
        session_id=session_id,
        provider="openai",
        model="gpt-5.4",
        prompt_name="agent_prompt_foundation",
        prompt_version=prompt_version,
        schema_version=prompt_version,
        status=status,
    )
    root = Path(run.artifacts_root_path)
    llm_dir = root / "llm"
    llm_dir.mkdir(parents=True, exist_ok=True)
    review_payload = build_scenario2_review_payload(
        verifier_status=verifier_status,
        verifier_warnings=[],
    )
    if review_status:
        review_payload["status"] = review_status
    verifier_gate_payload = build_scenario2_verifier_gate_payload(
        verifier_policy=verifier_policy,
        verifier_status=verifier_status,
        llm_executed=llm_executed,
        verifier_warnings=[],
    )
    if verifier_gate_status:
        verifier_gate_payload["status"] = verifier_gate_status
    trace_path = llm_dir / "scenario2_trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "response_mode": "plain_text",
                "final_text": f"scenario2-{prompt_version}-{status}",
                "steps": ["scenario2_openai_start", "openai_request"],
                "tool_trace": [
                    {"tool": "search", "status": "ok"},
                    {"tool": "fetch_fragments", "status": "ok"},
                ]
                if fetch_fragments_called
                else [{"tool": "search", "status": "ok"}],
                "diagnostics": {
                    "fragment_grounding_status": fragment_grounding_status,
                    "citation_binding_status": citation_binding_status,
                    "fetch_fragments_called": fetch_fragments_called,
                    "fetch_fragments_returned_usable_fragments": (
                        fetch_fragments_returned_usable_fragments
                    ),
                    "repair_turn_used": repair_turn_used,
                    "tool_usage_counts": {
                        "search": 1,
                        "fetch_fragments": 1 if fetch_fragments_called else 0,
                        "expand_related": 0,
                        "get_provenance": 0,
                    },
                    "fetched_fragment_citations": fetched_fragment_citations,
                    "fetched_fragment_doc_uids": fetched_fragment_doc_uids,
                    "fetched_fragment_source_hashes": fetched_fragment_source_hashes,
                    "fetched_fragment_quote_checksums": (
                        fetched_fragment_quote_checksums or []
                    ),
                    "verifier_status": verifier_status,
                    "citation_format_status": citation_format_status,
                    "legal_citation_count": legal_citation_count,
                    "user_doc_citation_count": user_doc_citation_count,
                    "citations_in_analysis_sections": citations_in_analysis_sections,
                    "missing_sections": missing_sections or [],
                    "sources_section_present": sources_section_present,
                    "fetched_sources_referenced": fetched_sources_referenced,
                    "verifier_policy": verifier_gate_payload["policy"],
                    "verifier_gate_status": verifier_gate_payload["status"],
                },
                "runner_mode": SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
                "llm_executed": llm_executed,
                "tool_round_count": tool_round_count,
                "model": "gpt-5.4",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (llm_dir / "response_raw.txt").write_text(
        f"scenario2-{prompt_version}-{status}",
        encoding="utf-8",
    )

    (root / "run.json").write_text(
        json.dumps(
            {
                "run_id": run.run_id,
                "status": status,
                "inputs": {
                    "scenario_id": SCENARIO_2_ID,
                    "provider": run.provider,
                    "model": run.model,
                    "prompt_name": run.prompt_name,
                    "prompt_version": run.prompt_version,
                },
                "artifacts": {
                    "llm": {
                        "trace_path": str(trace_path.resolve()),
                        "runner_mode": SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
                        "llm_executed": llm_executed,
                    }
                },
                "metrics": {
                    "timings": {"t_total_ms": 50.0 + tool_round_count},
                    "usage": {},
                    "usage_normalized": {"total_tokens": 10 + tool_round_count},
                    "cost": {"total_cost_usd": 0.01 + (tool_round_count / 1000)},
                },
                "validation": {
                    "status": "failed" if status == "failed" else "not_applicable",
                    "errors": [],
                },
                "review_status": review_payload["status"],
                "review": review_payload,
                "verifier_policy": verifier_gate_payload["policy"],
                "verifier_gate_status": verifier_gate_payload["status"],
                "verifier_gate": verifier_gate_payload,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    repo.update_run_metrics(
        run_id=run.run_id,
        timings_json={"t_total_ms": 50.0 + tool_round_count},
        usage_json={},
        usage_normalized_json={"total_tokens": 10 + tool_round_count},
        cost_json={"total_cost_usd": 0.01 + (tool_round_count / 1000)},
    )
    repo.update_run_status(run_id=run.run_id, status=status)
    return run.run_id


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


def test_build_run_snapshot_loads_scenario2_trace_payload(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-scenario2-snapshot")
    run_id = _seed_scenario2_run(
        repo=repo,
        session_id=session.session_id,
        prompt_version="v1.1",
        status="completed",
        fragment_grounding_status="fragments_fetched",
        citation_binding_status="fragments_fetched",
        fetch_fragments_called=True,
        fetch_fragments_returned_usable_fragments=True,
        repair_turn_used=False,
        tool_round_count=2,
        fetched_fragment_citations=["Art. 6 KC"],
        fetched_fragment_doc_uids=["doc-1"],
        fetched_fragment_source_hashes=["sha256:doc-1"],
        fetched_fragment_quote_checksums=["sha256:frag-1"],
        llm_executed=True,
        verifier_status="passed",
        citation_format_status="passed",
        legal_citation_count=2,
        user_doc_citation_count=1,
        citations_in_analysis_sections=True,
        missing_sections=[],
        sources_section_present=True,
        fetched_sources_referenced=True,
    )

    snapshot = build_run_snapshot(repo=repo, run_id=run_id)

    assert snapshot["scenario_id"] == SCENARIO_2_ID
    assert snapshot["review_status"] == "passed"
    assert (
        snapshot["scenario2"]["runner_mode"] == SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP
    )
    assert snapshot["scenario2"]["review_status"] == "passed"
    assert snapshot["scenario2"]["verifier_policy"] == "informational"
    assert snapshot["scenario2"]["verifier_gate_status"] == "passed"
    assert snapshot["scenario2"]["fragment_grounding_status"] == "fragments_fetched"
    assert snapshot["scenario2"]["fetched_fragment_citations"] == ["Art. 6 KC"]
    assert snapshot["scenario2"]["fetched_fragment_quote_checksums"] == [
        "sha256:frag-1"
    ]
    assert snapshot["scenario2"]["verifier_status"] == "passed"
    assert snapshot["scenario2"]["citation_format_status"] == "passed"
    assert snapshot["scenario2"]["legal_citation_count"] == 2
    assert snapshot["scenario2"]["user_doc_citation_count"] == 1
    assert snapshot["scenario2"]["citations_in_analysis_sections"] is True
    assert snapshot["scenario2"]["fetched_sources_referenced"] is True


def test_compare_runs_scenario2_success_vs_success(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-scenario2-compare")
    run_a = _seed_scenario2_run(
        repo=repo,
        session_id=session.session_id,
        prompt_version="v1.1-a",
        status="completed",
        fragment_grounding_status="fragments_fetched",
        citation_binding_status="fragments_fetched",
        fetch_fragments_called=True,
        fetch_fragments_returned_usable_fragments=True,
        repair_turn_used=False,
        tool_round_count=1,
        fetched_fragment_citations=["Art. 6 KC"],
        fetched_fragment_doc_uids=["doc-1"],
        fetched_fragment_source_hashes=["sha256:doc-1"],
        fetched_fragment_quote_checksums=["sha256:frag-1"],
        llm_executed=True,
        verifier_status="passed",
        citation_format_status="passed",
        legal_citation_count=2,
        user_doc_citation_count=1,
        citations_in_analysis_sections=True,
        missing_sections=[],
        sources_section_present=True,
        fetched_sources_referenced=True,
    )
    run_b = _seed_scenario2_run(
        repo=repo,
        session_id=session.session_id,
        prompt_version="v1.1-b",
        status="completed",
        fragment_grounding_status="fragments_fetched",
        citation_binding_status="fragments_fetched",
        fetch_fragments_called=True,
        fetch_fragments_returned_usable_fragments=True,
        repair_turn_used=False,
        tool_round_count=3,
        fetched_fragment_citations=["Art. 6 KC", "Art. 471 KC"],
        fetched_fragment_doc_uids=["doc-1", "doc-2"],
        fetched_fragment_source_hashes=["sha256:doc-1", "sha256:doc-2"],
        fetched_fragment_quote_checksums=["sha256:frag-1", "sha256:frag-2"],
        llm_executed=True,
        verifier_status="warning",
        citation_format_status="warning",
        legal_citation_count=0,
        user_doc_citation_count=1,
        citations_in_analysis_sections=False,
        missing_sections=["Источники"],
        sources_section_present=False,
        fetched_sources_referenced=False,
    )

    diff = compare_runs(repo=repo, run_id_a=run_a, run_id_b=run_b)

    assert diff["scenario_comparison"]["mode"] == "scenario2_pair"
    assert diff["scenario_comparison"]["checklist_applicable"] is False
    assert diff["checklist_diff"] == []
    assert diff["scenario2_diff"]["review_status"]["changed"] is True
    assert diff["scenario2_diff"]["verifier_policy"]["changed"] is False
    assert diff["scenario2_diff"]["verifier_gate_status"] == {
        "value_a": "passed",
        "value_b": "warning_not_blocking",
        "changed": True,
    }
    assert diff["scenario2_diff"]["tool_round_count"]["delta_b_minus_a"] == 2
    assert diff["scenario2_diff"]["fetched_fragment_citations"]["only_in_b"] == [
        "Art. 471 KC"
    ]
    assert diff["scenario2_diff"]["fetched_fragment_quote_checksums"]["only_in_b"] == [
        "sha256:frag-2"
    ]
    assert diff["scenario2_diff"]["verifier_status"]["changed"] is True
    assert diff["scenario2_diff"]["citation_format_status"]["changed"] is True
    assert diff["scenario2_diff"]["legal_citation_count"] == {
        "value_a": 2,
        "value_b": 0,
        "changed": True,
    }
    assert diff["scenario2_diff"]["missing_sections"]["only_in_b"] == ["Источники"]
    assert diff["scenario2_diff"]["fragment_grounding_status"]["changed"] is False


def test_compare_runs_scenario2_success_vs_failure(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-scenario2-failure")
    run_a = _seed_scenario2_run(
        repo=repo,
        session_id=session.session_id,
        prompt_version="v1.1-ok",
        status="completed",
        fragment_grounding_status="fragments_fetched",
        citation_binding_status="fragments_fetched",
        fetch_fragments_called=True,
        fetch_fragments_returned_usable_fragments=True,
        repair_turn_used=False,
        tool_round_count=2,
        fetched_fragment_citations=["Art. 6 KC"],
        fetched_fragment_doc_uids=["doc-1"],
        fetched_fragment_source_hashes=["sha256:doc-1"],
        fetched_fragment_quote_checksums=["sha256:frag-1"],
        llm_executed=True,
        verifier_status="passed",
        citation_format_status="passed",
        legal_citation_count=2,
        user_doc_citation_count=1,
        citations_in_analysis_sections=True,
        missing_sections=[],
        sources_section_present=True,
        fetched_sources_referenced=True,
    )
    run_b = _seed_scenario2_run(
        repo=repo,
        session_id=session.session_id,
        prompt_version="v1.1-failed",
        status="failed",
        fragment_grounding_status="empty_fragments",
        citation_binding_status="empty_fragments",
        fetch_fragments_called=True,
        fetch_fragments_returned_usable_fragments=False,
        repair_turn_used=True,
        tool_round_count=2,
        fetched_fragment_citations=[],
        fetched_fragment_doc_uids=[],
        fetched_fragment_source_hashes=[],
        fetched_fragment_quote_checksums=[],
        llm_executed=True,
        verifier_status="warning",
        citation_format_status="warning",
        legal_citation_count=0,
        user_doc_citation_count=0,
        citations_in_analysis_sections=False,
        missing_sections=["Источники"],
        sources_section_present=False,
        fetched_sources_referenced=False,
    )

    diff = compare_runs(repo=repo, run_id_a=run_a, run_id_b=run_b)

    assert diff["scenario_comparison"]["mode"] == "scenario2_pair"
    assert diff["scenario2_diff"]["review_status"] == {
        "value_a": "passed",
        "value_b": "needs_review",
        "changed": True,
    }
    assert diff["scenario2_diff"]["verifier_policy"]["changed"] is False
    assert diff["scenario2_diff"]["verifier_gate_status"] == {
        "value_a": "passed",
        "value_b": "warning_not_blocking",
        "changed": True,
    }
    assert diff["scenario2_diff"]["fragment_grounding_status"] == {
        "value_a": "fragments_fetched",
        "value_b": "empty_fragments",
        "changed": True,
    }
    assert diff["scenario2_diff"]["repair_turn_used"] == {
        "value_a": False,
        "value_b": True,
        "changed": True,
    }
    assert diff["scenario2_diff"]["fetched_sources_referenced"] == {
        "value_a": True,
        "value_b": False,
        "changed": True,
    }
    assert diff["scenario2_diff"]["citations_in_analysis_sections"] == {
        "value_a": True,
        "value_b": False,
        "changed": True,
    }
    assert diff["scenario2_diff"]["fetched_fragment_doc_uids"]["only_in_a"] == ["doc-1"]


def test_compare_runs_mixed_scenario_comparison_is_honest(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-mixed-compare")
    run_a = _seed_scenario1_run(
        repo=repo,
        session_id=session.session_id,
        run_id_suffix="001",
        payload=_payload(
            checklist=[
                _item(
                    item_id="KAUCJA_PAYMENT_PROOF",
                    status="missing",
                    confidence="low",
                    findings_quote="quote-a",
                    ask="Upload receipt",
                )
            ],
            gaps=["gap-a"],
            questions=["question-a"],
        ),
    )
    run_b = _seed_scenario2_run(
        repo=repo,
        session_id=session.session_id,
        prompt_version="v1.1",
        status="completed",
        fragment_grounding_status="fragments_fetched",
        citation_binding_status="fragments_fetched",
        fetch_fragments_called=True,
        fetch_fragments_returned_usable_fragments=True,
        repair_turn_used=False,
        tool_round_count=1,
        fetched_fragment_citations=["Art. 6 KC"],
        fetched_fragment_doc_uids=["doc-1"],
        fetched_fragment_source_hashes=["sha256:doc-1"],
        fetched_fragment_quote_checksums=["sha256:frag-1"],
        llm_executed=True,
        verifier_status="passed",
        citation_format_status="passed",
        legal_citation_count=2,
        user_doc_citation_count=1,
        citations_in_analysis_sections=True,
        missing_sections=[],
        sources_section_present=True,
        fetched_sources_referenced=True,
    )

    diff = compare_runs(repo=repo, run_id_a=run_a, run_id_b=run_b)

    assert diff["scenario_comparison"]["mode"] == "mixed"
    assert diff["scenario_comparison"]["compatible"] is False
    assert diff["scenario_comparison"]["checklist_applicable"] is False
    assert diff["checklist_diff"] == []
    assert diff["scenario2_diff"] is None
    assert diff["metadata"]["scenario_changed"] is True
    assert diff["run_a"]["review_status"] == "not_applicable"
    assert diff["run_b"]["review_status"] == "passed"


def test_compare_runs_scenario2_strict_policy_diff_is_visible(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-scenario2-strict-compare")
    run_a = _seed_scenario2_run(
        repo=repo,
        session_id=session.session_id,
        prompt_version="v1.1-info",
        status="completed",
        fragment_grounding_status="fragments_fetched",
        citation_binding_status="fragments_fetched",
        fetch_fragments_called=True,
        fetch_fragments_returned_usable_fragments=True,
        repair_turn_used=False,
        tool_round_count=2,
        fetched_fragment_citations=["Art. 6 KC"],
        fetched_fragment_doc_uids=["doc-1"],
        fetched_fragment_source_hashes=["sha256:doc-1"],
        fetched_fragment_quote_checksums=["sha256:frag-1"],
        llm_executed=True,
        verifier_status="warning",
        citation_format_status="warning",
        verifier_policy="informational",
        verifier_gate_status="warning_not_blocking",
    )
    run_b = _seed_scenario2_run(
        repo=repo,
        session_id=session.session_id,
        prompt_version="v1.1-strict",
        status="completed",
        fragment_grounding_status="fragments_fetched",
        citation_binding_status="fragments_fetched",
        fetch_fragments_called=True,
        fetch_fragments_returned_usable_fragments=True,
        repair_turn_used=False,
        tool_round_count=2,
        fetched_fragment_citations=["Art. 6 KC"],
        fetched_fragment_doc_uids=["doc-1"],
        fetched_fragment_source_hashes=["sha256:doc-1"],
        fetched_fragment_quote_checksums=["sha256:frag-1"],
        llm_executed=True,
        verifier_status="warning",
        citation_format_status="warning",
        verifier_policy="strict",
        verifier_gate_status="blocked",
    )

    diff = compare_runs(repo=repo, run_id_a=run_a, run_id_b=run_b)

    assert diff["scenario2_diff"]["verifier_policy"] == {
        "value_a": "informational",
        "value_b": "strict",
        "changed": True,
    }
    assert diff["scenario2_diff"]["verifier_gate_status"] == {
        "value_a": "warning_not_blocking",
        "value_b": "blocked",
        "changed": True,
    }
