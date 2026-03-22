from __future__ import annotations

import json

from agents import Agent

from app.legal_memo.anchor_models import AnchoredUserDocument
from app.legal_memo.config import LegalMemoConfig
from app.legal_memo.models import CaseIssueSheet, EvidenceRegisterItem
from app.legal_memo.prompt_loader import PromptLoader


def build_case_intake_agent(
    *,
    config: LegalMemoConfig,
    prompt_loader: PromptLoader,
) -> Agent[None]:
    prompt = prompt_loader.load(
        prompt_name="kaucja_case_intake_agent",
        version=config.prompt_versions.case_intake_agent,
    )
    return Agent(
        name="CaseIntakeAgent",
        instructions=prompt.system_prompt_text,
        model=config.model,
        output_type=CaseIssueSheet,
    )


def build_case_intake_input(
    *,
    user_message: str,
    anchored_documents: list[AnchoredUserDocument],
    evidence_register: list[EvidenceRegisterItem] | None = None,
) -> str:
    documents_payload = [
        {
            "doc_id": item.doc_id,
            "file_name": item.file_name,
            "annotated_markdown": item.annotated_markdown,
            "validation_warnings": item.validation_warnings,
        }
        for item in anchored_documents
    ]
    evidence_payload = [item.model_dump(mode="json") for item in (evidence_register or [])]
    return (
        f"<USER_MESSAGE>\n{user_message}\n</USER_MESSAGE>\n\n"
        "<ANCHORED_USER_DOCUMENTS>\n"
        f"{json.dumps(documents_payload, ensure_ascii=False, indent=2)}\n"
        "</ANCHORED_USER_DOCUMENTS>\n\n"
        "<EVIDENCE_REGISTER>\n"
        f"{json.dumps(evidence_payload, ensure_ascii=False, indent=2)}\n"
        "</EVIDENCE_REGISTER>"
    )
