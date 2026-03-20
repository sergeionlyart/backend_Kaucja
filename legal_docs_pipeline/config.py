"""Typed configuration loader for the NormaDepo pipeline."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .constants import (
    DEDUPE_VERSION,
    DEFAULT_MAX_FILE_SIZE_BYTES,
    DEFAULT_INPUT_GLOB,
    DEFAULT_PROMPT_PACK_ID,
    DEFAULT_PROMPT_PACK_VERSION,
    PIPELINE_IMPLEMENTATION_VERSION,
    PIPELINE_SCHEMA_VERSION,
)

DEFAULT_TRANSLATION_RU_MAX_OUTPUT_TOKENS = 24_000
DEFAULT_REQUEST_TIMEOUT_SECONDS = 120


class InputConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root_path: Path
    glob: str = Field(default=DEFAULT_INPUT_GLOB, min_length=1)
    ignore_hidden: bool = True
    max_file_size_bytes: int = Field(default=DEFAULT_MAX_FILE_SIZE_BYTES, ge=1)


class MongoConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    uri: str = Field(min_length=1)
    database: str = Field(min_length=1)
    collection: str = Field(min_length=1)


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = Field(default="openai", min_length=1)
    api: str = Field(default="responses", min_length=1)
    model_id: str = Field(default="gpt-5.4", min_length=1)
    reasoning_effort: str = Field(default="xhigh", min_length=1)
    text_verbosity: str = Field(default="low", min_length=1)
    truncation: str = Field(default="disabled", min_length=1)
    store: bool = False
    analysis_max_output_tokens: int = Field(default=32_000, ge=1)
    translation_ru_max_output_tokens: int = Field(
        default=DEFAULT_TRANSLATION_RU_MAX_OUTPUT_TOKENS,
        ge=DEFAULT_TRANSLATION_RU_MAX_OUTPUT_TOKENS,
    )
    request_timeout_seconds: int = Field(
        default=DEFAULT_REQUEST_TIMEOUT_SECONDS,
        ge=1,
    )
    temperature: float | None = None
    top_p: float | None = None
    logprobs: bool | None = None

    @model_validator(mode="after")
    def validate_reasoning_compatibility(self) -> "ModelConfig":
        if self.reasoning_effort != "none":
            forbidden_values = (
                self.temperature is not None
                or self.top_p is not None
                or self.logprobs is not None
            )
            if forbidden_values:
                raise ValueError(
                    "temperature, top_p, and logprobs must be omitted when "
                    "reasoning_effort is not 'none'."
                )
        return self


class PromptsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt_pack_id: str = Field(default=DEFAULT_PROMPT_PACK_ID, min_length=1)
    prompt_pack_version: str = Field(
        default=DEFAULT_PROMPT_PACK_VERSION,
        min_length=1,
    )
    prompt_dir: Path


class PipelineSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=PIPELINE_SCHEMA_VERSION, min_length=1)
    pipeline_version: str = Field(
        default=PIPELINE_IMPLEMENTATION_VERSION,
        min_length=1,
    )
    workers: int = Field(default=1, ge=1)
    dedup_version: str = Field(default=DEDUPE_VERSION, min_length=1)
    router_version: str = Field(default=PIPELINE_IMPLEMENTATION_VERSION, min_length=1)
    history_tail_size: int = Field(default=10, ge=1)
    retry_model_calls: int = Field(default=2, ge=0)
    retry_mongo_writes: int = Field(default=2, ge=0)

    @field_validator("workers")
    @classmethod
    def validate_workers(cls, value: int) -> int:
        if value != 1:
            raise ValueError("Foundation slice supports only workers=1.")
        return value


class PipelineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input: InputConfig
    mongo: MongoConfig
    model: ModelConfig
    prompts: PromptsConfig
    pipeline: PipelineSettings
    config_path: Path | None = Field(default=None, exclude=True)

    def with_resolved_paths(self, config_path: Path) -> "PipelineConfig":
        base_dir = config_path.resolve().parent
        resolved_input_root = _resolve_existing_directory(
            self.input.root_path,
            base_dir=base_dir,
            field_name="input.root_path",
        )
        resolved_prompt_dir = _resolve_existing_directory(
            self.prompts.prompt_dir,
            base_dir=base_dir,
            field_name="prompts.prompt_dir",
        )
        return self.model_copy(
            update={
                "input": self.input.model_copy(
                    update={"root_path": resolved_input_root}
                ),
                "prompts": self.prompts.model_copy(
                    update={"prompt_dir": resolved_prompt_dir}
                ),
                "config_path": config_path.resolve(),
            }
        )


def load_pipeline_config(config_path: Path | str) -> PipelineConfig:
    config_file = Path(config_path).expanduser().resolve()
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with config_file.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    if not isinstance(payload, dict):
        raise ValueError("Pipeline config root must be a mapping.")

    config = PipelineConfig.model_validate(payload)
    return config.with_resolved_paths(config_file)


def apply_cli_overrides(
    config: PipelineConfig,
    *,
    input_root: str | None = None,
    mongo_uri: str | None = None,
    mongo_db: str | None = None,
    mongo_collection: str | None = None,
    workers: int | None = None,
) -> PipelineConfig:
    input_model = config.input
    mongo_model = config.mongo
    pipeline_model = config.pipeline

    if input_root is not None:
        input_model = input_model.model_copy(
            update={
                "root_path": _resolve_existing_directory(
                    Path(input_root),
                    base_dir=Path.cwd(),
                    field_name="--input-root",
                )
            }
        )

    if mongo_uri is not None:
        mongo_model = mongo_model.model_copy(update={"uri": mongo_uri})
    if mongo_db is not None:
        mongo_model = mongo_model.model_copy(update={"database": mongo_db})
    if mongo_collection is not None:
        mongo_model = mongo_model.model_copy(update={"collection": mongo_collection})
    if workers is not None:
        pipeline_model = pipeline_model.model_copy(update={"workers": workers})

    updated = config.model_copy(
        update={
            "input": input_model,
            "mongo": mongo_model,
            "pipeline": pipeline_model,
        }
    )
    validated = PipelineConfig.model_validate(updated.model_dump())
    return validated.model_copy(update={"config_path": config.config_path})


def _resolve_existing_directory(
    raw_path: Path,
    *,
    base_dir: Path,
    field_name: str,
) -> Path:
    candidate = raw_path.expanduser()
    resolved = candidate if candidate.is_absolute() else (base_dir / candidate)
    resolved = resolved.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"{field_name} does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"{field_name} is not a directory: {resolved}")
    return resolved
