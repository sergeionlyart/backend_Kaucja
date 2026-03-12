from __future__ import annotations

from pathlib import Path
from typing import Any

from legal_ingest.config import ArtifactConfig, MongoConfig
from legal_ingest.metadata_migration import (
    _build_document_update,
    _compute_document_mutation,
    run_metadata_migration,
)


class FakeCollection:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def find(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for row in self.rows:
            if row.get("doc_uid") != query.get("doc_uid"):
                continue
            if (
                query.get("source_hash")
                and row.get("source_hash") != query["source_hash"]
            ):
                continue
            pattern = query.get("node_id", {}).get("$regex")
            if pattern == "^art:" and not str(row.get("node_id", "")).startswith(
                "art:"
            ):
                continue
            if projection is None:
                results.append(dict(row))
                continue
            results.append(
                {
                    key: value
                    for key, value in row.items()
                    if projection.get(key, 0) == 1
                }
            )
        return results


class FakeRuntime:
    def __init__(self, nodes: list[dict[str, Any]]) -> None:
        self.nodes = nodes

    def collection(self, name: str) -> FakeCollection:
        assert name == "nodes"
        return FakeCollection(self.nodes)


class FakeMongoCollection:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def find(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        if query:
            return []
        if projection is None:
            return [dict(row) for row in self.rows]
        return [self._project_row(row, projection) for row in self.rows]

    def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> dict[str, Any] | None:
        for row in self.rows:
            if row.get("doc_uid") != query.get("doc_uid"):
                continue
            if projection is None:
                return dict(row)
            return self._project_row(row, projection)
        return None

    @staticmethod
    def _project_row(
        row: dict[str, Any],
        projection: dict[str, int],
    ) -> dict[str, Any]:
        if any(value == 1 for value in projection.values()):
            return {
                key: value for key, value in row.items() if projection.get(key, 0) == 1
            }
        return {key: value for key, value in row.items() if projection.get(key, 1) != 0}


class FakeMongoRuntime:
    def __init__(
        self,
        *,
        documents: list[dict[str, Any]],
        document_sources: list[dict[str, Any]],
        nodes: list[dict[str, Any]] | None = None,
        pages: list[dict[str, Any]] | None = None,
    ) -> None:
        self.config = MongoConfig(uri="mongodb://example", db_name="test_db")
        self._collections = {
            "documents": FakeMongoCollection(documents),
            "document_sources": FakeMongoCollection(document_sources),
            "nodes": FakeCollection(nodes or []),
            "pages": FakeMongoCollection(pages or []),
        }

    def load_collection(
        self,
        name: str,
        *,
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        return self._collections[name].find({}, projection=projection)

    def collection(self, name: str):
        return self._collections[name]


def test_build_document_update_baselines_unclassified_saos_document() -> None:
    source_hash = "1" * 64
    document = {
        "doc_uid": "saos_pl:10138",
        "source_system": "saos_pl",
        "doc_type": "CASELAW",
        "title": "SENTENCE II Ca 34/13 (COMMON)",
        "source_urls": ["https://www.saos.org.pl/"],
        "external_ids": {"saos_id": "10138"},
        "current_source_hash": source_hash,
        "date_decision": "2013-03-19",
    }
    current_source = {
        "url": "https://www.saos.org.pl/",
        "raw_object_path": "artifacts/corpus/legal/saos_pl:10138/source.json",
        "source_hash": source_hash,
    }

    update_payload, manual_review = _build_document_update(
        runtime=FakeRuntime([]),
        article_inventory_cache={},
        docs_by_uid={"saos_pl:10138": document},
        document=document,
        current_source=current_source,
        exact_entry=None,
        source_entry=None,
        duplicate_resolution=None,
        act_context_item=None,
        owner_document=None,
        owner_current_source=None,
        owner_entry=None,
    )

    assert update_payload["status"] == "active"
    assert update_payload["document_kind"] == "CASELAW"
    assert update_payload["legal_role"] == "GENERAL_CASELAW"
    assert update_payload["source_tier"] == "saos"
    assert update_payload["canonical_title"] == "SENTENCE II Ca 34/13 (COMMON)"
    assert update_payload["source_url"] == "https://www.saos.org.pl/"
    assert update_payload["normalized_source_url"] == "https://www.saos.org.pl/"
    assert update_payload["external_id"] == "saos:10138"
    assert update_payload["checksum_sha256"] == source_hash
    assert update_payload["storage_uri"] == (
        "artifacts/corpus/legal/saos_pl:10138/source.json"
    )
    assert update_payload["title_short"] == "II CA 34/13"
    assert update_payload["case_signature"] == "II CA 34/13"
    assert update_payload["court_name"] == "Sad powszechny (SAOS)"
    assert update_payload["court_level"] == "common_court"
    assert update_payload["judgment_date"] == "2013-03-19"
    assert update_payload["artifact_type"] == "judgment"
    assert update_payload["same_case_group_id"].startswith("same_case:singleton:")
    assert update_payload["is_search_page"] is False
    assert manual_review == []


def test_build_document_update_backfills_act_layer() -> None:
    source_hash = "2" * 64
    document = {
        "doc_uid": "eli_pl:DU/1964/296",
        "source_system": "eli_pl",
        "doc_type": "STATUTE",
        "title": "Kodeks postepowania cywilnego",
        "source_urls": [
            "https://eli.gov.pl/api/acts/DU/1964/296/text/U/D19640296Lj.pdf"
        ],
        "external_ids": {"eli": "DU/1964/296"},
        "current_source_hash": source_hash,
    }
    current_source = {
        "url": "https://eli.gov.pl/api/acts/DU/1964/296/text/U/D19640296Lj.pdf",
        "raw_object_path": "artifacts/corpus/legal/eli_pl:DU/1964/296/raw/original.bin",
        "source_hash": source_hash,
    }
    nodes = [
        {
            "doc_uid": "eli_pl:DU/1964/296",
            "source_hash": source_hash,
            "node_id": "art:1",
            "order_index": 1,
        },
        {
            "doc_uid": "eli_pl:DU/1964/296",
            "source_hash": source_hash,
            "node_id": "art:2",
            "order_index": 2,
        },
    ]

    update_payload, manual_review = _build_document_update(
        runtime=FakeRuntime(nodes),
        article_inventory_cache={},
        docs_by_uid={"eli_pl:DU/1964/296": document},
        document=document,
        current_source=current_source,
        exact_entry={
            "entry_id": "required-addition-kpc",
            "status": "canonical",
            "document_kind": "STATUTE",
            "legal_role": "PROCESS_NORM",
            "canonical_title": "Kodeks postepowania cywilnego",
            "canonical_doc_uid": "eli_pl:DU/1964/296",
            "expected_external_id": "eli:DU/1964/296",
        },
        source_entry=None,
        duplicate_resolution=None,
        act_context_item={
            "act_id": "eli:DU/1964/296",
            "owner_doc_uid": "eli_pl:DU/1964/296",
        },
        owner_document=None,
        owner_current_source=None,
        owner_entry=None,
    )

    assert update_payload["status"] == "canonical"
    assert update_payload["canonical_doc_uid"] == "eli_pl:DU/1964/296"
    assert update_payload["act_id"] == "eli:DU/1964/296"
    assert update_payload["act_short_name"] == "Kodeks postepowania cywilnego"
    assert update_payload["article_nodes"] == ["art:1", "art:2"]
    assert update_payload["current_status"] == "current"
    assert update_payload["current_text_ref"] == "eli_pl:DU/1964/296"
    assert update_payload["is_consolidated_text"] is True
    assert update_payload["key_provisions"] == ["art:1", "art:2"]
    assert update_payload["title_short"] == "Kodeks postepowania cywilnego"
    assert update_payload["issue_tags"] == ["act", "civil_procedure"]
    assert update_payload["is_search_page"] is False
    assert manual_review == []


def test_compute_document_mutation_returns_noop_for_matching_payload() -> None:
    document = {
        "status": "canonical",
        "document_kind": "CASELAW",
        "legal_role": "FACTUAL_CASE",
        "source_tier": "saos",
        "canonical_title": "Wyrok III Ca 1707/18",
        "source_url": "https://www.saos.org.pl/judgments/385394",
        "normalized_source_url": "https://www.saos.org.pl/judgments/385394",
        "external_id": "saos:385394",
        "canonical_doc_uid": "saos_pl:385394",
        "checksum_sha256": "hash-123",
        "storage_uri": "artifacts/corpus/legal/saos_pl:385394/source.pdf",
        "title": "Wyrok III Ca 1707/18",
        "doc_type": "CASELAW",
        "same_case_group_id": "same_case:iii_ca_1707_18",
        "source_urls": ["https://www.saos.org.pl/judgments/385394"],
    }

    set_payload, unset_fields = _compute_document_mutation(
        document=document,
        desired_payload=document,
    )

    assert set_payload == {}
    assert unset_fields == []


def test_build_document_update_excludes_broken_artifact_record() -> None:
    document = {
        "doc_uid": "eurlex_eu:urlsha:broken",
        "source_system": "eurlex_eu",
        "doc_type": "CASELAW",
        "title": "EUR-Lex document celex:62011CJ0415",
        "source_urls": [
            "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415"
        ],
        "current_source_hash": "ERROR",
    }
    current_source = {
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415",
        "raw_object_path": "docs/eurlex_eu:urlsha:broken/raw/ERROR/original.bin",
        "source_hash": "ERROR",
    }

    update_payload, manual_review = _build_document_update(
        runtime=FakeRuntime([]),
        article_inventory_cache={},
        docs_by_uid={"eurlex_eu:urlsha:broken": document},
        document=document,
        current_source=current_source,
        exact_entry=None,
        source_entry=None,
        duplicate_resolution=None,
        act_context_item=None,
        owner_document=None,
        owner_current_source=None,
        owner_entry=None,
    )

    assert update_payload["status"] == "excluded"
    assert update_payload["legal_role"] == "INVENTORY_ONLY"
    assert "Broken imported artifact retained for inventory only." in str(
        update_payload["exclusion_reason"]
    )
    assert update_payload["holding_1line"].startswith("Excluded corpus record")
    assert update_payload["superseded_by"] == "inventory_only"
    assert manual_review == []


def test_run_metadata_migration_resolves_broken_artifact_docs_without_manual_review(
    tmp_path: Path,
) -> None:
    documents = [
        {
            "doc_uid": "eurlex_eu:urlsha:broken-a",
            "source_system": "eurlex_eu",
            "doc_type": "CASELAW",
            "title": "Broken A",
            "source_urls": [
                "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415"
            ],
            "current_source_hash": "ERROR",
        },
        {
            "doc_uid": "curia_eu:urlsha:broken-b",
            "source_system": "curia_eu",
            "doc_type": "GUIDANCE",
            "title": "Broken B",
            "source_urls": ["https://curia.europa.eu/jcms/jcms/p1_4220451/en/"],
            "current_source_hash": "ERROR",
        },
    ]
    document_sources = [
        {
            "doc_uid": "eurlex_eu:urlsha:broken-a",
            "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415",
            "final_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415",
            "raw_object_path": "docs/eurlex_eu:urlsha:broken-a/raw/ERROR/original.bin",
            "source_hash": "ERROR",
        },
        {
            "doc_uid": "curia_eu:urlsha:broken-b",
            "url": "https://curia.europa.eu/jcms/jcms/p1_4220451/en/",
            "final_url": "https://curia.europa.eu/jcms/jcms/p1_4220451/en/",
            "raw_object_path": "docs/curia_eu:urlsha:broken-b/raw/ERROR/original.bin",
            "source_hash": "ERROR",
        },
    ]
    runtime = FakeMongoRuntime(
        documents=documents,
        document_sources=document_sources,
    )

    report = run_metadata_migration(
        runtime,
        artifact_config=ArtifactConfig(root_dir=tmp_path / "artifacts"),
        apply_changes=False,
        scope="full",
    )

    manual_review_doc_uids = {item["doc_uid"] for item in report["manual_review_items"]}

    assert manual_review_doc_uids == set()


def test_build_document_update_closes_unknown_official_mirror_manual_review() -> None:
    source_hash = "3" * 64
    document = {
        "doc_uid": "unknown:urlsha:4307a0f3b0cab777",
        "source_system": "unknown",
        "doc_type": "STATUTE",
        "title": "Ustawa z dnia 21 czerwca 2001 r. o ochronie praw lokatorow",
        "source_urls": ["https://dziennikustaw.gov.pl/DU/2001/733"],
        "current_source_hash": source_hash,
    }
    current_source = {
        "url": "https://dziennikustaw.gov.pl/DU/2001/733",
        "final_url": "https://dziennikustaw.gov.pl/DU/2001/s/71/733",
        "raw_object_path": "artifacts_dev/docs/unknown:urlsha:4307/raw/source.bin",
        "source_hash": source_hash,
    }

    update_payload, manual_review = _build_document_update(
        runtime=FakeRuntime([]),
        article_inventory_cache={},
        docs_by_uid={
            "unknown:urlsha:4307a0f3b0cab777": document,
            "eli_pl:DU/2001/733": {"doc_uid": "eli_pl:DU/2001/733"},
        },
        document=document,
        current_source=current_source,
        exact_entry=None,
        source_entry=None,
        duplicate_resolution=None,
        act_context_item={
            "act_id": "eli:DU/2001/733",
            "owner_doc_uid": "eli_pl:DU/2001/733",
        },
        owner_document={"doc_uid": "eli_pl:DU/2001/733"},
        owner_current_source=None,
        owner_entry=None,
    )

    assert update_payload["status"] == "alias"
    assert update_payload["legal_role"] == "SECONDARY_SOURCE"
    assert update_payload["source_tier"] == "official"
    assert update_payload["superseded_by"] == "eli_pl:DU/2001/733"
    assert manual_review == []


def test_build_document_update_uses_page_text_for_portal_case_normalization() -> None:
    document = {
        "doc_uid": "courts_pl:urlsha:20c9c82554a6e7f2",
        "source_system": "courts_pl",
        "doc_type": "CASELAW",
        "title": "Wyrok I Ca 56/18",
        "source_urls": [
            "https://orzeczenia.wloclawek.so.gov.pl/content/$N/151030000000503_I_Ca_000056_2018_Uz_2018-05-08_001"
        ],
        "pageindex_tree": [
            {
                "title": "Root Document",
                "nodes": [
                    {
                        "title": (
                            "I Ca 56/18 - wyrok z uzasadnieniem "
                            "Sad Okregowy we Wloclawku z 2018-05-08"
                        ),
                        "nodes": [],
                    }
                ],
            }
        ],
        "same_case_group_id": "same_case:i_ca_56_18",
    }

    update_payload, manual_review = _build_document_update(
        runtime=FakeRuntime([]),
        article_inventory_cache={},
        page_text_by_doc_uid={
            "courts_pl:urlsha:20c9c82554a6e7f2": (
                "Sad Okregowy we Wloclawku. Publikacja 8 listopada 2018."
            )
        },
        docs_by_uid={"courts_pl:urlsha:20c9c82554a6e7f2": document},
        document=document,
        current_source=None,
        exact_entry=None,
        source_entry=None,
        duplicate_resolution=None,
        act_context_item=None,
        owner_document=None,
        owner_current_source=None,
        owner_entry=None,
    )

    assert update_payload["judgment_date"] == "2018-05-08"
    assert update_payload["court_name"] == "Sad Okregowy we Wloclawku"
    assert manual_review == ["missing current document_source"]
