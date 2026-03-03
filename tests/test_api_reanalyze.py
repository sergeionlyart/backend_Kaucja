"""Tests for POST /api/v2/case/documents/reanalyze endpoint."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("PIPELINE_STUB", "true")



@pytest.fixture()
def _clean_case(tmp_path, monkeypatch):
    """Redirect case storage to tmp_path for isolation."""
    monkeypatch.setattr("app.api.service._CASES_DIR", tmp_path)
    monkeypatch.setattr("app.api.service._DATA_DIR", tmp_path.parent)
    yield tmp_path


@pytest.fixture()
def client(_clean_case):
    from app.api.main import create_app

    return TestClient(create_app())


CASE_ID = "KJ-2026-TEST-REANA"


def _seed_case(cases_dir: Path, with_files: bool = True) -> None:
    """Create a case with stored files metadata (and optionally actual files)."""
    upload_dir = cases_dir / CASE_ID / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    catalog_entries = []
    if with_files:
        for i, (name, cat) in enumerate([
            ("umowa.pdf", "lease"),
            ("potw.pdf", "deposit_payment"),
        ]):
            fpath = upload_dir / f"doc_{i:04x}_{name}"
            content = f"fake-pdf-content-{i}".encode()
            fpath.write_bytes(content)
            import hashlib
            sha = hashlib.sha256(content).hexdigest()
            catalog_entries.append({
                "doc_id": f"doc_{i:04x}",
                "categoryId": cat,
                "original_name": name,
                "sha256": sha,
                "uploaded_at": "2026-01-01T00:00:00+00:00",
                "size_bytes": len(content),
                "client_doc_id": f"client_{i}",
                "saved_path": str(fpath),
            })

    # Write documents.json catalog
    doc_catalog_path = cases_dir / CASE_ID / "documents.json"
    doc_catalog_path.write_text(json.dumps(catalog_entries, indent=2))

    case_path = cases_dir / CASE_ID / "case.json"
    case_path.write_text(json.dumps({
        "case_id": CASE_ID,
        "status": "analyzed",
        "intake_text": "Test kaucja case",
    }, ensure_ascii=False), encoding="utf-8")


# -------------------------------------------------------------------------
# Success path
# -------------------------------------------------------------------------


def test_reanalyze_success(_clean_case, client):
    """Reanalyze returns valid DocumentAnalyzeResponse from stored files."""
    _seed_case(_clean_case, with_files=True)

    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["case_id"] == CASE_ID
    assert len(data["analyzed_documents"]) == 2
    assert data["analyzed_documents"][0]["status"] == "done"
    assert "analysis_run_id" in data


# -------------------------------------------------------------------------
# CASE_NOT_FOUND (404)
# -------------------------------------------------------------------------


def test_reanalyze_case_not_found(_clean_case, client):
    """Reanalyze returns 404 when case doesn't exist."""
    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": "KJ-NONEXISTENT"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "CASE_NOT_FOUND"


# -------------------------------------------------------------------------
# NO_STORED_DOCUMENTS (422)
# -------------------------------------------------------------------------


def test_reanalyze_no_stored_documents(_clean_case, client):
    """Reanalyze returns 422 when case exists but has no stored files."""
    _seed_case(_clean_case, with_files=False)

    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "NO_STORED_DOCUMENTS"


# -------------------------------------------------------------------------
# Incremental upload scenario
# -------------------------------------------------------------------------


def test_reanalyze_incremental_preserves_previous(_clean_case, client):
    """After initial analyze + second partial analyze, all stored files persist."""
    upload_dir = _clean_case / CASE_ID / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # First analysis: seed 1 file via documents.json catalog
    file1 = upload_dir / "doc_0001_umowa.pdf"
    file1.write_bytes(b"fake-pdf")
    import hashlib
    sha1 = hashlib.sha256(b"fake-pdf").hexdigest()

    case_dir = _clean_case / CASE_ID
    doc_catalog = case_dir / "documents.json"
    doc_catalog.write_text(json.dumps([{
        "doc_id": "doc_0001",
        "categoryId": "lease",
        "original_name": "umowa.pdf",
        "sha256": sha1,
        "uploaded_at": "2026-01-01T00:00:00+00:00",
        "size_bytes": len(b"fake-pdf"),
        "client_doc_id": "c1",
        "saved_path": str(file1),
    }]), encoding="utf-8")

    case_path = case_dir / "case.json"
    case_path.write_text(json.dumps({
        "case_id": CASE_ID,
        "status": "analyzed",
    }), encoding="utf-8")

    # Simulate second analysis adding another file via _persist_files_info
    from app.api.service import _persist_files_info

    file2 = upload_dir / "doc_0002_potw.pdf"
    file2.write_bytes(b"fake-pdf-2")
    _persist_files_info(
        CASE_ID,
        [{"doc_id": "doc_0002", "category_id": "deposit_payment",
          "name": "potw.pdf", "content_length": 10, "client_doc_id": "c2"}],
        [file2],
    )

    # Verify both files are in documents.json catalog
    catalog = json.loads(doc_catalog.read_text(encoding="utf-8"))
    assert len(catalog) == 2
    doc_ids = {e["doc_id"] for e in catalog}
    assert doc_ids == {"doc_0001", "doc_0002"}

    # Reanalyze should pick up both
    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID},
    )
    assert resp.status_code == 200
    assert len(resp.json()["analyzed_documents"]) == 2


# -------------------------------------------------------------------------
# Path traversal / tampered saved_path
# -------------------------------------------------------------------------


def test_reanalyze_rejects_tampered_path(_clean_case, client):
    """Tampered saved_path (path traversal) is filtered out → NO_STORED_DOCUMENTS."""
    case_dir = _clean_case / CASE_ID
    case_dir.mkdir(parents=True, exist_ok=True)

    # Write a tampered case.json with path outside uploads dir
    case_path = case_dir / "case.json"
    case_path.write_text(json.dumps({
        "case_id": CASE_ID,
        "status": "analyzed",
        "stored_files": [{
            "doc_id": "doc_evil",
            "category_id": "lease",
            "name": "../../etc/passwd",
            "size_mb": 0.01,
            "client_doc_id": "evil",
            "saved_path": "/etc/passwd",
        }],
    }), encoding="utf-8")

    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID},
    )
    # Either 422 (no valid stored docs) or filtered out
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "NO_STORED_DOCUMENTS"


# -------------------------------------------------------------------------
# Prefix-bypass: uploads_evil directory
# -------------------------------------------------------------------------


def test_reanalyze_rejects_prefix_bypass(_clean_case, client):
    """Path under 'uploads_evil' dir must be blocked (prefix-bypass attack)."""
    case_dir = _clean_case / CASE_ID
    evil_dir = case_dir / "uploads_evil"
    evil_dir.mkdir(parents=True, exist_ok=True)
    evil_file = evil_dir / "pwned.pdf"
    evil_file.write_bytes(b"evil-content")

    # Also create the real uploads dir so the test is about path containment
    (case_dir / "uploads").mkdir(parents=True, exist_ok=True)

    case_path = case_dir / "case.json"
    case_path.write_text(json.dumps({
        "case_id": CASE_ID,
        "status": "analyzed",
        "stored_files": [{
            "doc_id": "doc_prefix",
            "category_id": "lease",
            "name": "pwned.pdf",
            "size_mb": 0.01,
            "client_doc_id": "prefix",
            "saved_path": str(evil_file),
        }],
    }), encoding="utf-8")

    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "NO_STORED_DOCUMENTS"


# -------------------------------------------------------------------------
# Symlink escape
# -------------------------------------------------------------------------


def test_reanalyze_rejects_symlink_escape(_clean_case, client, tmp_path):
    """Symlink pointing outside uploads dir must be blocked."""
    case_dir = _clean_case / CASE_ID
    upload_dir = case_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Create a file outside the case
    outside_file = tmp_path / "outside_secret.txt"
    outside_file.write_bytes(b"secret-data")

    # Create symlink inside uploads pointing outside
    symlink = upload_dir / "link_to_secret.pdf"
    try:
        symlink.symlink_to(outside_file)
    except OSError:
        pytest.skip("Cannot create symlinks in this environment")

    case_path = case_dir / "case.json"
    case_path.write_text(json.dumps({
        "case_id": CASE_ID,
        "status": "analyzed",
        "stored_files": [{
            "doc_id": "doc_symlink",
            "category_id": "lease",
            "name": "link_to_secret.pdf",
            "size_mb": 0.01,
            "client_doc_id": "symlink",
            "saved_path": str(symlink),
        }],
    }), encoding="utf-8")

    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "NO_STORED_DOCUMENTS"


# -------------------------------------------------------------------------
# Selective reanalyze: success
# -------------------------------------------------------------------------


def test_reanalyze_selective_success(_clean_case, client):
    """Selective reanalyze with specific document_ids returns only those docs."""
    _seed_case(_clean_case, with_files=True)

    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID, "document_ids": ["doc_0000"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["analyzed_documents"]) == 1
    assert data["analyzed_documents"][0]["categoryId"] == "lease"


# -------------------------------------------------------------------------
# Selective reanalyze: unknown document_id
# -------------------------------------------------------------------------


def test_reanalyze_selective_unknown_id(_clean_case, client):
    """Unknown document_id returns 422 VALIDATION_ERROR."""
    _seed_case(_clean_case, with_files=True)

    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID, "document_ids": ["doc_0000", "doc_UNKNOWN"]},
    )
    assert resp.status_code == 422
    err = resp.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert "doc_UNKNOWN" in err["message"]


# =========================================================================
# client_document_ids contract tests
# =========================================================================


def test_reanalyze_by_client_doc_ids(_clean_case, client):
    """Selective reanalyze via client_document_ids resolves correctly."""
    _seed_case(_clean_case, with_files=True)

    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID, "client_document_ids": ["client_0"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["analyzed_documents"]) == 1


def test_reanalyze_by_client_doc_ids_unknown(_clean_case, client):
    """Unknown client_document_id returns 422."""
    _seed_case(_clean_case, with_files=True)

    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID, "client_document_ids": ["client_nope"]},
    )
    assert resp.status_code == 422
    assert "client_nope" in resp.json()["error"]["message"]


def test_reanalyze_mutual_exclusivity(_clean_case, client):
    """Providing both document_ids and client_document_ids → 422."""
    _seed_case(_clean_case, with_files=True)

    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={
            "case_id": CASE_ID,
            "document_ids": ["doc_0000"],
            "client_document_ids": ["client_0"],
        },
    )
    assert resp.status_code == 422
    assert "mutually_exclusive" in json.dumps(resp.json())


def test_reanalyze_duplicate_ids_rejected(_clean_case, client):
    """Duplicate document_ids → 422."""
    _seed_case(_clean_case, with_files=True)

    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID, "document_ids": ["doc_0000", "doc_0000"]},
    )
    assert resp.status_code == 422
    assert "duplicates" in json.dumps(resp.json())


def test_reanalyze_empty_selector_rejected(_clean_case, client):
    """Empty document_ids list → 422."""
    _seed_case(_clean_case, with_files=True)

    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID, "document_ids": []},
    )
    assert resp.status_code == 422
    assert "empty" in json.dumps(resp.json())


def test_reanalyze_ordering(_clean_case, client):
    """Result ordering follows input document_ids order."""
    _seed_case(_clean_case, with_files=True)

    # Request in reversed order
    resp = client.post(
        "/api/v2/case/documents/reanalyze",
        json={"case_id": CASE_ID, "document_ids": ["doc_0001", "doc_0000"]},
    )
    assert resp.status_code == 200
    docs = resp.json()["analyzed_documents"]
    assert len(docs) == 2
    # Verify the first doc matches the first requested id's category
    assert docs[0]["categoryId"] == "deposit_payment"
    assert docs[1]["categoryId"] == "lease"
