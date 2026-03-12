from __future__ import annotations

from pathlib import Path

from app.agentic.case_workspace_store import MongoCaseWorkspaceStore
from tests.fake_mongo_runtime import FakeMongoRuntime


def test_case_workspace_store_keeps_user_docs_separate_from_authoritative_corpus(
    tmp_path: Path,
) -> None:
    runtime = FakeMongoRuntime(collections={})
    store = MongoCaseWorkspaceStore(runtime=runtime)
    case_id = "session-001"
    file_one = tmp_path / "lease.pdf"
    file_one.write_bytes(b"%PDF-1.4 lease")

    store.ensure_workspace(case_id=case_id)
    records = store.register_case_documents(case_id=case_id, input_paths=[file_one])
    store.ensure_case_facts_slot(case_id=case_id)
    store.record_analysis_run(
        case_id=case_id,
        run_id="run-001",
        session_id=case_id,
        scenario_id="scenario_2",
        status="completed",
        review_status="passed",
        verifier_gate_status="passed",
        artifacts_root_path="/tmp/artifacts",
        diagnostics={"backend": "mongo"},
    )

    assert len(records) == 1
    workspace = runtime.load_collection("case_workspaces")[0]
    assert workspace["case_id"] == case_id
    assert workspace["claim_amount"] is None
    assert workspace["currency"] is None
    assert workspace["lease_start"] is None
    assert workspace["lease_end"] is None
    assert workspace["move_out_date"] is None
    assert workspace["deposit_return_due_date"] is None
    assert runtime.load_collection("case_documents")[0]["case_id"] == case_id
    case_fact = runtime.load_collection("case_facts")[0]
    assert case_fact["case_id"] == case_id
    assert case_fact["fact_type"] == "facts_pending"
    assert case_fact["technical_placeholder"] is True
    assert case_fact["value"]["status"] == "pending_extraction"
    analysis_run = runtime.load_collection("analysis_runs")[0]
    assert analysis_run["scenario_id"] == "scenario_2"
    assert analysis_run["review_status"] == "passed"
