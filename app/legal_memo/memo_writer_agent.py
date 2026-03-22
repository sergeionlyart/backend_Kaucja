from __future__ import annotations

import json

from agents import Agent

from app.legal_memo.config import LegalMemoConfig
from app.legal_memo.models import (
    CaseIssueSheet,
    EvidenceRegisterItem,
    ResearchBundle,
    StrategicMemo,
)
from app.legal_memo.prompt_loader import PromptLoader


def build_memo_writer_agent(
    *,
    config: LegalMemoConfig,
    prompt_loader: PromptLoader,
) -> Agent[None]:
    prompt = prompt_loader.load(
        prompt_name="kaucja_memo_writer_agent",
        version=config.prompt_versions.memo_writer_agent,
    )
    return Agent(
        name="MemoWriterAgent",
        instructions=prompt.system_prompt_text,
        model=config.model,
        output_type=StrategicMemo,
    )


def build_memo_writer_input(
    *,
    user_message: str,
    case_issue_sheet: CaseIssueSheet,
    research_bundle: ResearchBundle,
    evidence_register: list[EvidenceRegisterItem],
) -> str:
    return (
        f"<USER_MESSAGE>\n{user_message}\n</USER_MESSAGE>\n\n"
        "<CASE_ISSUE_SHEET>\n"
        f"{case_issue_sheet.model_dump_json(indent=2)}\n"
        "</CASE_ISSUE_SHEET>\n\n"
        "<RESEARCH_BUNDLE>\n"
        f"{research_bundle.model_dump_json(indent=2)}\n"
        "</RESEARCH_BUNDLE>\n\n"
        "<EVIDENCE_REGISTER>\n"
        f"{json.dumps([item.model_dump(mode='json') for item in evidence_register], ensure_ascii=False, indent=2)}\n"
        "</EVIDENCE_REGISTER>"
    )
