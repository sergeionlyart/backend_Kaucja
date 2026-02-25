from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Literal

RunStatus = Literal["created", "running", "completed", "failed"]
OCRStatus = Literal["pending", "ok", "failed"]


@dataclass(frozen=True, slots=True)
class SessionRecord:
    session_id: str
    created_at: str


@dataclass(frozen=True, slots=True)
class RunRecord:
    run_id: str
    session_id: str
    created_at: str
    provider: str
    model: str
    prompt_name: str
    prompt_version: str
    schema_version: str
    status: RunStatus
    artifacts_root_path: str
    openai_reasoning_effort: str | None = None
    gemini_thinking_level: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    timings_json: dict[str, Any] | None = None
    usage_json: dict[str, Any] | None = None
    usage_normalized_json: dict[str, Any] | None = None
    cost_json: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    id: int
    run_id: str
    doc_id: str
    original_filename: str
    original_mime: str | None
    original_path: str
    ocr_status: OCRStatus
    ocr_model: str | None
    pages_count: int | None
    ocr_artifacts_path: str | None
    ocr_error: str | None


@dataclass(frozen=True, slots=True)
class LLMOutputRecord:
    run_id: str
    response_json_path: str
    response_valid: bool
    schema_validation_errors_path: str | None


@dataclass(frozen=True, slots=True)
class RunBundle:
    run: RunRecord
    documents: list[DocumentRecord]
    llm_output: LLMOutputRecord | None


@dataclass(frozen=True, slots=True)
class DeleteRunResult:
    run_id: str
    deleted: bool
    error_code: str | None
    error_message: str | None
    technical_details: str | None
    artifacts_deleted: bool
    artifacts_missing: bool


@dataclass(frozen=True, slots=True)
class RetentionCleanupResult:
    cutoff_created_at: str
    dry_run: bool
    export_before_delete: bool
    export_dir: str | None
    report_path: str
    scanned_runs: int
    deleted_runs: int
    failed_runs: int
    skipped_runs: int
    deleted_run_ids: list[str]
    audit_entries: list[dict[str, Any]]
    errors: list[str]


@dataclass(frozen=True, slots=True)
class RestoreRunResult:
    status: str
    run_id: str | None
    session_id: str | None
    artifacts_root_path: str | None
    restored_paths: list[str]
    warnings: list[str]
    errors: list[str]
    error_code: str | None
    error_message: str | None
