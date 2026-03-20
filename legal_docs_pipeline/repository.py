"""Mongo repository foundation for the NormaDepo pipeline."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from time import sleep
from typing import Any, Protocol

from pymongo import MongoClient
from pymongo.errors import (
    AutoReconnect,
    ConnectionFailure,
    ExecutionTimeout,
    NetworkTimeout,
    WriteConcernError,
)

from .config import PipelineConfig
from .language import LanguageDetectionResult
from .llm import StructuredLlmRequest, StructuredLlmResponse
from .parser import ParsedMarkdownDocument
from .reader import ReadDocumentResult
from .scanner import DiscoveredDocument
from .schemas import (
    AnalysisAnnotationOutput,
    ClassificationResult,
    TranslationAnnotationOutput,
)

_DISCOVER_STAGE = "discover"
_READ_STAGE = "read"
_PARSE_STAGE = "parse"
_CLASSIFY_STAGE = "classify"
_ANNOTATE_ORIGINAL_STAGE = "annotate_original"
_ANNOTATE_RU_STAGE = "annotate_ru"
_PERSIST_STAGE = "persist"
_ALL_STAGES = (
    _DISCOVER_STAGE,
    _READ_STAGE,
    _PARSE_STAGE,
    _CLASSIFY_STAGE,
    _ANNOTATE_ORIGINAL_STAGE,
    _ANNOTATE_RU_STAGE,
    _PERSIST_STAGE,
)
_TRANSIENT_MONGO_WRITE_ERRORS = (
    AutoReconnect,
    ConnectionFailure,
    ExecutionTimeout,
    NetworkTimeout,
    WriteConcernError,
)


class _CollectionProtocol(Protocol):
    def create_index(self, keys: list[tuple[str, int]], **kwargs: Any) -> Any: ...

    def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> dict[str, Any] | None: ...

    def update_one(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class RepositoryWriteResult:
    created: bool
    revision_no: int


class MongoDocumentRepository:
    def __init__(
        self,
        *,
        collection: _CollectionProtocol,
        schema_version: str,
        pipeline_version: str,
        dedup_version: str,
        router_version: str,
        history_tail_size: int,
        retry_mongo_writes: int = 0,
        client: MongoClient[dict[str, Any]] | None = None,
    ) -> None:
        self._collection = collection
        self._schema_version = schema_version
        self._pipeline_version = pipeline_version
        self._dedup_version = dedup_version
        self._router_version = router_version
        self._history_tail_size = history_tail_size
        self._retry_mongo_writes = retry_mongo_writes
        self._client = client

    @classmethod
    def from_config(cls, config: PipelineConfig) -> "MongoDocumentRepository":
        client: MongoClient[dict[str, Any]] = MongoClient(
            config.mongo.uri,
            serverSelectionTimeoutMS=5_000,
            tz_aware=True,
        )
        client.admin.command("ping")
        collection = client[config.mongo.database][config.mongo.collection]
        return cls(
            collection=collection,
            schema_version=config.pipeline.schema_version,
            pipeline_version=config.pipeline.pipeline_version,
            dedup_version=config.pipeline.dedup_version,
            router_version=config.pipeline.router_version,
            history_tail_size=config.pipeline.history_tail_size,
            retry_mongo_writes=config.pipeline.retry_mongo_writes,
            client=client,
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def ensure_indexes(self) -> None:
        _safe_create_index(self._collection, [("_id", 1)])
        _safe_create_index(self._collection, [("source.file_sha256", 1)])
        _safe_create_index(self._collection, [("source.normalized_text_sha256", 1)])
        _safe_create_index(self._collection, [("processing.status", 1)])

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        return self._collection.find_one({"_id": doc_id})

    def upsert_discovered(
        self,
        *,
        discovered: DiscoveredDocument,
        input_root: Path,
        run_id: str,
        mode: str,
    ) -> RepositoryWriteResult:
        now = _utc_now()
        doc_id = discovered.relative_path.as_posix()
        existing = self.get_document(doc_id)
        created = existing is None
        document = (
            _new_document_skeleton(
                discovered=discovered,
                input_root=input_root,
                schema_version=self._schema_version,
                pipeline_version=self._pipeline_version,
                dedup_version=self._dedup_version,
                router_version=self._router_version,
                run_id=run_id,
                now=now,
            )
            if existing is None
            else copy.deepcopy(existing)
        )

        _ensure_document_defaults(
            document,
            discovered=discovered,
            input_root=input_root,
            schema_version=self._schema_version,
            pipeline_version=self._pipeline_version,
            dedup_version=self._dedup_version,
            router_version=self._router_version,
            run_id=run_id,
            now=now,
        )
        _reset_stages(document["processing"]["stages"])
        _update_scan_fields(document, discovered)

        processing = document["processing"]
        if created:
            processing["attempt_no"] = 1
            document["source"]["revision_no"] = 1
        else:
            processing["attempt_no"] = int(processing.get("attempt_no", 0)) + 1
            previous_sha = (
                existing.get("source", {}).get("file_sha256") if existing else None
            )
            if previous_sha != discovered.sha256_hex:
                current_revision = int(document["source"].get("revision_no", 1))
                document["source"]["revision_no"] = current_revision + 1

        processing["run_id"] = run_id
        processing["started_at"] = now
        processing["completed_at"] = None
        processing["current_stage"] = _DISCOVER_STAGE
        processing["status"] = "discovered"
        processing["error"] = None
        processing["warnings"] = []
        _set_stage_state(
            processing["stages"],
            stage_name=_DISCOVER_STAGE,
            status="completed",
            completed_at=now,
            error=None,
        )
        document["search"]["processing_status"] = "discovered"
        document["updated_at"] = now
        self._write_document(document)
        return RepositoryWriteResult(
            created=created,
            revision_no=int(document["source"]["revision_no"]),
        )

    def touch_seen(self, *, doc_id: str, run_id: str) -> None:
        document = self._load_required_document(doc_id)
        now = _utc_now()
        document["processing"]["last_seen_at"] = now
        document["processing"]["run_id"] = run_id
        document["updated_at"] = now
        self._write_document(document)

    def apply_read_result(
        self,
        *,
        doc_id: str,
        read_result: ReadDocumentResult,
    ) -> None:
        document = self._load_required_document(doc_id)
        now = _utc_now()
        source = document["source"]
        source["encoding"] = read_result.encoding
        source["raw_markdown"] = read_result.raw_markdown
        source["normalized_text"] = read_result.normalized_text
        source["normalized_text_sha256"] = read_result.normalized_text_sha256
        source["title"] = read_result.title
        source["text_stats"] = {
            "chars": read_result.text_stats.chars,
            "lines": read_result.text_stats.lines,
            "words": read_result.text_stats.words,
        }
        document["dedup"]["exact_content_key"] = read_result.normalized_text_sha256
        processing = document["processing"]
        processing["current_stage"] = _READ_STAGE
        processing["status"] = "read"
        processing["error"] = None
        _set_stage_state(
            processing["stages"],
            stage_name=_READ_STAGE,
            status="completed",
            completed_at=now,
            error=None,
        )
        document["search"]["processing_status"] = "read"
        document["updated_at"] = now
        self._write_document(document)

    def apply_parse_result(
        self,
        *,
        doc_id: str,
        parse_result: ParsedMarkdownDocument,
        language_result: LanguageDetectionResult,
    ) -> None:
        document = self._load_required_document(doc_id)
        now = _utc_now()
        source = document["source"]
        source["doc_metadata"] = dict(parse_result.doc_metadata)
        source["content_markdown"] = parse_result.content_markdown
        if parse_result.title:
            source["title"] = parse_result.title
        source["language_original"] = language_result.language_code

        canonical_doc_uid = parse_result.doc_metadata.get("canonical_doc_uid")
        document["dedup"]["canonical_doc_uid"] = canonical_doc_uid
        document["dedup"]["logical_doc_key"] = canonical_doc_uid or doc_id

        processing = document["processing"]
        processing["current_stage"] = _PARSE_STAGE
        processing["status"] = "pending_classification"
        processing["completed_at"] = None
        processing["error"] = None
        processing["warnings"] = _merge_warnings(
            processing.get("warnings", []),
            list(parse_result.warnings),
        )
        _set_stage_state(
            processing["stages"],
            stage_name=_PARSE_STAGE,
            status="completed",
            completed_at=now,
            error=None,
        )

        search = document["search"]
        search["language_original"] = language_result.language_code
        search["canonical_doc_uid"] = canonical_doc_uid
        search["processing_status"] = "pending_classification"
        document["updated_at"] = now
        self._write_document(document)

    def apply_classification_result(
        self,
        *,
        doc_id: str,
        classification_result: ClassificationResult,
        mode: str,
    ) -> None:
        document = self._load_required_document(doc_id)
        now = _utc_now()
        _update_classification_block(
            document=document,
            classification_result=classification_result,
        )

        processing = document["processing"]
        processing["current_stage"] = _CLASSIFY_STAGE
        processing["error"] = None
        _set_stage_state(
            processing["stages"],
            stage_name=_CLASSIFY_STAGE,
            status="completed",
            completed_at=now,
            error=None,
        )

        if classification_result.annotatable:
            processing["status"] = "pending_annotate_original"
            processing["completed_at"] = None
            document["search"]["processing_status"] = "pending_annotate_original"
        else:
            document["annotation"]["status"] = "skipped"
            document["search"]["authority_level"] = None
            document["search"]["relevance"] = None
            document["search"]["usually_supports"] = None
            document["search"]["topic_codes"] = []
            document["search"]["use_for_tasks_codes"] = []
            document["search"]["tags_original"] = []
            processing["status"] = "skipped_non_target"
            processing["completed_at"] = now
            processing["last_success_at"] = now
            _set_stage_state(
                processing["stages"],
                stage_name=_ANNOTATE_ORIGINAL_STAGE,
                status="skipped",
                completed_at=now,
                error=None,
            )
            _set_stage_state(
                processing["stages"],
                stage_name=_ANNOTATE_RU_STAGE,
                status="skipped",
                completed_at=now,
                error=None,
            )
            _append_history(
                processing,
                history_tail_size=self._history_tail_size,
                record={
                    "run_id": processing["run_id"],
                    "mode": mode,
                    "status": "skipped_non_target",
                    "stage": _CLASSIFY_STAGE,
                    "completed_at": now,
                },
            )
            document["search"]["processing_status"] = "skipped_non_target"

        document["updated_at"] = now
        self._write_document(document)

    def apply_analysis_result(
        self,
        *,
        doc_id: str,
        annotation_output: AnalysisAnnotationOutput,
        analysis_fingerprint: str,
        llm_request: StructuredLlmRequest,
        llm_response: StructuredLlmResponse,
        mode: str,
    ) -> None:
        document = self._load_required_document(doc_id)
        completed_at = llm_response.completed_at or _utc_now()
        annotation = document["annotation"]
        annotation["status"] = "partial"
        annotation["analysis_fingerprint"] = analysis_fingerprint
        annotation["semantic"] = annotation_output.semantic.model_dump(mode="json")
        annotation["original"] = annotation_output.annotation_original.model_dump(
            mode="json"
        )
        annotation.setdefault("qa", {})
        annotation["qa"]["manual_review_required"] = False
        annotation["qa"]["validation_errors"] = []
        annotation["qa"]["warnings"] = []

        llm_analysis = document["llm"].setdefault("analysis", {})
        llm_analysis.update(
            {
                "provider": llm_request.provider,
                "api": llm_request.api,
                "model_id": llm_request.model_id,
                "reasoning_effort": llm_request.reasoning_effort,
                "text_format": "json_schema",
                "text_verbosity": llm_request.text_verbosity,
                "max_output_tokens": llm_request.max_output_tokens,
                "store": llm_request.store,
                "truncation": llm_request.truncation,
                "prompt_pack_id": llm_request.prompt_pack_id,
                "prompt_pack_version": llm_request.prompt_pack_version,
                "prompt_profile": llm_request.prompt_profile,
                "prompt_hash": llm_request.prompt_hash,
                "request_hash": llm_request.request_hash,
                "response_id": llm_response.response_id,
                "duration_ms": llm_response.duration_ms,
                "usage": {
                    "input_tokens": llm_response.usage.input_tokens,
                    "output_tokens": llm_response.usage.output_tokens,
                    "reasoning_tokens": llm_response.usage.reasoning_tokens,
                },
                "completed_at": completed_at,
                "status": llm_response.status,
                "error": None,
            }
        )

        processing = document["processing"]
        processing["current_stage"] = _ANNOTATE_RU_STAGE
        processing["status"] = "partial"
        processing["completed_at"] = completed_at
        processing["error"] = None
        _set_stage_state(
            processing["stages"],
            stage_name=_ANNOTATE_ORIGINAL_STAGE,
            status="completed",
            completed_at=completed_at,
            error=None,
        )
        _append_history(
            processing,
            history_tail_size=self._history_tail_size,
            record={
                "run_id": processing["run_id"],
                "mode": mode,
                "status": "partial",
                "stage": _ANNOTATE_RU_STAGE,
                "completed_at": completed_at,
            },
        )

        search = document["search"]
        search["document_type_code"] = annotation_output.semantic.document_type_code
        search["authority_level"] = annotation_output.semantic.authority_level.value
        search["relevance"] = annotation_output.semantic.relevance.value
        search["usually_supports"] = annotation_output.semantic.usually_supports.value
        search["topic_codes"] = [
            topic.value for topic in annotation_output.semantic.topic_codes
        ]
        search["use_for_tasks_codes"] = [
            task.value for task in annotation_output.semantic.use_for_tasks_codes
        ]
        search["tags_original"] = list(annotation_output.annotation_original.tags)
        search["processing_status"] = "partial"

        document["updated_at"] = completed_at
        self._write_document(document)

    def apply_translation_result(
        self,
        *,
        doc_id: str,
        translation_output: TranslationAnnotationOutput,
        llm_request: StructuredLlmRequest,
        llm_response: StructuredLlmResponse,
        mode: str,
    ) -> None:
        document = self._load_required_document(doc_id)
        completed_at = llm_response.completed_at or _utc_now()
        annotation = document["annotation"]
        annotation["status"] = "completed"
        annotation["semantic"] = translation_output.semantic.model_dump(mode="json")
        annotation["ru"] = translation_output.annotation_ru.model_dump(mode="json")
        annotation.setdefault("qa", {})
        annotation["qa"]["manual_review_required"] = False
        annotation["qa"]["validation_errors"] = []

        llm_translation = document["llm"].setdefault("translation_ru", {})
        llm_translation.update(
            {
                "provider": llm_request.provider,
                "api": llm_request.api,
                "model_id": llm_request.model_id,
                "reasoning_effort": llm_request.reasoning_effort,
                "text_format": "json_schema",
                "text_verbosity": llm_request.text_verbosity,
                "max_output_tokens": llm_request.max_output_tokens,
                "store": llm_request.store,
                "truncation": llm_request.truncation,
                "prompt_pack_id": llm_request.prompt_pack_id,
                "prompt_pack_version": llm_request.prompt_pack_version,
                "prompt_profile": llm_request.prompt_profile,
                "prompt_hash": llm_request.prompt_hash,
                "request_hash": llm_request.request_hash,
                "response_id": llm_response.response_id,
                "duration_ms": llm_response.duration_ms,
                "usage": {
                    "input_tokens": llm_response.usage.input_tokens,
                    "output_tokens": llm_response.usage.output_tokens,
                    "reasoning_tokens": llm_response.usage.reasoning_tokens,
                },
                "completed_at": completed_at,
                "status": llm_response.status,
                "error": None,
            }
        )

        processing = document["processing"]
        processing["current_stage"] = _ANNOTATE_RU_STAGE
        processing["status"] = "completed"
        processing["completed_at"] = completed_at
        processing["last_success_at"] = completed_at
        processing["error"] = None
        _set_stage_state(
            processing["stages"],
            stage_name=_ANNOTATE_ORIGINAL_STAGE,
            status="completed",
            completed_at=completed_at,
            error=None,
        )
        _set_stage_state(
            processing["stages"],
            stage_name=_ANNOTATE_RU_STAGE,
            status="completed",
            completed_at=completed_at,
            error=None,
        )
        _append_history(
            processing,
            history_tail_size=self._history_tail_size,
            record={
                "run_id": processing["run_id"],
                "mode": mode,
                "status": "completed",
                "stage": _ANNOTATE_RU_STAGE,
                "completed_at": completed_at,
            },
        )

        search = document["search"]
        search["tags_ru"] = list(translation_output.annotation_ru.tags)
        search["processing_status"] = "completed"
        document["updated_at"] = completed_at
        self._write_document(document)

    def mark_translation_partial(
        self,
        *,
        doc_id: str,
        error_code: str,
        error_message: str,
        error_details: dict[str, Any] | None = None,
        mode: str,
        llm_updates: dict[str, Any] | None = None,
        validation_errors: list[str] | None = None,
        manual_review_required: bool = False,
    ) -> None:
        document = self._load_required_document(doc_id)
        now = _utc_now()
        if llm_updates:
            document.setdefault("llm", {}).setdefault("translation_ru", {}).update(
                llm_updates
            )
        annotation = document["annotation"]
        annotation["status"] = "partial"
        annotation.setdefault("qa", {})
        if validation_errors is not None:
            annotation["qa"]["validation_errors"] = validation_errors
        annotation["qa"]["manual_review_required"] = manual_review_required

        error_payload = _build_error_payload(
            error_code=error_code,
            error_message=error_message,
            error_details=error_details,
        )
        processing = document["processing"]
        processing["current_stage"] = _ANNOTATE_RU_STAGE
        processing["status"] = "partial"
        processing["completed_at"] = now
        processing["error"] = error_payload
        _set_stage_state(
            processing["stages"],
            stage_name=_ANNOTATE_ORIGINAL_STAGE,
            status="completed",
            completed_at=now,
            error=None,
        )
        _set_stage_state(
            processing["stages"],
            stage_name=_ANNOTATE_RU_STAGE,
            status="failed",
            completed_at=now,
            error=error_payload,
        )
        _append_history(
            processing,
            history_tail_size=self._history_tail_size,
            record={
                "run_id": processing["run_id"],
                "mode": mode,
                "status": "partial",
                "stage": _ANNOTATE_RU_STAGE,
                "completed_at": now,
                "error": error_payload,
            },
        )
        document["search"]["processing_status"] = "partial"
        document["updated_at"] = now
        self._write_document(document)

    def mark_failed(
        self,
        *,
        doc_id: str,
        stage: str,
        error_code: str,
        error_message: str,
        error_details: dict[str, Any] | None = None,
        mode: str,
        warnings: tuple[str, ...] = (),
        source_updates: dict[str, Any] | None = None,
        dedup_updates: dict[str, Any] | None = None,
        classification_updates: dict[str, Any] | None = None,
        llm_updates: dict[str, Any] | None = None,
        llm_block: str = "analysis",
        annotation_status: str | None = None,
        validation_errors: list[str] | None = None,
    ) -> None:
        document = self._load_required_document(doc_id)
        now = _utc_now()
        if source_updates:
            document["source"].update(source_updates)
        if dedup_updates:
            document["dedup"].update(dedup_updates)
        if classification_updates:
            document.setdefault("classification", {}).update(classification_updates)
            _update_search_from_classification(
                document=document,
                classification=document["classification"],
            )
        if llm_updates:
            document.setdefault("llm", {}).setdefault(llm_block, {}).update(llm_updates)
        if annotation_status is not None:
            document["annotation"]["status"] = annotation_status
        if validation_errors is not None:
            document["annotation"].setdefault("qa", {})
            document["annotation"]["qa"]["validation_errors"] = validation_errors
            document["annotation"]["qa"]["manual_review_required"] = bool(
                validation_errors
            )

        error_payload = _build_error_payload(
            error_code=error_code,
            error_message=error_message,
            error_details=error_details,
        )
        processing = document["processing"]
        processing["current_stage"] = stage
        processing["status"] = "failed"
        processing["completed_at"] = now
        processing["error"] = error_payload
        processing["warnings"] = _merge_warnings(
            processing.get("warnings", []),
            list(warnings),
        )
        _set_stage_state(
            processing["stages"],
            stage_name=stage,
            status="failed",
            completed_at=now,
            error=error_payload,
        )
        _append_history(
            processing,
            history_tail_size=self._history_tail_size,
            record={
                "run_id": processing["run_id"],
                "mode": mode,
                "status": "failed",
                "stage": stage,
                "completed_at": now,
                "error": error_payload,
            },
        )
        document["search"]["processing_status"] = "failed"
        document["updated_at"] = now
        self._write_document(document)

    def _load_required_document(self, doc_id: str) -> dict[str, Any]:
        document = self.get_document(doc_id)
        if document is None:
            raise KeyError(f"Document not found: {doc_id}")
        return copy.deepcopy(document)

    def _write_document(self, document: dict[str, Any]) -> None:
        attempts = self._retry_mongo_writes + 1
        for attempt in range(1, attempts + 1):
            try:
                self._collection.update_one(
                    {"_id": document["_id"]},
                    {"$set": document},
                    upsert=True,
                )
                return
            except _TRANSIENT_MONGO_WRITE_ERRORS:
                if attempt >= attempts:
                    raise
                sleep(_retry_backoff_seconds(attempt))


def _build_error_payload(
    *,
    error_code: str,
    error_message: str,
    error_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "code": error_code,
        "message": error_message,
    }
    if error_details:
        payload["details"] = error_details
    return payload


def _new_document_skeleton(
    *,
    discovered: DiscoveredDocument,
    input_root: Path,
    schema_version: str,
    pipeline_version: str,
    dedup_version: str,
    router_version: str,
    run_id: str,
    now: datetime,
) -> dict[str, Any]:
    doc_id = discovered.relative_path.as_posix()
    top_level_dir = discovered.top_level_dir or ""
    return {
        "_id": doc_id,
        "doc_id": doc_id,
        "schema_version": schema_version,
        "pipeline_version": pipeline_version,
        "corpus": {
            "name": input_root.name,
            "version": _infer_corpus_version(input_root.name),
            "input_root": str(input_root),
            "relative_path": doc_id,
            "top_level_dir": top_level_dir,
        },
        "source": {
            "file_name": discovered.file_name,
            "file_ext": discovered.absolute_path.suffix,
            "absolute_path": str(discovered.absolute_path),
            "relative_path": doc_id,
            "size_bytes": discovered.size_bytes,
            "modified_at": discovered.modified_at,
            "file_sha256": discovered.sha256_hex,
            "encoding": "utf-8",
            "title": None,
            "language_original": "und",
            "raw_markdown": "",
            "normalized_text": "",
            "normalized_text_sha256": "",
            "text_stats": {"chars": 0, "lines": 0, "words": 0},
            "doc_metadata": {},
            "content_markdown": None,
            "revision_no": 1,
        },
        "dedup": {
            "canonical_doc_uid": None,
            "logical_doc_key": doc_id,
            "exact_content_key": "",
            "is_exact_duplicate": False,
            "duplicate_of_doc_id": None,
            "dedup_version": dedup_version,
        },
        "classification": {},
        "annotation": {
            "status": "pending",
            "schema_version": schema_version,
            "analysis_fingerprint": "",
            "qa": {
                "manual_review_required": False,
                "validation_errors": [],
                "warnings": [],
            },
        },
        "llm": {"analysis": {}, "translation_ru": {}},
        "processing": {
            "status": "discovered",
            "current_stage": _DISCOVER_STAGE,
            "run_id": run_id,
            "attempt_no": 0,
            "first_seen_at": now,
            "last_seen_at": now,
            "started_at": now,
            "completed_at": None,
            "last_success_at": None,
            "error": None,
            "warnings": [],
            "stages": _empty_stage_map(),
            "history_tail": [],
        },
        "search": {
            "document_family": "unknown",
            "document_type_code": None,
            "language_original": "und",
            "authority_level": None,
            "relevance": None,
            "usually_supports": None,
            "topic_codes": [],
            "use_for_tasks_codes": [],
            "tags_original": [],
            "tags_ru": [],
            "canonical_doc_uid": None,
            "annotatable": False,
            "processing_status": "discovered",
        },
        "created_at": now,
        "updated_at": now,
    }


def _ensure_document_defaults(
    document: dict[str, Any],
    *,
    discovered: DiscoveredDocument,
    input_root: Path,
    schema_version: str,
    pipeline_version: str,
    dedup_version: str,
    router_version: str,
    run_id: str,
    now: datetime,
) -> None:
    if "_id" not in document:
        document.update(
            _new_document_skeleton(
                discovered=discovered,
                input_root=input_root,
                schema_version=schema_version,
                pipeline_version=pipeline_version,
                dedup_version=dedup_version,
                router_version=router_version,
                run_id=run_id,
                now=now,
            )
        )
        return

    document["schema_version"] = document.get("schema_version") or schema_version
    document["pipeline_version"] = document.get("pipeline_version") or pipeline_version
    document.setdefault("classification", {})
    document.setdefault("annotation", {})
    document.setdefault("llm", {})
    document.setdefault("search", {})
    document.setdefault("dedup", {})
    document.setdefault("source", {})
    document.setdefault("corpus", {})
    document.setdefault("processing", {})
    document.setdefault("created_at", now)
    document["updated_at"] = now

    document["corpus"].setdefault("name", input_root.name)
    document["corpus"].setdefault("version", _infer_corpus_version(input_root.name))
    document["corpus"]["input_root"] = str(input_root)
    document["corpus"]["relative_path"] = discovered.relative_path.as_posix()
    document["corpus"]["top_level_dir"] = discovered.top_level_dir or ""

    document["source"].setdefault("file_ext", discovered.absolute_path.suffix)
    document["source"].setdefault("encoding", "utf-8")
    document["source"].setdefault("title", None)
    document["source"].setdefault("language_original", "und")
    document["source"].setdefault("raw_markdown", "")
    document["source"].setdefault("normalized_text", "")
    document["source"].setdefault("normalized_text_sha256", "")
    document["source"].setdefault("text_stats", {"chars": 0, "lines": 0, "words": 0})
    document["source"].setdefault("doc_metadata", {})
    document["source"].setdefault("content_markdown", None)
    document["source"].setdefault("revision_no", 1)

    document["dedup"].setdefault("canonical_doc_uid", None)
    document["dedup"].setdefault("logical_doc_key", discovered.relative_path.as_posix())
    document["dedup"].setdefault("exact_content_key", "")
    document["dedup"].setdefault("is_exact_duplicate", False)
    document["dedup"].setdefault("duplicate_of_doc_id", None)
    document["dedup"].setdefault("dedup_version", dedup_version)

    document["annotation"].setdefault("status", "pending")
    document["annotation"].setdefault("schema_version", schema_version)
    document["annotation"].setdefault("analysis_fingerprint", "")
    document["annotation"].setdefault(
        "qa",
        {
            "manual_review_required": False,
            "validation_errors": [],
            "warnings": [],
        },
    )
    document["llm"].setdefault("analysis", {})
    document["llm"].setdefault("translation_ru", {})

    search = document["search"]
    search.setdefault("document_family", "unknown")
    search.setdefault("document_type_code", None)
    search.setdefault(
        "language_original", document["source"].get("language_original", "und")
    )
    search.setdefault("authority_level", None)
    search.setdefault("relevance", None)
    search.setdefault("usually_supports", None)
    search.setdefault("topic_codes", [])
    search.setdefault("use_for_tasks_codes", [])
    search.setdefault("tags_original", [])
    search.setdefault("tags_ru", [])
    search.setdefault("canonical_doc_uid", None)
    search.setdefault("annotatable", False)
    search.setdefault(
        "processing_status", document.get("processing", {}).get("status", "discovered")
    )

    processing = document["processing"]
    processing.setdefault("status", "discovered")
    processing.setdefault("current_stage", _DISCOVER_STAGE)
    processing.setdefault("run_id", run_id)
    processing.setdefault("attempt_no", 0)
    processing.setdefault("first_seen_at", now)
    processing["last_seen_at"] = now
    processing.setdefault("started_at", now)
    processing.setdefault("completed_at", None)
    processing.setdefault("last_success_at", None)
    processing.setdefault("error", None)
    processing.setdefault("warnings", [])
    processing.setdefault("stages", _empty_stage_map())
    processing.setdefault("history_tail", [])


def _update_scan_fields(document: dict[str, Any], discovered: DiscoveredDocument) -> None:
    doc_id = discovered.relative_path.as_posix()
    document["_id"] = doc_id
    document["doc_id"] = doc_id
    document["corpus"]["relative_path"] = doc_id
    document["corpus"]["top_level_dir"] = discovered.top_level_dir or ""
    source = document["source"]
    source["file_name"] = discovered.file_name
    source["file_ext"] = discovered.absolute_path.suffix
    source["absolute_path"] = str(discovered.absolute_path)
    source["relative_path"] = doc_id
    source["size_bytes"] = discovered.size_bytes
    source["modified_at"] = discovered.modified_at
    source["file_sha256"] = discovered.sha256_hex


def _empty_stage_map() -> dict[str, dict[str, Any]]:
    return {
        stage_name: {
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "error": None,
        }
        for stage_name in _ALL_STAGES
    }


def _reset_stages(stages: dict[str, dict[str, Any]]) -> None:
    for stage_name in _ALL_STAGES:
        stages[stage_name] = {
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "error": None,
        }


def _set_stage_state(
    stages: dict[str, dict[str, Any]],
    *,
    stage_name: str,
    status: str,
    completed_at: datetime,
    error: dict[str, Any] | None,
) -> None:
    stage = stages.setdefault(
        stage_name,
        {
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "error": None,
        },
    )
    stage["status"] = status
    stage["started_at"] = stage.get("started_at") or completed_at
    stage["completed_at"] = completed_at
    stage["error"] = error


def _update_classification_block(
    *,
    document: dict[str, Any],
    classification_result: ClassificationResult,
) -> None:
    classification = document.setdefault("classification", {})
    classification.update(classification_result.model_dump(mode="json"))
    _update_search_from_classification(
        document=document,
        classification=classification,
    )


def _update_search_from_classification(
    *,
    document: dict[str, Any],
    classification: dict[str, Any],
) -> None:
    search = document.setdefault("search", {})
    search["document_family"] = classification.get("document_family", "unknown")
    search["document_type_code"] = classification.get("document_type_code")
    search["language_original"] = document["source"].get("language_original", "und")
    search["annotatable"] = bool(classification.get("annotatable", False))


def _retry_backoff_seconds(attempt: int) -> float:
    return min(0.05 * (2 ** (attempt - 1)), 0.2)


def _append_history(
    processing: dict[str, Any],
    *,
    history_tail_size: int,
    record: dict[str, Any],
) -> None:
    history = list(processing.get("history_tail", []))
    history.append(record)
    processing["history_tail"] = history[-history_tail_size:]


def _merge_warnings(
    existing: list[str],
    incoming: list[str],
) -> list[str]:
    merged = list(existing)
    for warning in incoming:
        if warning not in merged:
            merged.append(warning)
    return merged


def _infer_corpus_version(corpus_name: str) -> str:
    match = re.search(r"v\d+(?:_\d+)*", corpus_name)
    if match is not None:
        return match.group(0)
    return corpus_name


def _safe_create_index(
    collection: _CollectionProtocol,
    keys: list[tuple[str, int]],
    **kwargs: Any,
) -> None:
    create_index = getattr(collection, "create_index", None)
    if callable(create_index):
        create_index(keys, **kwargs)


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)
