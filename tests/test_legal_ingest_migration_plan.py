from __future__ import annotations

import builtins
import importlib
import json
import sys
from pathlib import Path

import pytest


def test_migration_plan_is_self_contained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_import = builtins.__import__
    real_read_text = Path.read_text

    def guarded_import(name: str, *args: object, **kwargs: object):
        if name.startswith("app.ops.legal_collection"):
            raise AssertionError(
                "migration_plan must not import app.ops.legal_collection"
            )
        return real_import(name, *args, **kwargs)

    def guarded_read_text(self: Path, *args: object, **kwargs: object) -> str:
        if str(self).endswith("docs/legal/cas_law_V_2.2 2.md"):
            raise AssertionError(
                "migration_plan must not read docs/legal/cas_law_V_2.2 2.md"
            )
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    sys.modules.pop("legal_ingest.migration_plan", None)

    module = importlib.import_module("legal_ingest.migration_plan")
    output_path = tmp_path / "migration_map.json"
    written_path = module.write_migration_map(output_path)

    payload = json.loads(written_path.read_text(encoding="utf-8"))
    assert (
        payload["source_list_path"]
        == "legal_ingest.source_catalog.TECHSPEC_SOURCE_CATALOG"
    )
    assert payload["positions"][0]["source_url"].startswith("https://eli.gov.pl/")


def test_validate_migration_payload_rejects_canonical_entry_without_doc_uid() -> None:
    from legal_ingest.migration_plan import validate_migration_payload

    payload = {
        "schema_version": "techspec-3.1",
        "source_list_path": "legal_ingest.source_catalog.TECHSPEC_SOURCE_CATALOG",
        "positions": [
            {
                "entry_id": "broken-canonical-entry",
                "position": 35,
                "source_url": "https://example.com/doc.pdf",
                "source_id": "broken",
                "source_doc_uid": "uokik_pl:urlsha:c506ff470f4740ad",
                "status": "canonical",
                "canonical_title": "Broken canonical entry",
                "canonical_doc_uid": None,
                "document_kind": "GUIDANCE",
                "legal_role": "EU_CONSUMER_LAYER",
                "expected_external_id": "uokik:RKR-37/2013",
                "required_top_level": True,
                "notes": "broken",
                "match_doc_uids": [],
                "match_source_urls": [],
            }
        ],
        "derived_runtime_targets": [],
        "required_additions": [],
    }

    with pytest.raises(
        ValueError, match="canonical entry must define canonical_doc_uid"
    ):
        validate_migration_payload(payload)


def test_build_migration_payload_sets_canonical_doc_uid_for_position_35() -> None:
    from legal_ingest.migration_plan import build_migration_payload

    payload = build_migration_payload()
    position_35 = next(
        entry for entry in payload["positions"] if entry["entry_id"] == "position-35"
    )

    assert position_35["status"] == "canonical"
    assert position_35["canonical_doc_uid"] == "uokik_pl:urlsha:c506ff470f4740ad"
