from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.storage.artifacts import ArtifactsManager
from app.storage.db import connection, init_db
from app.storage.models import (
    DocumentRecord,
    LLMOutputRecord,
    OCRStatus,
    RunBundle,
    RunRecord,
    RunStatus,
    SessionRecord,
)


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

    def update_run_metrics(
        self,
        *,
        run_id: str,
        timings_json: dict[str, Any],
        usage_json: dict[str, Any],
        usage_normalized_json: dict[str, Any],
        cost_json: dict[str, Any],
    ) -> None:
        with connection(self.db_path) as conn:
            result = conn.execute(
                """
                UPDATE runs
                SET
                    timings_json = ?,
                    usage_json = ?,
                    usage_normalized_json = ?,
                    cost_json = ?
                WHERE run_id = ?
                """,
                (
                    _to_json_text(timings_json),
                    _to_json_text(usage_json),
                    _to_json_text(usage_normalized_json),
                    _to_json_text(cost_json),
                    run_id,
                ),
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
                    timings_json,
                    usage_json,
                    usage_normalized_json,
                    cost_json,
                    artifacts_root_path
                FROM runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()

        if row is None:
            return None

        return _row_to_run_record(row)

    def list_runs(
        self,
        *,
        session_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        prompt_version: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
    ) -> list[RunRecord]:
        filters: list[str] = []
        params: list[object] = []

        if session_id is not None and session_id.strip():
            filters.append("session_id = ?")
            params.append(session_id.strip())

        if provider is not None and provider.strip():
            filters.append("provider = ?")
            params.append(provider.strip())

        if model is not None and model.strip():
            filters.append("model = ?")
            params.append(model.strip())

        if prompt_version is not None and prompt_version.strip():
            filters.append("prompt_version = ?")
            params.append(prompt_version.strip())

        normalized_from = _normalize_date_from(date_from)
        if normalized_from is not None:
            filters.append("created_at >= ?")
            params.append(normalized_from)

        normalized_to = _normalize_date_to(date_to)
        if normalized_to is not None:
            filters.append("created_at <= ?")
            params.append(normalized_to)

        query = """
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
                timings_json,
                usage_json,
                usage_normalized_json,
                cost_json,
                artifacts_root_path
            FROM runs
        """
        if filters:
            query += f" WHERE {' AND '.join(filters)}"
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(max(limit, 1))

        with connection(self.db_path) as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        return [_row_to_run_record(row) for row in rows]

    def get_run_bundle(self, run_id: str) -> RunBundle | None:
        run = self.get_run(run_id)
        if run is None:
            return None

        documents = self.list_documents(run_id=run_id)
        llm_output = self.get_llm_output(run_id=run_id)
        return RunBundle(run=run, documents=documents, llm_output=llm_output)

    def create_document(
        self,
        *,
        run_id: str,
        doc_id: str,
        original_filename: str,
        original_mime: str | None,
        original_path: str,
        ocr_status: OCRStatus = "pending",
        ocr_model: str | None = None,
        pages_count: int | None = None,
        ocr_artifacts_path: str | None = None,
        ocr_error: str | None = None,
    ) -> DocumentRecord:
        with connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    run_id,
                    doc_id,
                    original_filename,
                    original_mime,
                    original_path,
                    ocr_status,
                    ocr_model,
                    pages_count,
                    ocr_artifacts_path,
                    ocr_error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    doc_id,
                    original_filename,
                    original_mime,
                    original_path,
                    ocr_status,
                    ocr_model,
                    pages_count,
                    ocr_artifacts_path,
                    ocr_error,
                ),
            )
            row = conn.execute(
                """
                SELECT
                    id,
                    run_id,
                    doc_id,
                    original_filename,
                    original_mime,
                    original_path,
                    ocr_status,
                    ocr_model,
                    pages_count,
                    ocr_artifacts_path,
                    ocr_error
                FROM documents
                WHERE run_id = ? AND doc_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (run_id, doc_id),
            ).fetchone()

        if row is None:
            raise RuntimeError("Failed to create document")

        return _row_to_document_record(row)

    def update_document_ocr(
        self,
        *,
        run_id: str,
        doc_id: str,
        ocr_status: OCRStatus,
        ocr_model: str | None,
        pages_count: int | None,
        ocr_artifacts_path: str | None,
        ocr_error: str | None,
    ) -> None:
        with connection(self.db_path) as conn:
            result = conn.execute(
                """
                UPDATE documents
                SET
                    ocr_status = ?,
                    ocr_model = ?,
                    pages_count = ?,
                    ocr_artifacts_path = ?,
                    ocr_error = ?
                WHERE run_id = ? AND doc_id = ?
                """,
                (
                    ocr_status,
                    ocr_model,
                    pages_count,
                    ocr_artifacts_path,
                    ocr_error,
                    run_id,
                    doc_id,
                ),
            )

        if result.rowcount == 0:
            raise KeyError(f"Document not found: run_id={run_id}, doc_id={doc_id}")

    def get_document(self, *, run_id: str, doc_id: str) -> DocumentRecord | None:
        with connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    id,
                    run_id,
                    doc_id,
                    original_filename,
                    original_mime,
                    original_path,
                    ocr_status,
                    ocr_model,
                    pages_count,
                    ocr_artifacts_path,
                    ocr_error
                FROM documents
                WHERE run_id = ? AND doc_id = ?
                LIMIT 1
                """,
                (run_id, doc_id),
            ).fetchone()

        if row is None:
            return None

        return _row_to_document_record(row)

    def list_documents(self, *, run_id: str) -> list[DocumentRecord]:
        with connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    id,
                    run_id,
                    doc_id,
                    original_filename,
                    original_mime,
                    original_path,
                    ocr_status,
                    ocr_model,
                    pages_count,
                    ocr_artifacts_path,
                    ocr_error
                FROM documents
                WHERE run_id = ?
                ORDER BY doc_id ASC
                """,
                (run_id,),
            ).fetchall()

        return [_row_to_document_record(row) for row in rows]

    def upsert_llm_output(
        self,
        *,
        run_id: str,
        response_json_path: str,
        response_valid: bool,
        schema_validation_errors_path: str | None,
    ) -> None:
        with connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO llm_outputs (
                    run_id,
                    response_json_path,
                    response_valid,
                    schema_validation_errors_path
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    response_json_path = excluded.response_json_path,
                    response_valid = excluded.response_valid,
                    schema_validation_errors_path = excluded.schema_validation_errors_path
                """,
                (
                    run_id,
                    response_json_path,
                    1 if response_valid else 0,
                    schema_validation_errors_path,
                ),
            )

    def get_llm_output(self, *, run_id: str) -> LLMOutputRecord | None:
        with connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    run_id,
                    response_json_path,
                    response_valid,
                    schema_validation_errors_path
                FROM llm_outputs
                WHERE run_id = ?
                LIMIT 1
                """,
                (run_id,),
            ).fetchone()

        if row is None:
            return None

        return LLMOutputRecord(
            run_id=str(row["run_id"]),
            response_json_path=str(row["response_json_path"]),
            response_valid=bool(row["response_valid"]),
            schema_validation_errors_path=_to_optional_str(
                row["schema_validation_errors_path"]
            ),
        )


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _to_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _row_to_document_record(row: object) -> DocumentRecord:
    return DocumentRecord(
        id=int(row["id"]),
        run_id=str(row["run_id"]),
        doc_id=str(row["doc_id"]),
        original_filename=str(row["original_filename"]),
        original_mime=_to_optional_str(row["original_mime"]),
        original_path=str(row["original_path"]),
        ocr_status=str(row["ocr_status"]),
        ocr_model=_to_optional_str(row["ocr_model"]),
        pages_count=_to_optional_int(row["pages_count"]),
        ocr_artifacts_path=_to_optional_str(row["ocr_artifacts_path"]),
        ocr_error=_to_optional_str(row["ocr_error"]),
    )


def _to_optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _row_to_run_record(row: object) -> RunRecord:
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
        timings_json=_from_json_text(row["timings_json"]),
        usage_json=_from_json_text(row["usage_json"]),
        usage_normalized_json=_from_json_text(row["usage_normalized_json"]),
        cost_json=_from_json_text(row["cost_json"]),
        artifacts_root_path=str(row["artifacts_root_path"]),
    )


def _normalize_date_from(value: str | None) -> str | None:
    if value is None:
        return None

    text = value.strip()
    if not text:
        return None

    if _looks_like_date_only(text):
        return f"{text}T00:00:00+00:00"
    return text


def _normalize_date_to(value: str | None) -> str | None:
    if value is None:
        return None

    text = value.strip()
    if not text:
        return None

    if _looks_like_date_only(text):
        return f"{text}T23:59:59.999999+00:00"
    return text


def _looks_like_date_only(value: str) -> bool:
    return len(value) == 10 and value[4] == "-" and value[7] == "-"


def _to_json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _from_json_text(value: object) -> dict[str, Any] | None:
    text = _to_optional_str(value)
    if text is None:
        return None

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"_raw": text}

    if not isinstance(parsed, dict):
        return {"_value": parsed}
    return parsed
