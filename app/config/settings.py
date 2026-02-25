from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="KAUCJA_",
        extra="ignore",
    )

    environment: str = "local"
    data_dir: Path = Path("data")
    sqlite_path: Path = Path("data/kaucja.sqlite3")

    providers_config_path: Path = Path("app/config/providers.yaml")
    pricing_config_path: Path = Path("app/config/pricing.yaml")

    default_provider: str = "openai"
    default_model: str = "gpt-5.1"
    default_prompt_name: str = "kaucja_gap_analysis"
    default_prompt_version: str = "v001"
    default_ocr_model: str = "mistral-ocr-latest"
    default_ocr_table_format: str = "html"
    default_ocr_include_image_base64: bool = True

    gradio_server_name: str = "127.0.0.1"
    gradio_server_port: int = Field(default=7860, ge=1, le=65535)

    restore_max_entries: int = Field(
        default=1_000,
        ge=1,
        validation_alias=AliasChoices(
            "KAUCJA_RESTORE_MAX_ENTRIES",
            "RESTORE_MAX_ENTRIES",
        ),
    )
    restore_max_total_uncompressed_bytes: int = Field(
        default=512 * 1024 * 1024,
        ge=1,
        validation_alias=AliasChoices(
            "KAUCJA_RESTORE_MAX_TOTAL_UNCOMPRESSED_BYTES",
            "RESTORE_MAX_TOTAL_UNCOMPRESSED_BYTES",
        ),
    )
    restore_max_single_file_bytes: int = Field(
        default=128 * 1024 * 1024,
        ge=1,
        validation_alias=AliasChoices(
            "KAUCJA_RESTORE_MAX_SINGLE_FILE_BYTES",
            "RESTORE_MAX_SINGLE_FILE_BYTES",
        ),
    )
    restore_max_compression_ratio: float = Field(
        default=200.0,
        ge=1.0,
        validation_alias=AliasChoices(
            "KAUCJA_RESTORE_MAX_COMPRESSION_RATIO",
            "RESTORE_MAX_COMPRESSION_RATIO",
        ),
    )
    restore_require_signature: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "KAUCJA_RESTORE_REQUIRE_SIGNATURE",
            "RESTORE_REQUIRE_SIGNATURE",
        ),
    )
    bundle_signing_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "KAUCJA_BUNDLE_SIGNING_KEY",
            "BUNDLE_SIGNING_KEY",
        ),
    )
    live_smoke_required_providers: str = Field(
        default="openai,google,mistral_ocr",
        validation_alias=AliasChoices(
            "KAUCJA_LIVE_SMOKE_REQUIRED_PROVIDERS",
            "LIVE_SMOKE_REQUIRED_PROVIDERS",
        ),
    )
    live_smoke_provider_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        validation_alias=AliasChoices(
            "KAUCJA_LIVE_SMOKE_PROVIDER_TIMEOUT_SECONDS",
            "LIVE_SMOKE_PROVIDER_TIMEOUT_SECONDS",
        ),
    )

    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("KAUCJA_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )
    google_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("KAUCJA_GOOGLE_API_KEY", "GOOGLE_API_KEY"),
    )
    mistral_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("KAUCJA_MISTRAL_API_KEY", "MISTRAL_API_KEY"),
    )

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def resolved_data_dir(self) -> Path:
        return self._resolve_path(self.data_dir)

    @property
    def resolved_sqlite_path(self) -> Path:
        return self._resolve_path(self.sqlite_path)

    @property
    def resolved_providers_config_path(self) -> Path:
        return self._resolve_path(self.providers_config_path)

    @property
    def resolved_pricing_config_path(self) -> Path:
        return self._resolve_path(self.pricing_config_path)

    def load_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        if not isinstance(data, dict):
            raise ValueError(f"YAML config must contain object root: {path}")

        return data

    @property
    def providers_config(self) -> dict[str, Any]:
        return self.load_yaml(self.resolved_providers_config_path)

    @property
    def pricing_config(self) -> dict[str, Any]:
        return self.load_yaml(self.resolved_pricing_config_path)

    def _resolve_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        return (self.project_root / path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
