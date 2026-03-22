from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.config.settings import Settings, get_settings


class PromptVersions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    anchor_markdown: str = "v001"
    case_intake_agent: str = "v001"
    legal_research_agent: str = "v001"
    memo_writer_agent: str = "v001"
    citation_qc_agent: str = "v001"
    main_pipeline_agent: str = "v001"


class LegalMemoConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    prompts_root: Path = Path("app/prompts")
    data_dir: Path = Path("data")

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "kaucja_legal_corpus"
    master_collection_name: str = "documents_cas_law_v2_2_prod_v3"
    anchor_collection_name: str = "legal_anchor_nodes_proto_v1"

    max_search_calls: int = Field(default=6, ge=1)
    max_docs_per_search: int = Field(default=5, ge=1)
    max_anchors_per_search: int = Field(default=8, ge=1)
    legal_refs_left: int = Field(default=10, ge=1)

    model: str = "gpt-5.4"
    anchor_model: str | None = None
    openai_api_key: str | None = None
    anchor_reasoning_effort: str = "low"
    anchor_max_output_tokens: int = Field(default=24_000, ge=1)

    prompt_versions: PromptVersions = Field(default_factory=PromptVersions)

    @property
    def resolved_prompts_root(self) -> Path:
        return self.prompts_root.resolve()

    @property
    def resolved_data_dir(self) -> Path:
        return self.data_dir.resolve()

    @property
    def effective_anchor_model(self) -> str:
        return self.anchor_model or self.model

    @classmethod
    def from_settings(
        cls,
        settings: Settings | None = None,
        **overrides: object,
    ) -> "LegalMemoConfig":
        active_settings = settings or get_settings()
        base = cls(
            prompts_root=active_settings.project_root / "app" / "prompts",
            data_dir=active_settings.resolved_data_dir,
            openai_api_key=active_settings.openai_api_key,
        )
        if not overrides:
            return base
        return base.model_copy(update=overrides)
