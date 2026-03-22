from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    anchor_id: str


class TimelineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: str
    date: str | None = None
    status: Literal["confirmed", "ambiguous", "missing", "conflict"]
    evidence: list[EvidenceRef] = Field(default_factory=list)


class MoneyFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: str | None = None
    status: Literal["confirmed", "ambiguous", "missing", "conflict"]
    evidence: list[EvidenceRef] = Field(default_factory=list)


class CaseIssueSheet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_goal: str
    case_summary: str
    timeline: list[TimelineItem] = Field(default_factory=list)
    money_facts: list[MoneyFact] = Field(default_factory=list)
    established_facts: list[str] = Field(default_factory=list)
    disputed_facts: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    issue_codes: list[str] = Field(min_length=1)


class ResearchIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_code: str
    question: str
    search_notes: str = ""


class LegalAuthority(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref_id: str = Field(pattern=r"^L\d{2}$")
    doc_id: str
    anchor_id: str
    document_title: str
    locator_label: str
    authority_level: str
    usually_supports: str | None = None
    topic_codes: list[str] = Field(default_factory=list)
    quote: str
    supports_position: Literal["supporting", "adverse", "neutral"]


class SearchTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_calls_used: int = 0
    queries: list[str] = Field(default_factory=list)


class ResearchBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issues: list[ResearchIssue] = Field(default_factory=list)
    legal_authorities: list[LegalAuthority] = Field(default_factory=list)
    coverage_gaps: list[str] = Field(default_factory=list)
    search_trace: SearchTrace


class MemoPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    legal_ref_ids: list[str] = Field(default_factory=list)
    evidence_ref_ids: list[str] = Field(default_factory=list)


class FactsPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    evidence_ref_ids: list[str] = Field(default_factory=list)


class RiskPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    legal_ref_ids: list[str] = Field(default_factory=list)


class LegalAnalysisSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_code: str
    issue_title: str
    analysis_points: list[MemoPoint] = Field(default_factory=list)
    risks: list[RiskPoint] = Field(default_factory=list)
    practical_takeaway: str


class LegalRegisterItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref_id: str = Field(pattern=r"^L\d{2}$")
    doc_id: str
    anchor_id: str
    locator_label: str
    preview: str


class EvidenceRegisterItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref_id: str = Field(pattern=r"^U\d{2}$")
    doc_id: str
    anchor_id: str
    preview: str


class CitationRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    legal: list[LegalRegisterItem] = Field(default_factory=list)
    evidence: list[EvidenceRegisterItem] = Field(default_factory=list)


class StrategicMemo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    executive_summary: list[MemoPoint] = Field(default_factory=list)
    facts_considered: list[FactsPoint] = Field(default_factory=list)
    legal_analysis: list[LegalAnalysisSection] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    citation_register: CitationRegister


class QcIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: Literal["critical", "major", "minor"]
    path: str
    message: str
    suggested_fix: str | None = None


class MemoQcReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pass", "needs_revision", "fail"]
    issues: list[QcIssue] = Field(default_factory=list)
    checked_paths: list[str] = Field(default_factory=list)
    summary: str
