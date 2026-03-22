from __future__ import annotations

from app.legal_memo.anchor_models import UserAnchorCatalogItem
from app.legal_memo.models import CaseIssueSheet, MoneyFact, TimelineItem, EvidenceRef
from app.legal_memo.validators import build_evidence_register


def test_build_evidence_register_is_deterministic_and_deduplicates() -> None:
    case_issue_sheet = CaseIssueSheet(
        user_goal="Recover the deposit",
        case_summary="Landlord retained funds",
        timeline=[
            TimelineItem(
                event="Lease signed",
                status="confirmed",
                evidence=[EvidenceRef(doc_id="lease.md", anchor_id="s01-p001")],
            ),
            TimelineItem(
                event="Move out",
                status="confirmed",
                evidence=[EvidenceRef(doc_id="lease.md", anchor_id="s01-p001")],
            ),
        ],
        money_facts=[
            MoneyFact(
                name="Deposit",
                value="3000 PLN",
                status="confirmed",
                evidence=[EvidenceRef(doc_id="handover.md", anchor_id="s02-p002")],
            )
        ],
        issue_codes=["deposit_return_term"],
    )
    catalog = [
        UserAnchorCatalogItem(
            doc_id="lease.md",
            file_name="lease.md",
            anchor_id="s01-p001",
            section_path="s01",
            anchor_type="paragraph",
            order=1,
            preview="The deposit is 3000 PLN.",
        ),
        UserAnchorCatalogItem(
            doc_id="handover.md",
            file_name="handover.md",
            anchor_id="s02-p002",
            section_path="s02",
            anchor_type="paragraph",
            order=2,
            preview="Keys were returned.",
        ),
    ]

    register = build_evidence_register(
        case_issue_sheet=case_issue_sheet,
        user_anchor_catalog=catalog,
    )
    assert [item.ref_id for item in register] == ["U01", "U02"]
    assert register[0].doc_id == "lease.md"
    assert register[1].doc_id == "handover.md"
