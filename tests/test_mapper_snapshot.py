"""Snapshot test: fixture parsed_json -> UI v2 contract via mapper."""

from __future__ import annotations

import pytest

from app.api.mapper import map_pipeline_to_ui
from app.api.models import DocumentAnalyzeResponse


@pytest.fixture()
def fixture_parsed_json() -> dict:
    """Minimal realistic parsed_json matching canonical schema."""
    return {
        "case_facts": {
            "parties": [
                {
                    "role": "tenant",
                    "fact": {
                        "value": "Jan Kowalski",
                        "status": "confirmed",
                        "sources": [],
                    },
                },
            ],
            "property_address": {
                "value": "ul. Testowa 1, Warszawa",
                "status": "confirmed",
                "sources": [],
            },
            "lease_type": {
                "value": "czas nieokreslony",
                "status": "confirmed",
                "sources": [],
            },
            "key_dates": [
                {
                    "name": "lease_start",
                    "fact": {
                        "value": "2024-01-01",
                        "status": "confirmed",
                        "sources": [],
                    },
                },
            ],
            "money": [
                {
                    "name": "kaucja",
                    "fact": {
                        "value": 3000,
                        "status": "confirmed",
                        "sources": [
                            {
                                "doc_id": "0000001",
                                "quote": "kaucja 3000 PLN",
                            }
                        ],
                    },
                },
            ],
            "notes": [],
        },
        "checklist": [
            {
                "item_id": "CONTRACT_EXISTS",
                "importance": "critical",
                "status": "confirmed",
                "what_it_supports": "Umowa istnieje",
                "findings": [
                    {
                        "doc_id": "0000001",
                        "quote": "Umowa najmu z dnia 01.01.2024",
                        "why_this_quote_matters": "potwierdzenie",
                    }
                ],
                "missing_what_exactly": "",
                "request_from_user": {
                    "type": "provide_info",
                    "ask": "",
                    "examples": [],
                },
                "confidence": "high",
            },
            {
                "item_id": "KAUCJA_AMOUNT_STATED",
                "importance": "critical",
                "status": "confirmed",
                "what_it_supports": "Kwota kaucji",
                "findings": [
                    {
                        "doc_id": "0000001",
                        "quote": "kaucja w wysokosci 3000 PLN",
                        "why_this_quote_matters": "kwota",
                    }
                ],
                "missing_what_exactly": "",
                "request_from_user": {
                    "type": "provide_info",
                    "ask": "",
                    "examples": [],
                },
                "confidence": "high",
            },
            {
                "item_id": "KAUCJA_PAYMENT_PROOF",
                "importance": "critical",
                "status": "missing",
                "what_it_supports": "Dowod wplaty",
                "findings": [],
                "missing_what_exactly": "brak potwierdzenia przelewu",
                "request_from_user": {
                    "type": "upload_document",
                    "ask": "Prosze dodac potwierdzenie przelewu kaucji.",
                    "examples": ["wyciag z konta"],
                },
                "confidence": "low",
            },
            {
                "item_id": "MOVE_OUT_PROTOCOL",
                "importance": "recommended",
                "status": "missing",
                "what_it_supports": "Protokol zdawczo-odbiorczy",
                "findings": [],
                "missing_what_exactly": "brak protokolu",
                "request_from_user": {
                    "type": "upload_document",
                    "ask": "Czy masz protokol zdawczo-odbiorczy?",
                    "examples": ["skan protokolu"],
                },
                "confidence": "low",
            },
        ],
        "critical_gaps_summary": [
            "Brak potwierdzenia wplaty kaucji",
            "Brak protokolu zdawczo-odbiorczego",
        ],
        "next_questions_to_user": [
            "Czy masz potwierdzenie przelewu kaucji?",
            "Czy podpisano protokol zdawczo-odbiorczy?",
        ],
        "conflicts_and_red_flags": [],
        "ocr_quality_warnings": [],
    }


@pytest.fixture()
def fixture_docs_info() -> list[dict]:
    # Use doc_id "0000001" to match the findings in parsed_json
    return [
        {
            "doc_id": "0000001",
            "category_id": "lease",
            "name": "umowa.pdf",
            "size_mb": 0.5,
            "analyzed_at": "2026-03-03T06:00:00+00:00",
        },
    ]


def test_mapper_returns_valid_response(
    fixture_parsed_json: dict, fixture_docs_info: list[dict]
) -> None:
    result = map_pipeline_to_ui(
        fixture_parsed_json,
        case_id="KJ-2026-SNAP",
        run_id="run-test-001",
        documents_info=fixture_docs_info,
    )
    parsed = DocumentAnalyzeResponse(**result)
    assert parsed.case_id == "KJ-2026-SNAP"
    assert parsed.analysis_run_id == "run-test-001"


def test_mapper_summary_fields_present(
    fixture_parsed_json: dict, fixture_docs_info: list[dict]
) -> None:
    result = map_pipeline_to_ui(
        fixture_parsed_json,
        case_id="KJ-2026-SNAP",
        run_id="run-test-001",
        documents_info=fixture_docs_info,
    )
    field_ids = {f.id for f in result["summary_fields"]}
    expected = {
        "lease_agreement",
        "deposit_amount",
        "deposit_payment_method",
        "handover_protocol",
        "move_out_date",
        "withholding_reason",
    }
    assert field_ids == expected


def test_confirmed_items_produce_ok_status(
    fixture_parsed_json: dict, fixture_docs_info: list[dict]
) -> None:
    result = map_pipeline_to_ui(
        fixture_parsed_json,
        case_id="KJ-2026-SNAP",
        run_id="run-test-001",
        documents_info=fixture_docs_info,
    )
    fields_by_id = {f.id: f for f in result["summary_fields"]}
    assert fields_by_id["lease_agreement"].status == "ok"
    assert fields_by_id["deposit_amount"].status == "ok"


def test_missing_items_produce_muted_status(
    fixture_parsed_json: dict, fixture_docs_info: list[dict]
) -> None:
    result = map_pipeline_to_ui(
        fixture_parsed_json,
        case_id="KJ-2026-SNAP",
        run_id="run-test-001",
        documents_info=fixture_docs_info,
    )
    fields_by_id = {f.id: f for f in result["summary_fields"]}
    assert fields_by_id["handover_protocol"].status == "muted"


def test_questions_from_pipeline(
    fixture_parsed_json: dict, fixture_docs_info: list[dict]
) -> None:
    result = map_pipeline_to_ui(
        fixture_parsed_json,
        case_id="KJ-2026-SNAP",
        run_id="run-test-001",
        documents_info=fixture_docs_info,
    )
    assert "questions" in result
    q_texts = [q.text for q in result["questions"]]
    assert any("potwierdzenie" in t.lower() for t in q_texts)


def test_missing_docs_from_pipeline(
    fixture_parsed_json: dict, fixture_docs_info: list[dict]
) -> None:
    result = map_pipeline_to_ui(
        fixture_parsed_json,
        case_id="KJ-2026-SNAP",
        run_id="run-test-001",
        documents_info=fixture_docs_info,
    )
    missing_types = {d.doc_type for d in result["missing_docs"]}
    assert "deposit_payment" in missing_types
    assert "handover_protocol" in missing_types


def test_analyzed_documents_list(
    fixture_parsed_json: dict, fixture_docs_info: list[dict]
) -> None:
    result = map_pipeline_to_ui(
        fixture_parsed_json,
        case_id="KJ-2026-SNAP",
        run_id="run-test-001",
        documents_info=fixture_docs_info,
    )
    assert len(result["analyzed_documents"]) == 1
    doc = result["analyzed_documents"][0]
    assert doc.id == "0000001"
    assert doc.categoryId == "lease"

    # Doc 0000001 should have extracted lease_agreement from CONTRACT_EXISTS
    # and deposit_amount from KAUCJA_AMOUNT_STATED findings
    assert "lease_agreement" in doc.extracted_fields
    assert "deposit_amount" in doc.extracted_fields


def test_warnings_passed_through(
    fixture_parsed_json: dict, fixture_docs_info: list[dict]
) -> None:
    result = map_pipeline_to_ui(
        fixture_parsed_json,
        case_id="KJ-2026-SNAP",
        run_id="run-test-001",
        documents_info=fixture_docs_info,
        warnings=["OCR quality low"],
    )
    assert result["warnings"] == ["OCR quality low"]
