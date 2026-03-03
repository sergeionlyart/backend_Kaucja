"""Tests for intake endpoint contract - TechSpec aligned.

Key changes from iter-32:
  - ``questions`` instead of ``open_questions``
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.api.models import IntakeResponse


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# Response shape validation
# ---------------------------------------------------------------------------


def test_response_shape_matches_pydantic_model(
    client: TestClient,
) -> None:
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Opis sytuacji z najmu mieszkania"},
    )
    assert resp.status_code == 200
    data = resp.json()
    parsed = IntakeResponse(**data)
    assert parsed.case_id
    assert parsed.case_status == "parsed"
    assert isinstance(parsed.summary_fields, list)
    assert isinstance(parsed.fields_meta, dict)
    assert isinstance(parsed.questions, list)
    assert isinstance(parsed.missing_docs, list)


def test_case_status_is_parsed(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Mam problem z kaucja"},
    )
    data = resp.json()
    assert data["case_status"] == "parsed"


def test_summary_fields_have_all_required_ids(
    client: TestClient,
) -> None:
    expected_ids = {
        "lease_agreement",
        "deposit_amount",
        "deposit_payment_method",
        "handover_protocol",
        "move_out_date",
        "withholding_reason",
    }
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Jakis opis sytuacji"},
    )
    data = resp.json()
    actual_ids = {f["id"] for f in data["summary_fields"]}
    assert actual_ids == expected_ids


def test_fields_meta_keys_match_summary_ids(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Jakis opis sytuacji"},
    )
    data = resp.json()
    summary_ids = {f["id"] for f in data["summary_fields"]}
    meta_keys = set(data["fields_meta"].keys())
    assert meta_keys == summary_ids


# ---------------------------------------------------------------------------
# Intake parsing - deposit amount detection
# ---------------------------------------------------------------------------


def test_deposit_amount_detected_from_pln(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Wplacilem kaucje 3000 PLN za mieszkanie"},
    )
    data = resp.json()
    deposit_field = next(
        f for f in data["summary_fields"] if f["id"] == "deposit_amount"
    )
    assert deposit_field["value"] == "3000 PLN"
    assert deposit_field["status"] == "ok"


def test_deposit_amount_detected_from_zl(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Kaucja wyniosla 2500 zl"},
    )
    data = resp.json()
    deposit_field = next(
        f for f in data["summary_fields"] if f["id"] == "deposit_amount"
    )
    assert deposit_field["value"] == "2500 PLN"
    assert deposit_field["status"] == "ok"


# ---------------------------------------------------------------------------
# Intake parsing - lease agreement detection
# ---------------------------------------------------------------------------


def test_lease_mentioned(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Mam umowe najmu na czas nieokreslony"},
    )
    data = resp.json()
    lease_field = next(
        f for f in data["summary_fields"] if f["id"] == "lease_agreement"
    )
    assert lease_field["status"] == "ok"
    assert lease_field["value"] != ""


# ---------------------------------------------------------------------------
# Intake parsing - empty input gives all muted
# ---------------------------------------------------------------------------


def test_no_data_all_muted(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Nie wiem co napisac"},
    )
    data = resp.json()
    for field in data["summary_fields"]:
        assert field["status"] == "muted", f"Field {field['id']} should be muted"
        assert field["value"] == ""


# ---------------------------------------------------------------------------
# Missing docs and questions (TechSpec key: questions)
# ---------------------------------------------------------------------------


def test_missing_docs_returned_when_no_docs(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Potrzebuje pomocy z odzyskaniem kaucji"},
    )
    data = resp.json()
    assert len(data["missing_docs"]) >= 3
    doc_types = {d["doc_type"] for d in data["missing_docs"]}
    assert "lease" in doc_types
    assert "deposit_payment" in doc_types


def test_questions_are_present(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Potrzebuje pomocy"},
    )
    data = resp.json()
    assert "questions" in data
    assert "open_questions" not in data  # old key must be gone
    assert len(data["questions"]) >= 1
    for q in data["questions"]:
        assert q["status"] == "open"
        assert q["priority"] in ("high", "medium", "low")


# ---------------------------------------------------------------------------
# Case ID generation
# ---------------------------------------------------------------------------


def test_case_id_generated_if_not_provided(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Test sytuacji"},
    )
    data = resp.json()
    assert data["case_id"].startswith("KJ-")


def test_case_id_preserved_if_provided(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/case/intake",
        json={"intake_text": "Test sytuacji", "case_id": "MY-CASE-1"},
    )
    data = resp.json()
    assert data["case_id"] == "MY-CASE-1"
