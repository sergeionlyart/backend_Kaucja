from __future__ import annotations

from agents import Agent

from app.legal_memo.config import LegalMemoConfig
from app.legal_memo.models import CaseIssueSheet, MemoQcReport, ResearchBundle, StrategicMemo
from app.legal_memo.prompt_loader import PromptLoader


def build_citation_qc_agent(
    *,
    config: LegalMemoConfig,
    prompt_loader: PromptLoader,
) -> Agent[None]:
    prompt = prompt_loader.load(
        prompt_name="kaucja_citation_qc_agent",
        version=config.prompt_versions.citation_qc_agent,
    )
    return Agent(
        name="CitationQCAgent",
        instructions=prompt.system_prompt_text,
        model=config.model,
        output_type=MemoQcReport,
    )


def build_citation_qc_input(
    *,
    memo: StrategicMemo,
    case_issue_sheet: CaseIssueSheet,
    research_bundle: ResearchBundle,
) -> str:
    return (
        "<STRATEGIC_MEMO>\n"
        f"{memo.model_dump_json(indent=2)}\n"
        "</STRATEGIC_MEMO>\n\n"
        "<CASE_ISSUE_SHEET>\n"
        f"{case_issue_sheet.model_dump_json(indent=2)}\n"
        "</CASE_ISSUE_SHEET>\n\n"
        "<RESEARCH_BUNDLE>\n"
        f"{research_bundle.model_dump_json(indent=2)}\n"
        "</RESEARCH_BUNDLE>"
    )
