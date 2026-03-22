from __future__ import annotations

import pytest

from app.legal_memo.models import (
    CaseIssueSheet,
    CitationRegister,
    EvidenceRegisterItem,
    LegalRegisterItem,
    MemoQcReport,
    QcIssue,
)


def test_case_issue_sheet_requires_non_empty_issue_codes() -> None:
    with pytest.raises(ValueError):
        CaseIssueSheet(
            user_goal="Recover the deposit",
            case_summary="Landlord withheld funds",
            issue_codes=[],
        )


def test_citation_register_validates_alias_patterns() -> None:
    with pytest.raises(ValueError):
        CitationRegister(
            legal=[
                LegalRegisterItem(
                    ref_id="LX1",
                    doc_id="doc-1",
                    anchor_id="s01-p001",
                    locator_label="Art. 6",
                    preview="Preview",
                )
            ],
            evidence=[],
        )

    register = CitationRegister(
        legal=[
            LegalRegisterItem(
                ref_id="L01",
                doc_id="doc-1",
                anchor_id="s01-p001",
                locator_label="Art. 6",
                preview="Preview",
            )
        ],
        evidence=[
            EvidenceRegisterItem(
                ref_id="U01",
                doc_id="lease.md",
                anchor_id="s01-p001",
                preview="Lease clause",
            )
        ],
    )
    assert register.legal[0].ref_id == "L01"
    assert register.evidence[0].ref_id == "U01"


def test_memo_qc_report_accepts_valid_payload() -> None:
    report = MemoQcReport(
        status="needs_revision",
        issues=[
            QcIssue(
                severity="major",
                path="executive_summary[0]",
                message="Missing legal support",
                suggested_fix="Add L01",
            )
        ],
        checked_paths=["executive_summary[0]"],
        summary="One issue found",
    )
    assert report.status == "needs_revision"
