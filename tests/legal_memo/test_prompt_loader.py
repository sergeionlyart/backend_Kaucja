from __future__ import annotations

from app.legal_memo.prompt_loader import PromptLoader


def test_prompt_loader_loads_plain_text_anchor_prompt() -> None:
    loader = PromptLoader("app/prompts")
    prompt = loader.load(prompt_name="kaucja_anchor_markdown", version="v001")
    assert prompt.response_mode == "plain_text"
    assert prompt.schema == {}
    assert "deterministic anchor-markup module" in prompt.system_prompt_text


def test_prompt_loader_loads_structured_prompt_schema() -> None:
    loader = PromptLoader("app/prompts")
    prompt = loader.load(prompt_name="kaucja_case_intake_agent", version="v001")
    assert prompt.response_mode == "structured_json"
    assert prompt.schema is not None
    assert prompt.schema["title"] == "CaseIssueSheet"
