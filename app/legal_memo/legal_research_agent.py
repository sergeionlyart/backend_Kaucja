from __future__ import annotations

from agents import Agent

from app.legal_memo.config import LegalMemoConfig
from app.legal_memo.models import CaseIssueSheet, ResearchBundle
from app.legal_memo.mongo_search_tools import LegalSearchContext, build_search_tools
from app.legal_memo.prompt_loader import PromptLoader


def build_legal_research_agent(
    *,
    config: LegalMemoConfig,
    prompt_loader: PromptLoader,
) -> Agent[LegalSearchContext]:
    prompt = prompt_loader.load(
        prompt_name="kaucja_legal_research_agent",
        version=config.prompt_versions.legal_research_agent,
    )
    return Agent(
        name="LegalResearchAgent",
        instructions=prompt.system_prompt_text,
        model=config.model,
        tools=build_search_tools(),
        output_type=ResearchBundle,
    )


def build_legal_research_input(
    *,
    user_message: str,
    case_issue_sheet: CaseIssueSheet,
) -> str:
    return (
        f"<USER_MESSAGE>\n{user_message}\n</USER_MESSAGE>\n\n"
        "<CASE_ISSUE_SHEET>\n"
        f"{case_issue_sheet.model_dump_json(indent=2)}\n"
        "</CASE_ISSUE_SHEET>"
    )
