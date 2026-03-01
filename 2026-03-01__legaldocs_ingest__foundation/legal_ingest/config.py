import yaml
import os
import re
from typing import Literal, Dict, Any, List, Optional
from pydantic import BaseModel, HttpUrl, Field, ConfigDict


class HttpConfig(BaseModel):
    user_agent: str = "LegalRAG-Ingest/0.1"
    timeout_seconds: int = 60
    max_retries: int = 4
    retry_backoff_seconds: float = 2.0
    model_config = ConfigDict(extra="forbid")


class RunConfig(BaseModel):
    run_id: str = "auto"
    dry_run: bool = False
    artifact_dir: str = "./artifacts"
    concurrency: int = 4
    http: HttpConfig = Field(default_factory=HttpConfig)
    model_config = ConfigDict(extra="forbid")


class MongoConfig(BaseModel):
    uri: str
    db: str
    write_concern: str = "majority"
    model_config = ConfigDict(extra="forbid")


class PdfParserConfig(BaseModel):
    engine: Literal["pymupdf"] = "pymupdf"
    min_avg_chars_per_page: int = 200
    max_empty_page_ratio: float = 0.30
    model_config = ConfigDict(extra="forbid")


class HtmlParserConfig(BaseModel):
    engine: Literal["bs4"] = "bs4"
    max_tokens_per_virtual_page: int = 1200
    min_heading_to_split: int = 2
    model_config = ConfigDict(extra="forbid")


class ParsersConfig(BaseModel):
    pdf: PdfParserConfig = Field(default_factory=PdfParserConfig)
    html: HtmlParserConfig = Field(default_factory=HtmlParserConfig)
    model_config = ConfigDict(extra="forbid")


class OcrConfig(BaseModel):
    enabled: bool = True
    provider: Literal["mistral"] = "mistral"
    endpoint: str = "https://api.mistral.ai/v1/ocr"
    api_key_env: str = "MISTRAL_API_KEY"
    model: str = "mistral-ocr-2512"
    table_format: str = "markdown"
    include_image_base64: bool = False
    extract_header: bool = False
    extract_footer: bool = False
    model_config = ConfigDict(extra="forbid")


class SourceConfig(BaseModel):
    source_id: str
    url: HttpUrl
    fetch_strategy: Literal["direct", "saos_judgment", "saos_search"]
    saos_search_params: Optional[Dict[str, Any]] = None
    doc_type_hint: Literal[
        "STATUTE", "CASELAW", "EU_ACT", "GUIDANCE", "COMMENTARY", "STATUTE_REF"
    ]
    jurisdiction: Literal["PL", "EU"]
    language: str
    external_ids: Optional[Dict[str, str]] = None
    license_tag: Literal["OFFICIAL", "COMMERCIAL", "UNKNOWN"] = "OFFICIAL"
    model_config = ConfigDict(extra="forbid")


class PipelineConfig(BaseModel):
    run: RunConfig
    mongo: MongoConfig
    parsers: ParsersConfig
    ocr: OcrConfig = Field(default_factory=OcrConfig)
    sources: List[SourceConfig]
    model_config = ConfigDict(extra="forbid")


def expand_env_vars(content: str) -> str:
    pattern = re.compile(r"\$\{([^}]+)\}")

    def replacer(match):
        var_name = match.group(1)
        if var_name not in os.environ:
            raise ValueError(
                f"Environment variable '{var_name}' is required but not set."
            )
        return os.environ[var_name]

    return pattern.sub(replacer, content)


def load_config(path: str) -> PipelineConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw_content = f.read()
    expanded = expand_env_vars(raw_content)
    data = yaml.safe_load(expanded)
    return PipelineConfig(**data)
