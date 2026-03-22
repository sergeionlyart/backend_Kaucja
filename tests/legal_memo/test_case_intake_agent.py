from __future__ import annotations

from app.legal_memo.case_intake_agent import build_case_intake_agent
from app.legal_memo.config import LegalMemoConfig
from app.legal_memo.models import CaseIssueSheet
from app.legal_memo.prompt_loader import PromptLoader


def test_case_intake_agent_instantiates_with_output_type() -> None:
    agent = build_case_intake_agent(
        config=LegalMemoConfig.from_settings(),
        prompt_loader=PromptLoader("app/prompts"),
    )
    assert agent.output_type is CaseIssueSheet
