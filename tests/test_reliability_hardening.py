from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.llm_client.base import LLMResult
from app.ocr_client.types import OCROptions, OCRResult
from app.pipeline.orchestrator import OCRPipelineOrchestrator
from app.storage.artifacts import ArtifactsManager
from app.storage.repo import StorageRepo


class HttpStatusError(RuntimeError):
    def __init__(self, status_code: int, message: str = "http error") -> None:
        super().__init__(message)
        self.status_code = status_code


class OCRFailOnceClient:
    def __init__(self) -> None:
        self.attempts = 0

    def process_document(
        self,
        *,
        input_path: Path,
        doc_id: str,
        options: OCROptions,
        output_dir: Path,
    ) -> OCRResult:
        del input_path, options
        self.attempts += 1
        if self.attempts == 1:
            raise HttpStatusError(429, "rate limit")

        output_dir.mkdir(parents=True, exist_ok=True)
        combined = output_dir / "combined.md"
        raw = output_dir / "raw_response.json"
        quality = output_dir / "quality.json"
        combined.write_text("markdown", encoding="utf-8")
        raw.write_text('{"pages":[]}', encoding="utf-8")
        quality.write_text('{"warnings":[],"bad_pages":[]}', encoding="utf-8")

        return OCRResult(
            doc_id=doc_id,
            ocr_model="mistral-ocr-latest",
            pages_count=1,
            combined_markdown_path=str(combined.resolve()),
            raw_response_path=str(raw.resolve()),
            tables_dir=str((output_dir / "tables").resolve()),
            images_dir=str((output_dir / "images").resolve()),
            page_renders_dir=str((output_dir / "page_renders").resolve()),
            quality_path=str(quality.resolve()),
            quality_warnings=[],
        )


class OCRSimpleClient:
    def __init__(self, content: str = "markdown") -> None:
        self.content = content

    def process_document(
        self,
        *,
        input_path: Path,
        doc_id: str,
        options: OCROptions,
        output_dir: Path,
    ) -> OCRResult:
        del input_path, options
        output_dir.mkdir(parents=True, exist_ok=True)
        combined = output_dir / "combined.md"
        raw = output_dir / "raw_response.json"
        quality = output_dir / "quality.json"
        combined.write_text(self.content, encoding="utf-8")
        raw.write_text('{"pages":[]}', encoding="utf-8")
        quality.write_text('{"warnings":[],"bad_pages":[]}', encoding="utf-8")
        return OCRResult(
            doc_id=doc_id,
            ocr_model="mistral-ocr-latest",
            pages_count=1,
            combined_markdown_path=str(combined.resolve()),
            raw_response_path=str(raw.resolve()),
            tables_dir=str((output_dir / "tables").resolve()),
            images_dir=str((output_dir / "images").resolve()),
            page_renders_dir=str((output_dir / "page_renders").resolve()),
            quality_path=str(quality.resolve()),
            quality_warnings=[],
        )


class LLMRetryOnceClient:
    def __init__(self, parsed_json: dict[str, Any]) -> None:
        self.parsed_json = parsed_json
        self.attempts = 0

    def generate_json(self, **kwargs: Any) -> LLMResult:
        del kwargs
        self.attempts += 1
        if self.attempts == 1:
            raise HttpStatusError(503, "temporary outage")
        return _llm_result(self.parsed_json)


class LLMInvalidJsonClient:
    def __init__(self) -> None:
        self.attempts = 0

    def generate_json(self, **kwargs: Any) -> LLMResult:
        del kwargs
        self.attempts += 1
        raise json.JSONDecodeError("invalid", "not-json", 0)


class LLMSchemaInvalidClient:
    def __init__(self, parsed_json: dict[str, Any]) -> None:
        self.parsed_json = parsed_json
        self.attempts = 0

    def generate_json(self, **kwargs: Any) -> LLMResult:
        del kwargs
        self.attempts += 1
        return _llm_result(self.parsed_json)


class NeverCalledLLMClient:
    def __init__(self) -> None:
        self.attempts = 0

    def generate_json(self, **kwargs: Any) -> LLMResult:
        del kwargs
        self.attempts += 1
        raise AssertionError("LLM should not be called for oversized context")


class LLMStorageErrorClient:
    def __init__(self) -> None:
        self.attempts = 0

    def generate_json(self, **kwargs: Any) -> LLMResult:
        del kwargs
        self.attempts += 1
        raise sqlite3.OperationalError("database locked")


class LLMUnknownErrorClient:
    def __init__(self) -> None:
        self.attempts = 0

    def generate_json(self, **kwargs: Any) -> LLMResult:
        del kwargs
        self.attempts += 1
        raise LookupError("unexpected provider shape")


def _load_schema() -> dict[str, Any]:
    path = Path("app/prompts/kaucja_gap_analysis/v001/schema.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _valid_llm_payload(schema: dict[str, Any]) -> dict[str, Any]:
    item_ids = schema["$defs"]["checklist_item"]["properties"]["item_id"]["enum"]
    checklist: list[dict[str, Any]] = []
    for idx, item_id in enumerate(item_ids):
        status = "confirmed" if idx == 0 else "missing"
        checklist.append(
            {
                "item_id": item_id,
                "importance": "critical",
                "status": status,
                "what_it_supports": "support",
                "findings": [
                    {
                        "doc_id": "0000001",
                        "quote": "quoted",
                        "why_this_quote_matters": "reason",
                    }
                ]
                if status == "confirmed"
                else [],
                "missing_what_exactly": "missing",
                "request_from_user": {
                    "type": "upload_document",
                    "ask": "upload",
                    "examples": ["example"],
                },
                "confidence": "high",
            }
        )

    fact = {
        "value": "v",
        "status": "confirmed",
        "sources": [{"doc_id": "0000001", "quote": "q"}],
    }
    return {
        "case_facts": {
            "parties": {"tenant": fact},
            "property_address": fact,
            "lease_type": fact,
            "key_dates": {"start": fact},
            "money": {"deposit": fact},
            "notes": [],
        },
        "checklist": checklist,
        "critical_gaps_summary": ["gap1"],
        "next_questions_to_user": ["q1"],
        "conflicts_and_red_flags": [],
        "ocr_quality_warnings": [],
    }


def _llm_result(parsed_json: dict[str, Any]) -> LLMResult:
    return LLMResult(
        raw_text=json.dumps(parsed_json),
        parsed_json=parsed_json,
        raw_response={"provider": "mock"},
        usage_raw={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
        usage_normalized={
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "thoughts_tokens": None,
        },
        cost={"llm_cost_usd": 0.0001, "total_cost_usd": 0.0001},
        timings={"t_llm_total_ms": 3.0},
    )


def _setup_orchestrator(
    *,
    tmp_path: Path,
    ocr_client: Any,
    llm_clients: dict[str, Any],
) -> OCRPipelineOrchestrator:
    artifacts_manager = ArtifactsManager(tmp_path / "data")
    repo = StorageRepo(
        db_path=tmp_path / "kaucja.sqlite3",
        artifacts_manager=artifacts_manager,
    )
    return OCRPipelineOrchestrator(
        repo=repo,
        artifacts_manager=artifacts_manager,
        ocr_client=ocr_client,
        llm_clients=llm_clients,
        prompt_root=Path("app/prompts"),
        sleep_fn=lambda _: None,
    )


def test_ocr_retry_success_after_first_transient_failure(tmp_path: Path) -> None:
    ocr_client = OCRFailOnceClient()
    orchestrator = _setup_orchestrator(
        tmp_path=tmp_path,
        ocr_client=ocr_client,
        llm_clients={},
    )
    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_ocr_stage(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    assert result.documents[0].ocr_status == "ok"
    assert ocr_client.attempts == 2


def test_llm_retry_on_5xx_then_success(tmp_path: Path) -> None:
    schema = _load_schema()
    payload = _valid_llm_payload(schema)
    llm_client = LLMRetryOnceClient(payload)
    orchestrator = _setup_orchestrator(
        tmp_path=tmp_path,
        ocr_client=OCRSimpleClient(),
        llm_clients={"openai": llm_client},
    )
    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    assert llm_client.attempts == 2


def test_no_retry_for_llm_invalid_json(tmp_path: Path) -> None:
    llm_client = LLMInvalidJsonClient()
    orchestrator = _setup_orchestrator(
        tmp_path=tmp_path,
        ocr_client=OCRSimpleClient(),
        llm_clients={"openai": llm_client},
    )
    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.error_code == "LLM_INVALID_JSON"
    assert llm_client.attempts == 1


def test_no_retry_for_schema_invalid_output(tmp_path: Path) -> None:
    schema = _load_schema()
    invalid_payload = _valid_llm_payload(schema)
    invalid_payload["checklist"] = invalid_payload["checklist"][:-1]

    llm_client = LLMSchemaInvalidClient(invalid_payload)
    orchestrator = _setup_orchestrator(
        tmp_path=tmp_path,
        ocr_client=OCRSimpleClient(),
        llm_clients={"openai": llm_client},
    )
    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.error_code == "LLM_SCHEMA_INVALID"
    assert llm_client.attempts == 1


def test_context_too_large_branch_persists_failure(tmp_path: Path) -> None:
    llm_client = NeverCalledLLMClient()
    orchestrator = _setup_orchestrator(
        tmp_path=tmp_path,
        ocr_client=OCRSimpleClient(content="X" * 2000),
        llm_clients={"openai": llm_client},
    )
    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        ocr_options=OCROptions(model="mistral-ocr-latest"),
        llm_params={"context_char_limit": 50},
    )

    assert result.run_status == "failed"
    assert result.error_code == "CONTEXT_TOO_LARGE"
    assert llm_client.attempts == 0

    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    assert run.error_code == "CONTEXT_TOO_LARGE"

    manifest = json.loads(
        Path(run.artifacts_root_path, "run.json").read_text(encoding="utf-8")
    )
    assert manifest["error_code"] == "CONTEXT_TOO_LARGE"
    assert "context threshold" in manifest["error_message"]


def test_llm_storage_error_maps_to_storage_error(tmp_path: Path) -> None:
    llm_client = LLMStorageErrorClient()
    orchestrator = _setup_orchestrator(
        tmp_path=tmp_path,
        ocr_client=OCRSimpleClient(),
        llm_clients={"openai": llm_client},
    )
    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "failed"
    assert result.error_code == "STORAGE_ERROR"
    assert llm_client.attempts == 1


def test_llm_unknown_error_maps_to_unknown_error(tmp_path: Path) -> None:
    llm_client = LLMUnknownErrorClient()
    orchestrator = _setup_orchestrator(
        tmp_path=tmp_path,
        ocr_client=OCRSimpleClient(),
        llm_clients={"openai": llm_client},
    )
    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "failed"
    assert result.error_code == "UNKNOWN_ERROR"
    assert llm_client.attempts == 1


def test_storage_error_during_failure_persistence_returns_storage_error(
    tmp_path: Path,
) -> None:
    llm_client = LLMUnknownErrorClient()
    orchestrator = _setup_orchestrator(
        tmp_path=tmp_path,
        ocr_client=OCRSimpleClient(),
        llm_clients={"openai": llm_client},
    )
    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    original_update_run_metrics = orchestrator.repo.update_run_metrics

    def _broken_update_run_metrics(**kwargs: Any) -> None:
        raise sqlite3.OperationalError("metrics write failed")

    orchestrator.repo.update_run_metrics = _broken_update_run_metrics  # type: ignore[method-assign]
    try:
        result = orchestrator.run_full_pipeline(
            input_files=[file_one],
            session_id=None,
            provider="openai",
            model="gpt-5.1",
            prompt_name="kaucja_gap_analysis",
            prompt_version="v001",
            ocr_options=OCROptions(model="mistral-ocr-latest"),
        )
    finally:
        orchestrator.repo.update_run_metrics = original_update_run_metrics  # type: ignore[method-assign]

    assert result.run_status == "failed"
    assert result.error_code == "STORAGE_ERROR"
