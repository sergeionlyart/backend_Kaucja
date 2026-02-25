from __future__ import annotations

from pathlib import Path

from app.storage.artifacts import ArtifactsManager


def test_create_run_artifacts_creates_deterministic_tree(tmp_path: Path) -> None:
    manager = ArtifactsManager(tmp_path / "data")

    artifacts = manager.create_run_artifacts(session_id="s-001", run_id="r-001")

    assert (
        artifacts.artifacts_root_path
        == tmp_path / "data" / "sessions" / "s-001" / "runs" / "r-001"
    )
    assert artifacts.logs_dir == artifacts.artifacts_root_path / "logs"
    assert artifacts.run_log_path == artifacts.logs_dir / "run.log"
    assert artifacts.run_log_path.is_file()


def test_ensure_run_structure_creates_log_for_existing_root(tmp_path: Path) -> None:
    manager = ArtifactsManager(tmp_path / "data")
    root = tmp_path / "data" / "sessions" / "s-002" / "runs" / "r-002"

    artifacts = manager.ensure_run_structure(root)

    assert artifacts.artifacts_root_path == root
    assert artifacts.run_log_path.is_file()


def test_create_document_artifacts_creates_expected_layout(tmp_path: Path) -> None:
    manager = ArtifactsManager(tmp_path / "data")
    run_artifacts = manager.create_run_artifacts(session_id="s-003", run_id="r-003")

    document = manager.create_document_artifacts(
        artifacts_root_path=run_artifacts.artifacts_root_path,
        doc_id="0000001",
    )

    assert document.original_dir.is_dir()
    assert document.ocr_dir.is_dir()
    assert document.pages_dir.is_dir()
    assert document.tables_dir.is_dir()
    assert document.images_dir.is_dir()
    assert document.page_renders_dir.is_dir()


def test_create_llm_artifacts_creates_expected_files(tmp_path: Path) -> None:
    manager = ArtifactsManager(tmp_path / "data")
    run_artifacts = manager.create_run_artifacts(session_id="s-004", run_id="r-004")

    llm_artifacts = manager.create_llm_artifacts(
        artifacts_root_path=run_artifacts.artifacts_root_path
    )

    assert llm_artifacts.llm_dir.is_dir()
    assert llm_artifacts.request_path.name == "request.txt"
    assert llm_artifacts.response_raw_path.name == "response_raw.txt"
    assert llm_artifacts.response_parsed_path.name == "response_parsed.json"
    assert llm_artifacts.validation_path.name == "validation.json"
