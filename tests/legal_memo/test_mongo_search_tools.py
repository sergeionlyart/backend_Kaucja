from __future__ import annotations

from dataclasses import dataclass

from tests.fake_mongo_runtime import FakeMongoCollection

from app.legal_memo.mongo_search_tools import (
    GetAnchorDetailsItem,
    LegalSearchContext,
    _get_anchor_details_logic,
    _search_legal_anchors_logic,
    _search_legal_docs_logic,
)


@dataclass
class FakeDb:
    collections: dict[str, FakeMongoCollection]

    def __getitem__(self, name: str) -> FakeMongoCollection:
        return self.collections[name]


def build_search_context() -> LegalSearchContext:
    master = FakeMongoCollection(
        [
            {
                "_id": "act-1",
                "processing": {"status": "completed"},
                "source": {"title": "Ustawa o ochronie praw lokatorow"},
                "search": {
                    "document_family": "normative_act",
                    "authority_level": "primary",
                    "usually_supports": "both",
                    "topic_codes": ["deposit_return_term", "allowed_deductions"],
                    "tags_original": ["kaucja", "zwrot"],
                    "tags_ru": ["залог"],
                },
            },
            {
                "_id": "commentary-1",
                "processing": {"status": "completed"},
                "source": {"title": "Komentarz"},
                "search": {
                    "document_family": "commentary_article",
                    "authority_level": "medium",
                    "usually_supports": "both",
                    "topic_codes": ["allowed_deductions"],
                    "tags_original": ["potracenie"],
                    "tags_ru": [],
                },
            },
        ]
    )
    anchors = FakeMongoCollection(
        [
            {
                "doc_id": "act-1",
                "anchor_id": "s01-p001",
                "passage_text": "Zwrot kaucji powinien nastapic w terminie miesiaca.",
                "preview": "Zwrot kaucji powinien nastapic...",
                "locator": {"label": "Art. 6 ust. 4"},
                "doc_meta": {
                    "title": "Ustawa o ochronie praw lokatorow",
                    "topic_codes": ["deposit_return_term"],
                    "authority_level": "primary",
                    "usually_supports": "both",
                    "document_family": "normative_act",
                },
            }
        ]
    )
    return LegalSearchContext(
        db=FakeDb({"master": master, "anchors": anchors}),
        master_collection_name="master",
        anchor_collection_name="anchors",
        search_calls_left=2,
        max_docs_per_search=5,
        max_anchors_per_search=8,
        legal_refs_left=2,
    )


def test_search_legal_docs_returns_budget_and_hits() -> None:
    context = build_search_context()
    result = _search_legal_docs_logic(
        ctx=context,
        question="How fast must the deposit be returned?",
        issue_codes=["deposit_return_term"],
    )
    assert result.status == "ok"
    assert result.hits[0].doc_id == "act-1"
    assert result.budget_remaining.search_calls_left == 1


def test_search_legal_anchors_prefilters_by_candidate_docs() -> None:
    context = build_search_context()
    result = _search_legal_anchors_logic(
        ctx=context,
        query="zwrot kaucji termin",
        candidate_doc_ids=["act-1"],
        issue_code="deposit_return_term",
    )
    assert result.status == "ok"
    assert result.hits[0].anchor_id == "s01-p001"
    assert result.budget_remaining.search_calls_left == 1


def test_get_anchor_details_respects_legal_ref_budget() -> None:
    context = build_search_context()
    result = _get_anchor_details_logic(
        ctx=context,
        items=[
            GetAnchorDetailsItem(doc_id="act-1", anchor_id="s01-p001"),
            GetAnchorDetailsItem(doc_id="act-1", anchor_id="s01-p999"),
        ],
    )
    assert result.status == "ok"
    assert result.items[0].doc_id == "act-1"
    assert result.budget_remaining.legal_refs_left == 0
