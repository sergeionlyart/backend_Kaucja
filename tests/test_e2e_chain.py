"""End-to-end API chain test: analyze → reanalyze → submit.

Tests the full Slice A critical path through the API with stub pipeline,
verifying contract keys and dedup compatibility at each step.
"""
from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.api import service



CASE_ID = "KJ-2026-E2E-CHAIN"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture()
def _clean_case(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "_CASES_DIR", tmp_path)
    yield tmp_path


def _pdf(label: str) -> bytes:
    return f"%PDF-1.4 e2e-{label}-{id(label)}".encode()


class TestE2EChain:
    """Full chain: analyze → selective reanalyze → submit."""

    def test_full_chain(self, _clean_case, client):
        # ── Step 1: Analyze two documents ────────────────────────────
        pdf_lease = _pdf("lease")
        pdf_deposit = _pdf("deposit")

        resp_analyze = client.post(
            "/api/v2/case/documents/analyze",
            data={
                "case_id": CASE_ID,
                "files_category": ["lease", "deposit_payment"],
                "client_doc_id": ["c_lease_01", "c_deposit_01"],
            },
            files=[
                ("files", ("umowa.pdf", io.BytesIO(pdf_lease), "application/pdf")),
                ("files", ("wp.pdf", io.BytesIO(pdf_deposit), "application/pdf")),
            ],
        )
        assert resp_analyze.status_code == 200
        data1 = resp_analyze.json()

        # Contract keys present
        assert "analyzed_documents" in data1
        assert "summary_fields" in data1
        assert "questions" in data1
        assert "missing_docs" in data1
        assert "analysis_run_id" in data1
        assert isinstance(data1["analysis_run_id"], str)
        assert len(data1["analysis_run_id"]) > 0
        assert "case_id" in data1

        # Warnings field: always present, always list[str]
        assert "warnings" in data1, \
            f"'warnings' key must be present, got keys: {list(data1.keys())}"
        w1 = data1["warnings"]
        assert isinstance(w1, list), f"warnings must be list, got {type(w1)}"
        for w in w1:
            assert isinstance(w, str), f"each warning must be str, got {type(w)}"

        docs = data1["analyzed_documents"]
        assert len(docs) == 2

        # Each doc has required fields
        for doc in docs:
            assert "id" in doc
            assert "categoryId" in doc
            assert "status" in doc
            assert doc["status"] == "done"

        doc_id_lease = docs[0]["id"]

        # ── Step 2: Selective reanalyze (by server doc_id) ──────────
        resp_reanalyze = client.post(
            "/api/v2/case/documents/reanalyze",
            json={"case_id": CASE_ID, "document_ids": [doc_id_lease]},
        )
        assert resp_reanalyze.status_code == 200
        data2 = resp_reanalyze.json()

        # Contract keys
        assert "analyzed_documents" in data2
        assert "analysis_run_id" in data2
        assert isinstance(data2["analysis_run_id"], str)
        assert len(data2["analysis_run_id"]) > 0

        # Warnings on reanalyze: always list[str], same contract as analyze
        assert "warnings" in data2, \
            f"'warnings' key must be present in reanalyze response, got keys: {list(data2.keys())}"
        w2 = data2["warnings"]
        assert isinstance(w2, list), f"reanalyze warnings must be list, got {type(w2)}"
        for w in w2:
            assert isinstance(w, str), f"each warning must be str, got {type(w)}"

        reanalyzed = data2["analyzed_documents"]
        reanalyzed_ids = {d["id"] for d in reanalyzed}
        assert doc_id_lease in reanalyzed_ids

        # ── Step 3: Dedup consistency after reanalyze ───────────────
        catalog = service._load_documents_catalog(CASE_ID)
        assert len(catalog) >= 2
        for entry in catalog:
            assert entry.get("sha256"), f"Empty sha256: {entry}"
            assert Path(entry["saved_path"]).is_file(), f"Phantom: {entry['saved_path']}"

        # ── Step 4: Submit ──────────────────────────────────────────
        resp_submit = client.post(
            "/api/v2/case/submit",
            json={
                "case_id": CASE_ID,
                "locale": "pl",
                "email": "test@example.com",
                "consents": {"terms": True, "privacy": True},
            },
        )
        assert resp_submit.status_code == 200
        data3 = resp_submit.json()

        # Submit contract keys — strict assertions
        assert "case_id" in data3
        assert data3["case_id"] == CASE_ID
        assert "case_status" in data3
        assert isinstance(data3["case_status"], str)
        assert len(data3["case_status"]) > 0
        assert "submitted_at" in data3
        assert isinstance(data3["submitted_at"], str)
        assert len(data3["submitted_at"]) > 0

    def test_dedup_then_reanalyze_chain(self, _clean_case, client):
        """Dedup scenario: same file twice, then reanalyze still works."""
        pdf = _pdf("same-content")

        # Analyze first
        resp1 = client.post(
            "/api/v2/case/documents/analyze",
            data={"case_id": CASE_ID, "files_category": ["lease"]},
            files=[("files", ("a.pdf", io.BytesIO(pdf), "application/pdf"))],
        )
        assert resp1.status_code == 200
        doc_id = resp1.json()["analyzed_documents"][0]["id"]

        # Same content again (dedup hit)
        resp2 = client.post(
            "/api/v2/case/documents/analyze",
            data={"case_id": CASE_ID, "files_category": ["lease"]},
            files=[("files", ("b.pdf", io.BytesIO(pdf), "application/pdf"))],
        )
        assert resp2.status_code == 200
        doc_id_2 = resp2.json()["analyzed_documents"][0]["id"]
        assert doc_id_2 == doc_id  # stable identity

        # Reanalyze after dedup
        resp3 = client.post(
            "/api/v2/case/documents/reanalyze",
            json={"case_id": CASE_ID, "reuse_existing": True},
        )
        assert resp3.status_code == 200
        assert len(resp3.json()["analyzed_documents"]) >= 1


class TestE2ENegative:
    """Negative e2e — unified error envelope verification."""

    def _assert_error_envelope(self, body: dict, expected_code: str) -> None:
        """Assert the unified error envelope shape."""
        assert "error" in body, f"Missing 'error' key in: {body}"
        err = body["error"]
        assert err["code"] == expected_code
        assert isinstance(err["message"], str) and len(err["message"]) > 0, \
            f"error.message must be non-empty str, got: {err.get('message')!r}"
        assert isinstance(err.get("request_id"), str) and len(err["request_id"]) > 0, \
            f"error.request_id must be non-empty str, got: {err.get('request_id')!r}"
        if "details" in err:
            assert isinstance(err["details"], dict), \
                f"error.details must be dict, got: {type(err['details'])}"

    def test_analyze_missing_case_id(self, _clean_case, client):
        """Missing case_id → 422 with full error envelope."""
        pdf = _pdf("neg")
        resp = client.post(
            "/api/v2/case/documents/analyze",
            data={"files_category": ["lease"]},
            files=[("files", ("neg.pdf", io.BytesIO(pdf), "application/pdf"))],
        )
        assert resp.status_code == 422
        self._assert_error_envelope(resp.json(), "VALIDATION_ERROR")

    def test_submit_missing_email(self, _clean_case, client):
        """Submit without email → 422 with full error envelope."""
        resp = client.post(
            "/api/v2/case/submit",
            json={
                "case_id": CASE_ID,
                "consents": {"terms": True, "privacy": True},
            },
        )
        assert resp.status_code == 422
        self._assert_error_envelope(resp.json(), "VALIDATION_ERROR")

    def test_reanalyze_nonexistent_case(self, _clean_case, client):
        """Reanalyze unknown case_id → exactly 404 CASE_NOT_FOUND."""
        resp = client.post(
            "/api/v2/case/documents/reanalyze",
            json={"case_id": "KJ-NONEXISTENT", "reuse_existing": True},
        )
        assert resp.status_code == 404
        self._assert_error_envelope(resp.json(), "CASE_NOT_FOUND")
