from __future__ import annotations

from pathlib import Path

from app.ops.seed_e2e_data import DEFAULT_SESSION_ID, seed_e2e_data
from app.storage.artifacts import ArtifactsManager
from app.storage.repo import StorageRepo


def test_seed_e2e_data_creates_deterministic_history_and_artifacts(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "e2e.sqlite3"
    data_dir = tmp_path / "e2e_data"

    report = seed_e2e_data(
        db_path=db_path,
        data_dir=data_dir,
        session_id=DEFAULT_SESSION_ID,
    )

    assert report["status"] == "ok"
    seeded_runs = report["seeded_runs"]
    assert isinstance(seeded_runs, list)
    assert [item["run_id"] for item in seeded_runs] == ["e2e-run-a", "e2e-run-b"]

    repo = StorageRepo(
        db_path=db_path,
        artifacts_manager=ArtifactsManager(data_dir),
    )
    runs = repo.list_runs(session_id=DEFAULT_SESSION_ID, limit=10)
    assert [run.run_id for run in runs] == ["e2e-run-b", "e2e-run-a"]

    for run_id in ("e2e-run-a", "e2e-run-b"):
        run = repo.get_run(run_id)
        assert run is not None
        root = Path(run.artifacts_root_path)
        assert (root / "run.json").is_file()
        assert (root / "logs" / "run.log").is_file()
        assert (root / "llm" / "response_parsed.json").is_file()
        assert (root / "documents" / "0000001" / "ocr" / "combined.md").is_file()


def test_seed_e2e_data_is_idempotent_for_seeded_runs(tmp_path: Path) -> None:
    db_path = tmp_path / "seed.sqlite3"
    data_dir = tmp_path / "seed_data"

    first = seed_e2e_data(
        db_path=db_path,
        data_dir=data_dir,
        session_id=DEFAULT_SESSION_ID,
    )
    second = seed_e2e_data(
        db_path=db_path,
        data_dir=data_dir,
        session_id=DEFAULT_SESSION_ID,
    )

    first_run_ids = [item["run_id"] for item in first["seeded_runs"]]
    second_run_ids = [item["run_id"] for item in second["seeded_runs"]]

    assert first_run_ids == ["e2e-run-a", "e2e-run-b"]
    assert second_run_ids == ["e2e-run-a", "e2e-run-b"]

    repo = StorageRepo(
        db_path=db_path,
        artifacts_manager=ArtifactsManager(data_dir),
    )
    runs = repo.list_runs(session_id=DEFAULT_SESSION_ID, limit=20)
    assert len(runs) == 2
