"""Mongo-backed state storage for annotate_original batch jobs and items."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from pymongo import MongoClient

from .config import PipelineConfig

_TERMINAL_PROVIDER_STATUSES = frozenset({"completed", "failed", "expired", "cancelled"})
_INFLIGHT_PROVIDER_STATUSES = frozenset(
    {"submitted", "validating", "in_progress", "finalizing"}
)
_TRULY_APPLIED_STATUSES = frozenset(
    {"applied_success", "fallback_completed", "stale", "superseded"}
)
_TERMINAL_FAILED_APPLY_STATUSES = frozenset({"applied_failed", "fallback_failed"})
_TERMINAL_APPLY_STATUSES = frozenset(
    _TRULY_APPLIED_STATUSES | _TERMINAL_FAILED_APPLY_STATUSES
)


class _CollectionProtocol(Protocol):
    def create_index(self, keys: list[tuple[str, int]], **kwargs: Any) -> Any: ...

    def find(
        self,
        query: dict[str, Any] | None = None,
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]: ...

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
class BatchQueueWriteResult:
    created: bool
    status: str


class MongoBatchStateRepository:
    def __init__(
        self,
        *,
        jobs_collection: _CollectionProtocol,
        items_collection: _CollectionProtocol,
        target_database: str,
        target_collection: str,
        schema_version: str,
        jobs_collection_name: str,
        items_collection_name: str,
        client: MongoClient[dict[str, Any]] | None = None,
    ) -> None:
        self._jobs = jobs_collection
        self._items = items_collection
        self._target_database = target_database
        self._target_collection = target_collection
        self._schema_version = schema_version
        self._jobs_collection_name = jobs_collection_name
        self._items_collection_name = items_collection_name
        self._client = client

    @classmethod
    def from_config(cls, config: PipelineConfig) -> "MongoBatchStateRepository":
        client: MongoClient[dict[str, Any]] = MongoClient(
            config.mongo.uri,
            serverSelectionTimeoutMS=5_000,
            tz_aware=True,
        )
        client.admin.command("ping")
        db = client[config.mongo.database]
        jobs_collection_name = config.pipeline.batch_jobs_collection
        items_collection_name = config.pipeline.batch_items_collection
        return cls(
            jobs_collection=db[jobs_collection_name],
            items_collection=db[items_collection_name],
            target_database=config.mongo.database,
            target_collection=config.mongo.collection,
            schema_version=config.pipeline.schema_version,
            jobs_collection_name=jobs_collection_name,
            items_collection_name=items_collection_name,
            client=client,
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def ensure_indexes(self) -> None:
        self._items.create_index([("_id", 1)])
        self._items.create_index(
            [
                ("target_database", 1),
                ("target_collection", 1),
                ("provider_status", 1),
                ("queued_at", 1),
            ]
        )
        self._items.create_index(
            [
                ("target_database", 1),
                ("target_collection", 1),
                ("batch_job_id", 1),
            ]
        )
        self._items.create_index(
            [
                ("target_database", 1),
                ("target_collection", 1),
                ("doc_id", 1),
                ("stage", 1),
                ("request_hash", 1),
            ]
        )
        self._jobs.create_index([("_id", 1)])
        self._jobs.create_index(
            [
                ("target_database", 1),
                ("target_collection", 1),
                ("provider_status", 1),
                ("submitted_at", 1),
            ]
        )

    def get_item(self, custom_id: str) -> dict[str, Any] | None:
        item = self._items.find_one({"_id": self._storage_item_id(custom_id)})
        return copy.deepcopy(item) if item is not None else None

    def queue_item(
        self,
        *,
        custom_id: str,
        doc_id: str,
        stage: str,
        request_hash: str,
        prompt_hash: str,
        source_language_code: str,
        request_record: dict[str, Any],
        request_body: dict[str, Any],
        analysis_fingerprint: str,
        cost_estimate: dict[str, Any] | None,
    ) -> BatchQueueWriteResult:
        now = _utc_now()
        self._invalidate_superseded_queued_items(
            doc_id=doc_id,
            stage=stage,
            exclude_custom_id=custom_id,
        )
        existing = self.get_item(custom_id)
        if existing is not None:
            apply_status = str(existing.get("apply_status", "pending"))
            provider_status = self._item_provider_status(existing)
            if apply_status in {"stale", "superseded"}:
                self._items.update_one(
                    {"_id": self._storage_item_id(custom_id)},
                    {
                        "$set": self._build_item_document(
                            custom_id=custom_id,
                            doc_id=doc_id,
                            stage=stage,
                            request_hash=request_hash,
                            prompt_hash=prompt_hash,
                            source_language_code=source_language_code,
                            request_record=request_record,
                            request_body=request_body,
                            analysis_fingerprint=analysis_fingerprint,
                            cost_estimate=cost_estimate,
                            queued_at=now,
                        )
                    },
                    upsert=False,
                )
                return BatchQueueWriteResult(created=False, status="stale_replaced")
            if apply_status in _TERMINAL_FAILED_APPLY_STATUSES:
                self._items.update_one(
                    {"_id": self._storage_item_id(custom_id)},
                    {
                        "$set": self._build_item_document(
                            custom_id=custom_id,
                            doc_id=doc_id,
                            stage=stage,
                            request_hash=request_hash,
                            prompt_hash=prompt_hash,
                            source_language_code=source_language_code,
                            request_record=request_record,
                            request_body=request_body,
                            analysis_fingerprint=analysis_fingerprint,
                            cost_estimate=cost_estimate,
                            queued_at=now,
                        )
                    },
                    upsert=False,
                )
                return BatchQueueWriteResult(created=False, status="queued")
            if apply_status in _TRULY_APPLIED_STATUSES:
                return BatchQueueWriteResult(created=False, status="existing_applied")
            if provider_status in _TERMINAL_PROVIDER_STATUSES:
                return BatchQueueWriteResult(created=False, status="existing_completed")
            if provider_status == "submitted":
                return BatchQueueWriteResult(created=False, status="existing_submitted")
            if provider_status == "queued":
                return BatchQueueWriteResult(created=False, status="existing_queued")

        document = self._build_item_document(
            custom_id=custom_id,
            doc_id=doc_id,
            stage=stage,
            request_hash=request_hash,
            prompt_hash=prompt_hash,
            source_language_code=source_language_code,
            request_record=request_record,
            request_body=request_body,
            analysis_fingerprint=analysis_fingerprint,
            cost_estimate=cost_estimate,
            queued_at=now,
        )
        self._items.update_one(
            {"_id": self._storage_item_id(custom_id)},
            {"$set": document},
            upsert=True,
        )
        return BatchQueueWriteResult(created=existing is None, status="queued")

    def list_queued_items(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        items = self._items.find(
            {
                "target_database": self._target_database,
                "target_collection": self._target_collection,
                "provider_status": "queued",
                "apply_status": "pending",
            }
        )
        items = sorted(items, key=lambda item: str(item.get("queued_at", "")))
        if limit is not None:
            items = items[:limit]
        return [copy.deepcopy(item) for item in items]

    def list_items_for_job(self, batch_job_id: str) -> list[dict[str, Any]]:
        items = self._items.find(
            {
                "target_database": self._target_database,
                "target_collection": self._target_collection,
                "batch_job_id": batch_job_id,
            }
        )
        items = sorted(items, key=lambda item: str(item.get("custom_id", "")))
        return [copy.deepcopy(item) for item in items]

    def mark_submitted(
        self,
        *,
        batch_job_id: str,
        custom_ids: list[str],
        raw_payload: dict[str, Any],
    ) -> None:
        now = _utc_now()
        self._jobs.update_one(
            {"_id": self._storage_job_id(batch_job_id)},
            {
                "$set": {
                    "_id": self._storage_job_id(batch_job_id),
                    "batch_job_id": batch_job_id,
                    "target_database": self._target_database,
                    "target_collection": self._target_collection,
                    "jobs_collection": self._jobs_collection_name,
                    "items_collection": self._items_collection_name,
                    "provider_status": "submitted",
                    "status": "submitted",
                    "apply_status": "pending",
                    "submitted_at": now,
                    "completed_at": None,
                    "applied_at": None,
                    "output_file_id": None,
                    "error_file_id": None,
                    "raw_payload": raw_payload,
                }
            },
            upsert=True,
        )
        for custom_id in custom_ids:
            self._items.update_one(
                {"_id": self._storage_item_id(custom_id)},
                {
                    "$set": {
                        "provider_status": "submitted",
                        "status": "submitted",
                        "submitted_at": now,
                        "batch_job_id": batch_job_id,
                    }
                },
                upsert=False,
            )

    def get_inflight_jobs(self) -> list[dict[str, Any]]:
        jobs = self._jobs.find(
            {
                "target_database": self._target_database,
                "target_collection": self._target_collection,
            }
        )
        inflight = [
            copy.deepcopy(job)
            for job in jobs
            if str(job.get("provider_status", job.get("status", "")))
            in _INFLIGHT_PROVIDER_STATUSES
        ]
        return inflight

    def count_inflight_jobs(self) -> int:
        return len(self.get_inflight_jobs())

    def update_job_status(
        self,
        *,
        batch_job_id: str,
        status: str,
        raw_payload: dict[str, Any],
        output_file_id: str | None,
        error_file_id: str | None,
        completed_at: datetime | None,
    ) -> None:
        self._jobs.update_one(
            {"_id": self._storage_job_id(batch_job_id)},
            {
                "$set": {
                    "provider_status": status,
                    "status": status,
                    "raw_payload": raw_payload,
                    "output_file_id": output_file_id,
                    "error_file_id": error_file_id,
                    "completed_at": completed_at,
                }
            },
            upsert=False,
        )

    def get_terminal_jobs_ready_for_apply(self) -> list[dict[str, Any]]:
        jobs = self._jobs.find(
            {
                "target_database": self._target_database,
                "target_collection": self._target_collection,
            }
        )
        ready: list[dict[str, Any]] = []
        for job in jobs:
            provider_status = str(job.get("provider_status", job.get("status", "")))
            apply_status = str(job.get("apply_status", "pending"))
            if provider_status not in _TERMINAL_PROVIDER_STATUSES:
                continue
            if apply_status in {"fully_applied", "apply_failed"}:
                continue
            ready.append(copy.deepcopy(job))
        return sorted(ready, key=lambda item: str(item.get("submitted_at", "")))

    def mark_item_provider_state(
        self,
        *,
        custom_id: str,
        provider_status: str,
        completed_at: datetime | None = None,
        error_payload: dict[str, Any] | None = None,
    ) -> None:
        update_payload: dict[str, Any] = {
            "provider_status": provider_status,
            "status": provider_status,
        }
        if completed_at is not None:
            update_payload["completed_at"] = completed_at
        if error_payload is not None:
            update_payload["error_payload"] = error_payload
        self._items.update_one(
            {"_id": self._storage_item_id(custom_id)},
            {"$set": update_payload},
            upsert=False,
        )

    def mark_item_apply_state(
        self,
        *,
        custom_id: str,
        apply_status: str,
        error_payload: dict[str, Any] | None = None,
    ) -> None:
        now = _utc_now()
        update_payload: dict[str, Any] = {
            "apply_status": apply_status,
            "applied_at": now,
        }
        if error_payload is not None:
            update_payload["error_payload"] = error_payload
        self._items.update_one(
            {"_id": self._storage_item_id(custom_id)},
            {"$set": update_payload},
            upsert=False,
        )

    def update_job_apply_status(
        self,
        *,
        batch_job_id: str,
        apply_status: str,
    ) -> None:
        update_payload: dict[str, Any] = {"apply_status": apply_status}
        if apply_status in {"fully_applied", "partially_applied", "apply_failed"}:
            update_payload["applied_at"] = _utc_now()
        self._jobs.update_one(
            {"_id": self._storage_job_id(batch_job_id)},
            {"$set": update_payload},
            upsert=False,
        )

    def get_job(self, batch_job_id: str) -> dict[str, Any] | None:
        job = self._jobs.find_one({"_id": self._storage_job_id(batch_job_id)})
        return copy.deepcopy(job) if job is not None else None

    def _build_item_document(
        self,
        *,
        custom_id: str,
        doc_id: str,
        stage: str,
        request_hash: str,
        prompt_hash: str,
        source_language_code: str,
        request_record: dict[str, Any],
        request_body: dict[str, Any],
        analysis_fingerprint: str,
        cost_estimate: dict[str, Any] | None,
        queued_at: datetime,
    ) -> dict[str, Any]:
        return {
            "_id": self._storage_item_id(custom_id),
            "custom_id": custom_id,
            "doc_id": doc_id,
            "stage": stage,
            "request_hash": request_hash,
            "prompt_hash": prompt_hash,
            "source_language_code": source_language_code,
            "request_record": request_record,
            "request_body": request_body,
            "analysis_fingerprint": analysis_fingerprint,
            "cost_estimate": cost_estimate,
            "target_database": self._target_database,
            "target_collection": self._target_collection,
            "schema_version": self._schema_version,
            "provider_status": "queued",
            "status": "queued",
            "apply_status": "pending",
            "queued_at": queued_at,
            "submitted_at": None,
            "completed_at": None,
            "applied_at": None,
            "batch_job_id": None,
            "error_payload": None,
        }

    def _invalidate_superseded_queued_items(
        self,
        *,
        doc_id: str,
        stage: str,
        exclude_custom_id: str,
    ) -> None:
        now = _utc_now()
        queued_items = self._items.find(
            {
                "target_database": self._target_database,
                "target_collection": self._target_collection,
                "doc_id": doc_id,
                "stage": stage,
                "provider_status": "queued",
                "apply_status": "pending",
            }
        )
        for item in queued_items:
            custom_id = str(item.get("custom_id", ""))
            if custom_id == exclude_custom_id:
                continue
            self._items.update_one(
                {"_id": self._storage_item_id(custom_id)},
                {
                    "$set": {
                        "apply_status": "superseded",
                        "status": "superseded",
                        "applied_at": now,
                        "error_payload": {
                            "code": "batch_item_superseded",
                            "message": (
                                "Queued batch item was superseded by a newer "
                                "request for the same document and stage."
                            ),
                            "superseded_by": exclude_custom_id,
                        },
                    }
                },
                upsert=False,
            )

    def _storage_item_id(self, custom_id: str) -> str:
        return (
            f"{self._target_database}::{self._target_collection}::"
            f"item::{custom_id}"
        )

    def _storage_job_id(self, batch_job_id: str) -> str:
        return (
            f"{self._target_database}::{self._target_collection}::"
            f"job::{batch_job_id}"
        )

    @staticmethod
    def _item_provider_status(item: dict[str, Any]) -> str:
        return str(item.get("provider_status", item.get("status", "queued")))


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)
