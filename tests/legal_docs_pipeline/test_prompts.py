from __future__ import annotations

from pathlib import Path

import pytest

from legal_docs_pipeline.constants import PromptProfile
from legal_docs_pipeline.prompts import (
    FilePromptResolver,
    build_analysis_fingerprint,
    build_request_hash,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_prompt_resolver_builds_analysis_prompt_and_hash() -> None:
    resolver = FilePromptResolver(PROJECT_ROOT / "prompts/kaucja")

    resolved = resolver.resolve_analysis_prompt(PromptProfile.ADDON_CASE_LAW)

    assert [path.name for path in resolved.prompt_paths] == [
        "base_system.txt",
        "addon_case_law.txt",
    ]
    assert "судебным решением" in resolved.prompt_text
    assert len(resolved.prompt_hash) == 64
    assert resolved.prompt_hash == resolver.resolve_analysis_prompt(
        PromptProfile.ADDON_CASE_LAW
    ).prompt_hash


def test_prompt_resolver_rejects_non_annotatable_profile() -> None:
    resolver = FilePromptResolver(PROJECT_ROOT / "prompts/kaucja")

    with pytest.raises(ValueError):
        resolver.resolve_analysis_prompt(PromptProfile.SKIP_NON_TARGET)


def test_prompt_resolver_builds_translation_prompt() -> None:
    resolver = FilePromptResolver(PROJECT_ROOT / "prompts/kaucja")

    resolved = resolver.resolve_translation_prompt()

    assert [path.name for path in resolved.prompt_paths] == ["translate_to_ru.txt"]
    assert "Не перечитывай исходный markdown" in resolved.prompt_text


def test_prompt_hash_and_fingerprint_are_deterministic() -> None:
    resolver = FilePromptResolver(PROJECT_ROOT / "prompts/kaucja")
    resolved = resolver.resolve_analysis_prompt(PromptProfile.ADDON_NORMATIVE)

    fingerprint_one = build_analysis_fingerprint(
        normalized_text_sha256="text-sha",
        prompt_profile=PromptProfile.ADDON_NORMATIVE,
        prompt_pack_version="2026-03-16",
        prompt_hash=resolved.prompt_hash,
        model_id="gpt-5.4",
        reasoning_effort="xhigh",
        text_verbosity="low",
        output_schema_version="1.0.0",
        pipeline_version="1.0.0",
    )
    fingerprint_two = build_analysis_fingerprint(
        normalized_text_sha256="text-sha",
        prompt_profile=PromptProfile.ADDON_NORMATIVE,
        prompt_pack_version="2026-03-16",
        prompt_hash=resolved.prompt_hash,
        model_id="gpt-5.4",
        reasoning_effort="xhigh",
        text_verbosity="low",
        output_schema_version="1.0.0",
        pipeline_version="1.0.0",
    )

    assert fingerprint_one == fingerprint_two
    assert len(fingerprint_one) == 64


def test_request_hash_changes_when_input_changes() -> None:
    base_hash = build_request_hash(
        system_prompt="system",
        input_payload={"doc_id": "a"},
        output_schema={"type": "object"},
        model_id="gpt-5.4",
        reasoning_effort="xhigh",
        text_verbosity="low",
        max_output_tokens=32000,
    )
    changed_hash = build_request_hash(
        system_prompt="system",
        input_payload={"doc_id": "b"},
        output_schema={"type": "object"},
        model_id="gpt-5.4",
        reasoning_effort="xhigh",
        text_verbosity="low",
        max_output_tokens=32000,
    )

    assert base_hash != changed_hash
