from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.llm_client.base import LLMResult
from app.ocr_client.types import OCROptions, OCRResult
from app.pipeline.orchestrator import OCRPipelineOrchestrator
from app.storage.artifacts import ArtifactsManager
from app.storage.repo import StorageRepo


class FakeOCRClient:
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
        combined_path = output_dir / "combined.md"
        raw_response_path = output_dir / "raw_response.json"
        quality_path = output_dir / "quality.json"

        combined_path.write_text(
            "markdown [tbl-0.html](tbl-0.html) ![img-0.png](img-0.png)",
            encoding="utf-8",
        )
        raw_response_path.write_text('{"pages": []}', encoding="utf-8")
        quality_path.write_text('{"warnings": [], "bad_pages": []}', encoding="utf-8")

        return OCRResult(
            doc_id=doc_id,
            ocr_model="mistral-ocr-latest",
            pages_count=1,
            combined_markdown_path=str(combined_path.resolve()),
            raw_response_path=str(raw_response_path.resolve()),
            tables_dir=str((output_dir / "tables").resolve()),
            images_dir=str((output_dir / "images").resolve()),
            page_renders_dir=str((output_dir / "page_renders").resolve()),
            quality_path=str(quality_path.resolve()),
            quality_warnings=[],
        )


class SuccessLLMClient:
    def __init__(self, parsed_json: dict[str, Any]) -> None:
        self._parsed_json = parsed_json

    def generate_json(self, **kwargs: Any) -> LLMResult:
        del kwargs
        return LLMResult(
            raw_text=json.dumps(self._parsed_json),
            parsed_json=self._parsed_json,
            raw_response={"provider": "mock"},
            usage_raw={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            usage_normalized={
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
                "thoughts_tokens": None,
            },
            cost={"llm_cost_usd": 0.0001, "total_cost_usd": 0.0001},
            timings={"t_llm_total_ms": 5.0},
        )


class FailingLLMClient:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def generate_json(self, **kwargs: Any) -> LLMResult:
        del kwargs
        raise self._error


def _load_schema() -> dict[str, Any]:
    path = Path("app/prompts/kaucja_gap_analysis/v001/schema.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _valid_llm_payload(schema: dict[str, Any]) -> dict[str, Any]:
    item_ids = schema["$defs"]["checklist_item"]["properties"]["item_id"]["enum"]
    checklist = []
    for idx, item_id in enumerate(item_ids):
        status = "confirmed" if idx == 0 else "missing"
        checklist.append(
            {
                "item_id": item_id,
                "importance": "critical" if idx == 0 else "recommended",
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
            "parties": [{"role": "tenant", "fact": fact}],
            "property_address": fact,
            "lease_type": fact,
            "key_dates": [{"name": "start", "fact": fact}],
            "money": [{"name": "deposit", "fact": fact}],
            "notes": [],
        },
        "checklist": checklist,
        "critical_gaps_summary": ["gap1"],
        "next_questions_to_user": ["q1"],
        "conflicts_and_red_flags": [],
        "ocr_quality_warnings": [],
    }


def _setup_orchestrator(
    tmp_path: Path,
    llm_clients: dict[str, Any],
) -> OCRPipelineOrchestrator:
    artifacts_manager = ArtifactsManager(tmp_path / "data")
    repo = StorageRepo(
        db_path=tmp_path / "kaucja.sqlite3", artifacts_manager=artifacts_manager
    )
    return OCRPipelineOrchestrator(
        repo=repo,
        artifacts_manager=artifacts_manager,
        ocr_client=FakeOCRClient(),
        llm_clients=llm_clients,
        prompt_root=Path("app/prompts"),
    )


def test_full_pipeline_success_persists_artifacts_db_and_metrics(
    tmp_path: Path,
) -> None:
    schema = _load_schema()
    llm_payload = _valid_llm_payload(schema)
    orchestrator = _setup_orchestrator(
        tmp_path, {"openai": SuccessLLMClient(llm_payload)}
    )

    file_one = tmp_path / "one.pdf"
    file_two = tmp_path / "two.pdf"
    file_one.write_bytes(b"one")
    file_two.write_bytes(b"two")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one, file_two],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        ocr_options=OCROptions(model="mistral-ocr-latest"),
        llm_params={"openai_reasoning_effort": "auto"},
    )

    assert result.run_status == "completed"
    assert result.validation_valid is True

    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    assert run.status == "completed"
    assert run.timings_json is not None
    assert run.usage_normalized_json is not None

    llm_output = orchestrator.repo.get_llm_output(run_id=result.run_id)
    assert llm_output is not None
    assert llm_output.response_valid is True

    artifacts_root = Path(run.artifacts_root_path)
    assert (artifacts_root / "llm" / "request.txt").is_file()
    assert (artifacts_root / "llm" / "response_raw.txt").is_file()
    assert (artifacts_root / "llm" / "response_parsed.json").is_file()
    assert (artifacts_root / "llm" / "validation.json").is_file()

    manifest_path = artifacts_root / "run.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["session_id"] == result.session_id
    assert manifest["run_id"] == result.run_id
    assert manifest["status"] == "completed"
    assert "inputs" in manifest
    assert "stages" in manifest
    assert "artifacts" in manifest
    assert "metrics" in manifest
    assert "validation" in manifest


def test_full_pipeline_llm_api_error_marks_run_failed(tmp_path: Path) -> None:
    orchestrator = _setup_orchestrator(
        tmp_path,
        {"openai": FailingLLMClient(RuntimeError("API down"))},
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
    assert result.error_code == "LLM_API_ERROR"

    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    assert run.status == "failed"
    assert run.error_code == "LLM_API_ERROR"


def test_full_pipeline_schema_invalid_marks_run_failed_and_persists_validation(
    tmp_path: Path,
) -> None:
    schema = _load_schema()
    invalid_payload = _valid_llm_payload(schema)
    invalid_payload["checklist"] = invalid_payload["checklist"][:-1]

    orchestrator = _setup_orchestrator(
        tmp_path, {"openai": SuccessLLMClient(invalid_payload)}
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
    assert result.error_code == "LLM_SCHEMA_INVALID"

    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    assert run.status == "failed"
    assert run.error_code == "LLM_SCHEMA_INVALID"

    llm_output = orchestrator.repo.get_llm_output(run_id=result.run_id)
    assert llm_output is not None
    assert llm_output.response_valid is False
    assert llm_output.schema_validation_errors_path is not None
    assert Path(llm_output.schema_validation_errors_path).is_file()


def test_full_pipeline_invalid_json_marks_run_failed(tmp_path: Path) -> None:
    orchestrator = _setup_orchestrator(
        tmp_path,
        {
            "openai": FailingLLMClient(
                json.JSONDecodeError("Expecting value", "not-json", 0)
            )
        },
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
    assert result.error_code == "LLM_INVALID_JSON"

    llm_output = orchestrator.repo.get_llm_output(run_id=result.run_id)
    assert llm_output is not None
    assert llm_output.response_valid is False
