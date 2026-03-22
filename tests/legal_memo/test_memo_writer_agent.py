from __future__ import annotations

from app.legal_memo.config import LegalMemoConfig
from app.legal_memo.memo_writer_agent import build_memo_writer_agent
from app.legal_memo.models import StrategicMemo
from app.legal_memo.prompt_loader import PromptLoader


def test_memo_writer_agent_instantiates_with_output_type() -> None:
    agent = build_memo_writer_agent(
        config=LegalMemoConfig.from_settings(),
        prompt_loader=PromptLoader("app/prompts"),
    )
    assert agent.output_type is StrategicMemo
