from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _matches(row: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, value in query.items():
        if row.get(key) != value:
            return False
    return True


def _project_row(
    row: dict[str, Any],
    projection: dict[str, int] | None,
) -> dict[str, Any]:
    if projection is None:
        return copy.deepcopy(row)
    if any(value == 1 for value in projection.values()):
        projected: dict[str, Any] = {}
        for key, include in projection.items():
            if include != 1:
                continue
            value = _get_path(row, key)
            if value is not None:
                _set_path(projected, key, copy.deepcopy(value))
        return projected
    projected = copy.deepcopy(row)
    for key, include in projection.items():
        if include == 0:
            _unset_path(projected, key)
    return projected


def _get_path(row: dict[str, Any], path: str) -> Any:
    current: Any = row
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _set_path(row: dict[str, Any], path: str, value: Any) -> None:
    current = row
    parts = path.split(".")
    for part in parts[:-1]:
        nested = current.get(part)
        if not isinstance(nested, dict):
            nested = {}
            current[part] = nested
        current = nested
    current[parts[-1]] = value


def _unset_path(row: dict[str, Any], path: str) -> None:
    current = row
    parts = path.split(".")
    for part in parts[:-1]:
        nested = current.get(part)
        if not isinstance(nested, dict):
            return
        current = nested
    current.pop(parts[-1], None)


class FakeMongoCollection:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows = rows or []
        self.indexes: list[dict[str, Any]] = []

    def find(
        self,
        query: dict[str, Any] | None = None,
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        effective_query = query or {}
        return [
            _project_row(row, projection)
            for row in self.rows
            if _matches(row, effective_query)
        ]

    def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> dict[str, Any] | None:
        for row in self.rows:
            if _matches(row, query):
                return _project_row(row, projection)
        return None

    def delete_many(self, query: dict[str, Any]) -> None:
        if not query:
            self.rows = []
            return
        self.rows = [row for row in self.rows if not _matches(row, query)]

    def insert_many(self, rows: list[dict[str, Any]]) -> None:
        self.rows.extend(dict(row) for row in rows)

    def insert_one(self, row: dict[str, Any]) -> None:
        self.rows.append(dict(row))

    def update_one(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
    ) -> None:
        for index, row in enumerate(self.rows):
            if not _matches(row, query):
                continue
            updated = copy.deepcopy(row)
            for key, value in update.get("$set", {}).items():
                _set_path(updated, key, copy.deepcopy(value))
            for key in update.get("$unset", {}):
                _unset_path(updated, key)
            self.rows[index] = updated
            return
        if not upsert:
            return
        inserted = copy.deepcopy(query)
        for key, value in update.get("$setOnInsert", {}).items():
            _set_path(inserted, key, copy.deepcopy(value))
        for key, value in update.get("$set", {}).items():
            _set_path(inserted, key, copy.deepcopy(value))
        for key in update.get("$unset", {}):
            _unset_path(inserted, key)
        self.rows.append(inserted)

    def create_index(self, keys: list[tuple[str, int]], **kwargs: Any) -> None:
        if kwargs.get("unique"):
            seen: set[tuple[Any, ...]] = set()
            for row in self.rows:
                key = tuple(row.get(field) for field, _direction in keys)
                if key in seen:
                    raise RuntimeError(
                        "duplicate key error on unique index "
                        f"{keys}: {key}"
                    )
                seen.add(key)
        self.indexes.append({"keys": keys, "kwargs": kwargs})


@dataclass(slots=True)
class FakeMongoRuntime:
    collections: dict[str, FakeMongoCollection]
    db_name: str = "test_legal_runtime"
    config: Any = field(init=False)

    def __post_init__(self) -> None:
        self.config = type("Config", (), {"db_name": self.db_name})()

    def collection(self, name: str) -> FakeMongoCollection:
        return self.collections.setdefault(name, FakeMongoCollection())

    def load_collection(
        self,
        name: str,
        *,
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        return self.collection(name).find({}, projection=projection)


def build_legal_corpus_runtime() -> FakeMongoRuntime:
    act_doc_uid = "eli_pl:DU/2001/733"
    case_doc_uid = "saos_pl:171957"
    alias_doc_uid = "courts_pl:urlsha:mirror-171957"
    broken_doc_uid = "curia_eu:urlsha:broken"
    act_current_hash = "sha256:act-current"
    act_historical_hash = "sha256:act-historical"
    case_hash = "sha256:case-current"
    alias_hash = "sha256:alias-current"
    broken_hash = "sha256:broken-current"
    now_iso = datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc).isoformat()

    documents = [
        {
            "doc_uid": act_doc_uid,
            "current_source_hash": act_current_hash,
            "source_system": "eli_pl",
            "doc_type": "STATUTE",
            "document_kind": "STATUTE",
            "status": "canonical",
            "legal_role": "TENANCY_NORM",
            "source_tier": "official",
            "canonical_title": "Ustawa o ochronie praw lokatorow",
            "title_short": "Ustawa o ochronie praw lokatorow",
            "act_id": "eli:DU/2001/733",
            "act_short_name": "Ustawa o ochronie praw lokatorow",
            "display_citation": "Ustawa o ochronie praw lokatorow [eli_pl:DU/2001/733]",
            "issue_tags": ["deposit_return", "tenant_law"],
            "facts_tags": [],
            "related_provisions": ["art. 6 ust. 4 ustawy o ochronie praw lokatorow"],
            "current_status": "current",
            "jurisdiction": "pl",
            "language": "pl",
            "authority_weight": 100,
            "source_url": "https://eli.gov.pl/api/acts/DU/2001/733/text/U/D20010733Lj.pdf",
        },
        {
            "doc_uid": case_doc_uid,
            "current_source_hash": case_hash,
            "source_system": "saos_pl",
            "doc_type": "CASELAW",
            "document_kind": "CASELAW",
            "status": "canonical",
            "legal_role": "FACTUAL_CASE",
            "source_tier": "saos",
            "canonical_title": "Wyrok II Ca 886/14",
            "title_short": "II CA 886/14",
            "case_signature": "II CA 886/14",
            "court_name": "Sad Okregowy w Sieradzu",
            "court_level": "regional",
            "judgment_date": "2015-05-13",
            "same_case_group_id": "same_case:171957",
            "issue_tags": ["deposit_return", "tenant_law"],
            "facts_tags": ["property_damage", "utilities_after_move_out"],
            "related_provisions": ["art. 6 ust. 4 ustawy o ochronie praw lokatorow"],
            "display_citation": "Sad Okregowy w Sieradzu, II CA 886/14",
            "authority_weight": 85,
            "source_url": "https://www.saos.org.pl/judgments/171957",
        },
        {
            "doc_uid": alias_doc_uid,
            "current_source_hash": alias_hash,
            "source_system": "courts_pl",
            "doc_type": "CASELAW",
            "document_kind": "CASELAW",
            "status": "alias",
            "legal_role": "SECONDARY_SOURCE",
            "source_tier": "court_portal",
            "canonical_title": "Wyrok II Ca 886/14",
            "title_short": "II CA 886/14",
            "case_signature": "II CA 886/14",
            "court_name": "Sad Okregowy w Sieradzu",
            "court_level": "regional",
            "judgment_date": "2015-05-13",
            "same_case_group_id": "same_case:171957",
            "duplicate_owner_doc_uid": case_doc_uid,
            "operational_status": "alias",
            "is_indexable": False,
            "display_citation": "Sad Okregowy w Sieradzu, II CA 886/14 (mirror)",
            "source_url": "https://orzeczenia.example/171957",
        },
        {
            "doc_uid": broken_doc_uid,
            "current_source_hash": broken_hash,
            "source_system": "curia_eu",
            "doc_type": "CASELAW",
            "document_kind": "CASELAW",
            "status": "excluded",
            "legal_role": "INVENTORY_ONLY",
            "operational_status": "broken",
            "is_indexable": False,
            "canonical_title": "Broken inventory record",
            "display_citation": "Broken inventory record",
            "source_url": "https://curia.example/broken",
            "exclusion_reason": "Broken imported artifact retained for inventory only.",
        },
    ]

    document_sources = [
        {
            "doc_uid": act_doc_uid,
            "source_hash": act_historical_hash,
            "final_url": "https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.txt",
            "raw_object_path": "artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/historical.bin",
            "response_meta_path": "artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/historical.json",
            "storage_uri_normalized": "file://artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/historical.bin",
            "storage_backend": "file",
            "artifact_manifest": {
                "raw_bin_uri": "file://artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/historical.bin",
                "response_meta_uri": "file://artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/historical.json",
                "normalized_pages_uri": None,
                "normalized_nodes_uri": "file://artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/historical_nodes.json",
                "availability_flags": {
                    "raw_bin": True,
                    "response_meta": True,
                    "normalized_pages": False,
                    "normalized_nodes": True,
                },
            },
            "integrity_status": "ok",
            "is_current_source": False,
            "effective_from": "2001-07-10",
            "effective_to": "2024-12-31",
            "version_date": "2001-07-10",
            "version_kind": "historical",
        },
        {
            "doc_uid": act_doc_uid,
            "source_hash": act_current_hash,
            "final_url": "https://eli.gov.pl/api/acts/DU/2001/733/text/U/D20010733Lj.pdf",
            "raw_object_path": "artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/current.bin",
            "response_meta_path": "artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/current.json",
            "storage_uri_normalized": "file://artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/current.bin",
            "storage_backend": "file",
            "artifact_manifest": {
                "raw_bin_uri": "file://artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/current.bin",
                "response_meta_uri": "file://artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/current.json",
                "normalized_pages_uri": None,
                "normalized_nodes_uri": "file://artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/current_nodes.json",
                "availability_flags": {
                    "raw_bin": True,
                    "response_meta": True,
                    "normalized_pages": False,
                    "normalized_nodes": True,
                },
            },
            "integrity_status": "ok",
            "is_current_source": True,
            "effective_from": "2025-01-01",
            "effective_to": None,
            "version_date": "2025-01-01",
            "version_kind": "current",
        },
        {
            "doc_uid": case_doc_uid,
            "source_hash": case_hash,
            "final_url": "https://www.saos.org.pl/judgments/171957",
            "raw_object_path": "artifacts/legal_ingest/corpus/docs/saos_pl:171957/current.bin",
            "response_meta_path": "artifacts/legal_ingest/corpus/docs/saos_pl:171957/current.json",
            "storage_uri_normalized": "file://artifacts/legal_ingest/corpus/docs/saos_pl:171957/current.bin",
            "storage_backend": "file",
            "artifact_manifest": {
                "raw_bin_uri": "file://artifacts/legal_ingest/corpus/docs/saos_pl:171957/current.bin",
                "response_meta_uri": "file://artifacts/legal_ingest/corpus/docs/saos_pl:171957/current.json",
                "normalized_pages_uri": None,
                "normalized_nodes_uri": "file://artifacts/legal_ingest/corpus/docs/saos_pl:171957/current_nodes.json",
                "availability_flags": {
                    "raw_bin": True,
                    "response_meta": True,
                    "normalized_pages": False,
                    "normalized_nodes": True,
                },
            },
            "integrity_status": "ok",
            "is_current_source": True,
            "effective_from": "2015-05-13",
            "effective_to": None,
            "version_date": "2015-05-13",
            "version_kind": "official",
        },
        {
            "doc_uid": alias_doc_uid,
            "source_hash": alias_hash,
            "final_url": "https://orzeczenia.example/171957",
            "raw_object_path": "artifacts/legal_ingest/corpus/docs/courts_pl:urlsha:mirror-171957/current.bin",
            "response_meta_path": "artifacts/legal_ingest/corpus/docs/courts_pl:urlsha:mirror-171957/current.json",
            "storage_uri_normalized": "file://artifacts/legal_ingest/corpus/docs/courts_pl:urlsha:mirror-171957/current.bin",
            "storage_backend": "file",
            "artifact_manifest": {
                "raw_bin_uri": "file://artifacts/legal_ingest/corpus/docs/courts_pl:urlsha:mirror-171957/current.bin",
                "response_meta_uri": "file://artifacts/legal_ingest/corpus/docs/courts_pl:urlsha:mirror-171957/current.json",
                "normalized_pages_uri": None,
                "normalized_nodes_uri": "file://artifacts/legal_ingest/corpus/docs/courts_pl:urlsha:mirror-171957/current_nodes.json",
                "availability_flags": {
                    "raw_bin": True,
                    "response_meta": True,
                    "normalized_pages": False,
                    "normalized_nodes": True,
                },
            },
            "integrity_status": "ok",
            "is_current_source": True,
            "effective_from": "2015-05-13",
            "effective_to": None,
            "version_date": "2015-05-13",
            "version_kind": "mirror",
        },
        {
            "doc_uid": broken_doc_uid,
            "source_hash": broken_hash,
            "final_url": "https://curia.example/broken",
            "raw_object_path": "artifacts/legal_ingest/corpus/docs/curia_eu:urlsha:broken/ERROR/original.bin",
            "storage_uri_normalized": "file://artifacts/legal_ingest/corpus/docs/curia_eu:urlsha:broken/ERROR/original.bin",
            "storage_backend": "file",
            "integrity_status": "missing_artifact",
            "is_current_source": True,
            "version_kind": "inventory_only",
        },
    ]

    nodes = [
        {
            "doc_uid": act_doc_uid,
            "source_hash": act_historical_hash,
            "node_id": "art:6",
            "order_index": 1,
            "title": "Art. 6 ust. 4",
            "title_path": ["Ustawa o ochronie praw lokatorow", "Art. 6 ust. 4"],
            "text": (
                "Kaucja po wyprowadzce podlega zwrotowi po potraceniu naleznosci "
                "wynikajacych z najmu."
            ),
            "page_start": 4,
            "page_end": 4,
            "locator": {"article": "6", "ustep": "4"},
        },
        {
            "doc_uid": act_doc_uid,
            "source_hash": act_current_hash,
            "node_id": "art:6",
            "order_index": 1,
            "title": "Art. 6 ust. 4",
            "title_path": ["Ustawa o ochronie praw lokatorow", "Art. 6 ust. 4"],
            "text": (
                "Kaucja po wyprowadzce powinna zostac zwrocona w miesiac, "
                "a wlasciciel moze potrącic tylko naleznosci z tytulu najmu, "
                "szkody oraz zalegle oplaty za media i komunalne."
            ),
            "page_start": 5,
            "page_end": 5,
            "locator": {"article": "6", "ustep": "4"},
        },
        {
            "doc_uid": case_doc_uid,
            "source_hash": case_hash,
            "node_id": "holding:1",
            "order_index": 1,
            "semantic_role": "holding",
            "title": "Teza",
            "title_path": ["Wyrok II Ca 886/14", "Teza"],
            "text": (
                "Po wyjezdzie wlasciciel nie moze zatrzymac kaucji za "
                "uszkodzenia ani za zaleglosci komunalne bez udowodnienia "
                "wysokosci i podstawy roszczenia."
            ),
            "page_start": 2,
            "page_end": 2,
            "locator": {"paragraph": 1},
        },
        {
            "doc_uid": alias_doc_uid,
            "source_hash": alias_hash,
            "node_id": "holding:1",
            "order_index": 1,
            "semantic_role": "holding",
            "title": "Teza",
            "title_path": ["Wyrok II Ca 886/14", "Teza"],
            "text": (
                "Mirror copy: po wyjezdzie wlasciciel nie moze zatrzymac kaucji "
                "za uszkodzenia ani za zaleglosci komunalne bez dowodu."
            ),
            "page_start": 2,
            "page_end": 2,
            "locator": {"paragraph": 1},
        },
        {
            "doc_uid": broken_doc_uid,
            "source_hash": broken_hash,
            "node_id": "holding:1",
            "order_index": 1,
            "semantic_role": "holding",
            "title": "Broken",
            "title_path": ["Broken inventory"],
            "text": "Broken inventory mentions kaucja and szkody but should not be searchable.",
            "page_start": 1,
            "page_end": 1,
            "locator": {"paragraph": 1},
        },
    ]

    citations = [
        {
            "citation_uid": "citation:case-to-act",
            "from_doc_uid": case_doc_uid,
            "from_source_hash": case_hash,
            "from_node_id": "holding:1",
            "target_external_id": "eli:DU/2001/733",
        }
    ]

    ingest_runs = [
        {
            "run_id": "ingest-002",
            "status": "completed",
            "finished_at": now_iso,
            "updated_at": now_iso,
        }
    ]

    return FakeMongoRuntime(
        collections={
            "documents": FakeMongoCollection(documents),
            "document_sources": FakeMongoCollection(document_sources),
            "nodes": FakeMongoCollection(nodes),
            "pages": FakeMongoCollection([]),
            "citations": FakeMongoCollection(citations),
            "ingest_runs": FakeMongoCollection(ingest_runs),
        }
    )
