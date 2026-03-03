"""Tests for documents/analyze endpoint contract - TechSpec aligned.

Validates:
  - ``analyzed_documents`` is a list (not dict)
  - Each doc has: id, categoryId, name, sizeMb, status (done|error),
    progress (0..100), extracted_fields, analyzed_at
  - ``questions`` key (not ``open_questions``)
  - Summary fields and fields_meta present
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.api.models import DocumentAnalyzeResponse


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def _make_pdf(size: int = 200) -> bytes:
    return b"%PDF-1.4 " + b"x" * size


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------


def test_analyze_response_shape(client: TestClient) -> None:
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-SHAPE",
            "files_category": ["lease"],
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 200
    data = resp.json()

    # Must parse via Pydantic model without error
    parsed = DocumentAnalyzeResponse(**data)
    assert parsed.case_id == "KJ-2026-SHAPE"
    assert isinstance(parsed.analyzed_documents, list)
    assert isinstance(parsed.summary_fields, list)
    assert isinstance(parsed.fields_meta, dict)
    assert isinstance(parsed.questions, list)
    assert isinstance(parsed.missing_docs, list)


def test_analyzed_documents_is_list_not_dict(client: TestClient) -> None:
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-LIST",
            "files_category": ["lease"],
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    data = resp.json()
    assert "analyzed_documents" in data
    assert isinstance(data["analyzed_documents"], list)
    assert "documents_by_id" not in data


# ---------------------------------------------------------------------------
# Document model keys
# ---------------------------------------------------------------------------


def test_document_keys_match_ui_v2(client: TestClient) -> None:
    """Each doc must have: id, categoryId, name, sizeMb, status, progress,
    extracted_fields, analyzed_at."""
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-KEYS",
            "files_category": ["deposit_payment"],
        },
        files=[("files", ("potwierdzenie.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    data = resp.json()
    docs = data["analyzed_documents"]
    assert len(docs) == 1

    doc = docs[0]
    # Required keys
    assert "id" in doc
    assert "categoryId" in doc
    assert "name" in doc
    assert "sizeMb" in doc
    assert "status" in doc
    assert "progress" in doc
    assert "extracted_fields" in doc
    assert "analyzed_at" in doc

    # Old keys must NOT be present
    assert "doc_id" not in doc
    assert "category_id" not in doc
    assert "size_mb" not in doc


def test_document_status_is_done(client: TestClient) -> None:
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-STAT",
            "files_category": ["lease"],
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    data = resp.json()
    doc = data["analyzed_documents"][0]
    assert doc["status"] in ("done", "error")
    assert doc["status"] == "done"  # stub always returns done


def test_document_progress_0_to_100(client: TestClient) -> None:
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-PROG",
            "files_category": ["lease"],
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    data = resp.json()
    doc = data["analyzed_documents"][0]
    assert isinstance(doc["progress"], int)
    assert 0 <= doc["progress"] <= 100
    assert doc["progress"] == 100  # stub


# ---------------------------------------------------------------------------
# Questions key
# ---------------------------------------------------------------------------


def test_questions_key_not_open_questions(client: TestClient) -> None:
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-QKEY",
            "files_category": ["lease"],
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    data = resp.json()
    assert "questions" in data
    assert "open_questions" not in data


# ---------------------------------------------------------------------------
# Extracted fields
# ---------------------------------------------------------------------------


def test_lease_extracts_expected_fields(client: TestClient) -> None:
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-EXT",
            "files_category": ["lease"],
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    data = resp.json()
    doc = data["analyzed_documents"][0]
    assert "lease_agreement" in doc["extracted_fields"]


# ---------------------------------------------------------------------------
# Multiple files
# ---------------------------------------------------------------------------


def test_multiple_files_analyzed(client: TestClient) -> None:
    pdf1 = _make_pdf()
    pdf2 = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-MULTI",
            "files_category": ["lease", "deposit_payment"],
        },
        files=[
            ("files", ("umowa.pdf", io.BytesIO(pdf1), "application/pdf")),
            ("files", ("potwierdzenie.pdf", io.BytesIO(pdf2), "application/pdf")),
        ],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["analyzed_documents"]) == 2
    cats = {d["categoryId"] for d in data["analyzed_documents"]}
    assert cats == {"lease", "deposit_payment"}


# ---------------------------------------------------------------------------
# Missing docs reduced with uploads
# ---------------------------------------------------------------------------


def test_missing_docs_reduced_with_lease_upload(
    client: TestClient,
) -> None:
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-MISS",
            "files_category": ["lease"],
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    data = resp.json()
    missing_types = {d["doc_type"] for d in data["missing_docs"]}
    assert "lease" not in missing_types  # uploaded, so no longer missing


# ---------------------------------------------------------------------------
# Optional intake_text parameter
# ---------------------------------------------------------------------------


def test_intake_text_optional_param_accepted(client: TestClient) -> None:
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-INT",
            "files_category": ["lease"],
            "intake_text": "Potrzebuje zwrotu kaucji",
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# client_doc_id support
# ---------------------------------------------------------------------------


def test_client_doc_id_echoed_in_response(client: TestClient) -> None:
    """When client_doc_id is sent, it must appear in analyzed_documents."""
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-CID",
            "files_category": ["lease"],
            "client_doc_id": ["v2_doc_123_abc"],
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 200
    data = resp.json()
    doc = data["analyzed_documents"][0]
    assert doc["client_doc_id"] == "v2_doc_123_abc"


def test_client_doc_id_absent_backward_compat(client: TestClient) -> None:
    """Without client_doc_id, API works as before (null in response)."""
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-NOCID",
            "files_category": ["lease"],
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 200
    data = resp.json()
    doc = data["analyzed_documents"][0]
    assert doc.get("client_doc_id") is None


def test_client_doc_id_length_mismatch_rejected(client: TestClient) -> None:
    """client_doc_id count != files count → validation error."""
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-CIDMM",
            "files_category": ["lease"],
            "client_doc_id": ["id1", "id2"],  # 2 IDs but 1 file
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "FILES_VALIDATION_ERROR"
    assert "client_doc_id" in body["error"]["details"]


def test_client_doc_id_multi_file(client: TestClient) -> None:
    """Multiple files with client_doc_id — each echoed back correctly."""
    pdf1 = _make_pdf()
    pdf2 = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-CIDM",
            "files_category": ["lease", "deposit_payment"],
            "client_doc_id": ["frontend_id_A", "frontend_id_B"],
        },
        files=[
            ("files", ("umowa.pdf", io.BytesIO(pdf1), "application/pdf")),
            ("files", ("potw.pdf", io.BytesIO(pdf2), "application/pdf")),
        ],
    )
    assert resp.status_code == 200
    data = resp.json()
    docs = data["analyzed_documents"]
    assert len(docs) == 2
    client_ids = {d["client_doc_id"] for d in docs}
    assert client_ids == {"frontend_id_A", "frontend_id_B"}


def test_client_doc_id_with_intake_text(client: TestClient) -> None:
    """client_doc_id + intake_text together work correctly."""
    pdf = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-CIDIT",
            "files_category": ["lease"],
            "client_doc_id": ["my_local_id"],
            "intake_text": "Potrzebuje zwrotu kaucji za mieszkanie.",
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 200
    data = resp.json()
    doc = data["analyzed_documents"][0]
    assert doc["client_doc_id"] == "my_local_id"


def test_client_doc_id_duplicates_rejected(client: TestClient) -> None:
    """Duplicate client_doc_id values within one request → 422."""
    pdf1 = _make_pdf()
    pdf2 = _make_pdf()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-CIDDUP",
            "files_category": ["lease", "deposit_payment"],
            "client_doc_id": ["same_id", "same_id"],  # duplicate!
        },
        files=[
            ("files", ("umowa.pdf", io.BytesIO(pdf1), "application/pdf")),
            ("files", ("potw.pdf", io.BytesIO(pdf2), "application/pdf")),
        ],
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "FILES_VALIDATION_ERROR"
    assert body["error"]["details"]["client_doc_id"] == "duplicate"
    assert "same_id" in body["error"]["details"]["duplicates"]

