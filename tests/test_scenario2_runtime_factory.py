from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agentic.legal_corpus_local import LocalLegalCorpusTool
from app.agentic.legal_corpus_mongo import MongoLegalCorpusTool
from app.agentic.openai_scenario2_runner import OpenAIScenario2Runner
from app.agentic.scenario2_runtime_factory import build_scenario2_runtime
from app.config.settings import Settings
from app.ocr_client.types import OCROptions, OCRResult
from app.ops.legal_collection import FetchResponse, build_local_collection
from app.pipeline.orchestrator import OCRPipelineOrchestrator
from app.pipeline.scenario_router import SCENARIO_2_ID, SCENARIO2_CONFIG_ERROR
from app.storage.artifacts import ArtifactsManager
from app.storage.repo import StorageRepo
from tests.fake_mongo_runtime import build_legal_corpus_runtime


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

        combined_path.write_text("scenario2 source markdown", encoding="utf-8")
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


class FakeResponsesService:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if not self.responses:
            raise AssertionError("No more mock responses")
        return self.responses.pop(0)


def _build_collection_root(tmp_path: Path) -> Path:
    input_path = tmp_path / "sources.md"
    input_path.write_text(
        "\n".join(
            [
                "Acts",
                "1. https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.txt",
                "Case law",
                "2. https://www.saos.org.pl/judgments/171957",
            ]
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "legal_collection"
    text_payloads = {
        "https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.txt": (
            "Art. 6. The party alleging damage must prove the damage."
        ),
        "https://www.saos.org.pl/judgments/171957": (
            "Judgment 171957. Deposit should be returned unless the landlord "
            "proves concrete damage and amount."
        ),
    }

    def fetcher(url: str, timeout_seconds: float) -> FetchResponse:
        del timeout_seconds
        body = text_payloads[url].encode("utf-8")
        return FetchResponse(
            url=url,
            status_code=200,
            headers={"Content-Type": "text/plain; charset=utf-8"},
            body=body,
        )

    build_local_collection(
        input_path=input_path,
        output_dir=output_dir,
        fetcher=fetcher,
    )
    return output_dir


def _prepare_scenario2_prompt(tmp_path: Path) -> None:
    prompt_path = tmp_path / "app" / "prompts" / "agent_prompt_V1.1.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text("Scenario2 local runtime prompt", encoding="utf-8")


def test_local_legal_corpus_tool_search_fetch_and_provenance(tmp_path: Path) -> None:
    collection_root = _build_collection_root(tmp_path)
    tool = LocalLegalCorpusTool(root=collection_root)

    search_result = tool.search(
        {
            "query": "landlord proves damage",
            "scope": "mixed",
            "return_level": "fragment",
            "top_k": 2,
        }
    )

    assert search_result["result_count"] == 2
    first_result = search_result["results"][0]
    machine_ref = first_result["machine_ref"]
    assert first_result["metadata"]["scope"] in {"acts", "case_law"}

    fragments_result = tool.fetch_fragments(
        {
            "refs": [machine_ref],
            "include_neighbors": True,
            "neighbor_window": 1,
            "max_chars_per_fragment": 400,
        }
    )
    assert fragments_result["ref_count"] == 1
    assert fragments_result["fragments"][0]["text"]
    assert fragments_result["fragments"][0]["quote_checksum"]

    provenance = tool.get_provenance({"ref": machine_ref, "include_artifacts": True})
    assert provenance["doc_uid"] == machine_ref["doc_uid"]
    assert provenance["artifact_integrity"]["status"] == "ok"
    assert provenance["raw_object_path"]

    related = tool.expand_related(
        {
            "refs": [machine_ref],
            "relation_types": ["cites", "same_case"],
        }
    )
    assert related["results"] == []
    assert related["status"] == "not_available_local"


def test_build_scenario2_runtime_stub_mode_keeps_safe_defaults() -> None:
    settings = Settings(_env_file=None).model_copy(
        update={"scenario2_runner_mode": "stub"}
    )

    runtime = build_scenario2_runtime(settings=settings)

    assert runtime.runner_mode == "stub"
    assert runtime.bootstrap_error is None
    assert runtime.legal_corpus_tool is None


def test_build_scenario2_runtime_openai_mode_builds_real_components(
    tmp_path: Path,
) -> None:
    collection_root = _build_collection_root(tmp_path)
    responses_service = FakeResponsesService(responses=[])
    settings = Settings(_env_file=None).model_copy(
        update={
            "scenario2_runner_mode": "openai_tool_loop",
            "openai_api_key": "openai-key",
            "scenario2_legal_corpus_backend": "local",
            "scenario2_legal_corpus_local_root": collection_root,
        }
    )

    runtime = build_scenario2_runtime(
        settings=settings,
        responses_service=responses_service,
    )

    assert runtime.bootstrap_error is None
    assert isinstance(runtime.runner, OpenAIScenario2Runner)
    assert isinstance(runtime.legal_corpus_tool, LocalLegalCorpusTool)
    assert runtime.case_workspace_store is None


def test_build_scenario2_runtime_mongo_mode_builds_production_components() -> None:
    runtime_fixture = build_legal_corpus_runtime()
    responses_service = FakeResponsesService(responses=[])
    settings = Settings(_env_file=None).model_copy(
        update={
            "scenario2_runner_mode": "openai_tool_loop",
            "openai_api_key": "openai-key",
            "scenario2_legal_corpus_backend": "mongo",
            "scenario2_legal_corpus_mongo_uri": "mongodb://fake",
            "scenario2_legal_corpus_mongo_db": "fake_db",
        }
    )

    runtime = build_scenario2_runtime(
        settings=settings,
        responses_service=responses_service,
        mongo_runtime_factory=lambda _: runtime_fixture,
    )

    assert runtime.bootstrap_error is None
    assert isinstance(runtime.runner, OpenAIScenario2Runner)
    assert isinstance(runtime.legal_corpus_tool, MongoLegalCorpusTool)
    assert runtime.case_workspace_store is not None


def test_build_scenario2_runtime_openai_mode_fails_closed_for_invalid_local_root(
    tmp_path: Path,
) -> None:
    settings = Settings(_env_file=None).model_copy(
        update={
            "scenario2_runner_mode": "openai_tool_loop",
            "openai_api_key": "openai-key",
            "scenario2_legal_corpus_backend": "local",
            "scenario2_legal_corpus_local_root": tmp_path / "missing_collection",
        }
    )

    runtime = build_scenario2_runtime(settings=settings, responses_service=object())

    assert runtime.bootstrap_error is not None
    assert "local legal corpus root not found" in runtime.bootstrap_error


def test_build_scenario2_runtime_mongo_mode_fails_closed_for_bootstrap_error() -> None:
    settings = Settings(_env_file=None).model_copy(
        update={
            "scenario2_runner_mode": "openai_tool_loop",
            "openai_api_key": "openai-key",
            "scenario2_legal_corpus_backend": "mongo",
        }
    )

    runtime = build_scenario2_runtime(
        settings=settings,
        responses_service=object(),
        mongo_runtime_factory=lambda _: (_ for _ in ()).throw(
            RuntimeError("mongo runtime unavailable")
        ),
    )

    assert runtime.bootstrap_error == "mongo runtime unavailable"
    assert runtime.legal_corpus_tool is None
    assert runtime.case_workspace_store is None


def test_factory_built_real_runtime_completes_scenario2_end_to_end(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    collection_root = _build_collection_root(tmp_path)
    _prepare_scenario2_prompt(tmp_path)
    monkeypatch.chdir(tmp_path)

    responses_service = FakeResponsesService(
        responses=[
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "search",
                        "arguments": json.dumps(
                            {
                                "query": "deposit damage proof",
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
                                        "doc_uid": "saos_pl:171957",
                                        "unit_id": "fragment:0:120",
                                        "locator": {
                                            "start_char": 0,
                                            "end_char": 120,
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
                                "text": "Scenario2 local runtime completed.",
                            }
                        ],
                    }
                ]
            },
        ]
    )
    settings = Settings(_env_file=None).model_copy(
        update={
            "scenario2_runner_mode": "openai_tool_loop",
            "openai_api_key": "openai-key",
            "scenario2_legal_corpus_backend": "local",
            "scenario2_legal_corpus_local_root": collection_root,
        }
    )
    runtime = build_scenario2_runtime(
        settings=settings,
        responses_service=responses_service,
    )
    assert runtime.bootstrap_error is None

    artifacts_manager = ArtifactsManager(tmp_path / "data")
    repo = StorageRepo(
        db_path=tmp_path / "kaucja.sqlite3",
        artifacts_manager=artifacts_manager,
    )
    orchestrator = OCRPipelineOrchestrator(
        repo=repo,
        artifacts_manager=artifacts_manager,
        ocr_client=FakeOCRClient(),
        llm_clients={},
        prompt_root=tmp_path,
        scenario2_runner=runtime.runner,
        legal_corpus_tool=runtime.legal_corpus_tool,
        scenario2_runner_mode=settings.scenario2_runner_mode,
        scenario2_bootstrap_error=runtime.bootstrap_error,
    )

    input_file = tmp_path / "lease.pdf"
    input_file.write_bytes(b"pdf")
    result = orchestrator.run_full_pipeline(
        input_files=[input_file],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    assert result.raw_json_text == "Scenario2 local runtime completed."

    run = repo.get_run(result.run_id)
    assert run is not None
    manifest = json.loads((Path(run.artifacts_root_path) / "run.json").read_text())
    assert manifest["stages"]["llm"]["status"] == "completed"
    assert manifest["artifacts"]["llm"]["runner_mode"] == "openai_tool_loop"
    trace_payload = json.loads(
        Path(manifest["artifacts"]["llm"]["trace_path"]).read_text(encoding="utf-8")
    )
    assert trace_payload["tool_trace"][0]["tool"] == "search"
    assert trace_payload["tool_trace"][1]["tool"] == "fetch_fragments"
    assert trace_payload["diagnostics"]["tool_usage_counts"] == {
        "search": 1,
        "fetch_fragments": 1,
        "expand_related": 0,
        "get_provenance": 0,
    }
    assert (
        trace_payload["diagnostics"]["fragment_grounding_status"] == "fragments_fetched"
    )
    assert trace_payload["diagnostics"]["citation_binding_status"] == (
        "fragments_fetched"
    )
    assert trace_payload["diagnostics"]["fetch_fragments_called"] is True
    assert (
        trace_payload["diagnostics"]["fetch_fragments_returned_usable_fragments"]
        is True
    )
    assert trace_payload["diagnostics"]["successful_fetch_fragments"] is True
    assert trace_payload["diagnostics"]["repair_turn_used"] is False
    assert trace_payload["diagnostics"]["fetched_fragment_doc_uids"] == [
        "saos_pl:171957"
    ]
    assert trace_payload["diagnostics"]["fetched_fragment_source_hashes"]
    assert trace_payload["diagnostics"]["fetched_fragment_refs"]
    assert trace_payload["diagnostics"]["fetched_fragment_ledger"]
    assert trace_payload["diagnostics"]["fetched_fragment_quote_checksums"]
    assert trace_payload["diagnostics"]["fetched_fragment_ledger"][0]["text_excerpt"]
    assert trace_payload["diagnostics"]["fetched_fragment_ledger"][0]["locator"]
    assert trace_payload["diagnostics"]["verifier_status"] in {"passed", "warning"}
    assert trace_payload["diagnostics"]["citation_format_status"] in {
        "passed",
        "warning",
        "not_applicable",
    }


def test_factory_built_mongo_runtime_completes_scenario2_end_to_end(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    runtime_fixture = build_legal_corpus_runtime()
    _prepare_scenario2_prompt(tmp_path)
    monkeypatch.chdir(tmp_path)

    final_text = "\n".join(
        [
            "Краткий вывод",
            "Кауция подлежит возврату, если удержания не доказаны.",
            "",
            "Что подтверждено документами",
            "Суд требует доказать ущерб и задолженность [Практика: Sad Okregowy w Sieradzu, II CA 886/14].",
            "",
            "Что спорно или не доказано",
            "Размер удержаний надо подтвердить отдельными расчетами.",
            "",
            "Применимые нормы и практика",
            "Применима норма о возврате кауции после выезда [Норма: Ustawa o ochronie praw lokatorow [eli_pl:DU/2001/733]].",
            "",
            "Анализ по вопросам",
            "Удержание за коммунальные и повреждения допустимо только при доказанности [Практика: Sad Okregowy w Sieradzu, II CA 886/14].",
            "",
            "Что делать дальше",
            "Запросить расчет и доказательства ущерба.",
            "",
            "Источники",
            "- [Норма: Ustawa o ochronie praw lokatorow [eli_pl:DU/2001/733]]",
            "- [Практика: Sad Okregowy w Sieradzu, II CA 886/14]",
        ]
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
                                "query": "niewozwrot kaucji uszkodzenia komunalne po wyjezdzie",
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
                                        "doc_uid": "saos_pl:171957",
                                        "source_hash": "sha256:case-current",
                                        "unit_id": "unit:saos_pl:171957:sha256:case-current:holding:1",
                                        "node_id": "holding:1",
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
                                "text": final_text,
                            }
                        ],
                    }
                ]
            },
        ]
    )
    settings = Settings(_env_file=None).model_copy(
        update={
            "scenario2_runner_mode": "openai_tool_loop",
            "openai_api_key": "openai-key",
            "scenario2_legal_corpus_backend": "mongo",
            "scenario2_legal_corpus_mongo_uri": "mongodb://fake",
            "scenario2_legal_corpus_mongo_db": "fake_db",
        }
    )
    runtime = build_scenario2_runtime(
        settings=settings,
        responses_service=responses_service,
        mongo_runtime_factory=lambda _: runtime_fixture,
    )
    assert runtime.bootstrap_error is None

    artifacts_manager = ArtifactsManager(tmp_path / "data")
    repo = StorageRepo(
        db_path=tmp_path / "kaucja.sqlite3",
        artifacts_manager=artifacts_manager,
    )
    orchestrator = OCRPipelineOrchestrator(
        repo=repo,
        artifacts_manager=artifacts_manager,
        ocr_client=FakeOCRClient(),
        llm_clients={},
        prompt_root=tmp_path,
        scenario2_runner=runtime.runner,
        legal_corpus_tool=runtime.legal_corpus_tool,
        scenario2_case_workspace_store=runtime.case_workspace_store,
        scenario2_runner_mode=settings.scenario2_runner_mode,
        scenario2_bootstrap_error=runtime.bootstrap_error,
    )

    input_file = tmp_path / "lease.pdf"
    input_file.write_bytes(b"pdf")
    result = orchestrator.run_full_pipeline(
        input_files=[input_file],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    assert result.raw_json_text == final_text
    assert runtime_fixture.load_collection("analysis_runs")[0]["status"] == "completed"
    assert runtime_fixture.load_collection("case_workspaces")
    assert runtime_fixture.load_collection("case_documents")
    run = repo.get_run(result.run_id)
    assert run is not None
    manifest = json.loads((Path(run.artifacts_root_path) / "run.json").read_text())
    trace_payload = json.loads(
        Path(manifest["artifacts"]["llm"]["trace_path"]).read_text(encoding="utf-8")
    )
    assert trace_payload["tool_trace"][0]["audit"]["request_id"]
    assert trace_payload["tool_trace"][0]["audit"]["tool_call_id"]
    assert trace_payload["tool_trace"][0]["audit"]["request_hash"]
    assert trace_payload["tool_trace"][0]["audit"]["query_hash"]
    assert trace_payload["tool_trace"][1]["audit"]["returned_ref_count"] >= 1


def test_real_runtime_with_bootstrap_error_fails_closed_on_direct_scenario2_run(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _prepare_scenario2_prompt(tmp_path)
    monkeypatch.chdir(tmp_path)

    artifacts_manager = ArtifactsManager(tmp_path / "data")
    repo = StorageRepo(
        db_path=tmp_path / "kaucja.sqlite3",
        artifacts_manager=artifacts_manager,
    )
    orchestrator = OCRPipelineOrchestrator(
        repo=repo,
        artifacts_manager=artifacts_manager,
        ocr_client=FakeOCRClient(),
        llm_clients={},
        prompt_root=tmp_path,
        scenario2_runner_mode="openai_tool_loop",
        scenario2_bootstrap_error="Scenario 2 local legal corpus root not found.",
    )

    input_file = tmp_path / "lease.pdf"
    input_file.write_bytes(b"pdf")
    result = orchestrator.run_full_pipeline(
        input_files=[input_file],
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
    assert "local legal corpus root not found" in str(result.error_message)
