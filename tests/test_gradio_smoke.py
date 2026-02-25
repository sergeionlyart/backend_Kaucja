from __future__ import annotations

from pathlib import Path

import gradio as gr

from app.pipeline.orchestrator import FullPipelineResult, OCRDocumentStageResult
from app.storage.repo import StorageRepo
from app.ui.gradio_app import build_app, run_full_pipeline as run_full_pipeline_ui


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
    assert rows[0][0] == "0000001"
    assert rows[1][0] == "0000002"
    assert "gap1" in summary
    assert '"ok": true' in raw_json
    assert "Validation: valid" in validation
    assert "total_tokens" in metrics
