"""Mongo-backed state storage for annotate_original batch jobs and items."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from pymongo import MongoClient

from .config import PipelineConfig
from .constants import (
    ANALYSIS_BATCH_ITEMS_COLLECTION,
    ANALYSIS_BATCH_JOBS_COLLECTION,
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
        client: MongoClient[dict[str, Any]] | None = None,
    ) -> None:
        self._jobs = jobs_collection
        self._items = items_collection
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
        return cls(
            jobs_collection=db[ANALYSIS_BATCH_JOBS_COLLECTION],
            items_collection=db[ANALYSIS_BATCH_ITEMS_COLLECTION],
            client=client,
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def ensure_indexes(self) -> None:
        self._items.create_index([("_id", 1)])
        self._items.create_index([("status", 1), ("queued_at", 1)])
        self._items.create_index([("batch_job_id", 1)])
        self._items.create_index([("doc_id", 1), ("stage", 1), ("request_hash", 1)])
        self._jobs.create_index([("_id", 1)])
        self._jobs.create_index([("status", 1), ("submitted_at", 1)])

    def get_item(self, custom_id: str) -> dict[str, Any] | None:
        item = self._items.find_one({"_id": custom_id})
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
        existing = self.get_item(custom_id)
        if existing is not None and existing.get("status") in {
            "queued",
            "submitted",
            "completed",
            "applied",
        }:
            return BatchQueueWriteResult(
                created=False,
                status=str(existing["status"]),
            )
        document = {
            "_id": custom_id,
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
            "status": "queued",
            "queued_at": now,
            "submitted_at": None,
            "completed_at": None,
            "applied_at": None,
            "batch_job_id": None,
            "error_payload": None,
        }
        self._items.update_one({"_id": custom_id}, {"$set": document}, upsert=True)
        return BatchQueueWriteResult(created=existing is None, status="queued")

    def list_queued_items(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        items = self._items.find({"status": "queued"})
        items = sorted(items, key=lambda item: str(item.get("queued_at", "")))
        if limit is not None:
            items = items[:limit]
        return [copy.deepcopy(item) for item in items]

    def list_items_for_job(self, batch_job_id: str) -> list[dict[str, Any]]:
        items = self._items.find({"batch_job_id": batch_job_id})
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
            {"_id": batch_job_id},
            {
                "$set": {
                    "_id": batch_job_id,
                    "batch_job_id": batch_job_id,
                    "status": "submitted",
                    "submitted_at": now,
                    "completed_at": None,
                    "raw_payload": raw_payload,
                    "applied_at": None,
                }
            },
            upsert=True,
        )
        for custom_id in custom_ids:
            self._items.update_one(
                {"_id": custom_id},
                {
                    "$set": {
                        "status": "submitted",
                        "submitted_at": now,
                        "batch_job_id": batch_job_id,
                    }
                },
                upsert=False,
            )

    def get_inflight_jobs(self) -> list[dict[str, Any]]:
        jobs = self._jobs.find({})
        inflight = [
            copy.deepcopy(job)
            for job in jobs
            if str(job.get("status", ""))
            in {"submitted", "validating", "in_progress", "finalizing"}
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
            {"_id": batch_job_id},
            {
                "$set": {
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
        jobs = self._jobs.find({})
        ready: list[dict[str, Any]] = []
        for job in jobs:
            status = str(job.get("status", ""))
            if status not in {"completed", "failed", "expired", "cancelled"}:
                continue
            if job.get("applied_at") is not None:
                continue
            ready.append(copy.deepcopy(job))
        return sorted(ready, key=lambda item: str(item.get("submitted_at", "")))

    def mark_item_status(
        self,
        *,
        custom_id: str,
        status: str,
        completed_at: datetime | None = None,
        error_payload: dict[str, Any] | None = None,
    ) -> None:
        update_payload: dict[str, Any] = {"status": status}
        if completed_at is not None:
            update_payload["completed_at"] = completed_at
        if error_payload is not None:
            update_payload["error_payload"] = error_payload
        self._items.update_one(
            {"_id": custom_id},
            {"$set": update_payload},
            upsert=False,
        )

    def mark_item_applied(self, *, custom_id: str) -> None:
        now = _utc_now()
        self._items.update_one(
            {"_id": custom_id},
            {
                "$set": {
                    "status": "applied",
                    "applied_at": now,
                }
            },
            upsert=False,
        )

    def mark_job_applied(self, *, batch_job_id: str) -> None:
        self._jobs.update_one(
            {"_id": batch_job_id},
            {"$set": {"applied_at": _utc_now()}},
            upsert=False,
        )


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)
