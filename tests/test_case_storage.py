from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.api import service


CASE_ID = "KJ-2026-STORAGE-TEST"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture()
def _clean_case(tmp_path, monkeypatch):
    """Use tmp_path for case storage."""
    monkeypatch.setattr(service, "_CASES_DIR", tmp_path)
    yield tmp_path


# =========================================================================
# SHA256 dedup
# =========================================================================


def test_save_upload_dedup_same_content(_clean_case):
    """Uploading identical content returns same path, dedup hit."""
    content = b"%PDF-1.4 identical content"
    r1 = service.save_upload(CASE_ID, "a.pdf", content)
    r2 = service.save_upload(CASE_ID, "b.pdf", content)
    assert r1["saved_path"] == r2["saved_path"]
    assert r1["sha256"] == r2["sha256"]
    assert r2["is_dedup_hit"] is True


def test_save_upload_different_content(_clean_case):
    """Different content creates different files."""
    r1 = service.save_upload(CASE_ID, "a.pdf", b"%PDF-1.4 AAA")
    r2 = service.save_upload(CASE_ID, "b.pdf", b"%PDF-1.4 BBB")
    assert r1["saved_path"] != r2["saved_path"]
    assert r1["is_dedup_hit"] is False
    assert r2["is_dedup_hit"] is False


def test_save_upload_dedup_does_not_overwrite(_clean_case):
    """Dedup returns existing path without modifying the file."""
    content = b"%PDF-1.4 same"
    r1 = service.save_upload(CASE_ID, "original.pdf", content)
    mtime_before = r1["saved_path"].stat().st_mtime
    time.sleep(0.05)  # ensure different mtime if re-written

    r2 = service.save_upload(CASE_ID, "duplicate.pdf", content)
    assert r2["saved_path"] == r1["saved_path"]
    assert r2["saved_path"].stat().st_mtime == mtime_before  # not re-written


def test_save_upload_returns_existing_doc_id(_clean_case):
    """Catalog dedup hit returns existing_doc_id."""
    content = b"%PDF-1.4 stable identity"
    # First upload
    r1 = service.save_upload(CASE_ID, "first.pdf", content)
    assert r1["is_dedup_hit"] is False

    # Seed catalog with a doc_id for this sha256
    service._save_documents_catalog(CASE_ID, [{
        "doc_id": "doc_stable_001",
        "sha256": r1["sha256"],
        "saved_path": str(r1["saved_path"]),
        "original_name": "first.pdf",
    }])

    # Second upload with same content → should return existing doc_id
    r2 = service.save_upload(CASE_ID, "second.pdf", content)
    assert r2["is_dedup_hit"] is True
    assert r2["existing_doc_id"] == "doc_stable_001"


# =========================================================================
# Case lock
# =========================================================================


def test_case_lock_acquire_and_release(_clean_case):
    """Lock can be acquired, released, and re-acquired."""
    service.acquire_case_lock(CASE_ID)
    service.release_case_lock(CASE_ID)
    # Should not raise
    service.acquire_case_lock(CASE_ID)
    service.release_case_lock(CASE_ID)


def test_case_lock_busy_raises_409(_clean_case):
    """Second acquire without release raises CASE_BUSY (409)."""
    from app.api.errors import ApiError

    service.acquire_case_lock(CASE_ID)
    try:
        with pytest.raises(ApiError) as exc_info:
            service.acquire_case_lock(CASE_ID)
        assert exc_info.value.status_code == 409
        assert exc_info.value.error_code == "CASE_BUSY"
    finally:
        service.release_case_lock(CASE_ID)


def test_case_lock_different_cases_independent(_clean_case):
    """Different case_ids don't block each other."""
    service.acquire_case_lock("case_A")
    service.acquire_case_lock("case_B")
    service.release_case_lock("case_A")
    service.release_case_lock("case_B")


def test_case_lock_via_api_409(_clean_case, client):
    """API endpoint returns 409 CASE_BUSY when case is locked."""
    # Hold the lock
    service.acquire_case_lock(CASE_ID)
    try:
        resp = client.post(
            "/api/v2/case/documents/reanalyze",
            json={"case_id": CASE_ID},
        )
        # The reanalyze will try to acquire the lock and fail
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "CASE_BUSY"
    finally:
        service.release_case_lock(CASE_ID)


# =========================================================================
# Legacy migration: stored_files → documents.json
# =========================================================================


def test_legacy_stored_files_auto_migrated(_clean_case):
    """stored_files in case.json triggers auto-migration to documents.json."""
    import json

    case_dir = _clean_case / CASE_ID
    case_dir.mkdir(parents=True, exist_ok=True)
    upload_dir = case_dir / "uploads"
    upload_dir.mkdir()

    fpath = upload_dir / "doc_0000_test.pdf"
    fpath.write_bytes(b"old-content")

    # Write legacy format (stored_files in case.json)
    case_json = case_dir / "case.json"
    case_json.write_text(json.dumps({
        "case_id": CASE_ID,
        "status": "analyzed",
        "stored_files": [{
            "doc_id": "doc_0000",
            "category_id": "lease",
            "name": "test.pdf",
            "size_mb": 0.01,
            "saved_path": str(fpath),
        }],
    }))

    # list_stored_documents should trigger migration
    docs = service.list_stored_documents(CASE_ID)
    assert len(docs) == 1
    assert docs[0]["doc_id"] == "doc_0000"

    # documents.json should now exist
    cat_path = case_dir / "documents.json"
    assert cat_path.is_file()
    catalog = json.loads(cat_path.read_text())
    assert len(catalog) == 1


# =========================================================================
# Catalog persistence (_persist_files_info)
# =========================================================================


def test_persist_files_writes_catalog(_clean_case):
    """_persist_files_info writes documents.json with sha256."""
    import json

    case_dir = _clean_case / CASE_ID
    upload_dir = case_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    fpath = upload_dir / "doc_0000_test.pdf"
    fpath.write_bytes(b"test-content")

    service._persist_files_info(
        CASE_ID,
        [{"doc_id": "doc_0000", "category_id": "lease", "name": "test.pdf",
          "content_length": 12, "client_doc_id": "c1"}],
        [fpath],
    )

    cat_path = case_dir / "documents.json"
    assert cat_path.is_file()
    catalog = json.loads(cat_path.read_text())
    assert len(catalog) == 1
    assert catalog[0]["sha256"] != ""
    assert catalog[0]["categoryId"] == "lease"
    assert catalog[0]["original_name"] == "test.pdf"
    assert catalog[0]["size_bytes"] == 12


def test_lock_release_after_exception(_clean_case):
    """Lock is released even when an exception occurs inside critical section."""
    service.acquire_case_lock(CASE_ID)
    try:
        raise ValueError("simulated failure")
    except ValueError:
        pass
    finally:
        service.release_case_lock(CASE_ID)

    # Lock should be available again
    service.acquire_case_lock(CASE_ID)
    service.release_case_lock(CASE_ID)


# =========================================================================
# No side-effects on 409 CASE_BUSY
# =========================================================================


def test_409_no_side_effects_on_analyze(_clean_case, client):
    """When 409 CASE_BUSY fires, no files are created in the case dir."""
    import io
    import os

    case_dir = _clean_case / CASE_ID
    case_dir.mkdir(parents=True, exist_ok=True)

    # Snapshot case dir before (exclude .lock files — infrastructure only)
    def snapshot_dir(d):
        result = set()
        if d.exists():
            for root, _dirs, files in os.walk(d):
                for f in files:
                    if f == ".lock":
                        continue
                    p = os.path.join(root, f)
                    result.add((os.path.relpath(p, d), os.path.getsize(p)))
        return result

    before = snapshot_dir(case_dir)

    # Hold the lock -> any analyze should get 409
    service.acquire_case_lock(CASE_ID)
    try:
        pdf = b"%PDF-1.4 " + b"x" * 50
        resp = client.post(
            "/api/v2/case/documents/analyze",
            data={
                "case_id": CASE_ID,
                "files_category": ["lease"],
            },
            files=[("files", ("test.pdf", io.BytesIO(pdf), "application/pdf"))],
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "CASE_BUSY"

        # Case dir should be unchanged
        after = snapshot_dir(case_dir)
        assert before == after, f"Side effect detected: before={before}, after={after}"
    finally:
        service.release_case_lock(CASE_ID)


def test_concurrent_analyze_one_wins(_clean_case, client):
    """First analyze succeeds, second gets 409 if lock is held."""
    import io

    pdf = b"%PDF-1.4 concurrent"
    # Hold lock -> next request gets 409
    service.acquire_case_lock(CASE_ID)
    try:
        resp = client.post(
            "/api/v2/case/documents/analyze",
            data={"case_id": CASE_ID, "files_category": ["lease"]},
            files=[("files", ("a.pdf", io.BytesIO(pdf), "application/pdf"))],
        )
        assert resp.status_code == 409
    finally:
        service.release_case_lock(CASE_ID)

    # After release, analyze should work
    resp2 = client.post(
        "/api/v2/case/documents/analyze",
        data={"case_id": CASE_ID, "files_category": ["lease"]},
        files=[("files", ("a.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp2.status_code == 200


# =========================================================================
# Catalog consistency after stub persistence fix
# =========================================================================


def test_analyze_catalog_paths_valid(_clean_case, client):
    """After analyze, catalog entries have existing paths and non-empty sha256."""
    import io

    pdf = b"%PDF-1.4 catalog check"
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={"case_id": CASE_ID, "files_category": ["lease"]},
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 200

    catalog = service._load_documents_catalog(CASE_ID)
    assert len(catalog) >= 1
    for entry in catalog:
        assert entry.get("sha256"), f"Empty sha256 in catalog entry: {entry}"
        p = Path(entry["saved_path"])
        assert p.is_file(), f"saved_path does not exist: {p}"


def test_analyze_dedup_reuses_doc_id(_clean_case, client):
    """Same file uploaded in two analyze calls → doc_id is stable."""
    import io

    pdf = b"%PDF-1.4 stable identity via API"

    # First analyze
    resp1 = client.post(
        "/api/v2/case/documents/analyze",
        data={"case_id": CASE_ID, "files_category": ["lease"]},
        files=[("files", ("contract.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp1.status_code == 200
    doc_id_1 = resp1.json()["analyzed_documents"][0]["id"]

    # Second analyze with same content
    resp2 = client.post(
        "/api/v2/case/documents/analyze",
        data={"case_id": CASE_ID, "files_category": ["lease"]},
        files=[("files", ("contract_v2.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp2.status_code == 200
    doc_id_2 = resp2.json()["analyzed_documents"][0]["id"]

    # doc_id should be reused from catalog
    assert doc_id_2 == doc_id_1, f"Expected stable doc_id, got {doc_id_1} vs {doc_id_2}"


def test_reanalyze_after_dedup_no_lost_docs(_clean_case, client):
    """Reanalyze after dedup scenario preserves all documents."""
    import io

    pdf = b"%PDF-1.4 reanalyze after dedup"
    # Initial analyze
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={"case_id": CASE_ID, "files_category": ["lease"]},
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 200

    catalog_before = service._load_documents_catalog(CASE_ID)
    assert len(catalog_before) >= 1

    # Reanalyze
    resp2 = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID, "reuse_existing": True},
    )
    assert resp2.status_code == 200

    catalog_after = service._load_documents_catalog(CASE_ID)
    assert len(catalog_after) >= len(catalog_before), \
        f"Lost documents: {len(catalog_before)} → {len(catalog_after)}"


# =========================================================================
# Dedup policy invariants
# =========================================================================


def test_dedup_policy_same_file_two_uploads(_clean_case, client):
    """Same file uploaded twice → same physical path + stable doc_id."""
    import io

    pdf = b"%PDF-1.4 policy invariant test"

    # Upload 1
    resp1 = client.post(
        "/api/v2/case/documents/analyze",
        data={"case_id": CASE_ID, "files_category": ["lease"]},
        files=[("files", ("doc.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp1.status_code == 200
    doc1 = resp1.json()["analyzed_documents"][0]

    # Upload 2 same content
    resp2 = client.post(
        "/api/v2/case/documents/analyze",
        data={"case_id": CASE_ID, "files_category": ["lease"]},
        files=[("files", ("doc_copy.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp2.status_code == 200
    doc2 = resp2.json()["analyzed_documents"][0]

    # Logical identity: same doc_id (catalog hit reuses)
    assert doc2["id"] == doc1["id"], \
        f"doc_id not reused: {doc1['id']} vs {doc2['id']}"

    # Physical dedup: catalog has only one saved_path
    catalog = service._load_documents_catalog(CASE_ID)
    paths = {e["saved_path"] for e in catalog}
    assert len(paths) == 1, f"Expected 1 physical path, got {paths}"


def test_dedup_policy_selective_reanalyze_targets_only(_clean_case, client):
    """Selective reanalyze only updates targeted documents."""
    import io

    pdf_a = b"%PDF-1.4 selective A"
    pdf_b = b"%PDF-1.4 selective B"

    # Upload 2 different docs
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={"case_id": CASE_ID, "files_category": ["lease", "deposit_payment"]},
        files=[
            ("files", ("a.pdf", io.BytesIO(pdf_a), "application/pdf")),
            ("files", ("b.pdf", io.BytesIO(pdf_b), "application/pdf")),
        ],
    )
    assert resp.status_code == 200
    docs = resp.json()["analyzed_documents"]
    assert len(docs) == 2

    doc_id_a = docs[0]["id"]

    # Selective reanalyze targeting only doc A
    resp2 = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID, "document_ids": [doc_id_a]},
    )
    assert resp2.status_code == 200
    reanalyzed = resp2.json()["analyzed_documents"]
    reanalyzed_ids = {d["id"] for d in reanalyzed}
    assert doc_id_a in reanalyzed_ids


def test_dedup_policy_no_phantom_paths(_clean_case, client):
    """After dedup + analyze, no catalog entry has a non-existent saved_path."""
    import io

    pdf = b"%PDF-1.4 phantom check"

    # First analyze
    client.post(
        "/api/v2/case/documents/analyze",
        data={"case_id": CASE_ID, "files_category": ["lease"]},
        files=[("files", ("x.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    # Second analyze (dedup hit)
    client.post(
        "/api/v2/case/documents/analyze",
        data={"case_id": CASE_ID, "files_category": ["lease"]},
        files=[("files", ("y.pdf", io.BytesIO(pdf), "application/pdf"))],
    )

    catalog = service._load_documents_catalog(CASE_ID)
    for entry in catalog:
        sp = entry.get("saved_path", "")
        assert sp, f"Empty saved_path in entry: {entry}"
        assert Path(sp).is_file(), f"Phantom path: {sp}"
        assert entry.get("sha256"), f"Empty sha256 in entry: {entry}"
