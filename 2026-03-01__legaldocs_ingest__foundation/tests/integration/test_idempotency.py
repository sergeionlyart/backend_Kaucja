import pytest
import pymongo
from legal_ingest.config import MongoConfig
from legal_ingest.store.mongo import save_document_pipeline_results
from legal_ingest.store.models import (
    Document,
    DocumentSource,
    Page,
    Node,
    PageExtraction,
    PageExtractionQuality,
    ContentStats,
)


@pytest.fixture
def mongo_cfg():
    return MongoConfig(uri="mongodb://localhost:27017", db="test_legal_rag_idempotency")


def test_idempotent_upsert(mongo_cfg):
    client = pymongo.MongoClient(mongo_cfg.uri)
    db = client[mongo_cfg.db]

    # clean before test
    db.documents.drop()
    db.document_sources.drop()
    db.pages.drop()
    db.nodes.drop()

    ds = DocumentSource(
        _id="doc1|hash1",
        doc_uid="doc1",
        source_hash="hash1",
        source_id="test_source",
        url="http://test.com",
        final_url="http://test.com",
        http={"status_code": 200},
        raw_object_path="none",
        raw_mime="text/html",
        license_tag="OFFICIAL",
    )

    page = Page(
        _id="doc1|hash1|p:0",
        doc_uid="doc1",
        source_hash="hash1",
        page_index=0,
        text="test page",
        token_count_est=2,
        char_count=9,
        extraction=PageExtraction(
            method="HTML", quality=PageExtractionQuality(alpha_ratio=1.0, empty=False)
        ),
    )

    node = Node(
        _id="doc1|hash1|node:root",
        doc_uid="doc1",
        source_hash="hash1",
        node_id="root",
        parent_node_id="none",
        depth=0,
        order_index=0,
        title="root",
        start_index=0,
        end_index=1,
    )

    doc = Document(
        _id="doc1",
        doc_uid="doc1",
        doc_type="STATUTE",
        jurisdiction="PL",
        language="pl",
        source_system="test",
        source_urls=["http://test.com"],
        license_tag="OFFICIAL",
        access_status="OK",
        current_source_hash="hash1",
        mime="text/html",
        page_count=1,
        content_stats=ContentStats(
            total_chars=9, total_tokens_est=2, parse_method="HTML", ocr_used=False
        ),
    )

    # First upsert
    save_document_pipeline_results(mongo_cfg, ds, [page], [node], [], doc)

    assert db.document_sources.count_documents({}) == 1
    assert db.pages.count_documents({}) == 1
    assert db.nodes.count_documents({}) == 1
    assert db.documents.count_documents({}) == 1

    assert db.documents.count_documents({}) == 1

    # Second upsert (idempotent, exact same payload)
    save_document_pipeline_results(mongo_cfg, ds, [page], [node], [], doc)

    # Counts should NOT grow
    assert db.document_sources.count_documents({}) == 1
    assert db.pages.count_documents({}) == 1
    assert db.nodes.count_documents({}) == 1
    assert db.documents.count_documents({}) == 1
    assert db.documents.find_one({"_id": "doc1"})["current_source_hash"] == "hash1"

    # Third upsert: New source_hash simulating changed content
    ds2 = ds.model_copy(update={"id": "doc1|hash2", "source_hash": "hash2"})
    page2 = page.model_copy(update={"id": "doc1|hash2|p:0", "source_hash": "hash2"})
    node2 = node.model_copy(
        update={"id": "doc1|hash2|node:root", "source_hash": "hash2"}
    )
    doc2 = doc.model_copy(update={"current_source_hash": "hash2"})

    save_document_pipeline_results(mongo_cfg, ds2, [page2], [node2], [], doc2)

    # Historical values preserved, documents is replaced
    assert db.document_sources.count_documents({}) == 2
    assert db.pages.count_documents({}) == 2
    assert db.nodes.count_documents({}) == 2
    assert db.documents.count_documents({}) == 1
    assert db.documents.find_one({"_id": "doc1"})["current_source_hash"] == "hash2"
