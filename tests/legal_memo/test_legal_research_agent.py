from __future__ import annotations

from app.legal_memo.config import LegalMemoConfig
from app.legal_memo.legal_research_agent import build_legal_research_agent
from app.legal_memo.models import ResearchBundle
from app.legal_memo.prompt_loader import PromptLoader


def test_legal_research_agent_instantiates_with_output_type_and_tools() -> None:
    agent = build_legal_research_agent(
        config=LegalMemoConfig.from_settings(),
        prompt_loader=PromptLoader("app/prompts"),
    )
    assert agent.output_type is ResearchBundle
    assert len(agent.tools) == 3
