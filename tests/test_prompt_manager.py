from __future__ import annotations

import json
from pathlib import Path

import yaml

from app.prompts.manager import PromptManager


def _create_prompt_version(
    *,
    root: Path,
    prompt_name: str,
    version: str,
    prompt_text: str,
    schema_payload: dict[str, object],
) -> None:
    target = root / prompt_name / version
    target.mkdir(parents=True, exist_ok=True)
    (target / "system_prompt.txt").write_text(prompt_text, encoding="utf-8")
    (target / "schema.json").write_text(json.dumps(schema_payload), encoding="utf-8")
    (target / "meta.yaml").write_text(
        yaml.safe_dump({"created_at": "2026-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )


def test_prompt_manager_discovery_and_next_version(tmp_path: Path) -> None:
    prompts_root = tmp_path / "prompts"
    _create_prompt_version(
        root=prompts_root,
        prompt_name="kaucja_gap_analysis",
        version="v001",
        prompt_text="prompt 1",
        schema_payload={"type": "object"},
    )
    _create_prompt_version(
        root=prompts_root,
        prompt_name="kaucja_gap_analysis",
        version="v002",
        prompt_text="prompt 2",
        schema_payload={"type": "object"},
    )

    manager = PromptManager(prompts_root)

    assert manager.list_prompt_names() == ["kaucja_gap_analysis"]
    assert manager.list_versions("kaucja_gap_analysis") == ["v001", "v002"]
    assert manager.next_version("kaucja_gap_analysis") == "v003"


def test_prompt_manager_save_new_version_copies_schema_and_writes_meta(
    tmp_path: Path,
) -> None:
    prompts_root = tmp_path / "prompts"
    schema_payload = {
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
        "additionalProperties": False,
    }
    _create_prompt_version(
        root=prompts_root,
        prompt_name="kaucja_gap_analysis",
        version="v001",
        prompt_text="base prompt",
        schema_payload=schema_payload,
    )

    manager = PromptManager(prompts_root)
    new_version = manager.save_as_new_version(
        prompt_name="kaucja_gap_analysis",
        source_version="v001",
        system_prompt_text="updated prompt",
        author="tester",
        note="new version note",
    )

    assert new_version == "v002"
    created = prompts_root / "kaucja_gap_analysis" / "v002"
    assert (created / "system_prompt.txt").read_text(
        encoding="utf-8"
    ) == "updated prompt"
    assert (
        json.loads((created / "schema.json").read_text(encoding="utf-8"))
        == schema_payload
    )

    meta = yaml.safe_load((created / "meta.yaml").read_text(encoding="utf-8"))
    assert meta["author"] == "tester"
    assert meta["note"] == "new version note"
    assert meta["source_version"] == "v001"
