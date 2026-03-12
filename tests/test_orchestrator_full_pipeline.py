from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from app.agentic.case_workspace_store import (
    MongoCaseWorkspaceStore,
    Scenario2CaseMetadata,
)
from app.llm_client.base import LLMResult
from app.agentic.openai_scenario2_runner import OpenAIScenario2Runner
from app.ocr_client.types import OCROptions, OCRResult
from app.pipeline.orchestrator import OCRPipelineOrchestrator
from app.agentic.scenario2_runner import (
    Scenario2RunConfig,
    Scenario2RunResult,
)
from app.pipeline.scenario_router import (
    SCENARIO_2_ID,
    SCENARIO_2_PLACEHOLDER,
    SCENARIO_2_VALIDATION_MESSAGE,
    SCENARIO_2_VALIDATION_STATUS,
    SCENARIO2_CONFIG_ERROR,
    SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    SCENARIO2_RUNNER_MODE_STUB,
    SCENARIO2_RUNTIME_ERROR,
    SCENARIO2_TRACE_PERSIST_ERROR,
)
from app.storage.artifacts import ArtifactsManager
from app.storage.repo import StorageRepo
from tests.fake_mongo_runtime import FakeMongoRuntime


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


class CallTrackingLLMClient:
    def __init__(self) -> None:
        self.called = False

    def generate_json(self, **kwargs: Any) -> LLMResult:
        self.called = True
        raise AssertionError("LLM should not be called for scenario_2")


class FailingScenario2Runner:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def run(
        self,
        *,
        packed_documents: str,
        config: Scenario2RunConfig,
        system_prompt_path: str,
        legal_corpus_tool: object | None = None,
    ) -> Scenario2RunResult:
        del packed_documents, config, system_prompt_path, legal_corpus_tool
        raise self._error


class FakeResponsesService:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(copy.deepcopy(kwargs))
        if not self.responses:
            raise AssertionError("No more mock responses")
        return self.responses.pop(0)


class FakeLegalCorpusTool:
    def __init__(self) -> None:
        self.search_calls: list[dict[str, Any]] = []
        self.fetch_fragments_calls: list[dict[str, Any]] = []
        self.expand_related_calls: list[dict[str, Any]] = []
        self.get_provenance_calls: list[dict[str, Any]] = []

    def search(self, request: dict[str, Any]) -> dict[str, Any]:
        self.search_calls.append(request)
        return {"hits": ["search-hit"]}

    def fetch_fragments(self, request: dict[str, Any]) -> dict[str, Any]:
        self.fetch_fragments_calls.append(request)
        first_ref = request.get("refs", [{}])[0]
        return {
            "fragments": [
                {
                    "machine_ref": first_ref,
                    "doc_uid": first_ref.get("doc_uid", "doc-1"),
                    "source_hash": first_ref.get("source_hash", "sha256:doc-1"),
                    "display_citation": "Doc 1 fragment",
                    "text": "Exact supporting fragment.",
                    "locator": first_ref.get(
                        "locator",
                        {"start_char": 0, "end_char": 24},
                    ),
                    "locator_precision": "char_offsets_only",
                    "page_truth_status": "not_available_local",
                    "quote_checksum": "sha256:fragment",
                }
            ]
        }

    def expand_related(self, request: dict[str, Any]) -> dict[str, Any]:
        self.expand_related_calls.append(request)
        return {"related": ["related"]}

    def get_provenance(self, request: dict[str, Any]) -> dict[str, Any]:
        self.get_provenance_calls.append(request)
        return {"provenance": ["prov"]}


class EmptyFragmentsLegalCorpusTool(FakeLegalCorpusTool):
    def fetch_fragments(self, request: dict[str, Any]) -> dict[str, Any]:
        self.fetch_fragments_calls.append(request)
        return {"fragments": []}


class RecordingScenario2Runner:
    def __init__(self, diagnostics: dict[str, Any] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.diagnostics = diagnostics or {"runner": "recording"}

    def run(
        self,
        *,
        packed_documents: str,
        config: Scenario2RunConfig,
        system_prompt_path: str,
        legal_corpus_tool: object | None = None,
    ) -> Scenario2RunResult:
        self.calls.append(
            {
                "packed_documents": packed_documents,
                "provider": config.provider,
                "model": config.model,
                "prompt_name": config.prompt_name,
                "prompt_version": config.prompt_version,
                "system_prompt_path": system_prompt_path,
                "tool": type(legal_corpus_tool).__name__
                if legal_corpus_tool
                else "none",
            }
        )
        return Scenario2RunResult(
            final_text="custom scenario2 result",
            response_mode="plain_text",
            steps=["custom.step"],
            tool_trace=[
                {
                    "tool": "test",
                    "status": "ok",
                }
            ],
            diagnostics=dict(self.diagnostics),
        )


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
    monkeypatch: Any,
    llm_clients: dict[str, Any],
    scenario2_runner_mode: str = SCENARIO2_RUNNER_MODE_STUB,
    scenario2_verifier_policy: str = "informational",
    scenario2_case_workspace_store: Any | None = None,
) -> OCRPipelineOrchestrator:
    artifacts_manager = ArtifactsManager(tmp_path / "data")
    repo = StorageRepo(
        db_path=tmp_path / "kaucja.sqlite3", artifacts_manager=artifacts_manager
    )

    prompt_root = tmp_path / "prompts"
    prompt_dir = prompt_root / "kaucja_gap_analysis" / "v001"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    canonical_prompt_text = Path("app/prompts/canonical_prompt.txt").read_text(
        encoding="utf-8"
    )
    canonical_schema_text = Path("app/schemas/canonical_schema.json").read_text(
        encoding="utf-8"
    )
    (prompt_dir / "system_prompt.txt").write_text(
        canonical_prompt_text, encoding="utf-8"
    )
    (prompt_dir / "schema.json").write_text(canonical_schema_text, encoding="utf-8")

    # To pass TechSpec Fail-Closed logic which checks 'app/prompts/...' relative to cwd:
    app_prompts = tmp_path / "app" / "prompts"
    app_schemas = tmp_path / "app" / "schemas"
    app_prompts.mkdir(parents=True, exist_ok=True)
    app_schemas.mkdir(parents=True, exist_ok=True)
    (app_prompts / "canonical_prompt.txt").write_text(
        canonical_prompt_text, encoding="utf-8"
    )
    (app_schemas / "canonical_schema.json").write_text(
        canonical_schema_text, encoding="utf-8"
    )

    monkeypatch.chdir(tmp_path)

    return OCRPipelineOrchestrator(
        repo=repo,
        artifacts_manager=artifacts_manager,
        ocr_client=FakeOCRClient(),
        llm_clients=llm_clients,
        prompt_root=prompt_root,
        scenario2_runner_mode=scenario2_runner_mode,
        scenario2_verifier_policy=scenario2_verifier_policy,
        scenario2_case_workspace_store=scenario2_case_workspace_store,
    )


def test_full_pipeline_success_persists_artifacts_db_and_metrics(
    tmp_path: Path, monkeypatch: Any
) -> None:
    schema = _load_schema()
    llm_payload = _valid_llm_payload(schema)
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={"openai": SuccessLLMClient(llm_payload)},
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


def test_full_pipeline_llm_api_error_marks_run_failed(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={"openai": FailingLLMClient(RuntimeError("API down"))},
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
    tmp_path: Path, monkeypatch: Any
) -> None:
    schema = _load_schema()
    invalid_payload = _valid_llm_payload(schema)
    invalid_payload["checklist"] = invalid_payload["checklist"][:-1]

    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={"openai": SuccessLLMClient(invalid_payload)},
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


def test_full_pipeline_scenario_2_uses_ocr_only_placeholder_path(
    tmp_path: Path, monkeypatch: Any
) -> None:
    call_tracking_llm = CallTrackingLLMClient()
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={"openai": call_tracking_llm},
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
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.scenario_id == SCENARIO_2_ID
    assert result.run_status == "completed"
    assert result.error_code is None
    assert result.raw_json_text == SCENARIO_2_PLACEHOLDER
    assert result.parsed_json is None
    assert not call_tracking_llm.called

    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    assert run.status == "completed"
    assert run.model == "gpt-5.4"
    assert run.provider == "openai"

    manifest_path = Path(run.artifacts_root_path) / "run.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["inputs"]["scenario_id"] == SCENARIO_2_ID
    assert manifest["validation"]["status"] == SCENARIO_2_VALIDATION_STATUS
    assert manifest["validation"]["errors"] == [SCENARIO_2_VALIDATION_MESSAGE]
    trace_path = manifest.get("artifacts", {}).get("llm", {}).get("trace_path")
    assert trace_path is not None
    assert Path(trace_path).is_file()
    trace_payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    assert trace_payload["response_mode"] == "plain_text"
    assert trace_payload["final_text"] == SCENARIO_2_PLACEHOLDER
    assert trace_payload["steps"] == ["ocr_complete", "scenario2_stub_response"]
    assert "scenario2_success_failed" not in trace_payload["steps"]
    assert trace_payload["runner_mode"] == SCENARIO2_RUNNER_MODE_STUB
    assert trace_payload["llm_executed"] is False
    assert len(trace_payload["tool_trace"]) == 1
    assert trace_payload["tool_trace"][0]["tool"] == "scenario2_stub"
    assert trace_payload["diagnostics"]["prompt_exists"] is True


def test_full_pipeline_scenario_2_persists_known_case_workspace_metadata(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    workspace_runtime = FakeMongoRuntime(collections={})
    workspace_store = MongoCaseWorkspaceStore(runtime=workspace_runtime)
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={"openai": CallTrackingLLMClient()},
        scenario2_case_workspace_store=workspace_store,
    )

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id="session-case-001",
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
        scenario2_case_workspace_id="case-001",
        scenario2_case_metadata=Scenario2CaseMetadata(
            claim_amount=1200.0,
            currency="PLN",
            move_out_date="2026-01-15",
        ),
    )

    assert result.run_status == "completed"
    workspace = workspace_runtime.load_collection("case_workspaces")[0]
    assert workspace["case_id"] == "case-001"
    assert workspace["claim_amount"] == 1200.0
    assert workspace["currency"] == "PLN"
    assert workspace["move_out_date"] == "2026-01-15"
    assert workspace["lease_start"] is None
    assert workspace["lease_end"] is None
    assert workspace["deposit_return_due_date"] is None
    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    manifest = json.loads((Path(run.artifacts_root_path) / "run.json").read_text())
    assert manifest["inputs"]["case_workspace_id"] == "case-001"


def test_full_pipeline_scenario_2_case_workspace_metadata_defaults_to_none(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    workspace_runtime = FakeMongoRuntime(collections={})
    workspace_store = MongoCaseWorkspaceStore(runtime=workspace_runtime)
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={"openai": CallTrackingLLMClient()},
        scenario2_case_workspace_store=workspace_store,
    )

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id="case-002",
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    workspace = workspace_runtime.load_collection("case_workspaces")[0]
    assert workspace["case_id"] == "case-002"
    assert workspace["claim_amount"] is None
    assert workspace["currency"] is None
    assert workspace["lease_start"] is None
    assert workspace["lease_end"] is None
    assert workspace["move_out_date"] is None
    assert workspace["deposit_return_due_date"] is None
    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    manifest = json.loads((Path(run.artifacts_root_path) / "run.json").read_text())
    assert manifest["inputs"]["case_workspace_id"] == "case-002"


def test_full_pipeline_scenario_2_stub_mode_ignores_injected_runner(
    tmp_path: Path, monkeypatch: Any
) -> None:
    recording_runner = RecordingScenario2Runner()
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={"openai": SuccessLLMClient(_valid_llm_payload(_load_schema()))},
    )
    orchestrator.scenario2_runner = recording_runner

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.scenario_id == SCENARIO_2_ID
    assert result.raw_json_text == SCENARIO_2_PLACEHOLDER
    assert result.parsed_json is None
    assert recording_runner.calls == []
    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    manifest = json.loads(
        Path(run.artifacts_root_path, "run.json").read_text(encoding="utf-8")
    )
    assert manifest["stages"]["llm"]["status"] == "skipped"
    assert manifest["artifacts"]["llm"]["runner_mode"] == SCENARIO2_RUNNER_MODE_STUB
    assert manifest["artifacts"]["llm"]["llm_executed"] is False
    assert manifest["review_status"] == "not_applicable"
    assert manifest["review"]["warnings_count"] == 0
    assert manifest["verifier_policy"] == "informational"
    assert manifest["verifier_gate_status"] == "not_applicable"
    trace_path = manifest.get("artifacts", {}).get("llm", {}).get("trace_path")
    assert trace_path is not None
    assert Path(trace_path).is_file()
    trace_payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    assert trace_payload["response_mode"] == "plain_text"
    assert trace_payload["final_text"] == SCENARIO_2_PLACEHOLDER
    assert trace_payload["steps"] == ["ocr_complete", "scenario2_stub_response"]
    assert "scenario2_success_failed" not in trace_payload["steps"]
    assert trace_payload["tool_trace"][0]["tool"] == "scenario2_stub"
    assert trace_payload["runner_mode"] == SCENARIO2_RUNNER_MODE_STUB
    assert trace_payload["llm_executed"] is False
    assert trace_payload["diagnostics"]["verifier_policy"] == "informational"
    assert trace_payload["diagnostics"]["verifier_gate_status"] == "not_applicable"


def test_full_pipeline_scenario_2_openai_mode_uses_injected_runner(
    tmp_path: Path, monkeypatch: Any
) -> None:
    recording_runner = RecordingScenario2Runner(
        diagnostics={
            "runner": "recording",
            "verifier_status": "passed",
            "verifier_warnings": [],
        }
    )
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={},
        scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    )
    orchestrator.scenario2_runner = recording_runner
    orchestrator.legal_corpus_tool = FakeLegalCorpusTool()

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.scenario_id == SCENARIO_2_ID
    assert result.run_status == "completed"
    assert result.raw_json_text == "custom scenario2 result"
    assert len(recording_runner.calls) == 1
    call = recording_runner.calls[0]
    assert call["provider"] == "openai"
    assert call["model"] == "gpt-5.4"
    assert call["prompt_name"] == "agent_prompt_foundation"
    assert call["prompt_version"] == "v1.1"
    assert Path(call["system_prompt_path"]).is_file()
    assert "<BEGIN_DOCUMENTS>" in call["packed_documents"]
    assert call["tool"] == "FakeLegalCorpusTool"

    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    manifest = json.loads(
        Path(run.artifacts_root_path, "run.json").read_text(encoding="utf-8")
    )
    assert manifest["stages"]["llm"]["status"] == "completed"
    assert (
        manifest["artifacts"]["llm"]["runner_mode"]
        == SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP
    )
    assert manifest["artifacts"]["llm"]["llm_executed"] is True
    assert manifest["review_status"] == "passed"
    assert manifest["review"]["warnings_count"] == 0
    assert manifest["verifier_policy"] == "informational"
    assert manifest["verifier_gate_status"] == "passed"
    trace_path = manifest.get("artifacts", {}).get("llm", {}).get("trace_path")
    assert trace_path is not None
    assert Path(trace_path).is_file()
    trace_payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    assert trace_payload["response_mode"] == "plain_text"
    assert trace_payload["final_text"] == "custom scenario2 result"
    assert trace_payload["steps"] == ["custom.step"]
    assert "scenario2_success_failed" not in trace_payload["steps"]
    assert trace_payload["tool_trace"][0]["tool"] == "test"
    assert trace_payload["runner_mode"] == SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP
    assert trace_payload["llm_executed"] is True
    assert trace_payload["diagnostics"]["verifier_policy"] == "informational"
    assert trace_payload["diagnostics"]["verifier_gate_status"] == "passed"


def test_full_pipeline_scenario_2_real_openai_runner_uses_injected_tooling(
    tmp_path: Path, monkeypatch: Any
) -> None:
    legal_tool = FakeLegalCorpusTool()
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={},
        scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    )

    responses_service = FakeResponsesService(
        responses=[
            {
                "id": "resp_search_1",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_item_search_1",
                        "call_id": "fc_call_search_1",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ],
            },
            {
                "id": "resp_fetch_1",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_item_fetch_1",
                        "call_id": "fc_call_fetch_1",
                        "name": "fetch_fragments",
                        "arguments": json.dumps(
                            {
                                "refs": [
                                    {
                                        "doc_uid": "doc-1",
                                        "unit_id": "fragment:0:48",
                                        "locator": {
                                            "start_char": 0,
                                            "end_char": 48,
                                        },
                                    }
                                ]
                            }
                        ),
                    }
                ],
            },
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Scenario2 real runner completed.",
                            }
                        ],
                    }
                ]
            },
        ]
    )
    orchestrator.scenario2_runner = OpenAIScenario2Runner(
        responses_service=responses_service,
        max_tool_rounds=6,
    )
    orchestrator.legal_corpus_tool = legal_tool

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    assert result.scenario_id == SCENARIO_2_ID
    assert result.raw_json_text == "Scenario2 real runner completed."
    assert legal_tool.search_calls
    assert responses_service.calls
    assert len(responses_service.calls) == 3
    second_round_input = responses_service.calls[1]["input"]
    assert responses_service.calls[1]["previous_response_id"] == "resp_search_1"
    assert second_round_input == [
        {
            "type": "function_call_output",
            "call_id": "fc_call_search_1",
            "output": json.dumps({"hits": ["search-hit"]}, ensure_ascii=False),
        }
    ]
    assert "tool_name" not in second_round_input[-1]
    assert responses_service.calls[2]["previous_response_id"] == "resp_fetch_1"

    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    assert run.status == "completed"
    manifest = json.loads(
        Path(run.artifacts_root_path, "run.json").read_text(encoding="utf-8")
    )
    assert manifest["stages"]["llm"]["status"] == "completed"
    assert (
        manifest["artifacts"]["llm"]["runner_mode"]
        == SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP
    )
    assert manifest["artifacts"]["llm"]["llm_executed"] is True
    assert manifest["review_status"] == "passed"
    assert manifest["review"]["warnings_count"] == 0
    assert manifest["verifier_policy"] == "informational"
    assert manifest["verifier_gate_status"] == "passed"
    trace_path = manifest.get("artifacts", {}).get("llm", {}).get("trace_path")
    assert trace_path is not None
    trace_payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    assert trace_payload["response_mode"] == "plain_text"
    assert trace_payload["model"] == "gpt-5.4"
    assert trace_payload["tool_round_count"] > 0
    assert "scenario2_success_failed" not in trace_payload["steps"]
    assert trace_payload["runner_mode"] == SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP
    assert trace_payload["llm_executed"] is True
    assert isinstance(trace_payload["tool_trace"], list)
    assert trace_payload["tool_trace"]
    assert trace_payload["tool_trace"][0]["tool"] == "search"
    assert trace_payload["tool_trace"][1]["tool"] == "fetch_fragments"
    assert trace_payload["diagnostics"]["fragment_grounding_status"] == (
        "fragments_fetched"
    )
    assert trace_payload["diagnostics"]["citation_binding_status"] == (
        "fragments_fetched"
    )
    assert trace_payload["diagnostics"]["fetch_fragments_called"] is True
    assert (
        trace_payload["diagnostics"]["fetch_fragments_returned_usable_fragments"]
        is True
    )
    assert trace_payload["diagnostics"]["search_budget_limit"] == 40
    assert trace_payload["diagnostics"]["search_budget_used"] == 1
    assert trace_payload["diagnostics"]["tool_round_limit"] == 6
    assert trace_payload["diagnostics"]["successful_fetch_fragments"] is True
    assert trace_payload["diagnostics"]["tool_usage_counts"] == {
        "search": 1,
        "fetch_fragments": 1,
        "expand_related": 0,
        "get_provenance": 0,
    }
    assert trace_payload["diagnostics"]["fetched_fragment_doc_uids"] == ["doc-1"]
    assert trace_payload["diagnostics"]["fetched_fragment_source_hashes"] == [
        "sha256:doc-1"
    ]
    assert trace_payload["diagnostics"]["fetched_fragment_refs"]
    assert trace_payload["diagnostics"]["fetched_fragment_ledger"]
    assert trace_payload["diagnostics"]["openai_threading_trace"][0]["response_id"] == (
        "resp_search_1"
    )
    assert (
        trace_payload["diagnostics"]["openai_threading_trace"][1][
            "previous_response_id"
        ]
        == "resp_search_1"
    )
    assert trace_payload["tool_trace"][0]["openai_call_id"] == "fc_call_search_1"
    assert trace_payload["tool_trace"][1]["openai_previous_response_id"] == (
        "resp_fetch_1"
    )


def test_full_pipeline_scenario_2_normalizes_fetch_fragments_references_alias(
    tmp_path: Path, monkeypatch: Any
) -> None:
    legal_tool = FakeLegalCorpusTool()
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={},
        scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    )

    responses_service = FakeResponsesService(
        responses=[
            {
                "id": "resp_search_alias_1",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_item_search_alias_1",
                        "call_id": "fc_call_search_alias_1",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ],
            },
            {
                "id": "resp_fetch_alias_1",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_item_fetch_alias_1",
                        "call_id": "fc_call_fetch_alias_1",
                        "name": "fetch_fragments",
                        "arguments": json.dumps(
                            {
                                "references": [
                                    {
                                        "doc_uid": "doc-1",
                                        "unit_id": "fragment:0:48",
                                        "locator": {
                                            "start_char": 0,
                                            "end_char": 48,
                                        },
                                    }
                                ]
                            }
                        ),
                    }
                ],
            },
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Scenario2 real runner completed.",
                            }
                        ],
                    }
                ]
            },
        ]
    )
    orchestrator.scenario2_runner = OpenAIScenario2Runner(
        responses_service=responses_service,
        max_tool_rounds=6,
    )
    orchestrator.legal_corpus_tool = legal_tool

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    assert legal_tool.fetch_fragments_calls == [
        {
            "refs": [
                {
                    "doc_uid": "doc-1",
                    "unit_id": "fragment:0:48",
                    "locator": {
                        "start_char": 0,
                        "end_char": 48,
                    },
                }
            ]
        }
    ]
    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    manifest = json.loads(
        Path(run.artifacts_root_path, "run.json").read_text(encoding="utf-8")
    )
    trace_path = manifest.get("artifacts", {}).get("llm", {}).get("trace_path")
    assert trace_path is not None
    trace_payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    assert trace_payload["tool_trace"][1]["tool"] == "fetch_fragments"
    assert trace_payload["tool_trace"][1]["request_args"] == {
        "refs": [
            {
                "doc_uid": "doc-1",
                "unit_id": "fragment:0:48",
                "locator": {
                    "start_char": 0,
                    "end_char": 48,
                },
            }
        ]
    }
    assert trace_payload["tool_trace"][1]["request_args_raw"] == {
        "references": [
            {
                "doc_uid": "doc-1",
                "unit_id": "fragment:0:48",
                "locator": {
                    "start_char": 0,
                    "end_char": 48,
                },
            }
        ]
    }
    assert trace_payload["tool_trace"][1]["request_aliases_applied"] == {
        "references": "refs"
    }
    assert trace_payload["diagnostics"]["fetched_fragment_quote_checksums"] == [
        "sha256:fragment"
    ]
    assert trace_payload["diagnostics"]["search_budget_limit"] == 40
    assert trace_payload["diagnostics"]["search_budget_used"] == 1
    assert trace_payload["diagnostics"]["tool_round_limit"] == 6
    assert (
        trace_payload["diagnostics"]["fetched_fragment_ledger"][0]["text_excerpt"]
        == "Exact supporting fragment."
    )
    assert trace_payload["diagnostics"]["verifier_status"] == "passed"
    assert trace_payload["diagnostics"]["verifier_policy"] == "informational"
    assert trace_payload["diagnostics"]["verifier_gate_status"] == "passed"
    assert trace_payload["diagnostics"]["citation_format_status"] == "not_applicable"
    assert trace_payload["diagnostics"]["legal_citation_count"] == 0
    assert trace_payload["diagnostics"]["user_doc_citation_count"] == 0
    assert trace_payload["diagnostics"]["citations_in_analysis_sections"] is None
    assert trace_payload["diagnostics"]["missing_sections"] == []
    assert "tool_round_count" in trace_payload["diagnostics"]


def test_full_pipeline_scenario_2_normalizes_fetch_fragments_machine_refs_alias(
    tmp_path: Path, monkeypatch: Any
) -> None:
    legal_tool = FakeLegalCorpusTool()
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={},
        scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    )

    responses_service = FakeResponsesService(
        responses=[
            {
                "id": "resp_search_machine_1",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_item_search_machine_1",
                        "call_id": "fc_call_search_machine_1",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ],
            },
            {
                "id": "resp_fetch_machine_1",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_item_fetch_machine_1",
                        "call_id": "fc_call_fetch_machine_1",
                        "name": "fetch_fragments",
                        "arguments": json.dumps(
                            {
                                "machine_refs": [
                                    {
                                        "doc_uid": "doc-1",
                                        "unit_id": "fragment:0:48",
                                        "locator": {
                                            "start_char": 0,
                                            "end_char": 48,
                                        },
                                    }
                                ]
                            }
                        ),
                    }
                ],
            },
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Scenario2 real runner completed.",
                            }
                        ],
                    }
                ]
            },
        ]
    )
    orchestrator.scenario2_runner = OpenAIScenario2Runner(
        responses_service=responses_service,
        max_tool_rounds=6,
    )
    orchestrator.legal_corpus_tool = legal_tool

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    assert legal_tool.fetch_fragments_calls == [
        {
            "refs": [
                {
                    "doc_uid": "doc-1",
                    "unit_id": "fragment:0:48",
                    "locator": {
                        "start_char": 0,
                        "end_char": 48,
                    },
                }
            ]
        }
    ]
    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    manifest = json.loads(
        Path(run.artifacts_root_path, "run.json").read_text(encoding="utf-8")
    )
    trace_path = manifest.get("artifacts", {}).get("llm", {}).get("trace_path")
    assert trace_path is not None
    trace_payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    assert trace_payload["tool_trace"][1]["request_args"] == {
        "refs": [
            {
                "doc_uid": "doc-1",
                "unit_id": "fragment:0:48",
                "locator": {
                    "start_char": 0,
                    "end_char": 48,
                },
            }
        ]
    }
    assert trace_payload["tool_trace"][1]["request_args_raw"] == {
        "machine_refs": [
            {
                "doc_uid": "doc-1",
                "unit_id": "fragment:0:48",
                "locator": {
                    "start_char": 0,
                    "end_char": 48,
                },
            }
        ]
    }
    assert trace_payload["tool_trace"][1]["request_aliases_applied"] == {
        "machine_refs": "refs"
    }


def test_full_pipeline_scenario_2_normalizes_fetch_fragments_machine_ref_alias(
    tmp_path: Path, monkeypatch: Any
) -> None:
    legal_tool = FakeLegalCorpusTool()
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={},
        scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    )

    responses_service = FakeResponsesService(
        responses=[
            {
                "id": "resp_search_machine_single_1",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_item_search_machine_single_1",
                        "call_id": "fc_call_search_machine_single_1",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ],
            },
            {
                "id": "resp_fetch_machine_single_1",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_item_fetch_machine_single_1",
                        "call_id": "fc_call_fetch_machine_single_1",
                        "name": "fetch_fragments",
                        "arguments": json.dumps(
                            {
                                "machine_ref": {
                                    "doc_uid": "doc-1",
                                    "unit_id": "fragment:0:48",
                                    "locator": {
                                        "start_char": 0,
                                        "end_char": 48,
                                    },
                                }
                            }
                        ),
                    }
                ],
            },
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Scenario2 real runner completed.",
                            }
                        ],
                    }
                ]
            },
        ]
    )
    orchestrator.scenario2_runner = OpenAIScenario2Runner(
        responses_service=responses_service,
        max_tool_rounds=6,
    )
    orchestrator.legal_corpus_tool = legal_tool

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    assert legal_tool.fetch_fragments_calls == [
        {
            "refs": [
                {
                    "doc_uid": "doc-1",
                    "unit_id": "fragment:0:48",
                    "locator": {
                        "start_char": 0,
                        "end_char": 48,
                    },
                }
            ]
        }
    ]
    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    manifest = json.loads(
        Path(run.artifacts_root_path, "run.json").read_text(encoding="utf-8")
    )
    trace_path = manifest.get("artifacts", {}).get("llm", {}).get("trace_path")
    assert trace_path is not None
    trace_payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    assert trace_payload["tool_trace"][1]["request_args"] == {
        "refs": [
            {
                "doc_uid": "doc-1",
                "unit_id": "fragment:0:48",
                "locator": {
                    "start_char": 0,
                    "end_char": 48,
                },
            }
        ]
    }
    assert trace_payload["tool_trace"][1]["request_args_raw"] == {
        "machine_ref": {
            "doc_uid": "doc-1",
            "unit_id": "fragment:0:48",
            "locator": {
                "start_char": 0,
                "end_char": 48,
            },
        }
    }
    assert trace_payload["tool_trace"][1]["request_aliases_applied"] == {
        "machine_ref": "refs"
    }


def test_full_pipeline_scenario_2_strict_verifier_policy_passes_plain_text_answer(
    tmp_path: Path, monkeypatch: Any
) -> None:
    legal_tool = FakeLegalCorpusTool()
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={},
        scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
        scenario2_verifier_policy="strict",
    )

    responses_service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps(
                            {
                                "refs": [
                                    {
                                        "doc_uid": "doc-1",
                                        "unit_id": "fragment:0:48",
                                        "locator": {
                                            "start_char": 0,
                                            "end_char": 48,
                                        },
                                    }
                                ]
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Scenario2 strict verifier gate warning.",
                            }
                        ],
                    }
                ]
            },
        ]
    )
    orchestrator.scenario2_runner = OpenAIScenario2Runner(
        responses_service=responses_service,
        max_tool_rounds=6,
    )
    orchestrator.legal_corpus_tool = legal_tool

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    manifest = json.loads(
        Path(run.artifacts_root_path, "run.json").read_text(encoding="utf-8")
    )
    assert manifest["verifier_policy"] == "strict"
    assert manifest["review_status"] == "passed"
    assert manifest["verifier_gate_status"] == "passed"
    trace_path = manifest.get("artifacts", {}).get("llm", {}).get("trace_path")
    assert trace_path is not None
    trace_payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    assert trace_payload["diagnostics"]["verifier_policy"] == "strict"
    assert trace_payload["diagnostics"]["verifier_status"] == "passed"
    assert trace_payload["diagnostics"]["verifier_gate_status"] == "passed"


def test_full_pipeline_scenario_2_strict_verifier_policy_passes_cleanly(
    tmp_path: Path, monkeypatch: Any
) -> None:
    recording_runner = RecordingScenario2Runner(
        diagnostics={
            "runner": "recording",
            "verifier_status": "passed",
            "verifier_warnings": [],
        }
    )
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={},
        scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
        scenario2_verifier_policy="strict",
    )
    orchestrator.scenario2_runner = recording_runner
    orchestrator.legal_corpus_tool = FakeLegalCorpusTool()

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    manifest = json.loads(
        Path(run.artifacts_root_path, "run.json").read_text(encoding="utf-8")
    )
    assert manifest["verifier_policy"] == "strict"
    assert manifest["verifier_gate_status"] == "passed"


def test_full_pipeline_scenario_2_real_openai_runner_without_legal_corpus_tool_fails(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={},
        scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    )
    orchestrator.scenario2_runner = OpenAIScenario2Runner(
        responses_service=FakeResponsesService(
            responses=[
                {
                    "output": [
                        {
                            "type": "function_call",
                            "name": "search",
                            "arguments": json.dumps(
                                {
                                    "query": "kaucja",
                                    "scope": "mixed",
                                    "return_level": "fragment",
                                }
                            ),
                        }
                    ]
                }
            ]
        ),
        max_tool_rounds=1,
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
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "failed"
    assert result.error_code == SCENARIO2_RUNTIME_ERROR
    assert "Legal corpus tool adapter is not configured" in result.error_message

    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    assert run.status == "failed"
    assert run.error_code == SCENARIO2_RUNTIME_ERROR

    manifest = json.loads(
        (Path(run.artifacts_root_path) / "run.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] == "failed"
    stages = manifest.get("stages", {})
    assert isinstance(stages, dict)
    assert stages["llm"]["status"] == "skipped"
    assert stages["finalize"]["status"] == "failed"
    assert manifest["error_code"] == SCENARIO2_RUNTIME_ERROR
    assert (
        manifest["artifacts"]["llm"]["runner_mode"]
        == SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP
    )
    assert manifest["artifacts"]["llm"]["llm_executed"] is False

    trace_path = manifest.get("artifacts", {}).get("llm", {}).get("trace_path")
    assert trace_path is not None
    trace_payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    assert trace_payload["diagnostics"]["error_code"] == SCENARIO2_RUNTIME_ERROR


def test_full_pipeline_scenario_2_config_failure_marks_run_failed(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={"openai": SuccessLLMClient(_valid_llm_payload(_load_schema()))},
    )

    def _missing_prompt(*_args: Any, **_kwargs: Any) -> str:
        raise FileNotFoundError("Scenario prompt source missing")

    monkeypatch.setattr(
        "app.pipeline.orchestrator.resolve_scenario_prompt_source_path", _missing_prompt
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
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "failed"
    assert result.error_code == SCENARIO2_CONFIG_ERROR

    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    assert run.status == "failed"
    assert run.error_code == SCENARIO2_CONFIG_ERROR

    manifest = json.loads(
        (Path(run.artifacts_root_path) / "run.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] == "failed"
    stages = manifest.get("stages", {})
    assert isinstance(stages, dict)
    assert stages["llm"]["status"] == "skipped"
    assert stages["finalize"]["status"] == "failed"
    assert manifest["error_code"] == SCENARIO2_CONFIG_ERROR


def test_full_pipeline_scenario_2_runner_exception_marks_run_failed(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={},
        scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    )
    orchestrator.scenario2_runner = FailingScenario2Runner(
        RuntimeError("runner failed")
    )
    orchestrator.legal_corpus_tool = FakeLegalCorpusTool()

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "failed"
    assert result.error_code == SCENARIO2_RUNTIME_ERROR

    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    assert run.status == "failed"
    assert run.error_code == SCENARIO2_RUNTIME_ERROR

    manifest = json.loads(
        (Path(run.artifacts_root_path) / "run.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] == "failed"
    stages = manifest.get("stages", {})
    assert isinstance(stages, dict)
    assert stages["llm"]["status"] == "failed"
    assert stages["finalize"]["status"] == "failed"
    assert manifest["error_code"] == SCENARIO2_RUNTIME_ERROR


def test_full_pipeline_scenario_2_runner_failure_preserves_partial_trace(
    tmp_path: Path, monkeypatch: Any
) -> None:
    legal_tool = EmptyFragmentsLegalCorpusTool()
    responses_service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "kaucja",
                                "scope": "mixed",
                                "return_level": "fragment",
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "fetch_fragments",
                        "arguments": json.dumps(
                            {
                                "refs": [
                                    {
                                        "doc_uid": "doc-1",
                                        "source_hash": "sha256:doc-1",
                                        "unit_id": "fragment:0:10",
                                    }
                                ]
                            }
                        ),
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "ungrounded final response",
                            }
                        ],
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "still ungrounded final response",
                            }
                        ],
                    }
                ]
            },
        ]
    )
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={},
        scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    )
    orchestrator.scenario2_runner = OpenAIScenario2Runner(
        responses_service=responses_service,
        max_tool_rounds=6,
    )
    orchestrator.legal_corpus_tool = legal_tool

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "failed"
    assert result.error_code == SCENARIO2_RUNTIME_ERROR
    assert "not source-grounded" in result.error_message

    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    manifest = json.loads(
        (Path(run.artifacts_root_path) / "run.json").read_text(encoding="utf-8")
    )
    trace_path = manifest.get("artifacts", {}).get("llm", {}).get("trace_path")
    assert trace_path is not None
    trace_payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))

    assert trace_payload["runner_mode"] == SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP
    assert trace_payload["llm_executed"] is True
    assert trace_payload["final_text"] == "still ungrounded final response"
    assert "tool_call:search" in trace_payload["steps"]
    assert "tool_call:fetch_fragments" in trace_payload["steps"]
    assert "fragment_grounding_repair_requested" in trace_payload["steps"]
    assert trace_payload["steps"][-1] == "scenario2_runner_failed"
    assert [item["tool"] for item in trace_payload["tool_trace"]] == [
        "search",
        "fetch_fragments",
    ]
    assert trace_payload["diagnostics"]["tool_usage_counts"] == {
        "search": 1,
        "fetch_fragments": 1,
        "expand_related": 0,
        "get_provenance": 0,
    }
    assert trace_payload["diagnostics"]["fragment_grounding_status"] == (
        "empty_fragments"
    )
    assert trace_payload["diagnostics"]["citation_binding_status"] == (
        "empty_fragments"
    )
    assert trace_payload["diagnostics"]["fetch_fragments_called"] is True
    assert (
        trace_payload["diagnostics"]["fetch_fragments_returned_usable_fragments"]
        is False
    )
    assert trace_payload["diagnostics"]["repair_turn_used"] is True
    assert trace_payload["diagnostics"]["error_code"] == SCENARIO2_RUNTIME_ERROR
    assert "not source-grounded" in trace_payload["diagnostics"]["error_message"]


def test_full_pipeline_scenario_2_trace_persistence_failure_marks_run_failed(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={"openai": SuccessLLMClient(_valid_llm_payload(_load_schema()))},
    )

    def _failing_trace_writer(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise OSError("trace write failed")

    monkeypatch.setattr(
        "app.pipeline.orchestrator._write_scenario2_trace_artifact",
        _failing_trace_writer,
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
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "failed"
    assert result.error_code == SCENARIO2_TRACE_PERSIST_ERROR

    run = orchestrator.repo.get_run(result.run_id)
    assert run is not None
    assert run.status == "failed"
    assert run.error_code == SCENARIO2_TRACE_PERSIST_ERROR

    manifest = json.loads(
        (Path(run.artifacts_root_path) / "run.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] == "failed"
    stages = manifest.get("stages", {})
    assert isinstance(stages, dict)
    assert stages["llm"]["status"] == "failed"
    assert stages["finalize"]["status"] == "failed"
    assert manifest["error_code"] == SCENARIO2_TRACE_PERSIST_ERROR


def test_full_pipeline_scenario_2_success_survives_artifact_write_failures(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={"openai": SuccessLLMClient(_valid_llm_payload(_load_schema()))},
    )

    def _failing_scenario2_writer(
        *,
        path: Path,
        payload: str,
        label: str,
        run_log_path: Path,
    ) -> str | None:
        del path, run_log_path
        if label == "scenario2_validation":
            return "validation persistence blocked"
        return None

    monkeypatch.setattr(
        "app.pipeline.orchestrator._safe_write_text_file",
        _failing_scenario2_writer,
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
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    assert result.error_code == "STORAGE_ERROR"
    assert result.error_message is not None
    assert "validation persistence blocked" in result.error_message


def test_full_pipeline_scenario_2_failure_preserves_code_if_writing_artifacts_fails(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={},
        scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    )

    def _failing_scenario2_writer(
        *,
        path: Path,
        payload: str,
        label: str,
        run_log_path: Path,
    ) -> str | None:
        del path, payload, label, run_log_path
        return "response persistence blocked"

    monkeypatch.setattr(
        "app.pipeline.orchestrator._safe_write_text_file",
        _failing_scenario2_writer,
    )

    orchestrator.scenario2_runner = FailingScenario2Runner(
        RuntimeError("runner failed")
    )
    orchestrator.legal_corpus_tool = FakeLegalCorpusTool()

    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    result = orchestrator.run_full_pipeline(
        input_files=[file_one],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "failed"
    assert result.error_code == SCENARIO2_RUNTIME_ERROR
    assert result.error_message is not None
    assert "response persistence blocked" in result.error_message


def test_full_pipeline_invalid_json_marks_run_failed(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _setup_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        llm_clients={
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
