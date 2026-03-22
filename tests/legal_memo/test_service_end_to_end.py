from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tests.fake_mongo_runtime import FakeMongoCollection

from app.legal_memo.anchor_models import AnchorIndex, AnchoredUserDocument
from app.legal_memo.config import LegalMemoConfig
from app.legal_memo.models import (
    CaseIssueSheet,
    CitationRegister,
    EvidenceRef,
    LegalAnalysisSection,
    LegalAuthority,
    LegalRegisterItem,
    MemoPoint,
    MemoQcReport,
    ResearchBundle,
    ResearchIssue,
    SearchTrace,
    StrategicMemo,
    TimelineItem,
)
from app.legal_memo.prompt_loader import PromptLoader
from app.legal_memo.service import StrategicMemoService, UserDocumentInput


@dataclass
class FakeDb:
    collections: dict[str, FakeMongoCollection]

    def __getitem__(self, name: str) -> FakeMongoCollection:
        return self.collections[name]


class FakeAnchorService:
    def anchor_document(self, *, doc_id: str, file_name: str, markdown: str) -> AnchoredUserDocument:
        anchor_index = AnchorIndex.model_validate(
            {
                "anchor_schema": "md-anchor-v0-proto",
                "doc_id": doc_id,
                "source_wrapper": "doc_wrapper",
                "validation_warnings": [],
                "anchors": [
                    {
                        "anchor_id": "s01-p001",
                        "parent_anchor": None,
                        "type": "paragraph",
                        "section_path": "s01",
                        "order": 1,
                        "synthetic": False,
                        "locator": {"kind": "block", "row": None},
                        "preview": markdown[:40],
                    }
                ],
            }
        )
        return AnchoredUserDocument(
            doc_id=doc_id,
            file_name=file_name,
            source_markdown=markdown,
            annotated_markdown=f'<DOC_START id="{doc_id}">\n<!--anchor:s01-p001-->{markdown}\n<DOC_END>',
            anchor_index=anchor_index,
            user_anchor_catalog=[
                {
                    "doc_id": doc_id,
                    "file_name": file_name,
                    "anchor_id": "s01-p001",
                    "parent_anchor": None,
                    "section_path": "s01",
                    "anchor_type": "paragraph",
                    "order": 1,
                    "preview": markdown[:40],
                }
            ],
        )


@dataclass
class FakeRunResult:
    final_output: object


def fake_runner(agent, input: str, *, context=None):  # noqa: ANN001
    if agent.name == "CaseIntakeAgent":
        return FakeRunResult(
            CaseIssueSheet(
                user_goal="Recover deposit",
                case_summary="Tenant seeks return of the deposit.",
                timeline=[
                    TimelineItem(
                        event="Move out",
                        status="confirmed",
                        evidence=[EvidenceRef(doc_id="lease.md", anchor_id="s01-p001")],
                    )
                ],
                issue_codes=["deposit_return_term"],
            )
        )
    if agent.name == "LegalResearchAgent":
        return FakeRunResult(
            ResearchBundle(
                issues=[ResearchIssue(issue_code="deposit_return_term", question="Deadline?")],
                legal_authorities=[
                    LegalAuthority(
                        ref_id="L01",
                        doc_id="act-1",
                        anchor_id="s01-p001",
                        document_title="Ustawa o ochronie praw lokatorow",
                        locator_label="Art. 6 ust. 4",
                        authority_level="primary",
                        usually_supports="both",
                        topic_codes=["deposit_return_term"],
                        quote="Zwrot kaucji powinien nastapic...",
                        supports_position="supporting",
                    )
                ],
                coverage_gaps=[],
                search_trace=SearchTrace(),
            )
        )
    if agent.name == "MemoWriterAgent":
        return FakeRunResult(
            StrategicMemo(
                title="Стратегический меморандум",
                executive_summary=[
                    MemoPoint(
                        text="Арендатор может требовать возврат депозита.",
                        legal_ref_ids=["L01"],
                        evidence_ref_ids=["U01"],
                    )
                ],
                facts_considered=[],
                legal_analysis=[
                    LegalAnalysisSection(
                        issue_code="deposit_return_term",
                        issue_title="Срок возврата кауции",
                        analysis_points=[
                            MemoPoint(
                                text="Срок возврата связан с завершением найма.",
                                legal_ref_ids=["L01"],
                                evidence_ref_ids=["U01"],
                            )
                        ],
                        risks=[],
                        practical_takeaway="Нужно направить требование о возврате.",
                    )
                ],
                recommended_next_steps=["Подготовить wezwanie do zaplaty."],
                limitations=[],
                citation_register=CitationRegister(
                    legal=[
                        LegalRegisterItem(
                            ref_id="L01",
                            doc_id="act-1",
                            anchor_id="s01-p001",
                            locator_label="Art. 6 ust. 4",
                            preview="Zwrot kaucji powinien nastapic...",
                        )
                    ],
                    evidence=[
                        {
                            "ref_id": "U01",
                            "doc_id": "lease.md",
                            "anchor_id": "s01-p001",
                            "preview": "Kaucja wynosi 3000 PLN.",
                        }
                    ],
                ),
            )
        )
    if agent.name == "CitationQCAgent":
        return FakeRunResult(
            MemoQcReport(
                status="pass",
                issues=[],
                checked_paths=["executive_summary[0]"],
                summary="All checks passed.",
            )
        )
    raise AssertionError(f"Unexpected agent {agent.name}")


def test_service_runs_vertical_slice(tmp_path) -> None:
    config = LegalMemoConfig.from_settings(
        data_dir=tmp_path / "data",
        prompts_root=Path("app/prompts"),
        master_collection_name="master",
        anchor_collection_name="anchors",
    )
    mongo_db = FakeDb(
        {
            "master": FakeMongoCollection([]),
            "anchors": FakeMongoCollection([]),
        }
    )
    service = StrategicMemoService(
        config=config,
        mongo_db=mongo_db,
        prompt_loader=PromptLoader("app/prompts"),
        anchor_service=FakeAnchorService(),
        agent_runner=fake_runner,
    )
    result = service.run(
        user_message="Please help recover the deposit.",
        user_documents=[
            UserDocumentInput(
                doc_id="lease.md",
                file_name="lease.md",
                markdown="Kaucja wynosi 3000 PLN.",
            ),
            UserDocumentInput(
                doc_id="handover.md",
                file_name="handover.md",
                markdown="Lokal zwrocono bez uwag.",
            ),
        ],
        session_id="session-1",
        run_id="run-1",
    )

    assert result.case_issue_sheet.issue_codes == ["deposit_return_term"]
    assert result.strategic_memo.citation_register.legal[0].ref_id == "L01"
    assert result.qc_report.status == "pass"
    assert result.memo_markdown_path.exists()
    assert result.citation_register_path.exists()
    assert (tmp_path / "data" / "sessions" / "session-1" / "runs" / "run-1" / "documents" / "lease.md" / "anchors" / "anchor_index.json").exists()
