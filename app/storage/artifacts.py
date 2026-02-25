from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RunArtifacts:
    artifacts_root_path: Path
    logs_dir: Path
    run_log_path: Path


class ArtifactsManager:
    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)

    def build_run_root(self, *, session_id: str, run_id: str) -> Path:
        return self.data_dir / "sessions" / session_id / "runs" / run_id

    def create_run_artifacts(self, *, session_id: str, run_id: str) -> RunArtifacts:
        root_path = self.build_run_root(session_id=session_id, run_id=run_id)
        return self.ensure_run_structure(root_path)

    def ensure_run_structure(self, artifacts_root_path: Path | str) -> RunArtifacts:
        root_path = Path(artifacts_root_path)
        logs_dir = root_path / "logs"

        logs_dir.mkdir(parents=True, exist_ok=True)

        run_log_path = logs_dir / "run.log"
        run_log_path.touch(exist_ok=True)

        return RunArtifacts(
            artifacts_root_path=root_path,
            logs_dir=logs_dir,
            run_log_path=run_log_path,
        )
