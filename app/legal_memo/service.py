from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from agents import Runner

from app.legal_memo.anchor_models import AnchoredUserDocument
from app.legal_memo.case_intake_agent import (
    build_case_intake_agent,
    build_case_intake_input,
)
from app.legal_memo.citation_qc_agent import (
    build_citation_qc_agent,
    build_citation_qc_input,
)
from app.legal_memo.config import LegalMemoConfig
from app.legal_memo.legal_research_agent import (
    build_legal_research_agent,
    build_legal_research_input,
)
from app.legal_memo.memo_writer_agent import (
    build_memo_writer_agent,
    build_memo_writer_input,
)
from app.legal_memo.models import (
    CaseIssueSheet,
    MemoQcReport,
    ResearchBundle,
    StrategicMemo,
)
from app.legal_memo.mongo_search_tools import LegalSearchContext
from app.legal_memo.prompt_loader import PromptLoader
from app.legal_memo.renderer import render_memo_markdown
from app.legal_memo.user_anchor_service import UserAnchorService
from app.legal_memo.validators import (
    build_evidence_register,
    citation_register_from_memo,
    validate_memo_references,
)
from app.storage.artifacts import ArtifactsManager


class RunnerProtocol(Protocol):
    def __call__(
        self,
        agent: Any,
        input: str,
        *,
        context: Any | None = None,
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class UserDocumentInput:
    doc_id: str
    file_name: str
    markdown: str


@dataclass(frozen=True, slots=True)
class StrategicMemoServiceResult:
    session_id: str
    run_id: str
    artifacts_root_path: Path
    anchored_documents: list[AnchoredUserDocument]
    case_issue_sheet: CaseIssueSheet
    evidence_register_path: Path
    research_bundle: ResearchBundle
    strategic_memo: StrategicMemo
    qc_report: MemoQcReport
    memo_markdown_path: Path
    citation_register_path: Path
    search_trace_path: Path


class StrategicMemoService:
    def __init__(
        self,
        *,
        config: LegalMemoConfig,
        mongo_db: Any,
        prompt_loader: PromptLoader | None = None,
        anchor_service: UserAnchorService | None = None,
        agent_runner: RunnerProtocol | None = None,
    ) -> None:
        self.config = config
        self.mongo_db = mongo_db
        self.prompt_loader = prompt_loader or PromptLoader(config.resolved_prompts_root)
        self.anchor_service = anchor_service or UserAnchorService(
            config=config,
            prompt_loader=self.prompt_loader,
        )
        self.agent_runner = agent_runner or _default_agent_runner
        self.artifacts_manager = ArtifactsManager(config.resolved_data_dir)

    def run(
        self,
        *,
        user_message: str,
        user_documents: list[UserDocumentInput],
        session_id: str | None = None,
        run_id: str | None = None,
    ) -> StrategicMemoServiceResult:
        if not user_documents:
            raise ValueError("at least one user document is required")

        resolved_session_id = session_id or str(uuid4())
        resolved_run_id = run_id or str(uuid4())
        run_artifacts = self.artifacts_manager.create_run_artifacts(
            session_id=resolved_session_id,
            run_id=resolved_run_id,
        )
        outputs_dir = run_artifacts.artifacts_root_path / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        anchored_documents = self._anchor_documents(
            user_documents=user_documents,
            artifacts_root_path=run_artifacts.artifacts_root_path,
        )
        case_issue_sheet = self._run_case_intake(
            user_message=user_message,
            anchored_documents=anchored_documents,
        )
        evidence_register = build_evidence_register(
            case_issue_sheet=case_issue_sheet,
            user_anchor_catalog=[
                item
                for document in anchored_documents
                for item in document.user_anchor_catalog
            ],
        )
        evidence_register_path = outputs_dir / "evidence_register.json"
        _write_json(
            evidence_register_path,
            [item.model_dump(mode="json") for item in evidence_register],
        )

        search_context = LegalSearchContext(
            db=self.mongo_db,
            master_collection_name=self.config.master_collection_name,
            anchor_collection_name=self.config.anchor_collection_name,
            search_calls_left=self.config.max_search_calls,
            max_docs_per_search=self.config.max_docs_per_search,
            max_anchors_per_search=self.config.max_anchors_per_search,
            legal_refs_left=self.config.legal_refs_left,
        )
        research_bundle = self._run_legal_research(
            user_message=user_message,
            case_issue_sheet=case_issue_sheet,
            search_context=search_context,
        )
        strategic_memo = self._run_memo_writer(
            user_message=user_message,
            case_issue_sheet=case_issue_sheet,
            research_bundle=research_bundle,
            evidence_register=evidence_register,
        )
        validate_memo_references(
            memo=strategic_memo,
            research_bundle=research_bundle,
        )
        qc_report = self._run_citation_qc(
            memo=strategic_memo,
            case_issue_sheet=case_issue_sheet,
            research_bundle=research_bundle,
        )

        case_issue_sheet_path = outputs_dir / "case_issue_sheet.json"
        research_bundle_path = outputs_dir / "research_bundle.json"
        memo_json_path = outputs_dir / "memo.json"
        memo_markdown_path = outputs_dir / "memo.md"
        citation_register_path = outputs_dir / "citation_register.json"
        search_trace_path = outputs_dir / "search_trace.json"
        qc_report_path = outputs_dir / "qc_report.json"

        _write_json(case_issue_sheet_path, case_issue_sheet.model_dump(mode="json"))
        _write_json(research_bundle_path, research_bundle.model_dump(mode="json"))
        _write_json(memo_json_path, strategic_memo.model_dump(mode="json"))
        memo_markdown_path.write_text(
            render_memo_markdown(strategic_memo),
            encoding="utf-8",
        )
        _write_json(
            citation_register_path,
            citation_register_from_memo(strategic_memo).model_dump(mode="json"),
        )
        _write_json(
            search_trace_path,
            search_context.to_search_trace().model_dump(mode="json"),
        )
        _write_json(qc_report_path, qc_report.model_dump(mode="json"))

        return StrategicMemoServiceResult(
            session_id=resolved_session_id,
            run_id=resolved_run_id,
            artifacts_root_path=run_artifacts.artifacts_root_path,
            anchored_documents=anchored_documents,
            case_issue_sheet=case_issue_sheet,
            evidence_register_path=evidence_register_path,
            research_bundle=research_bundle,
            strategic_memo=strategic_memo,
            qc_report=qc_report,
            memo_markdown_path=memo_markdown_path,
            citation_register_path=citation_register_path,
            search_trace_path=search_trace_path,
        )

    def _anchor_documents(
        self,
        *,
        user_documents: list[UserDocumentInput],
        artifacts_root_path: Path,
    ) -> list[AnchoredUserDocument]:
        anchored: list[AnchoredUserDocument] = []
        for document in user_documents:
            anchored_doc = self.anchor_service.anchor_document(
                doc_id=document.doc_id,
                file_name=document.file_name,
                markdown=document.markdown,
            )
            document_root = artifacts_root_path / "documents" / document.doc_id
            original_dir = document_root / "original"
            anchors_dir = document_root / "anchors"
            original_dir.mkdir(parents=True, exist_ok=True)
            anchors_dir.mkdir(parents=True, exist_ok=True)
            (original_dir / "source.md").write_text(
                document.markdown,
                encoding="utf-8",
            )
            (anchors_dir / "annotated.md").write_text(
                anchored_doc.annotated_markdown,
                encoding="utf-8",
            )
            _write_json(
                anchors_dir / "anchor_index.json",
                anchored_doc.anchor_index.model_dump(mode="json"),
            )
            anchored.append(anchored_doc)
        return anchored

    def _run_case_intake(
        self,
        *,
        user_message: str,
        anchored_documents: list[AnchoredUserDocument],
    ) -> CaseIssueSheet:
        agent = build_case_intake_agent(
            config=self.config,
            prompt_loader=self.prompt_loader,
        )
        raw_output = self.agent_runner(
            agent,
            build_case_intake_input(
                user_message=user_message,
                anchored_documents=anchored_documents,
            ),
            context=None,
        )
        return _coerce_model_output(raw_output, CaseIssueSheet)

    def _run_legal_research(
        self,
        *,
        user_message: str,
        case_issue_sheet: CaseIssueSheet,
        search_context: LegalSearchContext,
    ) -> ResearchBundle:
        agent = build_legal_research_agent(
            config=self.config,
            prompt_loader=self.prompt_loader,
        )
        raw_output = self.agent_runner(
            agent,
            build_legal_research_input(
                user_message=user_message,
                case_issue_sheet=case_issue_sheet,
            ),
            context=search_context,
        )
        return _coerce_model_output(raw_output, ResearchBundle)

    def _run_memo_writer(
        self,
        *,
        user_message: str,
        case_issue_sheet: CaseIssueSheet,
        research_bundle: ResearchBundle,
        evidence_register: list[Any],
    ) -> StrategicMemo:
        agent = build_memo_writer_agent(
            config=self.config,
            prompt_loader=self.prompt_loader,
        )
        raw_output = self.agent_runner(
            agent,
            build_memo_writer_input(
                user_message=user_message,
                case_issue_sheet=case_issue_sheet,
                research_bundle=research_bundle,
                evidence_register=evidence_register,
            ),
            context=None,
        )
        return _coerce_model_output(raw_output, StrategicMemo)

    def _run_citation_qc(
        self,
        *,
        memo: StrategicMemo,
        case_issue_sheet: CaseIssueSheet,
        research_bundle: ResearchBundle,
    ) -> MemoQcReport:
        agent = build_citation_qc_agent(
            config=self.config,
            prompt_loader=self.prompt_loader,
        )
        raw_output = self.agent_runner(
            agent,
            build_citation_qc_input(
                memo=memo,
                case_issue_sheet=case_issue_sheet,
                research_bundle=research_bundle,
            ),
            context=None,
        )
        return _coerce_model_output(raw_output, MemoQcReport)


def _default_agent_runner(agent: Any, input: str, *, context: Any | None = None) -> Any:
    return Runner.run_sync(agent, input, context=context)


def _coerce_model_output(raw_output: Any, model_type: type[Any]) -> Any:
    output = getattr(raw_output, "final_output", raw_output)
    if isinstance(output, model_type):
        return output
    return model_type.model_validate(output)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
