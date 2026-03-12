from __future__ import annotations

import hashlib
import mimetypes
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, Sequence


_CASE_WORKSPACES_COLLECTION = "case_workspaces"
_CASE_DOCUMENTS_COLLECTION = "case_documents"
_CASE_FACTS_COLLECTION = "case_facts"
_ANALYSIS_RUNS_COLLECTION = "analysis_runs"


class _CollectionProtocol(Protocol):
    def update_one(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
    ) -> Any: ...

    def insert_one(self, row: dict[str, Any]) -> Any: ...

    def create_index(self, keys: list[tuple[str, int]], **kwargs: Any) -> Any: ...


class _MongoRuntimeProtocol(Protocol):
    def collection(self, name: str) -> _CollectionProtocol: ...


@dataclass(frozen=True, slots=True)
class CaseWorkspaceDocumentRecord:
    document_id: str
    case_id: str
    file_name: str
    file_path: str
    size_bytes: int
    sha256: str
    mime_type: str | None


@dataclass(frozen=True, slots=True)
class Scenario2CaseMetadata:
    claim_amount: float | None = None
    currency: str | None = None
    lease_start: str | None = None
    lease_end: str | None = None
    move_out_date: str | None = None
    deposit_return_due_date: str | None = None

    def to_workspace_fields(self) -> dict[str, float | str | None]:
        return {
            "claim_amount": self.claim_amount,
            "currency": self.currency,
            "lease_start": self.lease_start,
            "lease_end": self.lease_end,
            "move_out_date": self.move_out_date,
            "deposit_return_due_date": self.deposit_return_due_date,
        }


class MongoCaseWorkspaceStore:
    """Separate Mongo workspace for Scenario 2 user documents and analysis runs."""

    def __init__(self, *, runtime: _MongoRuntimeProtocol) -> None:
        self._runtime = runtime
        self._ensure_indexes()

    def ensure_workspace(
        self,
        *,
        case_id: str,
        jurisdiction: str = "pl",
        claim_type: str = "deposit_return",
        status: str = "active",
        claim_amount: float | None = None,
        currency: str | None = None,
        lease_start: str | None = None,
        lease_end: str | None = None,
        move_out_date: str | None = None,
        deposit_return_due_date: str | None = None,
    ) -> None:
        self._runtime.collection(_CASE_WORKSPACES_COLLECTION).update_one(
            {"case_id": case_id},
            {
                "$setOnInsert": {
                    "case_id": case_id,
                    "created_at": _utc_now_iso(),
                    "jurisdiction": jurisdiction,
                    "claim_type": claim_type,
                    "status": status,
                    "claim_amount": claim_amount,
                    "currency": currency,
                    "lease_start": lease_start,
                    "lease_end": lease_end,
                    "move_out_date": move_out_date,
                    "deposit_return_due_date": deposit_return_due_date,
                },
                "$set": {
                    "updated_at": _utc_now_iso(),
                    "status": status,
                    "claim_amount": claim_amount,
                    "currency": currency,
                    "lease_start": lease_start,
                    "lease_end": lease_end,
                    "move_out_date": move_out_date,
                    "deposit_return_due_date": deposit_return_due_date,
                },
            },
            upsert=True,
        )

    def register_case_documents(
        self,
        *,
        case_id: str,
        input_paths: Sequence[Path],
    ) -> list[CaseWorkspaceDocumentRecord]:
        records: list[CaseWorkspaceDocumentRecord] = []
        for input_path in input_paths:
            content = input_path.read_bytes()
            sha256 = hashlib.sha256(content).hexdigest()
            document_id = f"case-doc:{sha256[:16]}"
            record = CaseWorkspaceDocumentRecord(
                document_id=document_id,
                case_id=case_id,
                file_name=input_path.name,
                file_path=str(input_path.resolve()),
                size_bytes=len(content),
                sha256=sha256,
                mime_type=mimetypes.guess_type(input_path.name)[0],
            )
            self._runtime.collection(_CASE_DOCUMENTS_COLLECTION).update_one(
                {"document_id": record.document_id},
                {
                    "$setOnInsert": {
                        "document_id": record.document_id,
                        "case_id": record.case_id,
                        "created_at": _utc_now_iso(),
                    },
                    "$set": {
                        "file_name": record.file_name,
                        "file_path": record.file_path,
                        "size_bytes": record.size_bytes,
                        "sha256": record.sha256,
                        "mime_type": record.mime_type,
                        "updated_at": _utc_now_iso(),
                    },
                },
                upsert=True,
            )
            records.append(record)
        return records

    def ensure_case_facts_slot(self, *, case_id: str) -> None:
        self._runtime.collection(_CASE_FACTS_COLLECTION).update_one(
            {"fact_id": f"facts-pending:{case_id}"},
            {
                "$setOnInsert": {
                    "fact_id": f"facts-pending:{case_id}",
                    "case_id": case_id,
                    "fact_type": "facts_pending",
                    "value": {
                        "status": "pending_extraction",
                        "placeholder_kind": "technical",
                        "reason": (
                            "Scenario 2 case workspace has not yet persisted "
                            "case-level extracted facts."
                        ),
                    },
                    "confidence": None,
                    "source_doc_refs": [],
                    "extracted_at": _utc_now_iso(),
                    "verified_by_user": False,
                    "technical_placeholder": True,
                },
                "$set": {
                    "updated_at": _utc_now_iso(),
                    "technical_placeholder": True,
                },
            },
            upsert=True,
        )

    def record_analysis_run(
        self,
        *,
        case_id: str,
        run_id: str,
        session_id: str,
        scenario_id: str,
        status: str,
        review_status: str,
        verifier_gate_status: str,
        artifacts_root_path: str,
        diagnostics: dict[str, Any] | None = None,
    ) -> None:
        self._runtime.collection(_ANALYSIS_RUNS_COLLECTION).update_one(
            {"run_id": run_id},
            {
                "$setOnInsert": {
                    "run_id": run_id,
                    "case_id": case_id,
                    "session_id": session_id,
                    "scenario_id": scenario_id,
                    "created_at": _utc_now_iso(),
                },
                "$set": {
                    "status": status,
                    "review_status": review_status,
                    "verifier_gate_status": verifier_gate_status,
                    "artifacts_root_path": artifacts_root_path,
                    "diagnostics": diagnostics or {},
                    "updated_at": _utc_now_iso(),
                },
            },
            upsert=True,
        )

    def _ensure_indexes(self) -> None:
        _safe_create_index(
            self._runtime.collection(_CASE_WORKSPACES_COLLECTION),
            [("case_id", 1)],
            unique=True,
        )
        _safe_create_index(
            self._runtime.collection(_CASE_DOCUMENTS_COLLECTION),
            [("document_id", 1)],
            unique=True,
        )
        _safe_create_index(
            self._runtime.collection(_CASE_DOCUMENTS_COLLECTION),
            [("case_id", 1)],
        )
        _safe_create_index(
            self._runtime.collection(_CASE_FACTS_COLLECTION),
            [("fact_id", 1)],
            unique=True,
        )
        _safe_create_index(
            self._runtime.collection(_CASE_FACTS_COLLECTION),
            [("case_id", 1)],
        )
        _safe_create_index(
            self._runtime.collection(_ANALYSIS_RUNS_COLLECTION),
            [("run_id", 1)],
            unique=True,
        )
        _safe_create_index(
            self._runtime.collection(_ANALYSIS_RUNS_COLLECTION),
            [("case_id", 1), ("scenario_id", 1)],
        )


def _safe_create_index(
    collection: _CollectionProtocol,
    keys: list[tuple[str, int]],
    **kwargs: Any,
) -> None:
    create_index = getattr(collection, "create_index", None)
    if callable(create_index):
        create_index(keys, **kwargs)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
