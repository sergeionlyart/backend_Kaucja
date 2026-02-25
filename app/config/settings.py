from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
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

    gradio_server_name: str = "127.0.0.1"
    gradio_server_port: int = Field(default=7860, ge=1, le=65535)

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
