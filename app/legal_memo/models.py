from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceRef(StrictModel):
    doc_id: str
    anchor_id: str


class TimelineItem(StrictModel):
    event: str
    date: str | None = None
    status: Literal["confirmed", "ambiguous", "missing", "conflict"]
    evidence: list[EvidenceRef] = Field(default_factory=list)


class MoneyFact(StrictModel):
    name: str
    value: str | None = None
    status: Literal["confirmed", "ambiguous", "missing", "conflict"]
    evidence: list[EvidenceRef] = Field(default_factory=list)


class CaseIssueSheet(StrictModel):
    user_goal: str
    case_summary: str
    timeline: list[TimelineItem] = Field(default_factory=list)
    money_facts: list[MoneyFact] = Field(default_factory=list)
    established_facts: list[str] = Field(default_factory=list)
    disputed_facts: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    issue_codes: list[str] = Field(default_factory=list)

    @field_validator("issue_codes")
    @classmethod
    def _validate_issue_codes(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if item.strip()]
        if not normalized:
            raise ValueError("issue_codes must contain at least one non-empty item")
        return normalized


class ResearchIssue(StrictModel):
    issue_code: str
    question: str
    search_notes: str = ""


class LegalAuthority(StrictModel):
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


class SearchTraceEntry(StrictModel):
    tool_name: str
    query: str
    hit_count: int = Field(default=0, ge=0)


class SearchTrace(StrictModel):
    tool_calls_used: int = Field(default=0, ge=0)
    queries: list[str] = Field(default_factory=list)
    entries: list[SearchTraceEntry] = Field(default_factory=list)


class ResearchBundle(StrictModel):
    issues: list[ResearchIssue] = Field(default_factory=list)
    legal_authorities: list[LegalAuthority] = Field(default_factory=list)
    coverage_gaps: list[str] = Field(default_factory=list)
    search_trace: SearchTrace

    @model_validator(mode="after")
    def _validate_authority_uniqueness(self) -> "ResearchBundle":
        seen_ref_ids: set[str] = set()
        seen_pairs: set[tuple[str, str]] = set()
        for authority in self.legal_authorities:
            if authority.ref_id in seen_ref_ids:
                raise ValueError(f"duplicate legal ref_id: {authority.ref_id}")
            pair = (authority.doc_id, authority.anchor_id)
            if pair in seen_pairs:
                raise ValueError(
                    "duplicate legal authority for doc_id/anchor_id: "
                    f"{authority.doc_id}#{authority.anchor_id}"
                )
            seen_ref_ids.add(authority.ref_id)
            seen_pairs.add(pair)
        return self


class MemoPoint(StrictModel):
    text: str
    legal_ref_ids: list[str] = Field(default_factory=list)
    evidence_ref_ids: list[str] = Field(default_factory=list)


class FactsPoint(StrictModel):
    text: str
    evidence_ref_ids: list[str] = Field(default_factory=list)


class RiskPoint(StrictModel):
    text: str
    legal_ref_ids: list[str] = Field(default_factory=list)


class LegalAnalysisSection(StrictModel):
    issue_code: str
    issue_title: str
    analysis_points: list[MemoPoint] = Field(default_factory=list)
    risks: list[RiskPoint] = Field(default_factory=list)
    practical_takeaway: str


class LegalRegisterItem(StrictModel):
    ref_id: str = Field(pattern=r"^L\d{2}$")
    doc_id: str
    anchor_id: str
    locator_label: str
    preview: str


class EvidenceRegisterItem(StrictModel):
    ref_id: str = Field(pattern=r"^U\d{2}$")
    doc_id: str
    anchor_id: str
    preview: str


class CitationRegister(StrictModel):
    legal: list[LegalRegisterItem] = Field(default_factory=list)
    evidence: list[EvidenceRegisterItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_alias_uniqueness(self) -> "CitationRegister":
        legal_ids = [item.ref_id for item in self.legal]
        evidence_ids = [item.ref_id for item in self.evidence]
        if len(legal_ids) != len(set(legal_ids)):
            raise ValueError("duplicate legal aliases in citation register")
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("duplicate evidence aliases in citation register")
        return self


class StrategicMemo(StrictModel):
    title: str
    executive_summary: list[MemoPoint] = Field(default_factory=list)
    facts_considered: list[FactsPoint] = Field(default_factory=list)
    legal_analysis: list[LegalAnalysisSection] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    citation_register: CitationRegister


class QcIssue(StrictModel):
    severity: Literal["critical", "major", "minor"]
    path: str
    message: str
    suggested_fix: str | None = None


class MemoQcReport(StrictModel):
    status: Literal["pass", "needs_revision", "fail"]
    issues: list[QcIssue] = Field(default_factory=list)
    checked_paths: list[str] = Field(default_factory=list)
    summary: str
