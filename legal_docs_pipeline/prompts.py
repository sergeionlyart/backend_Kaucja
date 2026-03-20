"""Prompt-pack resolution utilities for the NormaDepo pipeline."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import (
    ANNOTATABLE_PROMPT_PROFILES,
    BASE_PROMPT_FILENAME,
    OUTPUT_SCHEMA_INSTRUCTION,
    PROMPT_PROFILE_TO_FILENAME,
    REPAIR_ANALYSIS_PROMPT_FILENAME,
    REPAIR_TRANSLATION_PROMPT_FILENAME,
    PromptProfile,
    TRANSLATION_PROMPT_FILENAME,
)


@dataclass(frozen=True, slots=True)
class ResolvedPrompt:
    prompt_name: str
    prompt_paths: tuple[Path, ...]
    prompt_hash: str
    prompt_text: str


class FilePromptResolver:
    def __init__(self, prompt_dir: Path | str) -> None:
        self.prompt_dir = Path(prompt_dir).expanduser().resolve()

    def validate_prompt_pack(self) -> None:
        self._read_prompt_file(BASE_PROMPT_FILENAME)
        self._read_prompt_file(TRANSLATION_PROMPT_FILENAME)
        self._read_prompt_file(REPAIR_ANALYSIS_PROMPT_FILENAME)
        self._read_prompt_file(REPAIR_TRANSLATION_PROMPT_FILENAME)
        for profile in ANNOTATABLE_PROMPT_PROFILES:
            self.resolve_analysis_prompt(profile, source_language_code="pl")
            self.resolve_analysis_prompt(profile, source_language_code="en")

    def resolve_analysis_prompt(
        self,
        prompt_profile: PromptProfile,
        *,
        source_language_code: str,
        output_schema_instruction: str = OUTPUT_SCHEMA_INSTRUCTION,
    ) -> ResolvedPrompt:
        if prompt_profile not in ANNOTATABLE_PROMPT_PROFILES:
            raise ValueError(
                f"Prompt profile {prompt_profile.value!r} is not annotatable."
            )

        base_path = self.prompt_dir / BASE_PROMPT_FILENAME
        addon_path = self.prompt_dir / PROMPT_PROFILE_TO_FILENAME[prompt_profile]
        prompt_text = self._render_prompt(
            "\n\n".join(
                [
                    self._read_prompt_file(BASE_PROMPT_FILENAME),
                    self._read_prompt_file(addon_path.name),
                    output_schema_instruction,
                ]
            ),
            variables={
                "SOURCE_LANGUAGE_CODE": source_language_code,
                "OUTPUT_LANGUAGE": source_language_code,
            },
        )
        prompt_paths = (base_path, addon_path)
        return ResolvedPrompt(
            prompt_name=prompt_profile.value,
            prompt_paths=prompt_paths,
            prompt_hash=hash_prompt_text(prompt_text),
            prompt_text=prompt_text,
        )

    def resolve_analysis_repair_prompt(
        self,
        *,
        source_language_code: str,
        output_schema_instruction: str = OUTPUT_SCHEMA_INSTRUCTION,
    ) -> ResolvedPrompt:
        prompt_path = self.prompt_dir / REPAIR_ANALYSIS_PROMPT_FILENAME
        prompt_text = self._render_prompt(
            "\n\n".join(
                [
                    self._read_prompt_file(REPAIR_ANALYSIS_PROMPT_FILENAME),
                    output_schema_instruction,
                ]
            ),
            variables={
                "SOURCE_LANGUAGE_CODE": source_language_code,
                "OUTPUT_LANGUAGE": source_language_code,
            },
        )
        return ResolvedPrompt(
            prompt_name="repair_analysis",
            prompt_paths=(prompt_path,),
            prompt_hash=hash_prompt_text(prompt_text),
            prompt_text=prompt_text,
        )

    def resolve_translation_prompt(
        self,
        *,
        output_schema_instruction: str = OUTPUT_SCHEMA_INSTRUCTION,
    ) -> ResolvedPrompt:
        prompt_path = self.prompt_dir / TRANSLATION_PROMPT_FILENAME
        prompt_text = self._render_prompt(
            "\n\n".join(
                [
                    self._read_prompt_file(TRANSLATION_PROMPT_FILENAME),
                    output_schema_instruction,
                ]
            ),
            variables={},
        )
        return ResolvedPrompt(
            prompt_name="translate_to_ru",
            prompt_paths=(prompt_path,),
            prompt_hash=hash_prompt_text(prompt_text),
            prompt_text=prompt_text,
        )

    def resolve_translation_repair_prompt(
        self,
        *,
        output_schema_instruction: str = OUTPUT_SCHEMA_INSTRUCTION,
    ) -> ResolvedPrompt:
        prompt_path = self.prompt_dir / REPAIR_TRANSLATION_PROMPT_FILENAME
        prompt_text = self._render_prompt(
            "\n\n".join(
                [
                    self._read_prompt_file(REPAIR_TRANSLATION_PROMPT_FILENAME),
                    output_schema_instruction,
                ]
            ),
            variables={},
        )
        return ResolvedPrompt(
            prompt_name="repair_translate_to_ru",
            prompt_paths=(prompt_path,),
            prompt_hash=hash_prompt_text(prompt_text),
            prompt_text=prompt_text,
        )

    def _read_prompt_file(self, file_name: str) -> str:
        prompt_path = self.prompt_dir / file_name
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8").strip()

    def _render_prompt(self, prompt_text: str, *, variables: dict[str, str]) -> str:
        rendered = prompt_text
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{key}}}", value)
        unresolved = sorted(set(re.findall(r"\{[A-Z_]+\}", rendered)))
        if unresolved:
            raise ValueError(
                "Prompt contains unresolved placeholders: "
                + ", ".join(unresolved)
            )
        return rendered


def _hash_prompt_files(paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\n")
        digest.update(path.read_bytes())
        digest.update(b"\n")
    return digest.hexdigest()


def hash_prompt_text(prompt_text: str) -> str:
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()


def build_analysis_fingerprint(
    *,
    canonical_text_sha256: str,
    prompt_profile: PromptProfile,
    prompt_pack_version: str,
    prompt_hash: str,
    model_id: str,
    reasoning_effort: str,
    text_verbosity: str,
    output_schema_version: str,
    pipeline_version: str,
) -> str:
    payload = "|".join(
        [
            canonical_text_sha256,
            prompt_profile.value,
            prompt_pack_version,
            prompt_hash,
            model_id,
            reasoning_effort,
            text_verbosity,
            output_schema_version,
            pipeline_version,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_request_hash(
    *,
    system_prompt: str,
    input_payload: dict[str, Any],
    output_schema: dict[str, Any],
    model_id: str,
    reasoning_effort: str,
    text_verbosity: str,
    max_output_tokens: int,
) -> str:
    payload = {
        "system_prompt": system_prompt,
        "input_payload": input_payload,
        "output_schema": output_schema,
        "model_id": model_id,
        "reasoning_effort": reasoning_effort,
        "text_verbosity": text_verbosity,
        "max_output_tokens": max_output_tokens,
    }
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
