"""Integration test: documents/analyze with PIPELINE_STUB=false (monkeypatched)."""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.agentic.case_workspace_store import Scenario2CaseMetadata


@dataclass
class FakeFullPipelineResult:
    session_id: str = "fake-session"
    run_id: str = "fake-run-001"
    run_status: str = "completed"
    documents: list = field(default_factory=list)
    critical_gaps_summary: list = field(default_factory=list)
    next_questions_to_user: list = field(
        default_factory=lambda: ["Czy masz dowod wplaty?"]
    )
    raw_json_text: str = ""
    parsed_json: dict[str, Any] | None = None
    validation_valid: bool = True
    validation_errors: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None


FIXTURE_PARSED = {
    "case_facts": {
        "parties": [],
        "property_address": {"value": None, "status": "missing", "sources": []},
        "lease_type": {"value": None, "status": "missing", "sources": []},
        "key_dates": [],
        "money": [],
        "notes": [],
    },
    "checklist": [
        {
            "item_id": "CONTRACT_EXISTS",
            "importance": "critical",
            "status": "confirmed",
            "what_it_supports": "Umowa",
            "findings": [
                {
                    "doc_id": "0000001",
                    "quote": "Umowa najmu lokalu",
                    "why_this_quote_matters": "potwierdza istnienie umowy",
                }
            ],
            "missing_what_exactly": "",
            "request_from_user": {"type": "provide_info", "ask": "", "examples": []},
            "confidence": "high",
        },
    ],
    "critical_gaps_summary": [],
    "next_questions_to_user": ["Czy masz dowod wplaty?"],
    "conflicts_and_red_flags": [],
    "ocr_quality_warnings": [],
}


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def _make_pdf(size: int = 200) -> bytes:
    return b"%PDF-1.4 " + b"x" * size


def _post_analyze(
    client: TestClient,
    case_id: str = "KJ-2026-TEST",
    *,
    intake_text: str | None = None,
) -> Any:
    """Helper: POST analyze with a single PDF."""
    pdf = _make_pdf()
    data = {"case_id": case_id, "files_category": ["lease"]}
    if intake_text is not None:
        data["intake_text"] = intake_text
    return client.post(
        "/api/v2/case/documents/analyze",
        data=data,
        files=[("files", ("umowa.pdf", io.BytesIO(pdf), "application/pdf"))],
    )


# Patches for lazy imports inside handle_documents_analyze_real.
# They are imported from their actual source modules.
_REAL_PIPELINE_PATCHES = {
    "settings": "app.config.settings.Settings",
    "orchestrator": "app.pipeline.orchestrator.OCRPipelineOrchestrator",
    "repo": "app.storage.repo.StorageRepo",
    "artifacts": "app.storage.artifacts.ArtifactsManager",
    "ocr_client": "app.ocr_client.mistral_ocr.MistralOCRClient",
    "ocr_options": "app.ocr_client.types.OCROptions",
}


def _make_settings_mock() -> MagicMock:
    """Create a settings mock with all required attributes."""
    mock = MagicMock()
    mock.default_prompt_name = "kaucja_gap_analysis"
    mock.default_prompt_version = "v001"
    mock.default_provider = "openai"
    mock.default_model = "gpt-5.1"
    mock.scenario2_runner_mode = "stub"
    mock.scenario2_verifier_policy = "informational"
    mock.scenario2_legal_corpus_backend = "local"
    mock.scenario2_legal_corpus_local_root = "artifacts/legal_collection"
    mock.db_path = "data/test.db"
    mock.storage_root = "data"
    mock.ocr_api_key = "test-key"
    return mock


def _run_with_orchestrator_result(
    client: TestClient,
    fake_result: FakeFullPipelineResult,
    case_id: str = "KJ-2026-TEST",
    intake_text: str | None = None,
    settings_overrides: dict[str, Any] | None = None,
) -> tuple[Any, MagicMock]:
    """Run analyze endpoint with a mocked orchestrator returning fake_result.

    Returns (response, mock_orchestrator).
    """
    mock_orch_instance = MagicMock()
    mock_orch_instance.run_full_pipeline.return_value = fake_result
    mock_settings = _make_settings_mock()
    if settings_overrides:
        for k, v in settings_overrides.items():
            setattr(mock_settings, k, v)

    with (
        patch("app.api.service.PIPELINE_STUB", False),
        patch(_REAL_PIPELINE_PATCHES["settings"], return_value=mock_settings),
        patch(
            _REAL_PIPELINE_PATCHES["orchestrator"],
            return_value=mock_orch_instance,
        ),
        patch(_REAL_PIPELINE_PATCHES["repo"]),
        patch(_REAL_PIPELINE_PATCHES["artifacts"]),
        patch(_REAL_PIPELINE_PATCHES["ocr_client"]),
        patch(_REAL_PIPELINE_PATCHES["ocr_options"]),
    ):
        resp = _post_analyze(client, case_id, intake_text=intake_text)

    return resp, mock_orch_instance


def test_real_pipeline_passes_case_metadata_to_orchestrator_when_known(
    client: TestClient,
) -> None:
    fake_result = FakeFullPipelineResult(parsed_json=FIXTURE_PARSED)
    intake_text = "Kaucja 1200 PLN, wyprowadzka 2026-01-15."
    resp, mock_orch = _run_with_orchestrator_result(
        client,
        fake_result,
        "KJ-2026-META",
        intake_text=intake_text,
    )

    assert resp.status_code == 200
    call_kwargs = mock_orch.run_full_pipeline.call_args
    assert call_kwargs is not None
    case_metadata = call_kwargs.kwargs["scenario2_case_metadata"]
    assert isinstance(case_metadata, Scenario2CaseMetadata)
    assert case_metadata.claim_amount == 1200.0
    assert case_metadata.currency == "PLN"
    assert case_metadata.move_out_date == "2026-01-15"
    assert case_metadata.lease_start is None
    assert case_metadata.lease_end is None
    assert case_metadata.deposit_return_due_date is None


# ---------------------------------------------------------------------------
# Stub vs Real routing
# ---------------------------------------------------------------------------


def test_pipeline_stub_false_uses_real_path(client: TestClient) -> None:
    """When PIPELINE_STUB=false, the real pipeline path is invoked."""
    fake_result = FakeFullPipelineResult(parsed_json=FIXTURE_PARSED)
    resp, mock_orch = _run_with_orchestrator_result(client, fake_result, "KJ-2026-REAL")
    assert resp.status_code == 200
    mock_orch.run_full_pipeline.assert_called_once()
    data = resp.json()
    assert data["analysis_run_id"] == "fake-run-001"


def test_pipeline_stub_true_uses_stub_path(client: TestClient) -> None:
    """When PIPELINE_STUB=true (default), the stub path is used."""
    with patch("app.api.service.PIPELINE_STUB", True):
        resp = _post_analyze(client, "KJ-2026-STUB-CHK")
    assert resp.status_code == 200
    data = resp.json()
    assert data["analysis_run_id"].startswith("stub-")


def test_pipeline_failure_returns_500(client: TestClient) -> None:
    """When real pipeline raises, router returns 500 in unified format."""
    with (
        patch("app.api.service.PIPELINE_STUB", False),
        patch(
            "app.api.service.handle_documents_analyze_real",
            side_effect=RuntimeError("OCR unavailable"),
        ),
    ):
        resp = _post_analyze(client, "KJ-2026-FAIL")
    assert resp.status_code == 500
    body = resp.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "request_id" in body["error"]


def test_mapped_response_has_analysis_run_id(client: TestClient) -> None:
    """The mapped response must include analysis_run_id."""
    resp = _post_analyze(client, "KJ-2026-RUN")
    assert resp.status_code == 200
    data = resp.json()
    assert "analysis_run_id" in data
    assert data["analysis_run_id"] is not None


# ---------------------------------------------------------------------------
# Prompt name from Settings — verify actual orchestrator call
# ---------------------------------------------------------------------------


def test_real_pipeline_passes_settings_prompt_to_orchestrator(
    client: TestClient,
) -> None:
    """Verify prompt_name/prompt_version from Settings reach orchestrator."""
    fake_result = FakeFullPipelineResult(parsed_json=FIXTURE_PARSED)
    resp, mock_orch = _run_with_orchestrator_result(
        client,
        fake_result,
        "KJ-2026-SETTINGS",
        settings_overrides={
            "default_prompt_name": "custom_prompt_test",
            "default_prompt_version": "v042",
        },
    )

    assert resp.status_code == 200
    call_kwargs = mock_orch.run_full_pipeline.call_args
    assert call_kwargs is not None
    assert call_kwargs.kwargs["prompt_name"] == "custom_prompt_test"
    assert call_kwargs.kwargs["prompt_version"] == "v042"


def test_real_pipeline_passes_scenario2_runner_mode_to_orchestrator(
    client: TestClient,
) -> None:
    fake_result = FakeFullPipelineResult(parsed_json=FIXTURE_PARSED)
    mock_orch_instance = MagicMock()
    mock_orch_instance.run_full_pipeline.return_value = fake_result
    mock_settings = _make_settings_mock()
    mock_settings.scenario2_runner_mode = "openai_tool_loop"
    mock_settings.scenario2_verifier_policy = "strict"
    runtime_runner = object()
    runtime_tool = object()
    runtime_case_workspace_store = object()
    runtime = type(
        "Runtime",
        (),
        {
            "runner": runtime_runner,
            "legal_corpus_tool": runtime_tool,
            "case_workspace_store": runtime_case_workspace_store,
            "bootstrap_error": "local corpus missing",
        },
    )()

    with (
        patch("app.api.service.PIPELINE_STUB", False),
        patch(_REAL_PIPELINE_PATCHES["settings"], return_value=mock_settings),
        patch(
            _REAL_PIPELINE_PATCHES["orchestrator"],
            return_value=mock_orch_instance,
        ) as orchestrator_ctor,
        patch(_REAL_PIPELINE_PATCHES["repo"]),
        patch(_REAL_PIPELINE_PATCHES["artifacts"]),
        patch(_REAL_PIPELINE_PATCHES["ocr_client"]),
        patch(_REAL_PIPELINE_PATCHES["ocr_options"]),
        patch("app.llm_client.openai_client.OpenAILLMClient"),
        patch("app.llm_client.gemini_client.GeminiLLMClient"),
        patch(
            "app.agentic.scenario2_runtime_factory.build_scenario2_runtime",
            return_value=runtime,
        ),
    ):
        resp = _post_analyze(client, "KJ-2026-RUNNER-MODE")

    assert resp.status_code == 200
    assert orchestrator_ctor.call_args is not None
    assert (
        orchestrator_ctor.call_args.kwargs["scenario2_runner_mode"]
        == "openai_tool_loop"
    )
    assert orchestrator_ctor.call_args.kwargs["scenario2_verifier_policy"] == "strict"
    assert orchestrator_ctor.call_args.kwargs["scenario2_runner"] is runtime_runner
    assert orchestrator_ctor.call_args.kwargs["legal_corpus_tool"] is runtime_tool
    assert (
        orchestrator_ctor.call_args.kwargs["scenario2_case_workspace_store"]
        is runtime_case_workspace_store
    )
    assert (
        orchestrator_ctor.call_args.kwargs["scenario2_bootstrap_error"]
        == "local corpus missing"
    )


# ---------------------------------------------------------------------------
# Specific pipeline error codes (lowercase & UPPER_SNAKE)
# ---------------------------------------------------------------------------


def _test_error_code_mapping(
    client: TestClient,
    pipeline_error_code: str,
    expected_http_status: int,
    expected_api_code: str,
) -> None:
    """Helper: run pipeline with given error_code and assert API response."""
    fake_result = FakeFullPipelineResult(
        error_code=pipeline_error_code,
        error_message=f"Test error: {pipeline_error_code}",
    )
    resp, _ = _run_with_orchestrator_result(client, fake_result)

    assert resp.status_code == expected_http_status, (
        f"Expected {expected_http_status} for error_code={pipeline_error_code!r}, "
        f"got {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body["error"]["code"] == expected_api_code
    assert "request_id" in body["error"]


# -- OCR codes --


def test_ocr_failed_lowercase(client: TestClient) -> None:
    _test_error_code_mapping(client, "ocr_failed", 502, "OCR_FAILED")


def test_ocr_all_failed_lowercase(client: TestClient) -> None:
    _test_error_code_mapping(client, "ocr_all_failed", 502, "OCR_FAILED")


def test_ocr_timeout_lowercase(client: TestClient) -> None:
    _test_error_code_mapping(client, "ocr_timeout", 502, "OCR_FAILED")


def test_OCR_API_ERROR_upper(client: TestClient) -> None:
    _test_error_code_mapping(client, "OCR_API_ERROR", 502, "OCR_FAILED")


def test_OCR_FAILED_upper(client: TestClient) -> None:
    _test_error_code_mapping(client, "OCR_FAILED", 502, "OCR_FAILED")


# -- LLM codes --


def test_llm_failed_lowercase(client: TestClient) -> None:
    _test_error_code_mapping(client, "llm_failed", 502, "LLM_FAILED")


def test_llm_refused_lowercase(client: TestClient) -> None:
    _test_error_code_mapping(client, "llm_refused", 502, "LLM_FAILED")


def test_context_too_large_lowercase(client: TestClient) -> None:
    _test_error_code_mapping(client, "context_too_large", 502, "LLM_FAILED")


def test_LLM_API_ERROR_upper(client: TestClient) -> None:
    _test_error_code_mapping(client, "LLM_API_ERROR", 502, "LLM_FAILED")


def test_LLM_INVALID_JSON_upper(client: TestClient) -> None:
    _test_error_code_mapping(client, "LLM_INVALID_JSON", 502, "LLM_FAILED")


def test_CONTEXT_TOO_LARGE_upper(client: TestClient) -> None:
    _test_error_code_mapping(client, "CONTEXT_TOO_LARGE", 502, "LLM_FAILED")


# -- Validation codes --


def test_validation_failed_lowercase(client: TestClient) -> None:
    _test_error_code_mapping(
        client, "validation_failed", 422, "PIPELINE_VALIDATION_FAILED"
    )


def test_json_parse_failed_lowercase(client: TestClient) -> None:
    _test_error_code_mapping(
        client, "json_parse_failed", 422, "PIPELINE_VALIDATION_FAILED"
    )


def test_PIPELINE_VALIDATION_FAILED_upper(client: TestClient) -> None:
    _test_error_code_mapping(
        client, "PIPELINE_VALIDATION_FAILED", 422, "PIPELINE_VALIDATION_FAILED"
    )


# -- Fail-closed: unknown error_code --


def test_unknown_error_code_returns_500(client: TestClient) -> None:
    """An unrecognized error_code must produce 500, not 200 with empty payload."""
    _test_error_code_mapping(client, "SOME_UNKNOWN_ERROR", 500, "INTERNAL_ERROR")


# -- Fail-closed: no parsed_json and no error_code --


def test_no_parsed_json_no_error_code_returns_500(client: TestClient) -> None:
    """If pipeline returns neither parsed_json nor error_code, return 500."""
    fake_result = FakeFullPipelineResult(parsed_json=None, error_code=None)
    resp, _ = _run_with_orchestrator_result(client, fake_result, "KJ-2026-EMPTY")
    assert resp.status_code == 500
    body = resp.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"


# -- ApiError passthrough from router --


def test_pipeline_ocr_failed_returns_502(client: TestClient) -> None:
    """OCR_FAILED from service raises through router as 502."""
    from app.api.errors import ApiError

    with (
        patch("app.api.service.PIPELINE_STUB", False),
        patch(
            "app.api.service.handle_documents_analyze_real",
            side_effect=ApiError(
                status_code=502,
                error_code="OCR_FAILED",
                detail="OCR service unavailable",
            ),
        ),
    ):
        resp = _post_analyze(client, "KJ-2026-OCR")
    assert resp.status_code == 502
    body = resp.json()
    assert body["error"]["code"] == "OCR_FAILED"
    assert "request_id" in body["error"]


def test_pipeline_llm_failed_returns_502(client: TestClient) -> None:
    """LLM_FAILED from service raises through router as 502."""
    from app.api.errors import ApiError

    with (
        patch("app.api.service.PIPELINE_STUB", False),
        patch(
            "app.api.service.handle_documents_analyze_real",
            side_effect=ApiError(
                status_code=502,
                error_code="LLM_FAILED",
                detail="LLM provider timeout",
            ),
        ),
    ):
        resp = _post_analyze(client, "KJ-2026-LLM")
    assert resp.status_code == 502
    body = resp.json()
    assert body["error"]["code"] == "LLM_FAILED"


def test_pipeline_validation_failed_returns_422(client: TestClient) -> None:
    """PIPELINE_VALIDATION_FAILED returns 422 with details."""
    from app.api.errors import ApiError

    with (
        patch("app.api.service.PIPELINE_STUB", False),
        patch(
            "app.api.service.handle_documents_analyze_real",
            side_effect=ApiError(
                status_code=422,
                error_code="PIPELINE_VALIDATION_FAILED",
                detail="Schema validation failed",
                details={"validation_errors": ["field X missing"]},
            ),
        ),
    ):
        resp = _post_analyze(client, "KJ-2026-VAL")
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "PIPELINE_VALIDATION_FAILED"
    assert "validation_errors" in body["error"]["details"]
