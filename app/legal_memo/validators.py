from __future__ import annotations

from typing import Iterable

from app.legal_memo.anchor_models import UserAnchorCatalogItem
from app.legal_memo.anchor_validator import build_anchor_preview_lookup
from app.legal_memo.models import (
    CaseIssueSheet,
    CitationRegister,
    EvidenceRegisterItem,
    ResearchBundle,
    StrategicMemo,
)


def build_evidence_register(
    *,
    case_issue_sheet: CaseIssueSheet,
    user_anchor_catalog: Iterable[UserAnchorCatalogItem],
) -> list[EvidenceRegisterItem]:
    preview_lookup = build_anchor_preview_lookup(user_anchor_catalog)
    ordered_pairs: list[tuple[str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for evidence_ref in _iter_case_evidence_refs(case_issue_sheet):
        pair = (evidence_ref.doc_id, evidence_ref.anchor_id)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        ordered_pairs.append(pair)

    register: list[EvidenceRegisterItem] = []
    for index, pair in enumerate(ordered_pairs, start=1):
        preview = preview_lookup.get(pair, "")
        register.append(
            EvidenceRegisterItem(
                ref_id=f"U{index:02d}",
                doc_id=pair[0],
                anchor_id=pair[1],
                preview=preview,
            )
        )
    return register


def validate_memo_references(
    *,
    memo: StrategicMemo,
    research_bundle: ResearchBundle,
) -> None:
    citation_register = memo.citation_register
    legal_ids = {item.ref_id for item in citation_register.legal}
    evidence_ids = {item.ref_id for item in citation_register.evidence}
    research_ref_ids = {item.ref_id for item in research_bundle.legal_authorities}

    used_legal_ids: set[str] = set()
    used_evidence_ids: set[str] = set()
    for point in memo.executive_summary:
        used_legal_ids.update(point.legal_ref_ids)
        used_evidence_ids.update(point.evidence_ref_ids)
    for point in memo.facts_considered:
        used_evidence_ids.update(point.evidence_ref_ids)
    for section in memo.legal_analysis:
        for point in section.analysis_points:
            used_legal_ids.update(point.legal_ref_ids)
            used_evidence_ids.update(point.evidence_ref_ids)
        for risk in section.risks:
            used_legal_ids.update(risk.legal_ref_ids)

    missing_legal = sorted(used_legal_ids - legal_ids)
    missing_evidence = sorted(used_evidence_ids - evidence_ids)
    unknown_register_legal = sorted(legal_ids - research_ref_ids)
    if missing_legal:
        raise ValueError(f"memo uses unknown legal refs: {missing_legal}")
    if missing_evidence:
        raise ValueError(f"memo uses unknown evidence refs: {missing_evidence}")
    if unknown_register_legal:
        raise ValueError(
            "citation register contains legal refs missing from ResearchBundle: "
            f"{unknown_register_legal}"
        )
    _assert_no_raw_document_refs(
        memo=memo,
        citation_register=citation_register,
    )


def citation_register_from_memo(memo: StrategicMemo) -> CitationRegister:
    return memo.citation_register


def _iter_case_evidence_refs(case_issue_sheet: CaseIssueSheet):
    for item in case_issue_sheet.timeline:
        yield from item.evidence
    for item in case_issue_sheet.money_facts:
        yield from item.evidence


def _assert_no_raw_document_refs(
    *,
    memo: StrategicMemo,
    citation_register: CitationRegister,
) -> None:
    narrative_segments = [memo.title, *memo.recommended_next_steps, *memo.limitations]
    narrative_segments.extend(point.text for point in memo.executive_summary)
    narrative_segments.extend(point.text for point in memo.facts_considered)
    for section in memo.legal_analysis:
        narrative_segments.append(section.issue_title)
        narrative_segments.append(section.practical_takeaway)
        narrative_segments.extend(point.text for point in section.analysis_points)
        narrative_segments.extend(risk.text for risk in section.risks)

    narrative_text = "\n".join(narrative_segments)
    forbidden_tokens = {
        item.doc_id for item in citation_register.legal
    } | {
        item.anchor_id for item in citation_register.legal
    } | {
        item.doc_id for item in citation_register.evidence
    } | {
        item.anchor_id for item in citation_register.evidence
    }
    for token in sorted(forbidden_tokens):
        if token and token in narrative_text:
            raise ValueError(f"memo narrative contains raw citation token: {token}")
