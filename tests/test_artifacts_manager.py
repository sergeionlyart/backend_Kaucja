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
