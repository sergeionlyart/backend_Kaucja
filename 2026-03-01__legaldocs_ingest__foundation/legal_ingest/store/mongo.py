import pymongo
from .models import Document, DocumentSource, Page, Node, IngestRun
from ..config import MongoConfig


def get_client(config: MongoConfig) -> pymongo.MongoClient:
    return pymongo.MongoClient(config.uri)


def ensure_indexes(config: MongoConfig):
    client = get_client(config)
    db = client[config.db]

    # documents
    coll_docs = db["documents"]
    coll_docs.create_index("current_source_hash")
    coll_docs.create_index([("doc_type", 1), ("jurisdiction", 1), ("language", 1)])
    coll_docs.create_index("external_ids.eli", sparse=True)
    coll_docs.create_index("external_ids.saos_id", sparse=True)

    # document_sources
    coll_ds = db["document_sources"]
    coll_ds.create_index([("doc_uid", 1), ("source_hash", 1)], unique=True)
    coll_ds.create_index([("fetched_at", -1)])

    # pages
    coll_pages = db["pages"]
    coll_pages.create_index(
        [("doc_uid", 1), ("source_hash", 1), ("page_index", 1)], unique=True
    )
    coll_pages.create_index([("doc_uid", 1), ("source_hash", 1)])

    # nodes
    coll_nodes = db["nodes"]
    coll_nodes.create_index(
        [("doc_uid", 1), ("source_hash", 1), ("node_id", 1)], unique=True
    )
    coll_nodes.create_index([("doc_uid", 1), ("source_hash", 1), ("start_index", 1)])
    coll_nodes.create_index(
        [("doc_uid", 1), ("source_hash", 1), ("anchors.article", 1)], sparse=True
    )

    # citations
    coll_cit = db["citations"]
    coll_cit.create_index([("doc_uid", 1), ("source_hash", 1), ("_id", 1)], unique=True)
    coll_cit.create_index("target.external_id", sparse=True)

    # ingest_runs
    coll_runs = db["ingest_runs"]
    coll_runs.create_index([("started_at", -1)])

    print("MongoDB indexes ensured successfully.")


def save_run(config: MongoConfig, run_model: IngestRun):
    client = get_client(config)
    db = client[config.db]
    doc = run_model.model_dump(by_alias=True)
    db["ingest_runs"].replace_one({"_id": run_model.id}, doc, upsert=True)


def save_document_pipeline_results(
    config: MongoConfig,
    doc_source: DocumentSource,
    pages: list[Page],
    nodes: list[Node],
    citations: list,
    document: Document,
):
    """
    Persists data to MongoDB idempotently using bulk operations.
    Order required by TechSpec:
    1. document_sources
    2. pages
    3. nodes
    4. citations
    5. documents
    """
    client = get_client(config)
    db = client[config.db]

    # 1. document_sources
    # upsert on _id
    req_ds = pymongo.ReplaceOne(
        {"_id": doc_source.id}, doc_source.model_dump(by_alias=True), upsert=True
    )
    db["document_sources"].bulk_write([req_ds])

    # 2. pages
    if pages:
        reqs_pages = [
            pymongo.ReplaceOne({"_id": p.id}, p.model_dump(by_alias=True), upsert=True)
            for p in pages
        ]
        db["pages"].bulk_write(reqs_pages)

    # 3. nodes
    if nodes:
        reqs_nodes = [
            pymongo.ReplaceOne({"_id": n.id}, n.model_dump(by_alias=True), upsert=True)
            for n in nodes
        ]
        db["nodes"].bulk_write(reqs_nodes)

    # 4. citations
    if citations:
        reqs_cits = [
            pymongo.ReplaceOne({"_id": c.id}, c.model_dump(by_alias=True), upsert=True)
            for c in citations
        ]
        db["citations"].bulk_write(reqs_cits)

    # 5. documents
    req_docs = pymongo.ReplaceOne(
        {"_id": document.id}, document.model_dump(by_alias=True), upsert=True
    )
    db["documents"].bulk_write([req_docs])
