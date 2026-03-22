from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class LoadedPrompt:
    prompt_name: str
    version: str
    system_prompt_text: str
    schema: dict[str, Any] | None
    meta: dict[str, Any]
    prompt_dir: Path
    response_mode: str


class PromptLoader:
    def __init__(self, prompts_root: Path | str) -> None:
        self.prompts_root = Path(prompts_root)

    def load(self, *, prompt_name: str, version: str) -> LoadedPrompt:
        prompt_dir = self.prompts_root / prompt_name / version
        system_prompt_path = prompt_dir / "system_prompt.txt"
        schema_path = prompt_dir / "schema.json"
        meta_path = prompt_dir / "meta.yaml"

        if not system_prompt_path.exists():
            raise FileNotFoundError(f"system prompt not found: {system_prompt_path}")

        meta: dict[str, Any] = {}
        if meta_path.exists():
            parsed_meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
            if not isinstance(parsed_meta, dict):
                raise ValueError(f"meta.yaml must contain an object: {meta_path}")
            meta = parsed_meta

        schema: dict[str, Any] | None = None
        if schema_path.exists():
            parsed_schema = json.loads(schema_path.read_text(encoding="utf-8"))
            if not isinstance(parsed_schema, dict):
                raise ValueError(f"schema.json must contain an object: {schema_path}")
            schema = parsed_schema

        response_mode = str(meta.get("response_mode") or "structured_json").strip()
        if response_mode not in {"structured_json", "plain_text"}:
            raise ValueError(
                f"Unsupported response_mode={response_mode!r} for {prompt_name}/{version}"
            )

        return LoadedPrompt(
            prompt_name=prompt_name,
            version=version,
            system_prompt_text=system_prompt_path.read_text(encoding="utf-8"),
            schema=schema,
            meta=meta,
            prompt_dir=prompt_dir,
            response_mode=response_mode,
        )
