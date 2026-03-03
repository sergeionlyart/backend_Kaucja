"""Pydantic v2 request / response models for /api/v2 endpoints.

TechSpec-first contract:
  - intake: + ``case_status`` field
  - intake/analyze: ``questions`` (not ``open_questions``)
  - analyze: ``analyzed_documents`` (list), + ``analysis_run_id``, + ``warnings``
  - submit: ``case_status`` (not ``status``)
  - document: id/categoryId/name/sizeMb/status(done|error)/progress(0..100)
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------

V2SummaryFieldStatus = Literal["ok", "warn", "muted"]
V2SummaryFieldSourceType = Literal[
    "unknown",
    "intake",
    "document",
    "manual",
    "lease",
    "deposit_payment",
    "handover_protocol",
    "correspondence",
]
V2QuestionPriority = Literal["high", "medium", "low"]
V2DocumentCategoryId = Literal[
    "lease",
    "deposit_payment",
    "handover_protocol",
    "correspondence",
]


class SummaryField(BaseModel):
    id: str
    label: str
    value: str = ""
    status: V2SummaryFieldStatus = "muted"


class FieldMeta(BaseModel):
    source_type: V2SummaryFieldSourceType = "unknown"
    source_label: str = "brak danych"
    document_id: str | None = None
    document_name: str | None = None
    confidence: float | None = None


class ClarificationQuestion(BaseModel):
    id: str
    text: str
    priority: V2QuestionPriority = "medium"
    related_doc_types: list[V2DocumentCategoryId] = Field(default_factory=list)
    answer: str | None = None
    status: Literal["open", "answered"] = "open"


class MissingDoc(BaseModel):
    doc_type: str
    priority: V2QuestionPriority = "medium"
    reason: str = ""


class AnalyzedDocument(BaseModel):
    """Document model aligned with UI v2 TechSpec."""

    id: str
    categoryId: V2DocumentCategoryId  # noqa: N815  - camelCase per UI contract
    name: str
    sizeMb: float  # noqa: N815
    status: Literal["done", "error"] = "done"
    progress: int = Field(default=100, ge=0, le=100)
    extracted_fields: list[str] = Field(default_factory=list)
    analyzed_at: str | None = None
    client_doc_id: str | None = None  # echo back frontend's local doc ID


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


# ---------------------------------------------------------------------------
# Intake
# ---------------------------------------------------------------------------


class IntakeRequest(BaseModel):
    intake_text: str = Field(..., min_length=1, max_length=10_000)
    case_id: str | None = None
    locale: str | None = None


class IntakeResponse(BaseModel):
    case_id: str
    case_status: str
    summary_fields: list[SummaryField]
    fields_meta: dict[str, FieldMeta]
    questions: list[ClarificationQuestion]
    missing_docs: list[MissingDoc]


# ---------------------------------------------------------------------------
# Documents / Analyze
# ---------------------------------------------------------------------------


class DocumentAnalyzeResponse(BaseModel):
    case_id: str
    analyzed_documents: list[AnalyzedDocument]
    summary_fields: list[SummaryField]
    fields_meta: dict[str, FieldMeta]
    questions: list[ClarificationQuestion]
    missing_docs: list[MissingDoc]
    analysis_run_id: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ReanalyzeRequest(BaseModel):
    """Request for server-side reanalyze using previously stored files."""

    case_id: str = Field(..., min_length=1)
    locale: str | None = None
    document_ids: list[str] | None = None
    client_document_ids: list[str] | None = None


# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------


class SubmitConsents(BaseModel):
    terms: bool
    privacy: bool
    marketing: bool = False


class SubmitRequest(BaseModel):
    case_id: str = Field(..., min_length=1)
    locale: str | None = None
    email: str = Field(..., min_length=5)
    consents: SubmitConsents


class SubmitResponse(BaseModel):
    case_id: str
    case_status: str
    submitted_at: str
