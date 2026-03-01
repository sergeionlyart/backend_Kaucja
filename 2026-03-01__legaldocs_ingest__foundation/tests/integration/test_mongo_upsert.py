import pytest
import pymongo
from legal_ingest.store.mongo import ensure_indexes
from legal_ingest.config import MongoConfig


# These tests will quickly connect to localhost:27017 which is the docker-compose mongo.
@pytest.fixture
def mongo_cfg():
    return MongoConfig(uri="mongodb://localhost:27017", db="test_legal_rag")


def test_ensure_indexes(mongo_cfg):
    # This should not raise any exceptions.
    try:
        ensure_indexes(mongo_cfg)
    except pymongo.errors.ConnectionFailure:
        pytest.skip("MongoDB not running, skipping integration test.")

    client = pymongo.MongoClient(mongo_cfg.uri)
    db = client[mongo_cfg.db]
    idx = db["documents"].index_information()
    assert "current_source_hash_1" in idx
