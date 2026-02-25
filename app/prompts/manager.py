from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

VERSION_RE = re.compile(r"^v(\d{3})$")


@dataclass(frozen=True, slots=True)
class PromptSet:
    prompt_name: str
    version: str
    system_prompt_text: str
    schema_text: str
    meta: dict[str, Any]
    prompt_dir: Path


class PromptManager:
    def __init__(self, prompts_root: Path | str) -> None:
        self.prompts_root = Path(prompts_root)

    def list_prompt_names(self) -> list[str]:
        if not self.prompts_root.exists():
            return []

        names: list[str] = []
        for child in self.prompts_root.iterdir():
            if not child.is_dir():
                continue
            if child.name.startswith("__"):
                continue
            if self.list_versions(child.name):
                names.append(child.name)
        return sorted(names)

    def list_versions(self, prompt_name: str) -> list[str]:
        prompt_dir = self.prompts_root / prompt_name
        if not prompt_dir.exists() or not prompt_dir.is_dir():
            return []

        versions: list[str] = []
        for child in prompt_dir.iterdir():
            if not child.is_dir():
                continue
            if VERSION_RE.match(child.name):
                versions.append(child.name)

        return sorted(versions, key=_version_to_int)

    def next_version(self, prompt_name: str) -> str:
        versions = self.list_versions(prompt_name)
        if not versions:
            return "v001"
        return f"v{_version_to_int(versions[-1]) + 1:03d}"

    def load_prompt_set(self, *, prompt_name: str, version: str) -> PromptSet:
        prompt_dir = self._prompt_dir(prompt_name=prompt_name, version=version)
        system_prompt_path = prompt_dir / "system_prompt.txt"
        schema_path = prompt_dir / "schema.json"
        meta_path = prompt_dir / "meta.yaml"

        if not system_prompt_path.exists():
            raise FileNotFoundError(f"system prompt not found: {system_prompt_path}")
        if not schema_path.exists():
            raise FileNotFoundError(f"schema not found: {schema_path}")

        system_prompt_text = system_prompt_path.read_text(encoding="utf-8")
        schema_text = schema_path.read_text(encoding="utf-8")
        _validate_schema_text(schema_text)

        meta: dict[str, Any] = {}
        if meta_path.exists():
            parsed_meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
            if isinstance(parsed_meta, dict):
                meta = parsed_meta

        return PromptSet(
            prompt_name=prompt_name,
            version=version,
            system_prompt_text=system_prompt_text,
            schema_text=schema_text,
            meta=meta,
            prompt_dir=prompt_dir,
        )

    def save_as_new_version(
        self,
        *,
        prompt_name: str,
        source_version: str,
        system_prompt_text: str,
        author: str,
        note: str,
        schema_text: str | None = None,
    ) -> str:
        source = self.load_prompt_set(prompt_name=prompt_name, version=source_version)
        effective_schema_text = (
            source.schema_text if schema_text is None else schema_text
        )
        _validate_schema_text(effective_schema_text)

        new_version = self.next_version(prompt_name)
        new_dir = self._prompt_dir(prompt_name=prompt_name, version=new_version)
        new_dir.mkdir(parents=True, exist_ok=False)

        (new_dir / "system_prompt.txt").write_text(system_prompt_text, encoding="utf-8")
        (new_dir / "schema.json").write_text(effective_schema_text, encoding="utf-8")

        meta_payload = {
            "created_at": _utc_now(),
            "author": author.strip() or "unknown",
            "note": note.strip(),
            "source_version": source_version,
        }
        (new_dir / "meta.yaml").write_text(
            yaml.safe_dump(meta_payload, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )
        return new_version

    def _prompt_dir(self, *, prompt_name: str, version: str) -> Path:
        if not VERSION_RE.match(version):
            raise ValueError(f"Invalid prompt version format: {version}")
        return self.prompts_root / prompt_name / version


def _validate_schema_text(schema_text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(schema_text)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid schema JSON: {error}") from error

    if not isinstance(parsed, dict):
        raise ValueError("Schema JSON root must be an object")

    return parsed


def _version_to_int(version: str) -> int:
    match = VERSION_RE.match(version)
    if match is None:
        raise ValueError(f"Invalid version format: {version}")
    return int(match.group(1))


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
