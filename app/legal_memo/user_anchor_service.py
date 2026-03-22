from __future__ import annotations

from app.legal_memo.anchor_models import AnchoredUserDocument
from app.legal_memo.anchor_parser import parse_anchor_response
from app.legal_memo.anchor_validator import (
    build_user_anchor_catalog,
    validate_anchor_output,
)
from app.legal_memo.config import LegalMemoConfig
from app.legal_memo.prompt_loader import PromptLoader
from app.llm_client.base import LLMClient
from app.llm_client.openai_client import OpenAILLMClient


class UserAnchorService:
    def __init__(
        self,
        *,
        config: LegalMemoConfig,
        prompt_loader: PromptLoader,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.config = config
        self.prompt_loader = prompt_loader
        self.llm_client = llm_client or OpenAILLMClient(
            api_key=config.openai_api_key,
        )

    def anchor_document(
        self,
        *,
        doc_id: str,
        file_name: str,
        markdown: str,
    ) -> AnchoredUserDocument:
        prompt = self.prompt_loader.load(
            prompt_name="kaucja_anchor_markdown",
            version=self.config.prompt_versions.anchor_markdown,
        )
        wrapped_markdown = _wrap_markdown(doc_id=doc_id, markdown=markdown)
        result = self.llm_client.generate_text(
            system_prompt=prompt.system_prompt_text,
            user_content=wrapped_markdown,
            model=self.config.effective_anchor_model,
            params={
                "reasoning_effort": self.config.anchor_reasoning_effort,
                "max_output_tokens": self.config.anchor_max_output_tokens,
            },
            run_meta={"prompt_name": prompt.prompt_name, "prompt_version": prompt.version},
        )
        anchor_index, annotated_markdown = parse_anchor_response(result.raw_text)
        validate_anchor_output(
            source_markdown=wrapped_markdown,
            anchor_index=anchor_index,
            annotated_markdown=annotated_markdown,
            expected_doc_id=doc_id,
        )
        user_anchor_catalog = build_user_anchor_catalog(
            doc_id=doc_id,
            file_name=file_name,
            anchor_index=anchor_index,
        )
        return AnchoredUserDocument(
            doc_id=doc_id,
            file_name=file_name,
            source_markdown=markdown,
            annotated_markdown=annotated_markdown,
            anchor_index=anchor_index,
            validation_warnings=list(anchor_index.validation_warnings),
            user_anchor_catalog=user_anchor_catalog,
        )


def _wrap_markdown(*, doc_id: str, markdown: str) -> str:
    return f'<DOC_START id="{doc_id}">\n{markdown}\n<DOC_END>'
