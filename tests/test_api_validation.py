"""Tests for API endpoint validation (422/415/413 error bodies).

TechSpec contract:
  - ALL errors in unified format: code, message, request_id, details?
  - Framework 422s (RequestValidationError) also in unified format
  - error.code in UPPER_SNAKE_CASE
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health_returns_ok(client: TestClient) -> None:
    resp = client.get("/api/v2/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Intake validation
# ---------------------------------------------------------------------------


def test_intake_empty_body_returns_422(client: TestClient) -> None:
    resp = client.post("/api/v2/case/intake", json={})
    assert resp.status_code == 422


def test_intake_missing_intake_text_returns_422(client: TestClient) -> None:
    resp = client.post("/api/v2/case/intake", json={"case_id": "X"})
    assert resp.status_code == 422


def test_intake_blank_text_returns_422(client: TestClient) -> None:
    resp = client.post("/api/v2/case/intake", json={"intake_text": ""})
    assert resp.status_code == 422


def test_intake_valid_returns_200(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Mam problem z kaucja 3000 PLN"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "case_id" in data
    assert "case_status" in data
    assert data["case_status"] == "parsed"
    assert "summary_fields" in data
    assert "fields_meta" in data
    assert "questions" in data
    assert "open_questions" not in data
    assert "missing_docs" in data


# ---------------------------------------------------------------------------
# Framework 422 in unified error format
# ---------------------------------------------------------------------------


def test_framework_validation_returns_unified_format(
    client: TestClient,
) -> None:
    """FastAPI's own RequestValidationError must also use unified format."""
    resp = client.post("/api/v2/case/intake", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert "error" in body
    err = body["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert "message" in err
    assert "request_id" in err
    assert isinstance(err["request_id"], str)
    assert len(err["request_id"]) > 0


def test_framework_validation_has_details(client: TestClient) -> None:
    """Framework validation details should contain field info."""
    resp = client.post("/api/v2/case/intake", json={})
    body = resp.json()
    err = body["error"]
    assert "details" in err
    assert isinstance(err["details"], dict)


# ---------------------------------------------------------------------------
# Documents / analyze validation
# ---------------------------------------------------------------------------


def _make_pdf_bytes(size: int = 100) -> bytes:
    return b"%PDF-1.4 " + b"x" * size


def test_analyze_no_files_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-TEST",
            "files_category": ["lease"],
        },
    )
    assert resp.status_code == 422


def test_analyze_category_count_mismatch_returns_422(
    client: TestClient,
) -> None:
    pdf = _make_pdf_bytes()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-TEST",
            "files_category": ["lease", "deposit_payment"],
        },
        files=[("files", ("test.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "FILES_VALIDATION_ERROR"
    assert "request_id" in body["error"]


def test_analyze_invalid_category_returns_422(
    client: TestClient,
) -> None:
    pdf = _make_pdf_bytes()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-TEST",
            "files_category": ["dragons"],
        },
        files=[("files", ("test.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in body["error"]


def test_analyze_other_category_rejected(client: TestClient) -> None:
    """TechSpec: 'other' is NOT a valid category."""
    pdf = _make_pdf_bytes()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-TEST",
            "files_category": ["other"],
        },
        files=[("files", ("test.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_analyze_wrong_mime_returns_415(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-TEST",
            "files_category": ["lease"],
        },
        files=[("files", ("test.txt", io.BytesIO(b"hello"), "text/plain"))],
    )
    assert resp.status_code == 415
    body = resp.json()
    assert body["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert "request_id" in body["error"]


def test_analyze_valid_returns_200(client: TestClient) -> None:
    pdf = _make_pdf_bytes()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-STUB",
            "files_category": ["lease"],
        },
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == "KJ-2026-STUB"
    assert "analyzed_documents" in data
    assert "documents_by_id" not in data
    assert "questions" in data
    assert "open_questions" not in data
    assert "analysis_run_id" in data


def test_analyze_error_body_has_details_and_request_id(
    client: TestClient,
) -> None:
    pdf = _make_pdf_bytes()
    resp = client.post(
        "/api/v2/case/documents/analyze",
        data={
            "case_id": "KJ-2026-TEST",
            "files_category": ["lease", "lease"],
        },
        files=[("files", ("a.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert resp.status_code == 422
    body = resp.json()
    err = body["error"]
    assert "request_id" in err
    assert isinstance(err["request_id"], str)
    assert len(err["request_id"]) > 0
    assert "details" in err


# ---------------------------------------------------------------------------
# Submit validation
# ---------------------------------------------------------------------------

_VALID_SUBMIT = {
    "case_id": "KJ-2026-SUBMIT",
    "email": "test@example.com",
    "consents": {"terms": True, "privacy": True, "marketing": False},
}


def test_submit_missing_case_id_returns_422(client: TestClient) -> None:
    resp = client.post("/api/v2/case/submit", json={})
    assert resp.status_code == 422


def test_submit_blank_case_id_returns_422(client: TestClient) -> None:
    resp = client.post("/api/v2/case/submit", json={"case_id": ""})
    assert resp.status_code == 422


def test_submit_valid_returns_200_with_case_status(
    client: TestClient,
) -> None:
    resp = client.post("/api/v2/case/submit", json=_VALID_SUBMIT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == "KJ-2026-SUBMIT"
    assert data["case_status"] == "report_sent"
    assert "status" not in data
    assert "submitted_at" in data


def test_submit_missing_email_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/submit",
        json={"case_id": "KJ-2026-X", "consents": {"terms": True, "privacy": True}},
    )
    assert resp.status_code == 422


def test_submit_invalid_email_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/submit",
        json={
            "case_id": "KJ-2026-X",
            "email": "bad",
            "consents": {"terms": True, "privacy": True},
        },
    )
    assert resp.status_code == 422


def test_submit_missing_consents_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/submit",
        json={"case_id": "KJ-2026-X", "email": "user@example.com"},
    )
    assert resp.status_code == 422


def test_submit_terms_not_accepted_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/submit",
        json={
            "case_id": "KJ-2026-X",
            "email": "user@example.com",
            "consents": {"terms": False, "privacy": True},
        },
    )
    assert resp.status_code == 422
    assert "consents" in str(resp.json())


def test_submit_privacy_not_accepted_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/submit",
        json={
            "case_id": "KJ-2026-X",
            "email": "user@example.com",
            "consents": {"terms": True, "privacy": False},
        },
    )
    assert resp.status_code == 422
    assert "consents" in str(resp.json())


# ---------------------------------------------------------------------------
# HTTP status code → error code mapping (Task 4A)
# ---------------------------------------------------------------------------


def test_http_404_maps_to_not_found(client: TestClient) -> None:
    """A 404 from Starlette must produce code=NOT_FOUND, not INTERNAL_ERROR."""
    resp = client.get("/api/v2/nonexistent-route")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert "request_id" in body["error"]


def test_http_405_maps_to_method_not_allowed(client: TestClient) -> None:
    resp = client.delete("/api/v2/health")
    assert resp.status_code == 405
    body = resp.json()
    assert body["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert "request_id" in body["error"]

