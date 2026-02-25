from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.storage.artifacts import ArtifactsManager
from app.storage.db import connection, init_db
from app.storage.models import RunRecord, RunStatus, SessionRecord


class StorageRepo:
    def __init__(
        self,
        db_path: Path | str,
        artifacts_manager: ArtifactsManager | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.artifacts_manager = artifacts_manager or ArtifactsManager(
            self.db_path.parent
        )
        init_db(self.db_path)

    def create_session(self, session_id: str | None = None) -> SessionRecord:
        session_identifier = session_id or str(uuid4())
        created_at = _utc_now()

        with connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sessions (session_id, created_at)
                VALUES (?, ?)
                """,
                (session_identifier, created_at),
            )
            row = conn.execute(
                "SELECT session_id, created_at FROM sessions WHERE session_id = ?",
                (session_identifier,),
            ).fetchone()

        if row is None:
            raise RuntimeError("Failed to create or load session")

        return SessionRecord(
            session_id=str(row["session_id"]),
            created_at=str(row["created_at"]),
        )

    def create_run(
        self,
        *,
        session_id: str,
        provider: str,
        model: str,
        prompt_name: str,
        prompt_version: str,
        schema_version: str,
        status: RunStatus = "created",
        openai_reasoning_effort: str | None = None,
        gemini_thinking_level: str | None = None,
        artifacts_root_path: str | None = None,
    ) -> RunRecord:
        run_id = str(uuid4())
        created_at = _utc_now()

        if artifacts_root_path is None:
            artifacts = self.artifacts_manager.create_run_artifacts(
                session_id=session_id,
                run_id=run_id,
            )
        else:
            artifacts = self.artifacts_manager.ensure_run_structure(artifacts_root_path)

        artifacts_path = str(artifacts.artifacts_root_path.resolve())

        self.create_session(session_id=session_id)

        with connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    run_id,
                    session_id,
                    created_at,
                    provider,
                    model,
                    openai_reasoning_effort,
                    gemini_thinking_level,
                    prompt_name,
                    prompt_version,
                    schema_version,
                    status,
                    artifacts_root_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    session_id,
                    created_at,
                    provider,
                    model,
                    openai_reasoning_effort,
                    gemini_thinking_level,
                    prompt_name,
                    prompt_version,
                    schema_version,
                    status,
                    artifacts_path,
                ),
            )

        run = self.get_run(run_id)
        if run is None:
            raise RuntimeError("Failed to create run")

        return run

    def update_run_status(
        self,
        *,
        run_id: str,
        status: RunStatus,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        with connection(self.db_path) as conn:
            result = conn.execute(
                """
                UPDATE runs
                SET status = ?, error_code = ?, error_message = ?
                WHERE run_id = ?
                """,
                (status, error_code, error_message, run_id),
            )

        if result.rowcount == 0:
            raise KeyError(f"Run not found: {run_id}")

    def get_run(self, run_id: str) -> RunRecord | None:
        with connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    run_id,
                    session_id,
                    created_at,
                    provider,
                    model,
                    openai_reasoning_effort,
                    gemini_thinking_level,
                    prompt_name,
                    prompt_version,
                    schema_version,
                    status,
                    error_code,
                    error_message,
                    artifacts_root_path
                FROM runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()

        if row is None:
            return None

        return RunRecord(
            run_id=str(row["run_id"]),
            session_id=str(row["session_id"]),
            created_at=str(row["created_at"]),
            provider=str(row["provider"]),
            model=str(row["model"]),
            openai_reasoning_effort=_to_optional_str(row["openai_reasoning_effort"]),
            gemini_thinking_level=_to_optional_str(row["gemini_thinking_level"]),
            prompt_name=str(row["prompt_name"]),
            prompt_version=str(row["prompt_version"]),
            schema_version=str(row["schema_version"]),
            status=str(row["status"]),
            error_code=_to_optional_str(row["error_code"]),
            error_message=_to_optional_str(row["error_message"]),
            artifacts_root_path=str(row["artifacts_root_path"]),
        )


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _to_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
