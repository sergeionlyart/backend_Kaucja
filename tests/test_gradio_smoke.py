from __future__ import annotations

import json
from pathlib import Path

import gradio as gr

from app.pipeline.orchestrator import FullPipelineResult, OCRDocumentStageResult
from app.storage.run_manifest import init_run_manifest, update_run_manifest
from app.storage.repo import StorageRepo
from app.ui.gradio_app import (
    build_app,
    list_history_rows,
    load_history_run,
    run_full_pipeline as run_full_pipeline_ui,
)


class FakeOrchestrator:
    def run_full_pipeline(self, **kwargs: object) -> FullPipelineResult:
        input_files = kwargs["input_files"]
        assert len(input_files) == 2
        return FullPipelineResult(
            session_id="session-1",
            run_id="run-1",
            run_status="completed",
            documents=[
                OCRDocumentStageResult(
                    doc_id="0000001",
                    ocr_status="ok",
                    pages_count=2,
                    combined_markdown_path="/tmp/doc-1/combined.md",
                    ocr_artifacts_path="/tmp/doc-1/ocr",
                    ocr_error=None,
                ),
                OCRDocumentStageResult(
                    doc_id="0000002",
                    ocr_status="ok",
                    pages_count=3,
                    combined_markdown_path="/tmp/doc-2/combined.md",
                    ocr_artifacts_path="/tmp/doc-2/ocr",
                    ocr_error=None,
                ),
            ],
            critical_gaps_summary=["gap1"],
            next_questions_to_user=["question1"],
            raw_json_text='{"ok": true}',
            parsed_json={"ok": True},
            validation_valid=True,
            validation_errors=[],
            metrics={"usage": {"total_tokens": 10}},
            error_code=None,
            error_message=None,
        )


def test_build_app_returns_blocks(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")

    app = build_app(
        repo=repo,
        orchestrator=FakeOrchestrator(),
        preflight_checker=lambda provider: None,
    )

    assert isinstance(app, gr.Blocks)


def test_run_full_pipeline_ui_returns_outputs(tmp_path: Path) -> None:
    file_one = tmp_path / "one.pdf"
    file_two = tmp_path / "two.pdf"
    file_one.write_bytes(b"one")
    file_two.write_bytes(b"two")

    (
        status,
        session_state,
        run_id,
        session_id,
        artifacts_root,
        rows,
        summary,
        raw_json,
        validation,
        metrics,
    ) = run_full_pipeline_ui(
        orchestrator=FakeOrchestrator(),
        prompt_name="kaucja_gap_analysis",
        current_session_id="",
        uploaded_files=[file_one, file_two],
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        ocr_model="mistral-ocr-latest",
        table_format="html",
        include_image_base64=True,
        openai_reasoning_effort="auto",
        gemini_thinking_level="auto",
        preflight_checker=lambda provider: None,
    )

    assert "run-1" in status
    assert session_state == "session-1"
    assert run_id == "run-1"
    assert session_id == "session-1"
    assert artifacts_root == ""
    assert rows[0][0] == "0000001"
    assert rows[1][0] == "0000002"
    assert "gap1" in summary
    assert '"ok": true' in raw_json
    assert "Validation: valid" in validation
    assert "total_tokens" in metrics


def test_history_load_returns_saved_run_bundle(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-history")
    run = repo.create_run(
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        schema_version="v001",
        status="running",
    )

    run_root = Path(run.artifacts_root_path)
    llm_dir = run_root / "llm"
    llm_dir.mkdir(parents=True, exist_ok=True)
    parsed_payload = {
        "critical_gaps_summary": ["gap-from-history"],
        "next_questions_to_user": ["question-from-history"],
    }
    (llm_dir / "response_raw.txt").write_text(
        json.dumps(parsed_payload),
        encoding="utf-8",
    )
    parsed_path = llm_dir / "response_parsed.json"
    parsed_path.write_text(json.dumps(parsed_payload), encoding="utf-8")
    (llm_dir / "validation.json").write_text(
        json.dumps({"valid": True, "schema_errors": [], "invariant_errors": []}),
        encoding="utf-8",
    )

    doc_ocr_dir = run_root / "documents" / "0000001" / "ocr"
    doc_ocr_dir.mkdir(parents=True, exist_ok=True)
    (doc_ocr_dir / "combined.md").write_text("combined markdown", encoding="utf-8")

    repo.create_document(
        run_id=run.run_id,
        doc_id="0000001",
        original_filename="contract.pdf",
        original_mime="application/pdf",
        original_path=str(
            run_root / "documents" / "0000001" / "original" / "contract.pdf"
        ),
        ocr_status="ok",
        pages_count=1,
        ocr_artifacts_path=str(doc_ocr_dir),
    )
    repo.upsert_llm_output(
        run_id=run.run_id,
        response_json_path=str(parsed_path),
        response_valid=True,
        schema_validation_errors_path=None,
    )
    repo.update_run_metrics(
        run_id=run.run_id,
        timings_json={"t_total_ms": 25.0},
        usage_json={"input_tokens": 12},
        usage_normalized_json={"total_tokens": 20},
        cost_json={"total_cost_usd": 0.002},
    )
    repo.update_run_status(run_id=run.run_id, status="completed")

    init_run_manifest(
        artifacts_root_path=run.artifacts_root_path,
        session_id=run.session_id,
        run_id=run.run_id,
        inputs={
            "provider": run.provider,
            "model": run.model,
            "prompt_name": run.prompt_name,
            "prompt_version": run.prompt_version,
            "schema_version": run.schema_version,
            "ocr_params": {"model": "mistral-ocr-latest"},
            "llm_params": {"openai_reasoning_effort": "auto"},
        },
        artifacts={
            "root": run.artifacts_root_path,
            "run_log": str(run_root / "logs" / "run.log"),
            "documents": [],
            "llm": {},
        },
        status="running",
    )
    update_run_manifest(
        artifacts_root_path=run.artifacts_root_path,
        updates={
            "status": "completed",
            "stages": {
                "ocr": {"status": "completed"},
                "llm": {"status": "completed"},
                "finalize": {"status": "completed"},
            },
            "metrics": {
                "timings": {"t_total_ms": 25.0},
                "usage": {"input_tokens": 12},
                "usage_normalized": {"total_tokens": 20},
                "cost": {"total_cost_usd": 0.002},
            },
            "validation": {"valid": True, "errors": []},
        },
    )

    rows = list_history_rows(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        date_from="",
        date_to="",
        limit=10,
    )
    assert len(rows) == 1
    assert rows[0][0] == run.run_id

    (
        status,
        session_state,
        loaded_run_id,
        session_id,
        artifacts_root,
        ocr_rows,
        summary,
        raw_json,
        validation,
        metrics,
    ) = load_history_run(repo=repo, run_id=run.run_id)

    assert "History loaded." in status
    assert session_state == session.session_id
    assert loaded_run_id == run.run_id
    assert session_id == session.session_id
    assert artifacts_root == run.artifacts_root_path
    assert ocr_rows[0][0] == "0000001"
    assert "gap-from-history" in summary
    assert "critical_gaps_summary" in raw_json
    assert "Validation: valid" in validation
    assert "total_tokens" in metrics
