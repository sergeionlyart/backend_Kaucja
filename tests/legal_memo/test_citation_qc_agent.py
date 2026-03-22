from __future__ import annotations

from app.legal_memo.citation_qc_agent import build_citation_qc_agent
from app.legal_memo.config import LegalMemoConfig
from app.legal_memo.models import MemoQcReport
from app.legal_memo.prompt_loader import PromptLoader


def test_citation_qc_agent_instantiates_with_output_type() -> None:
    agent = build_citation_qc_agent(
        config=LegalMemoConfig.from_settings(),
        prompt_loader=PromptLoader("app/prompts"),
    )
    assert agent.output_type is MemoQcReport
