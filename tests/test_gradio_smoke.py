from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import gradio as gr
import pytest

import app.ui.gradio_app as gradio_app_module
from app.agentic.case_workspace_store import (
    MongoCaseWorkspaceStore,
    Scenario2CaseMetadata,
)
from app.agentic.scenario2_verifier import (
    build_scenario2_review_payload,
    build_scenario2_verifier_gate_payload,
)
from app.ocr_client.types import OCRResult
from app.pipeline.orchestrator import (
    FullPipelineResult,
    OCRDocumentStageResult,
    OCRPipelineOrchestrator,
)
from app.pipeline.scenario_router import (
    SCENARIO_2_ID,
    SCENARIO_2_PLACEHOLDER,
    SCENARIO_2_VALIDATION_MESSAGE,
    SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
    SCENARIO2_RUNNER_MODE_STUB,
    SCENARIO2_RUNTIME_ERROR,
)
from app.prompts.manager import PromptManager
from app.storage.artifacts import ArtifactsManager
from app.storage.models import RestoreRunResult
from app.storage.run_manifest import init_run_manifest, update_run_manifest
from app.storage.repo import StorageRepo
from app.storage.zip_export import ZipExportError
from app.ui.gradio_app import (
    build_app,
    compare_history_runs,
    _scenario2_case_block_update,
    _scenario_config_mode_updates,
    delete_history_run,
    export_history_run_bundle,
    list_history_rows,
    load_history_run,
    refresh_history_for_ui,
    render_details_from_state,
    restore_history_run_bundle,
    run_full_pipeline as run_full_pipeline_ui,
    save_prompt_as_new_version_for_ui,
)
from tests.fake_mongo_runtime import FakeMongoRuntime


def _sample_parsed_payload() -> dict[str, Any]:
    return {
        "checklist": [
            {
                "item_id": "deposit_transfer",
                "importance": "critical",
                "status": "missing",
                "confidence": "medium",
                "what_it_supports": "payment proof",
                "missing_what_exactly": "receipt",
                "request_from_user": {
                    "type": "upload_document",
                    "ask": "Upload transfer receipt",
                    "examples": ["bank statement"],
                },
                "findings": [],
            }
        ],
        "critical_gaps_summary": ["Missing deposit transfer receipt"],
        "next_questions_to_user": ["Please upload transfer receipt."],
    }


def _comparison_payload(
    *, status: str, ask: str, gap: str, question: str
) -> dict[str, Any]:
    return {
        "checklist": [
            {
                "item_id": "KAUCJA_PAYMENT_PROOF",
                "importance": "critical",
                "status": status,
                "confidence": "medium",
                "what_it_supports": "proof",
                "missing_what_exactly": "receipt",
                "request_from_user": {
                    "type": "upload_document",
                    "ask": ask,
                    "examples": ["bank transfer confirmation"],
                },
                "findings": [
                    {
                        "doc_id": "0000001",
                        "quote": "proof quote",
                        "why_this_quote_matters": "matters",
                    }
                ],
            }
        ],
        "critical_gaps_summary": [gap],
        "next_questions_to_user": [question],
    }


def _scenario2_fragment_ledger_entry() -> dict[str, Any]:
    return {
        "ref": {
            "doc_uid": "doc-1",
            "source_hash": "sha256:doc-1",
            "unit_id": "fragment:0:32",
            "locator": {"start_char": 0, "end_char": 32},
        },
        "doc_uid": "doc-1",
        "source_hash": "sha256:doc-1",
        "display_citation": "Art. 6 KC",
        "text_excerpt": "Najemca powinien wykazac zasadnosc potracen i szkody.",
        "locator": {"start_char": 0, "end_char": 32},
        "locator_precision": "char_offsets_only",
        "page_truth_status": "not_available_local",
        "quote_checksum": "sha256:frag-1",
    }


def _scenario2_review_manifest_update(
    *,
    verifier_status: str,
    verifier_warnings: list[str],
) -> dict[str, Any]:
    review_payload = build_scenario2_review_payload(
        verifier_status=verifier_status,
        verifier_warnings=verifier_warnings,
    )
    return {
        "review_status": review_payload["status"],
        "review": review_payload,
    }


def _scenario2_verifier_gate_manifest_update(
    *,
    verifier_policy: str,
    verifier_status: str,
    llm_executed: bool,
    verifier_warnings: list[str],
) -> dict[str, Any]:
    gate_payload = build_scenario2_verifier_gate_payload(
        verifier_policy=verifier_policy,
        verifier_status=verifier_status,
        llm_executed=llm_executed,
        verifier_warnings=verifier_warnings,
    )
    return {
        "verifier_policy": gate_payload["policy"],
        "verifier_gate_status": gate_payload["status"],
        "verifier_gate": gate_payload,
    }


class FakeOrchestrator:
    def __init__(
        self,
        *,
        scenario2_runner_mode: str = SCENARIO2_RUNNER_MODE_STUB,
        scenario2_verifier_policy: str = "informational",
        scenario2_runner: object | None = None,
        legal_corpus_tool: object | None = None,
        scenario2_bootstrap_error: str | None = None,
    ) -> None:
        self.last_kwargs: dict[str, object] = {}
        self.scenario2_runner_mode = scenario2_runner_mode
        self.scenario2_verifier_policy = scenario2_verifier_policy
        self.scenario2_runner = scenario2_runner
        self.legal_corpus_tool = legal_corpus_tool
        self.scenario2_bootstrap_error = scenario2_bootstrap_error

    def run_full_pipeline(self, **kwargs: object) -> FullPipelineResult:
        self.last_kwargs = kwargs
        input_files = kwargs["input_files"]
        assert len(input_files) == 2
        payload = _sample_parsed_payload()
        scenario_id = str(kwargs.get("scenario_id") or "scenario_1")
        if scenario_id == SCENARIO_2_ID:
            return FullPipelineResult(
                session_id="session-1",
                run_id="run-1",
                run_status="completed",
                documents=[
                    OCRDocumentStageResult(
                        doc_id="0000001",
                        ocr_status="ok",
                        pages_count=2,
                        combined_markdown_path="/tmp/doc-1/combined.md",
                        ocr_artifacts_path="/tmp/doc-1/ocr",
                        ocr_error=None,
                    )
                ],
                critical_gaps_summary=[],
                next_questions_to_user=[],
                raw_json_text=SCENARIO_2_PLACEHOLDER,
                parsed_json=None,
                validation_valid=True,
                validation_errors=[],
                metrics={"usage": {"total_tokens": 10}},
                error_code=None,
                error_message=None,
                scenario_id=scenario_id,
            )

        return FullPipelineResult(
            session_id="session-1",
            run_id="run-1",
            run_status="completed",
            documents=[
                OCRDocumentStageResult(
                    doc_id="0000001",
                    ocr_status="ok",
                    pages_count=2,
                    combined_markdown_path="/tmp/doc-1/combined.md",
                    ocr_artifacts_path="/tmp/doc-1/ocr",
                    ocr_error=None,
                ),
                OCRDocumentStageResult(
                    doc_id="0000002",
                    ocr_status="ok",
                    pages_count=3,
                    combined_markdown_path="/tmp/doc-2/combined.md",
                    ocr_artifacts_path="/tmp/doc-2/ocr",
                    ocr_error=None,
                ),
            ],
            critical_gaps_summary=["Missing deposit transfer receipt"],
            next_questions_to_user=["Please upload transfer receipt."],
            raw_json_text=json.dumps(payload),
            parsed_json=payload,
            validation_valid=True,
            validation_errors=[],
            metrics={"usage": {"total_tokens": 10}},
            error_code=None,
            error_message=None,
            scenario_id=scenario_id,
        )


class FakeScenario2OCRClient:
    def process_document(
        self,
        *,
        input_path: Path,
        doc_id: str,
        options: Any,
        output_dir: Path,
    ) -> OCRResult:
        del input_path, options
        output_dir.mkdir(parents=True, exist_ok=True)
        combined_path = output_dir / "combined.md"
        raw_response_path = output_dir / "raw_response.json"
        quality_path = output_dir / "quality.json"
        combined_path.write_text("scenario2 markdown", encoding="utf-8")
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


def _create_prompt_version(
    *,
    root: Path,
    prompt_name: str,
    version: str,
    prompt_text: str,
    schema_text: str,
) -> None:
    target = root / prompt_name / version
    target.mkdir(parents=True, exist_ok=True)
    (target / "system_prompt.txt").write_text(prompt_text, encoding="utf-8")
    (target / "schema.json").write_text(schema_text, encoding="utf-8")
    (target / "meta.yaml").write_text(
        "created_at: 2026-02-25T00:00:00+00:00\n", encoding="utf-8"
    )


def _seed_history_run_for_compare(
    *,
    repo: StorageRepo,
    session_id: str,
    provider: str,
    model: str,
    prompt_version: str,
    payload: dict[str, Any],
    tokens: int,
    total_cost: float,
    total_time_ms: float,
) -> str:
    run = repo.create_run(
        session_id=session_id,
        provider=provider,
        model=model,
        prompt_name="kaucja_gap_analysis",
        prompt_version=prompt_version,
        schema_version=prompt_version,
        status="running",
    )

    run_root = Path(run.artifacts_root_path)
    doc_ocr_dir = run_root / "documents" / "0000001" / "ocr"
    doc_ocr_dir.mkdir(parents=True, exist_ok=True)
    original_dir = run_root / "documents" / "0000001" / "original"
    original_dir.mkdir(parents=True, exist_ok=True)
    original_file = original_dir / "contract.pdf"
    original_file.write_bytes(b"%PDF-1.4 fake")
    llm_dir = run_root / "llm"
    llm_dir.mkdir(parents=True, exist_ok=True)
    parsed_path = llm_dir / "response_parsed.json"
    parsed_path.write_text(json.dumps(payload), encoding="utf-8")
    (llm_dir / "response_raw.txt").write_text(json.dumps(payload), encoding="utf-8")
    (llm_dir / "validation.json").write_text(
        json.dumps({"valid": True, "schema_errors": [], "invariant_errors": []}),
        encoding="utf-8",
    )
    (doc_ocr_dir / "combined.md").write_text("doc-combined", encoding="utf-8")
    (doc_ocr_dir / "raw_response.json").write_text("{}", encoding="utf-8")
    (run_root / "logs" / "run.log").write_text("run log line\n", encoding="utf-8")

    (run_root / "run.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "run_id": run.run_id,
                "status": "completed",
                "inputs": {
                    "provider": provider,
                    "model": model,
                    "prompt_name": "kaucja_gap_analysis",
                    "prompt_version": prompt_version,
                    "schema_version": prompt_version,
                    "ocr_params": {"model": "mistral-ocr-latest"},
                    "llm_params": {"openai_reasoning_effort": "auto"},
                },
                "artifacts": {
                    "root": str(run_root),
                    "run_log": str(run_root / "logs" / "run.log"),
                    "documents": [
                        {
                            "doc_id": "0000001",
                            "ocr_status": "ok",
                            "pages_count": 1,
                            "combined_markdown_path": str(doc_ocr_dir / "combined.md"),
                            "ocr_artifacts_path": str(doc_ocr_dir),
                            "ocr_error": None,
                        }
                    ],
                    "llm": {
                        "response_parsed_path": str(parsed_path),
                        "response_raw_path": str(llm_dir / "response_raw.txt"),
                        "validation_path": str(llm_dir / "validation.json"),
                    },
                },
                "metrics": {
                    "timings": {"t_total_ms": total_time_ms},
                    "usage": {"input_tokens": max(tokens // 2, 1)},
                    "usage_normalized": {"total_tokens": tokens},
                    "cost": {"total_cost_usd": total_cost},
                },
                "validation": {"valid": True, "errors": []},
                "created_at": "2026-02-25T00:00:00+00:00",
                "updated_at": "2026-02-25T00:00:00+00:00",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    repo.upsert_llm_output(
        run_id=run.run_id,
        response_json_path=str(parsed_path),
        response_valid=True,
        schema_validation_errors_path=None,
    )
    repo.update_run_metrics(
        run_id=run.run_id,
        timings_json={"t_total_ms": total_time_ms},
        usage_json={"input_tokens": max(tokens // 2, 1)},
        usage_normalized_json={"total_tokens": tokens},
        cost_json={"total_cost_usd": total_cost},
    )
    repo.update_run_status(run_id=run.run_id, status="completed")
    return run.run_id


def _seed_history_run_scenario_2(
    *,
    repo: StorageRepo,
    session_id: str,
) -> str:
    run = repo.create_run(
        session_id=session_id,
        provider="openai",
        model="gpt-5.4",
        prompt_name="agent_prompt_foundation",
        prompt_version="v1.1",
        schema_version="v1.1",
        status="running",
    )

    run_root = Path(run.artifacts_root_path)
    doc_ocr_dir = run_root / "documents" / "0000001" / "ocr"
    doc_ocr_dir.mkdir(parents=True, exist_ok=True)
    original_dir = run_root / "documents" / "0000001" / "original"
    original_dir.mkdir(parents=True, exist_ok=True)
    original_file = original_dir / "contract.pdf"
    original_file.write_bytes(b"%PDF-1.4 fake")
    llm_dir = run_root / "llm"
    llm_dir.mkdir(parents=True, exist_ok=True)
    (run_root / "logs").mkdir(parents=True, exist_ok=True)
    (doc_ocr_dir / "combined.md").write_text("doc-combined", encoding="utf-8")
    (llm_dir / "response_parsed.json").write_text(
        json.dumps({"placeholder": True}), encoding="utf-8"
    )
    (llm_dir / "response_raw.txt").write_text(SCENARIO_2_PLACEHOLDER, encoding="utf-8")
    (llm_dir / "validation.json").write_text(
        json.dumps(
            {
                "status": "not_applicable",
                "errors": [SCENARIO_2_VALIDATION_MESSAGE],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    scenario2_trace_path = llm_dir / "scenario2_trace.json"
    scenario2_trace_path.write_text(
        json.dumps(
            {
                "response_mode": "plain_text",
                "final_text": SCENARIO_2_PLACEHOLDER,
                "steps": ["ocr_complete", "scenario2_stub_response"],
                "tool_trace": [
                    {
                        "tool": "scenario2_stub",
                        "status": "ok",
                    }
                ],
                "diagnostics": {
                    "fragment_grounding_status": "not_applicable",
                    "citation_binding_status": "not_applicable",
                    "verifier_status": "not_applicable",
                    "verifier_policy": "informational",
                    "verifier_gate_status": "not_applicable",
                    "citation_format_status": "not_applicable",
                    "fetch_fragments_called": False,
                    "fetch_fragments_returned_usable_fragments": False,
                    "repair_turn_used": False,
                    "legal_citation_count": 0,
                    "user_doc_citation_count": 0,
                    "citations_in_analysis_sections": None,
                    "missing_sections": [],
                    "sources_section_present": None,
                    "fetched_sources_referenced": None,
                    "verifier_warnings": [],
                    "malformed_citation_warnings": [],
                    "fetched_fragment_ledger": [],
                    "fetched_fragment_citations": [],
                    "fetched_fragment_doc_uids": [],
                    "fetched_fragment_source_hashes": [],
                    "fetched_fragment_quote_checksums": [],
                },
                "runner_mode": SCENARIO2_RUNNER_MODE_STUB,
                "llm_executed": False,
                "tool_round_count": 0,
                "model": "gpt-5.4",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_root / "logs" / "run.log").write_text("line1\nline2\n", encoding="utf-8")

    repo.create_document(
        run_id=run.run_id,
        doc_id="0000001",
        original_filename="contract.pdf",
        original_mime="application/pdf",
        original_path=str(original_file),
        ocr_status="ok",
        pages_count=1,
        ocr_artifacts_path=str(doc_ocr_dir),
    )
    repo.upsert_llm_output(
        run_id=run.run_id,
        response_json_path=str((llm_dir / "response_parsed.json").resolve()),
        response_valid=True,
        schema_validation_errors_path=str((llm_dir / "validation.json").resolve()),
    )
    repo.update_run_metrics(
        run_id=run.run_id,
        timings_json={"t_total_ms": 33.0},
        usage_json={"input_tokens": 1},
        usage_normalized_json={"total_tokens": 1},
        cost_json={"total_cost_usd": 0.001},
    )
    init_run_manifest(
        artifacts_root_path=run.artifacts_root_path,
        session_id=session_id,
        run_id=run.run_id,
        inputs={
            "scenario_id": SCENARIO_2_ID,
            "provider": "openai",
            "model": "gpt-5.4",
            "prompt_name": "agent_prompt_foundation",
            "prompt_version": "v1.1",
            "schema_version": "v1.1",
            "ocr_params": {"model": "mistral-ocr-latest"},
            "llm_params": {},
        },
        artifacts={
            "root": str(run_root),
            "run_log": str(run_root / "logs" / "run.log"),
            "documents": [
                {
                    "doc_id": "0000001",
                    "ocr_status": "ok",
                    "pages_count": 1,
                    "combined_markdown_path": str(doc_ocr_dir / "combined.md"),
                    "ocr_artifacts_path": str(doc_ocr_dir),
                    "ocr_error": None,
                }
            ],
            "llm": {
                "response_parsed_path": str(
                    (llm_dir / "response_parsed.json").resolve()
                ),
                "response_raw_path": str((llm_dir / "response_raw.txt").resolve()),
                "validation_path": str((llm_dir / "validation.json").resolve()),
                "trace_path": str(scenario2_trace_path.resolve()),
                "runner_mode": SCENARIO2_RUNNER_MODE_STUB,
                "llm_executed": False,
            },
        },
        status="completed",
    )
    update_run_manifest(
        artifacts_root_path=run.artifacts_root_path,
        updates={
            "status": "completed",
            "stages": {
                "ocr": {"status": "completed"},
                "llm": {"status": "skipped"},
                "finalize": {"status": "completed"},
            },
            "validation": {
                "status": "not_applicable",
                "errors": [SCENARIO_2_VALIDATION_MESSAGE],
            },
            "metrics": {
                "timings": {"t_total_ms": 33.0},
                "usage": {"input_tokens": 1},
                "usage_normalized": {"total_tokens": 1},
                "cost": {"total_cost_usd": 0.001},
            },
            **_scenario2_review_manifest_update(
                verifier_status="not_applicable",
                verifier_warnings=[],
            ),
            **_scenario2_verifier_gate_manifest_update(
                verifier_policy="informational",
                verifier_status="not_applicable",
                llm_executed=False,
                verifier_warnings=[],
            ),
        },
    )
    repo.update_run_status(run_id=run.run_id, status="completed")
    return run.run_id


def _seed_history_run_scenario_2_real_with_fragments(
    *,
    repo: StorageRepo,
    session_id: str,
) -> str:
    run_id = _seed_history_run_scenario_2(repo=repo, session_id=session_id)
    run = repo.get_run(run_id)
    assert run is not None

    run_root = Path(run.artifacts_root_path)
    llm_dir = run_root / "llm"
    scenario2_trace_path = llm_dir / "scenario2_trace.json"
    fragment_entry = _scenario2_fragment_ledger_entry()
    scenario2_trace_path.write_text(
        json.dumps(
            {
                "response_mode": "plain_text",
                "final_text": "Grounded Scenario 2 answer",
                "steps": [
                    "scenario2_openai_start",
                    "openai_request",
                    "tool_call:search",
                    "openai_request",
                    "tool_call:fetch_fragments",
                    "openai_final_response",
                ],
                "tool_trace": [
                    {"tool": "search", "status": "ok"},
                    {"tool": "fetch_fragments", "status": "ok"},
                ],
                "diagnostics": {
                    "fragment_grounding_status": "fragments_fetched",
                    "citation_binding_status": "fragments_fetched",
                    "verifier_status": "passed",
                    "verifier_policy": "informational",
                    "verifier_gate_status": "passed",
                    "citation_format_status": "passed",
                    "fetch_fragments_called": True,
                    "fetch_fragments_returned_usable_fragments": True,
                    "repair_turn_used": False,
                    "legal_citation_count": 2,
                    "user_doc_citation_count": 1,
                    "citations_in_analysis_sections": True,
                    "missing_sections": [],
                    "sources_section_present": True,
                    "fetched_sources_referenced": True,
                    "verifier_warnings": [],
                    "malformed_citation_warnings": [],
                    "fetched_fragment_ledger": [fragment_entry],
                    "fetched_fragment_citations": ["Art. 6 KC"],
                    "fetched_fragment_doc_uids": ["doc-1"],
                    "fetched_fragment_source_hashes": ["sha256:doc-1"],
                    "fetched_fragment_quote_checksums": ["sha256:frag-1"],
                },
                "runner_mode": SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
                "llm_executed": True,
                "tool_round_count": 2,
                "model": "gpt-5.4",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (llm_dir / "response_raw.txt").write_text(
        "Grounded Scenario 2 answer",
        encoding="utf-8",
    )
    update_run_manifest(
        artifacts_root_path=run.artifacts_root_path,
        updates={
            "status": "completed",
            "stages": {
                "ocr": {"status": "completed"},
                "llm": {"status": "completed"},
                "finalize": {"status": "completed"},
            },
            "artifacts": {
                "llm": {
                    "trace_path": str(scenario2_trace_path.resolve()),
                    "runner_mode": SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
                    "llm_executed": True,
                }
            },
            **_scenario2_review_manifest_update(
                verifier_status="passed",
                verifier_warnings=[],
            ),
            **_scenario2_verifier_gate_manifest_update(
                verifier_policy="informational",
                verifier_status="passed",
                llm_executed=True,
                verifier_warnings=[],
            ),
        },
    )
    repo.update_run_status(run_id=run_id, status="completed")
    return run_id


def _seed_history_run_scenario_2_failure(
    *,
    repo: StorageRepo,
    session_id: str,
) -> str:
    run_id = _seed_history_run_scenario_2(repo=repo, session_id=session_id)
    run = repo.get_run(run_id)
    assert run is not None

    run_root = Path(run.artifacts_root_path)
    llm_dir = run_root / "llm"
    scenario2_trace_path = llm_dir / "scenario2_trace.json"
    scenario2_trace_path.write_text(
        json.dumps(
            {
                "response_mode": "plain_text",
                "final_text": "still ungrounded final response",
                "steps": [
                    "scenario2_openai_start",
                    "openai_request",
                    "tool_call:search",
                    "openai_request",
                    "tool_call:fetch_fragments",
                    "openai_request",
                    "fragment_grounding_repair_requested",
                    "openai_request",
                    "scenario2_runner_failed",
                ],
                "tool_trace": [
                    {"tool": "search", "status": "ok"},
                    {"tool": "fetch_fragments", "status": "ok"},
                ],
                "diagnostics": {
                    "stage": "runner",
                    "error_code": SCENARIO2_RUNTIME_ERROR,
                    "error_message": "Scenario 2 final answer is not source-grounded",
                    "tool_usage_counts": {
                        "search": 1,
                        "fetch_fragments": 1,
                        "expand_related": 0,
                        "get_provenance": 0,
                    },
                    "fragment_grounding_status": "empty_fragments",
                    "citation_binding_status": "empty_fragments",
                    "verifier_status": "warning",
                    "verifier_policy": "informational",
                    "verifier_gate_status": "warning_not_blocking",
                    "citation_format_status": "warning",
                    "fetch_fragments_called": True,
                    "fetch_fragments_returned_usable_fragments": False,
                    "repair_turn_used": True,
                    "legal_citation_count": 0,
                    "user_doc_citation_count": 0,
                    "citations_in_analysis_sections": False,
                    "missing_sections": [
                        "Краткий вывод",
                        "Что подтверждено документами",
                        "Что спорно или не доказано",
                        "Применимые нормы и практика",
                        "Анализ по вопросам",
                        "Что делать дальше",
                        "Источники",
                    ],
                    "sources_section_present": False,
                    "fetched_sources_referenced": False,
                    "verifier_warnings": [
                        "Missing required sections: Краткий вывод, Что подтверждено документами, Что спорно или не доказано, Применимые нормы и практика, Анализ по вопросам, Что делать дальше, Источники",
                        "Sources section is missing.",
                        "No legal inline citations found in the final text.",
                        "Legal citations are missing from analysis sections.",
                    ],
                    "malformed_citation_warnings": [],
                    "fetched_fragment_ledger": [],
                    "fetched_fragment_citations": [],
                    "fetched_fragment_doc_uids": [],
                    "fetched_fragment_source_hashes": [],
                    "fetched_fragment_quote_checksums": [],
                },
                "runner_mode": SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
                "llm_executed": True,
                "tool_round_count": 2,
                "model": "gpt-5.4",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (llm_dir / "response_raw.txt").write_text(
        "Scenario 2 final answer is not source-grounded",
        encoding="utf-8",
    )
    (llm_dir / "validation.json").write_text(
        json.dumps(
            {
                "status": "failed",
                "errors": ["Scenario 2 final answer is not source-grounded"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    update_run_manifest(
        artifacts_root_path=run.artifacts_root_path,
        updates={
            "status": "failed",
            "stages": {
                "ocr": {"status": "completed"},
                "llm": {"status": "failed"},
                "finalize": {"status": "failed"},
            },
            "validation": {
                "status": "failed",
                "errors": ["Scenario 2 final answer is not source-grounded"],
            },
            "artifacts": {
                "llm": {
                    "trace_path": str(scenario2_trace_path.resolve()),
                    "runner_mode": SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
                    "llm_executed": True,
                }
            },
            "error_code": SCENARIO2_RUNTIME_ERROR,
            "error_message": "Scenario 2 final answer is not source-grounded",
            **_scenario2_review_manifest_update(
                verifier_status="warning",
                verifier_warnings=[
                    "Missing required sections: Краткий вывод, Что подтверждено документами, Что спорно или не доказано, Применимые нормы и практика, Анализ по вопросам, Что делать дальше, Источники",
                    "Sources section is missing.",
                    "No legal inline citations found in the final text.",
                    "Legal citations are missing from analysis sections.",
                ],
            ),
            **_scenario2_verifier_gate_manifest_update(
                verifier_policy="informational",
                verifier_status="warning",
                llm_executed=True,
                verifier_warnings=[
                    "Missing required sections: Краткий вывод, Что подтверждено документами, Что спорно или не доказано, Применимые нормы и практика, Анализ по вопросам, Что делать дальше, Источники",
                    "Sources section is missing.",
                    "No legal inline citations found in the final text.",
                    "Legal citations are missing from analysis sections.",
                ],
            ),
        },
    )
    repo.update_run_status(
        run_id=run_id,
        status="failed",
        error_code=SCENARIO2_RUNTIME_ERROR,
        error_message="Scenario 2 final answer is not source-grounded",
    )
    return run_id


def test_build_app_returns_blocks(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")

    app = build_app(
        repo=repo,
        orchestrator=FakeOrchestrator(),
        preflight_checker=lambda provider: None,
    )

    assert isinstance(app, gr.Blocks)
    component_labels = [
        item.get("props", {}).get("label")
        for item in app.config.get("components", [])
        if isinstance(item, dict)
    ]
    assert any(
        label is not None and "Scenario" in str(label) for label in component_labels
    )
    assert "Scenario 2 Case ID" in component_labels
    assert "Claim Amount" in component_labels
    assert "Currency" in component_labels
    assert "Lease Start" in component_labels
    assert "Lease End" in component_labels
    assert "Move Out Date" in component_labels
    assert "Deposit Return Due Date" in component_labels
    assert "Scenario 2 Diagnostics" in component_labels
    assert "Scenario 2 Fetched Fragments" in component_labels


def test_build_app_passes_scenario2_runner_mode_to_orchestrator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    captured: dict[str, Any] = {}
    runtime_runner = object()
    runtime_tool = object()
    runtime_case_workspace_store = object()

    settings = gradio_app_module.get_settings().model_copy(
        update={
            "mistral_api_key": "mistral-key",
            "openai_api_key": "openai-key",
            "google_api_key": "google-key",
            "scenario2_runner_mode": SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
            "scenario2_verifier_policy": "strict",
        }
    )

    class CapturingOrchestrator(FakeOrchestrator):
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)
            super().__init__(
                scenario2_runner_mode=kwargs.get(
                    "scenario2_runner_mode",
                    SCENARIO2_RUNNER_MODE_STUB,
                ),
                scenario2_verifier_policy=kwargs.get(
                    "scenario2_verifier_policy",
                    "informational",
                ),
            )

    monkeypatch.setattr(gradio_app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(gradio_app_module, "MistralOCRClient", lambda api_key: object())
    monkeypatch.setattr(
        gradio_app_module,
        "OpenAILLMClient",
        lambda api_key, pricing_config: object(),
    )
    monkeypatch.setattr(
        gradio_app_module,
        "GeminiLLMClient",
        lambda api_key, pricing_config: object(),
    )
    monkeypatch.setattr(
        gradio_app_module,
        "OCRPipelineOrchestrator",
        CapturingOrchestrator,
    )
    monkeypatch.setattr(
        gradio_app_module,
        "build_scenario2_runtime",
        lambda settings: type(
            "Runtime",
            (),
            {
                "runner": runtime_runner,
                "legal_corpus_tool": runtime_tool,
                "case_workspace_store": runtime_case_workspace_store,
                "bootstrap_error": "local corpus missing",
            },
        )(),
    )

    app = build_app(
        repo=repo,
        orchestrator=None,
        preflight_checker=lambda provider: None,
    )

    assert isinstance(app, gr.Blocks)
    assert captured["scenario2_runner_mode"] == SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP
    assert captured["scenario2_runner"] is runtime_runner
    assert captured["legal_corpus_tool"] is runtime_tool
    assert captured["scenario2_case_workspace_store"] is runtime_case_workspace_store
    assert captured["scenario2_bootstrap_error"] == "local corpus missing"
    assert captured["scenario2_verifier_policy"] == "strict"


def test_run_full_pipeline_ui_returns_progress_log_and_result_blocks(
    tmp_path: Path,
) -> None:
    file_one = tmp_path / "one.pdf"
    file_two = tmp_path / "two.pdf"
    file_one.write_bytes(b"one")
    file_two.write_bytes(b"two")

    orchestrator = FakeOrchestrator()
    (
        status,
        session_state,
        run_id,
        session_id,
        artifacts_root,
        progress,
        log_tail,
        log_path,
        error_user,
        error_details,
        ocr_rows,
        checklist_rows,
        gap_rows,
        details_selector_update,
        details_text,
        summary,
        raw_json,
        validation,
        metrics,
        scenario2_diagnostics,
        scenario2_fragments,
        parsed_state,
    ) = run_full_pipeline_ui(
        orchestrator=orchestrator,
        prompt_name="kaucja_gap_analysis",
        current_session_id="",
        uploaded_files=[file_one, file_two],
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        ocr_model="mistral-ocr-latest",
        table_format="html",
        include_image_base64=True,
        openai_reasoning_effort="auto",
        gemini_thinking_level="auto",
        preflight_checker=lambda provider: None,
    )

    assert "run-1" in status
    assert session_state == "session-1"
    assert run_id == "run-1"
    assert session_id == "session-1"
    assert artifacts_root == ""
    assert "OCR:" in progress
    assert "not available" in log_tail.lower()
    assert log_path == ""
    assert error_user == "No errors."
    assert error_details == ""
    assert ocr_rows[0][0] == "0000001"
    assert checklist_rows[0][0] == "deposit_transfer"
    assert gap_rows[0][1] == "Upload transfer receipt"
    assert isinstance(details_selector_update, dict)
    assert "item_id: deposit_transfer" in details_text
    assert "Missing deposit transfer receipt" in summary
    assert "checklist" in raw_json
    assert "Validation: valid" in validation
    assert "total_tokens" in metrics
    assert scenario2_diagnostics.startswith("Scenario 2 diagnostics: not applicable")
    assert "review_status: not_applicable" in scenario2_diagnostics
    assert scenario2_fragments.startswith(
        "Scenario 2 fetched fragments: not applicable"
    )
    assert parsed_state["checklist"][0]["item_id"] == "deposit_transfer"
    assert orchestrator.last_kwargs["prompt_version"] == "v001"


def test_render_details_from_state_handles_none_selection() -> None:
    parsed_payload = _sample_parsed_payload()

    details = render_details_from_state(parsed_payload, None)

    assert details == "No details available for selected item."


def test_render_details_from_state_handles_scenario_2_empty_state() -> None:
    details = render_details_from_state(None, None)

    assert details == "No details available for selected item."


def test_run_full_pipeline_ui_routes_scenario_2_to_foundation_placeholder(
    tmp_path: Path,
) -> None:
    file_one = tmp_path / "one.pdf"
    file_two = tmp_path / "two.pdf"
    file_one.write_bytes(b"one")
    file_two.write_bytes(b"two")

    orchestrator = FakeOrchestrator()
    (
        status,
        _session_state,
        run_id,
        _session_id,
        artifacts_root,
        progress,
        _log_tail,
        _log_path,
        error_user,
        error_details,
        ocr_rows,
        checklist_rows,
        gap_rows,
        _details_selector_update,
        details_text,
        summary,
        raw_json,
        validation,
        _metrics,
        scenario2_diagnostics,
        scenario2_fragments,
        _parsed_state,
    ) = run_full_pipeline_ui(
        orchestrator=orchestrator,
        prompt_name="kaucja_gap_analysis",
        current_session_id="",
        uploaded_files=[file_one, file_two],
        provider="google",
        model="gemini-2.5-flash",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_model="mistral-ocr-latest",
        table_format="html",
        include_image_base64=True,
        openai_reasoning_effort="auto",
        gemini_thinking_level="auto",
        preflight_checker=lambda provider: None,
    )

    assert "run-1" in status
    assert "completed" in status
    assert summary == SCENARIO_2_PLACEHOLDER
    assert raw_json == ""
    normalized_validation = validation.lower()
    assert (
        "not_applicable" in normalized_validation
        or "not applicable" in normalized_validation
    )
    assert details_text.startswith("Details: not applicable")
    assert checklist_rows == []
    assert gap_rows == []
    assert run_id == "run-1"
    assert artifacts_root == ""
    assert error_user == "No errors."
    assert error_details == ""
    assert len(ocr_rows) == 1
    assert "runner_mode: stub" in scenario2_diagnostics
    assert "llm_executed: false" in scenario2_diagnostics
    assert "fragment_grounding_status: not_applicable" in scenario2_diagnostics
    assert "citation_binding_status: not_applicable" in scenario2_diagnostics
    assert "fetch_fragments_called: false" in scenario2_diagnostics
    assert "tool_round_count: 0" in scenario2_diagnostics
    assert "fetched_fragment_citations:" in scenario2_fragments
    assert "- none" in scenario2_fragments
    assert orchestrator.last_kwargs["provider"] == "openai"
    assert orchestrator.last_kwargs["model"] == "gpt-5.4"
    assert progress.startswith("OCR:")
    assert orchestrator.last_kwargs["scenario_id"] == SCENARIO_2_ID


def test_scenario2_case_block_visibility_updates_by_scenario() -> None:
    assert _scenario2_case_block_update(SCENARIO_2_ID)["visible"] is True
    assert _scenario2_case_block_update("scenario_1")["visible"] is False


def test_run_full_pipeline_ui_passes_scenario2_case_workspace_inputs(
    tmp_path: Path,
) -> None:
    file_one = tmp_path / "one.pdf"
    file_two = tmp_path / "two.pdf"
    file_one.write_bytes(b"one")
    file_two.write_bytes(b"two")
    orchestrator = FakeOrchestrator()

    run_full_pipeline_ui(
        orchestrator=orchestrator,
        prompt_name="kaucja_gap_analysis",
        current_session_id="session-ui",
        uploaded_files=[file_one, file_two],
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_model="mistral-ocr-latest",
        table_format="html",
        include_image_base64=True,
        openai_reasoning_effort="auto",
        gemini_thinking_level="auto",
        preflight_checker=lambda provider: None,
        scenario2_case_workspace_id="case-gradio-001",
        scenario2_claim_amount=1200.0,
        scenario2_currency="pln",
        scenario2_lease_start="2025-01-01",
        scenario2_lease_end="2025-12-31",
        scenario2_move_out_date="2026-01-15",
        scenario2_deposit_return_due_date="2026-02-15",
    )

    assert orchestrator.last_kwargs["scenario2_case_workspace_id"] == "case-gradio-001"
    case_metadata = orchestrator.last_kwargs["scenario2_case_metadata"]
    assert isinstance(case_metadata, Scenario2CaseMetadata)
    assert case_metadata.claim_amount == 1200.0
    assert case_metadata.currency == "PLN"
    assert case_metadata.lease_start == "2025-01-01"
    assert case_metadata.lease_end == "2025-12-31"
    assert case_metadata.move_out_date == "2026-01-15"
    assert case_metadata.deposit_return_due_date == "2026-02-15"


def test_run_full_pipeline_ui_persists_explicit_case_workspace_metadata(
    tmp_path: Path,
) -> None:
    artifacts_manager = ArtifactsManager(tmp_path / "data")
    repo = StorageRepo(
        db_path=tmp_path / "kaucja.sqlite3",
        artifacts_manager=artifacts_manager,
    )
    workspace_runtime = FakeMongoRuntime(collections={})
    workspace_store = MongoCaseWorkspaceStore(runtime=workspace_runtime)
    orchestrator = OCRPipelineOrchestrator(
        repo=repo,
        artifacts_manager=artifacts_manager,
        ocr_client=FakeScenario2OCRClient(),
        llm_clients={},
        prompt_root=Path("app/prompts"),
        scenario2_case_workspace_store=workspace_store,
    )
    file_one = tmp_path / "one.pdf"
    file_two = tmp_path / "two.pdf"
    file_one.write_bytes(b"one")
    file_two.write_bytes(b"two")

    payload = run_full_pipeline_ui(
        orchestrator=orchestrator,
        prompt_name="kaucja_gap_analysis",
        current_session_id="",
        uploaded_files=[file_one, file_two],
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_model="mistral-ocr-latest",
        table_format="html",
        include_image_base64=True,
        openai_reasoning_effort="auto",
        gemini_thinking_level="auto",
        preflight_checker=lambda provider: None,
        scenario2_case_workspace_id="case-gradio-explicit",
        scenario2_claim_amount=1500.0,
        scenario2_currency="PLN",
        scenario2_move_out_date="2026-01-20",
    )

    workspace = workspace_runtime.load_collection("case_workspaces")[0]
    assert workspace["case_id"] == "case-gradio-explicit"
    assert workspace["claim_amount"] == 1500.0
    assert workspace["currency"] == "PLN"
    assert workspace["move_out_date"] == "2026-01-20"
    assert workspace["lease_start"] is None
    run = repo.get_run(payload[2])
    assert run is not None
    manifest = json.loads((Path(run.artifacts_root_path) / "run.json").read_text())
    assert manifest["inputs"]["case_workspace_id"] == "case-gradio-explicit"
    assert "case_workspace_id=case-gradio-explicit" in payload[0]
    history_payload = load_history_run(repo=repo, run_id=payload[2])
    assert "case_workspace_id=case-gradio-explicit" in history_payload[0]


def test_run_full_pipeline_ui_case_workspace_id_falls_back_to_session_id(
    tmp_path: Path,
) -> None:
    artifacts_manager = ArtifactsManager(tmp_path / "data")
    repo = StorageRepo(
        db_path=tmp_path / "kaucja.sqlite3",
        artifacts_manager=artifacts_manager,
    )
    workspace_runtime = FakeMongoRuntime(collections={})
    workspace_store = MongoCaseWorkspaceStore(runtime=workspace_runtime)
    orchestrator = OCRPipelineOrchestrator(
        repo=repo,
        artifacts_manager=artifacts_manager,
        ocr_client=FakeScenario2OCRClient(),
        llm_clients={},
        prompt_root=Path("app/prompts"),
        scenario2_case_workspace_store=workspace_store,
    )
    file_one = tmp_path / "one.pdf"
    file_two = tmp_path / "two.pdf"
    file_one.write_bytes(b"one")
    file_two.write_bytes(b"two")

    payload = run_full_pipeline_ui(
        orchestrator=orchestrator,
        prompt_name="kaucja_gap_analysis",
        current_session_id="",
        uploaded_files=[file_one, file_two],
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_model="mistral-ocr-latest",
        table_format="html",
        include_image_base64=True,
        openai_reasoning_effort="auto",
        gemini_thinking_level="auto",
        preflight_checker=lambda provider: None,
        scenario2_case_workspace_id="",
    )

    session_state = payload[1]
    workspace = workspace_runtime.load_collection("case_workspaces")[0]
    assert workspace["case_id"] == session_state
    run = repo.get_run(payload[2])
    assert run is not None
    manifest = json.loads((Path(run.artifacts_root_path) / "run.json").read_text())
    assert manifest["inputs"]["case_workspace_id"] == session_state
    assert f"case_workspace_id={session_state}" in payload[0]
    history_payload = load_history_run(repo=repo, run_id=payload[2])
    assert f"case_workspace_id={session_state}" in history_payload[0]


def test_run_full_pipeline_ui_preflight_does_not_require_openai_for_scenario_2(
    tmp_path: Path,
) -> None:
    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")
    file_two = tmp_path / "two.pdf"
    file_two.write_bytes(b"two")

    orchestrator = FakeOrchestrator(scenario2_runner_mode=SCENARIO2_RUNNER_MODE_STUB)

    def _preflight_for_scenario2(provider: str) -> str | None:
        if provider == "openai":
            return "openai dependency is required"
        return None

    (
        status,
        _session_state,
        _run_id,
        _session_id,
        _artifacts_root,
        _progress,
        _log_tail,
        _log_path,
        error_user,
        _error_details,
        ocr_rows,
        checklist_rows,
        gap_rows,
        _details_selector_update,
        _details_text,
        summary,
        _raw_json,
        validation,
        _metrics,
        scenario2_diagnostics,
        scenario2_fragments,
        _parsed_state,
    ) = run_full_pipeline_ui(
        orchestrator=orchestrator,
        prompt_name="kaucja_gap_analysis",
        current_session_id="",
        uploaded_files=[file_one, file_two],
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_model="mistral-ocr-latest",
        table_format="html",
        include_image_base64=True,
        openai_reasoning_effort="auto",
        gemini_thinking_level="auto",
        preflight_checker=_preflight_for_scenario2,
    )

    assert "Run failed. Run aborted in preflight" not in status
    assert "run-1" in status
    assert summary == SCENARIO_2_PLACEHOLDER
    assert "not_applicable" in validation
    assert error_user == "No errors."
    assert ocr_rows[0][0] == "0000001"
    assert checklist_rows == []
    assert gap_rows == []
    assert "runner_mode: stub" in scenario2_diagnostics
    assert "fetched_fragment_doc_uids:" in scenario2_fragments


def test_run_full_pipeline_ui_preflight_requires_openai_for_scenario_2_openai_mode(
    tmp_path: Path,
) -> None:
    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")
    file_two = tmp_path / "two.pdf"
    file_two.write_bytes(b"two")

    orchestrator = FakeOrchestrator(
        scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
        scenario2_runner=object(),
        legal_corpus_tool=object(),
    )

    def _preflight_for_scenario2(provider: str) -> str | None:
        if provider == "openai":
            return "openai dependency is required"
        return None

    payload = run_full_pipeline_ui(
        orchestrator=orchestrator,
        prompt_name="kaucja_gap_analysis",
        current_session_id="",
        uploaded_files=[file_one, file_two],
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_model="mistral-ocr-latest",
        table_format="html",
        include_image_base64=True,
        openai_reasoning_effort="auto",
        gemini_thinking_level="auto",
        preflight_checker=_preflight_for_scenario2,
    )

    assert payload[0] == "openai dependency is required"
    assert payload[2] == ""


def test_scenario_config_round_trip_preserves_valid_scenario_1_values() -> None:
    to_scenario2 = _scenario_config_mode_updates(
        selected_scenario_id=SCENARIO_2_ID,
        fallback_provider="google",
        fallback_model="gemini-3.1-pro-preview",
        fallback_prompt_name="kaucja_gap_analysis",
        fallback_prompt_version="v001",
        scenario1_state=None,
        previous_scenario_id="scenario_1",
    )
    (
        provider_update,
        model_update,
        prompt_name_update,
        prompt_version_update,
        summary_update,
        scenario1_state,
        selected_scenario_1,
    ) = to_scenario2

    assert selected_scenario_1 == SCENARIO_2_ID
    assert provider_update["interactive"] is False
    assert model_update["interactive"] is False
    assert prompt_name_update["interactive"] is False
    assert prompt_version_update["interactive"] is False
    assert summary_update["visible"] is True
    assert "provider=openai" in summary_update["value"]
    assert "model=gpt-5.4" in summary_update["value"]
    assert scenario1_state["provider"] == "google"
    assert scenario1_state["model"] == "gemini-3.1-pro-preview"
    assert scenario1_state["prompt_name"] == "kaucja_gap_analysis"
    assert scenario1_state["prompt_version"] == "v001"

    back_to_scenario1 = _scenario_config_mode_updates(
        selected_scenario_id="scenario_1",
        fallback_provider="openai",
        fallback_model="gpt-5.2",
        fallback_prompt_name="other_prompt",
        fallback_prompt_version="v999",
        scenario1_state=scenario1_state,
        previous_scenario_id=selected_scenario_1,
    )
    (
        restored_provider_update,
        restored_model_update,
        restored_prompt_name_update,
        restored_prompt_version_update,
        restored_summary_update,
        _restored_state,
        selected_scenario_2,
    ) = back_to_scenario1

    assert selected_scenario_2 == "scenario_1"
    assert restored_provider_update["interactive"] is True
    assert restored_model_update["interactive"] is True
    assert restored_prompt_name_update["interactive"] is True
    assert restored_prompt_version_update["interactive"] is True
    assert restored_provider_update["value"] == "google"
    assert restored_model_update["value"] == "gemini-3.1-pro-preview"
    assert restored_prompt_name_update["value"] == "kaucja_gap_analysis"
    assert restored_prompt_version_update["value"] == "v001"
    assert restored_summary_update["visible"] is False


def test_prompt_save_flow_and_run_with_new_version(tmp_path: Path) -> None:
    prompts_root = tmp_path / "prompts"
    _create_prompt_version(
        root=prompts_root,
        prompt_name="kaucja_gap_analysis",
        version="v001",
        prompt_text="base prompt",
        schema_text='{"type":"object","properties":{},"additionalProperties":false}',
    )
    prompt_manager = PromptManager(prompts_root)

    save_message, version_update, _ = save_prompt_as_new_version_for_ui(
        prompt_manager=prompt_manager,
        prompt_name="kaucja_gap_analysis",
        source_version="v001",
        system_prompt_text="new prompt",
        schema_text='{"type":"object","properties":{},"additionalProperties":false}',
        author="tester",
        note="new version",
    )

    assert "Saved new version" in save_message
    assert isinstance(version_update, dict)
    new_version = str(version_update["value"])
    assert new_version == "v002"

    file_one = tmp_path / "one.pdf"
    file_two = tmp_path / "two.pdf"
    file_one.write_bytes(b"one")
    file_two.write_bytes(b"two")
    orchestrator = FakeOrchestrator()

    run_full_pipeline_ui(
        orchestrator=orchestrator,
        prompt_name="kaucja_gap_analysis",
        current_session_id="",
        uploaded_files=[file_one, file_two],
        provider="openai",
        model="gpt-5.1",
        prompt_version=new_version,
        ocr_model="mistral-ocr-latest",
        table_format="html",
        include_image_base64=True,
        openai_reasoning_effort="auto",
        gemini_thinking_level="auto",
        preflight_checker=lambda provider: None,
    )

    assert orchestrator.last_kwargs["prompt_version"] == "v002"


def test_history_load_returns_saved_run_bundle_with_progress_and_log(
    tmp_path: Path,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-history")
    run = repo.create_run(
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        schema_version="v001",
        status="running",
    )

    run_root = Path(run.artifacts_root_path)
    (run_root / "logs" / "run.log").write_text(
        "line1\nline2\nline3\n",
        encoding="utf-8",
    )
    llm_dir = run_root / "llm"
    llm_dir.mkdir(parents=True, exist_ok=True)
    parsed_payload = _sample_parsed_payload()
    (llm_dir / "response_raw.txt").write_text(
        json.dumps(parsed_payload),
        encoding="utf-8",
    )
    parsed_path = llm_dir / "response_parsed.json"
    parsed_path.write_text(json.dumps(parsed_payload), encoding="utf-8")
    (llm_dir / "validation.json").write_text(
        json.dumps({"valid": True, "schema_errors": [], "invariant_errors": []}),
        encoding="utf-8",
    )

    doc_ocr_dir = run_root / "documents" / "0000001" / "ocr"
    doc_ocr_dir.mkdir(parents=True, exist_ok=True)
    (doc_ocr_dir / "combined.md").write_text("combined markdown", encoding="utf-8")

    repo.create_document(
        run_id=run.run_id,
        doc_id="0000001",
        original_filename="contract.pdf",
        original_mime="application/pdf",
        original_path=str(
            run_root / "documents" / "0000001" / "original" / "contract.pdf"
        ),
        ocr_status="ok",
        pages_count=1,
        ocr_artifacts_path=str(doc_ocr_dir),
    )
    repo.upsert_llm_output(
        run_id=run.run_id,
        response_json_path=str(parsed_path),
        response_valid=True,
        schema_validation_errors_path=None,
    )
    repo.update_run_metrics(
        run_id=run.run_id,
        timings_json={"t_total_ms": 25.0},
        usage_json={"input_tokens": 12},
        usage_normalized_json={"total_tokens": 20},
        cost_json={"total_cost_usd": 0.002},
    )
    repo.update_run_status(run_id=run.run_id, status="completed")

    init_run_manifest(
        artifacts_root_path=run.artifacts_root_path,
        session_id=run.session_id,
        run_id=run.run_id,
        inputs={
            "provider": run.provider,
            "model": run.model,
            "prompt_name": run.prompt_name,
            "prompt_version": run.prompt_version,
            "schema_version": run.schema_version,
            "ocr_params": {"model": "mistral-ocr-latest"},
            "llm_params": {"openai_reasoning_effort": "auto"},
        },
        artifacts={
            "root": run.artifacts_root_path,
            "run_log": str(run_root / "logs" / "run.log"),
            "documents": [],
            "llm": {},
        },
        status="running",
    )
    update_run_manifest(
        artifacts_root_path=run.artifacts_root_path,
        updates={
            "status": "completed",
            "stages": {
                "ocr": {"status": "completed"},
                "llm": {"status": "completed"},
                "finalize": {"status": "completed"},
            },
            "metrics": {
                "timings": {"t_total_ms": 25.0},
                "usage": {"input_tokens": 12},
                "usage_normalized": {"total_tokens": 20},
                "cost": {"total_cost_usd": 0.002},
            },
            "validation": {"valid": True, "errors": []},
        },
    )

    rows = list_history_rows(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        date_from="",
        date_to="",
        limit=10,
    )
    assert len(rows) == 1
    assert rows[0][0] == run.run_id

    (
        status,
        session_state,
        loaded_run_id,
        session_id,
        artifacts_root,
        progress,
        log_tail,
        log_path,
        error_user,
        error_details,
        ocr_rows,
        checklist_rows,
        gap_rows,
        _details_selector_update,
        details_text,
        summary,
        raw_json,
        validation,
        metrics,
        scenario2_diagnostics,
        scenario2_fragments,
        parsed_state,
    ) = load_history_run(repo=repo, run_id=run.run_id)

    assert "History loaded." in status
    assert session_state == session.session_id
    assert loaded_run_id == run.run_id
    assert session_id == session.session_id
    assert artifacts_root == run.artifacts_root_path
    assert "OCR: completed" in progress
    assert "line3" in log_tail
    assert log_path.endswith("logs/run.log")
    assert error_user == "No errors."
    assert error_details == ""
    assert ocr_rows[0][0] == "0000001"
    assert checklist_rows[0][0] == "deposit_transfer"
    assert gap_rows[0][1] == "Upload transfer receipt"
    assert "item_id: deposit_transfer" in details_text
    assert "Missing deposit transfer receipt" in summary
    assert "checklist" in raw_json
    assert "Validation: valid" in validation
    assert "total_tokens" in metrics
    assert scenario2_diagnostics.startswith("Scenario 2 diagnostics: not applicable")
    assert scenario2_fragments.startswith(
        "Scenario 2 fetched fragments: not applicable"
    )
    assert parsed_state["checklist"][0]["item_id"] == "deposit_transfer"


def test_history_load_returns_scenario_2_placeholder_summary_and_not_applicable_validation(
    tmp_path: Path,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-history-2")
    run_id = _seed_history_run_scenario_2(repo=repo, session_id=session.session_id)

    (
        status,
        loaded_session,
        loaded_run_id,
        loaded_session_id,
        artifacts_root,
        progress,
        log_tail,
        log_path,
        error_user,
        error_details,
        ocr_rows,
        checklist_rows,
        gap_rows,
        _details_selector_update,
        details_text,
        summary,
        raw_json,
        validation,
        metrics,
        scenario2_diagnostics,
        scenario2_fragments,
        parsed_state,
    ) = load_history_run(repo=repo, run_id=run_id)

    assert "History loaded." in status
    assert loaded_run_id == run_id
    assert loaded_session_id == session.session_id
    assert loaded_session == session.session_id
    assert "not_applicable" in progress.lower()
    assert "Validation: not_applicable" in validation
    assert details_text.startswith("Details: not applicable")
    assert checklist_rows == []
    assert gap_rows == []
    assert summary == SCENARIO_2_PLACEHOLDER
    assert raw_json == ""
    assert "line2" in log_tail
    assert artifacts_root != ""
    assert log_path.endswith("logs/run.log")
    assert error_user == "No errors."
    assert parsed_state is None
    assert "usage" in metrics
    assert "review_status=not_applicable" in status
    assert "review_status: not_applicable" in scenario2_diagnostics
    assert "verifier_policy: informational" in scenario2_diagnostics
    assert "verifier_gate_status: not_applicable" in scenario2_diagnostics
    assert "runner_mode: stub" in scenario2_diagnostics
    assert "llm_executed: false" in scenario2_diagnostics
    assert "fragment_grounding_status: not_applicable" in scenario2_diagnostics
    assert "verifier_status: not_applicable" in scenario2_diagnostics
    assert "citation_format_status: not_applicable" in scenario2_diagnostics
    assert "legal_citation_count: 0" in scenario2_diagnostics
    assert "user_doc_citation_count: 0" in scenario2_diagnostics
    assert "tool_trace_summary:" in scenario2_diagnostics
    assert "- scenario2_stub: ok" in scenario2_diagnostics
    assert "fetched_fragment_citations:" in scenario2_fragments
    assert "fetched_fragment_doc_uids:" in scenario2_fragments
    assert "fetched_fragment_source_hashes:" in scenario2_fragments
    assert "fetched_fragment_quote_checksums:" in scenario2_fragments
    assert "- none" in scenario2_fragments


def test_history_load_returns_scenario_2_fragment_excerpts_from_trace(
    tmp_path: Path,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-history-2-real")
    run_id = _seed_history_run_scenario_2_real_with_fragments(
        repo=repo,
        session_id=session.session_id,
    )

    payload = load_history_run(repo=repo, run_id=run_id)
    scenario2_diagnostics = payload[19]
    scenario2_fragments = payload[20]

    assert "runner_mode: openai_tool_loop" in scenario2_diagnostics
    assert "review_status: passed" in scenario2_diagnostics
    assert "verifier_policy: informational" in scenario2_diagnostics
    assert "verifier_gate_status: passed" in scenario2_diagnostics
    assert "fragment_grounding_status: fragments_fetched" in scenario2_diagnostics
    assert "verifier_status: passed" in scenario2_diagnostics
    assert "citation_format_status: passed" in scenario2_diagnostics
    assert "legal_citation_count: 2" in scenario2_diagnostics
    assert "user_doc_citation_count: 1" in scenario2_diagnostics
    assert "citations_in_analysis_sections: true" in scenario2_diagnostics
    assert "sources_section_present: true" in scenario2_diagnostics
    assert "fetched_sources_referenced: true" in scenario2_diagnostics
    assert "missing_sections:\n- none" in scenario2_diagnostics
    assert "fetched_fragment_ledger:" in scenario2_fragments
    assert "display_citation: Art. 6 KC" in scenario2_fragments
    assert "text_excerpt: Najemca powinien wykazac zasadnosc potracen i szkody." in (
        scenario2_fragments
    )
    assert 'locator: {"end_char": 32, "start_char": 0}' in scenario2_fragments
    assert "locator_precision: char_offsets_only" in scenario2_fragments
    assert "page_truth_status: not_available_local" in scenario2_fragments
    assert "quote_checksum: sha256:frag-1" in scenario2_fragments
    assert "fetched_fragment_quote_checksums:" in scenario2_fragments


def test_history_load_returns_scenario_2_failure_partial_diagnostics(
    tmp_path: Path,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-history-2-failed")
    run_id = _seed_history_run_scenario_2_failure(
        repo=repo,
        session_id=session.session_id,
    )

    (
        status,
        _loaded_session,
        loaded_run_id,
        _loaded_session_id,
        _artifacts_root,
        _progress,
        _log_tail,
        _log_path,
        error_user,
        error_details,
        _ocr_rows,
        checklist_rows,
        gap_rows,
        _details_selector_update,
        _details_text,
        _summary,
        _raw_json,
        validation,
        _metrics,
        scenario2_diagnostics,
        scenario2_fragments,
        parsed_state,
    ) = load_history_run(repo=repo, run_id=run_id)

    assert "History loaded." in status
    assert loaded_run_id == run_id
    assert "Run failed" in error_user or error_user != "No errors."
    assert f"error_code={SCENARIO2_RUNTIME_ERROR}" in error_details
    assert checklist_rows == []
    assert gap_rows == []
    assert parsed_state is None
    assert "Validation: failed" in validation
    assert "runner_mode: openai_tool_loop" in scenario2_diagnostics
    assert "review_status: needs_review" in scenario2_diagnostics
    assert "verifier_policy: informational" in scenario2_diagnostics
    assert "verifier_gate_status: warning_not_blocking" in scenario2_diagnostics
    assert "llm_executed: true" in scenario2_diagnostics
    assert "fragment_grounding_status: empty_fragments" in scenario2_diagnostics
    assert "citation_binding_status: empty_fragments" in scenario2_diagnostics
    assert "verifier_status: warning" in scenario2_diagnostics
    assert "citation_format_status: warning" in scenario2_diagnostics
    assert "legal_citation_count: 0" in scenario2_diagnostics
    assert "user_doc_citation_count: 0" in scenario2_diagnostics
    assert "citations_in_analysis_sections: false" in scenario2_diagnostics
    assert "sources_section_present: false" in scenario2_diagnostics
    assert "fetched_sources_referenced: false" in scenario2_diagnostics
    assert "fetch_fragments_called: true" in scenario2_diagnostics
    assert "fetch_fragments_returned_usable_fragments: false" in scenario2_diagnostics
    assert "repair_turn_used: true" in scenario2_diagnostics
    assert "missing_sections:" in scenario2_diagnostics
    assert "- Источники" in scenario2_diagnostics
    assert "stage: runner" in scenario2_diagnostics
    assert f"error_code: {SCENARIO2_RUNTIME_ERROR}" in scenario2_diagnostics
    assert "- search: ok" in scenario2_diagnostics
    assert "- fetch_fragments: ok" in scenario2_diagnostics
    assert "- none" in scenario2_fragments


def test_history_load_returns_strict_verifier_gate_status_for_scenario_2(
    tmp_path: Path,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-history-2-strict-gate")
    run_id = _seed_history_run_scenario_2_failure(
        repo=repo,
        session_id=session.session_id,
    )
    run = repo.get_run(run_id)
    assert run is not None

    manifest_path = Path(run.artifacts_root_path) / "run.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        _scenario2_verifier_gate_manifest_update(
            verifier_policy="strict",
            verifier_status="warning",
            llm_executed=True,
            verifier_warnings=[
                "Sources section is missing.",
            ],
        )
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    trace_path = Path(run.artifacts_root_path) / "llm" / "scenario2_trace.json"
    trace_payload = json.loads(trace_path.read_text(encoding="utf-8"))
    diagnostics = trace_payload["diagnostics"]
    diagnostics["verifier_policy"] = "strict"
    diagnostics["verifier_gate_status"] = "blocked"
    trace_path.write_text(
        json.dumps(trace_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    payload = load_history_run(repo=repo, run_id=run_id)
    status = payload[0]
    scenario2_diagnostics = payload[19]

    assert "verifier_gate_status=blocked" in status
    assert "verifier_policy: strict" in scenario2_diagnostics
    assert "verifier_gate_status: blocked" in scenario2_diagnostics


def test_run_full_pipeline_ui_renders_scenario_2_fragment_excerpts_from_trace(
    tmp_path: Path,
) -> None:
    file_one = tmp_path / "one.pdf"
    file_two = tmp_path / "two.pdf"
    file_one.write_bytes(b"one")
    file_two.write_bytes(b"two")

    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-live-scenario2-real")
    run_id = _seed_history_run_scenario_2_real_with_fragments(
        repo=repo,
        session_id=session.session_id,
    )
    run = repo.get_run(run_id)
    assert run is not None

    class TraceBackedScenario2Orchestrator(FakeOrchestrator):
        def __init__(self) -> None:
            super().__init__(
                scenario2_runner_mode=SCENARIO2_RUNNER_MODE_OPENAI_TOOL_LOOP,
                scenario2_runner=object(),
                legal_corpus_tool=object(),
            )
            self.repo = repo

        def run_full_pipeline(self, **kwargs: object) -> FullPipelineResult:
            self.last_kwargs = kwargs
            return FullPipelineResult(
                session_id=session.session_id,
                run_id=run_id,
                run_status="completed",
                documents=[
                    OCRDocumentStageResult(
                        doc_id="0000001",
                        ocr_status="ok",
                        pages_count=1,
                        combined_markdown_path=str(
                            Path(run.artifacts_root_path)
                            / "documents"
                            / "0000001"
                            / "ocr"
                            / "combined.md"
                        ),
                        ocr_artifacts_path=str(
                            Path(run.artifacts_root_path)
                            / "documents"
                            / "0000001"
                            / "ocr"
                        ),
                        ocr_error=None,
                    )
                ],
                critical_gaps_summary=[],
                next_questions_to_user=[],
                raw_json_text="Grounded Scenario 2 answer",
                parsed_json=None,
                validation_valid=True,
                validation_errors=[],
                metrics={"usage": {"total_tokens": 11}},
                error_code=None,
                error_message=None,
                scenario_id=SCENARIO_2_ID,
            )

    payload = run_full_pipeline_ui(
        orchestrator=TraceBackedScenario2Orchestrator(),
        prompt_name="kaucja_gap_analysis",
        current_session_id="",
        uploaded_files=[file_one, file_two],
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        scenario_id=SCENARIO_2_ID,
        ocr_model="mistral-ocr-latest",
        table_format="html",
        include_image_base64=True,
        openai_reasoning_effort="auto",
        gemini_thinking_level="auto",
        preflight_checker=lambda provider: None,
    )

    scenario2_fragments = payload[20]
    scenario2_diagnostics = payload[19]
    assert "review_status: passed" in scenario2_diagnostics
    assert "verifier_policy: informational" in scenario2_diagnostics
    assert "verifier_gate_status: passed" in scenario2_diagnostics
    assert "verifier_status: passed" in scenario2_diagnostics
    assert "citation_format_status: passed" in scenario2_diagnostics
    assert "fetched_fragment_ledger:" in scenario2_fragments
    assert "display_citation: Art. 6 KC" in scenario2_fragments
    assert "quote_checksum: sha256:frag-1" in scenario2_fragments


def test_refresh_history_for_ui_populates_compare_choices(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-compare")
    first_run_id = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="missing",
            ask="Upload proof",
            gap="missing proof",
            question="please upload",
        ),
        tokens=80,
        total_cost=0.08,
        total_time_ms=100.0,
    )
    second_run_id = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="google",
        model="gemini-3.1-pro-preview",
        prompt_version="v002",
        payload=_comparison_payload(
            status="confirmed",
            ask="",
            gap="",
            question="",
        ),
        tokens=120,
        total_cost=0.12,
        total_time_ms=70.0,
    )

    rows, compare_a, compare_b = refresh_history_for_ui(
        repo=repo,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
    )

    assert len(rows) == 2
    assert first_run_id in compare_a["choices"]
    assert second_run_id in compare_b["choices"]


def test_list_history_rows_includes_scenario_and_review_status_and_filters(
    tmp_path: Path,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-history-review-filter")
    _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="missing",
            ask="Upload proof",
            gap="missing proof",
            question="please upload",
        ),
        tokens=80,
        total_cost=0.08,
        total_time_ms=100.0,
    )
    scenario2_passed = _seed_history_run_scenario_2_real_with_fragments(
        repo=repo,
        session_id=session.session_id,
    )
    scenario2_needs_review = _seed_history_run_scenario_2_failure(
        repo=repo,
        session_id=session.session_id,
    )

    all_rows = list_history_rows(
        repo=repo,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
        review_status="all",
    )
    passed_rows = list_history_rows(
        repo=repo,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
        review_status="passed",
    )
    needs_review_rows = list_history_rows(
        repo=repo,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
        review_status="needs_review",
    )
    not_applicable_rows = list_history_rows(
        repo=repo,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
        review_status="not_applicable",
    )
    filtered_rows, compare_a, compare_b = refresh_history_for_ui(
        repo=repo,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
        review_status="passed",
    )

    assert len(all_rows) == 3
    assert all_rows[0][3] in {SCENARIO_2_ID, "scenario_1"}
    assert passed_rows == [
        row for row in all_rows if row[0] == scenario2_passed and row[8] == "passed"
    ]
    assert needs_review_rows == [
        row
        for row in all_rows
        if row[0] == scenario2_needs_review and row[8] == "needs_review"
    ]
    assert len(not_applicable_rows) == 1
    assert not_applicable_rows[0][3] == "scenario_1"
    assert not_applicable_rows[0][8] == "not_applicable"
    assert len(filtered_rows) == 1
    assert filtered_rows[0][0] == scenario2_passed
    assert compare_a["value"] == scenario2_passed
    assert compare_b["value"] == scenario2_passed


def test_compare_history_runs_returns_diff_for_two_runs(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-compare-flow")
    run_a = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="missing",
            ask="Upload transfer receipt",
            gap="Missing transfer receipt",
            question="Please upload transfer receipt",
        ),
        tokens=100,
        total_cost=0.11,
        total_time_ms=140.0,
    )
    run_b = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="google",
        model="gemini-3.1-pro-preview",
        prompt_version="v002",
        payload=_comparison_payload(
            status="confirmed",
            ask="",
            gap="",
            question="",
        ),
        tokens=160,
        total_cost=0.14,
        total_time_ms=95.0,
    )

    (
        compare_status,
        compare_summary,
        compare_rows,
        compare_gaps,
        compare_metrics,
        compare_json,
    ) = compare_history_runs(repo=repo, run_id_a=run_a, run_id_b=run_b)

    assert "Comparison ready." in compare_status
    assert "improved: 1" in compare_summary
    assert "provider_changed=True" in compare_summary
    assert compare_rows[0][0] == "KAUCJA_PAYMENT_PROOF"
    assert compare_rows[0][-1] == "improved"
    assert "critical_gaps_summary" in compare_gaps
    assert "delta (B - A)" in compare_metrics
    parsed = json.loads(compare_json)
    assert parsed["run_a"]["run_id"] == run_a
    assert parsed["run_b"]["run_id"] == run_b


def test_compare_history_runs_returns_scenario_2_diagnostics_diff(
    tmp_path: Path,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-compare-scenario2")
    run_a = _seed_history_run_scenario_2_real_with_fragments(
        repo=repo,
        session_id=session.session_id,
    )
    run_b = _seed_history_run_scenario_2_failure(
        repo=repo,
        session_id=session.session_id,
    )

    (
        compare_status,
        compare_summary,
        compare_rows,
        compare_gaps,
        compare_metrics,
        compare_json,
    ) = compare_history_runs(repo=repo, run_id_a=run_a, run_id_b=run_b)

    assert "Comparison ready." in compare_status
    assert "Scenario 2 diagnostics comparison" in compare_summary
    assert "verifier_policy:" in compare_summary
    assert "verifier_gate_status:" in compare_summary
    assert "review_status:" in compare_summary
    assert "fragment_grounding_status:" in compare_summary
    assert "verifier_status:" in compare_summary
    assert "citation_format_status:" in compare_summary
    assert "tool_round_count:" in compare_summary
    assert compare_rows == []
    assert "scenario2_diagnostics:" in compare_gaps
    assert "missing_sections:" in compare_gaps
    assert "legal_citation_count:" in compare_gaps
    assert "fetched_fragment_citations:" in compare_gaps
    assert "fetched_fragment_quote_checksums:" in compare_gaps
    assert "review_status:" in compare_gaps
    assert "verifier_policy:" in compare_gaps
    assert "verifier_gate_status:" in compare_gaps
    assert "delta (B - A)" in compare_metrics
    parsed = json.loads(compare_json)
    assert parsed["scenario_comparison"]["mode"] == "scenario2_pair"


def test_compare_history_runs_handles_mixed_scenarios_honestly(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-compare-mixed")
    run_a = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="missing",
            ask="Upload transfer receipt",
            gap="Missing transfer receipt",
            question="Please upload transfer receipt",
        ),
        tokens=100,
        total_cost=0.11,
        total_time_ms=140.0,
    )
    run_b = _seed_history_run_scenario_2(repo=repo, session_id=session.session_id)

    (
        compare_status,
        compare_summary,
        compare_rows,
        compare_gaps,
        _compare_metrics,
        compare_json,
    ) = compare_history_runs(repo=repo, run_id_a=run_a, run_id_b=run_b)

    assert "Comparison ready." in compare_status
    assert "Mixed scenario comparison" in compare_summary
    assert "not applicable" in compare_summary
    assert "review_status_a=" in compare_summary
    assert "review_status_b=" in compare_summary
    assert compare_rows == []
    assert "mixed_scenario_comparison:" in compare_gaps
    assert "suppressed" in compare_gaps
    parsed = json.loads(compare_json)
    assert parsed["scenario_comparison"]["mode"] == "mixed"


def test_compare_history_runs_handles_missing_run(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-compare-missing")
    run_a = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="missing",
            ask="Upload transfer receipt",
            gap="Missing transfer receipt",
            question="Please upload transfer receipt",
        ),
        tokens=100,
        total_cost=0.11,
        total_time_ms=140.0,
    )

    (
        compare_status,
        compare_summary,
        compare_rows,
        _compare_gaps,
        _compare_metrics,
        compare_json,
    ) = compare_history_runs(repo=repo, run_id_a=run_a, run_id_b="missing-run")

    assert "Comparison completed with warnings." in compare_status
    assert "warnings:" in compare_summary
    assert compare_rows[0][0] == "KAUCJA_PAYMENT_PROOF"
    payload = json.loads(compare_json)
    assert payload["run_b"]["exists"] is False


def test_compare_history_runs_handles_none_inputs(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")

    (
        compare_status,
        compare_summary,
        compare_rows,
        compare_gaps,
        compare_metrics,
        compare_json,
    ) = compare_history_runs(repo=repo, run_id_a=None, run_id_b=None)

    assert "select both" in compare_status
    assert "improved: 0" in compare_summary
    assert compare_rows == []
    assert compare_gaps == ""
    assert compare_metrics == ""
    assert compare_json == "{}"


def test_export_history_run_bundle_success(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-export")
    run_id = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="confirmed",
            ask="",
            gap="",
            question="",
        ),
        tokens=100,
        total_cost=0.05,
        total_time_ms=50.0,
    )

    status, zip_path, download_path = export_history_run_bundle(
        repo=repo, run_id=run_id
    )

    assert "Export completed." in status
    assert zip_path.endswith("_bundle.zip")
    assert download_path == zip_path
    archive_path = Path(zip_path)
    assert archive_path.is_file()


def test_export_history_run_bundle_handles_missing_run(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")

    status, zip_path, download_path = export_history_run_bundle(
        repo=repo,
        run_id="missing-run",
    )

    assert "not found" in status
    assert zip_path == ""
    assert download_path is None


def test_delete_history_run_success_and_refreshes_history(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-delete-ui")
    run_id = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="confirmed",
            ask="",
            gap="",
            question="",
        ),
        tokens=80,
        total_cost=0.03,
        total_time_ms=42.0,
    )

    (
        status,
        backup_path,
        details,
        rows,
        compare_a,
        compare_b,
        run_id_update,
        confirm_update,
    ) = delete_history_run(
        repo=repo,
        run_id=run_id,
        confirm_run_id=run_id,
        create_backup_zip=False,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
    )

    assert "Delete completed." in status
    assert backup_path == ""
    assert "artifacts_deleted=True" in details
    assert repo.get_run(run_id) is None
    assert rows == []
    assert compare_a["choices"] == []
    assert compare_b["choices"] == []
    assert run_id_update["value"] == ""
    assert confirm_update["value"] == ""


def test_delete_history_run_requires_exact_confirmation(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-delete-confirm")
    run_id = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="missing",
            ask="Upload receipt",
            gap="Missing receipt",
            question="Please upload receipt",
        ),
        tokens=60,
        total_cost=0.02,
        total_time_ms=55.0,
    )

    (
        status,
        backup_path,
        details,
        rows,
        _compare_a,
        _compare_b,
        _run_update,
        _confirm_update,
    ) = delete_history_run(
        repo=repo,
        run_id=run_id,
        confirm_run_id="wrong-id",
        create_backup_zip=False,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
    )

    assert "confirmation mismatch" in status.lower()
    assert backup_path == ""
    assert "expected=" in details
    assert repo.get_run(run_id) is not None
    assert len(rows) == 1


def test_delete_history_run_with_backup_success(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-delete-backup")
    run_id = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="confirmed",
            ask="",
            gap="",
            question="",
        ),
        tokens=40,
        total_cost=0.01,
        total_time_ms=10.0,
    )

    (
        status,
        backup_path,
        details,
        rows,
        _compare_a,
        _compare_b,
        _run_update,
        _confirm_update,
    ) = delete_history_run(
        repo=repo,
        run_id=run_id,
        confirm_run_id=run_id,
        create_backup_zip=True,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
    )

    assert "Delete completed." in status
    assert backup_path.endswith("_bundle.zip")
    assert Path(backup_path).is_file()
    assert "artifacts_deleted=True" in details
    assert repo.get_run(run_id) is None
    assert rows == []


def test_delete_history_run_with_backup_failure_keeps_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-delete-backup-fail")
    run_id = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="missing",
            ask="Upload doc",
            gap="Missing doc",
            question="Please upload doc",
        ),
        tokens=40,
        total_cost=0.01,
        total_time_ms=10.0,
    )

    def _raise_backup_error(
        *,
        artifacts_root_path: str,
        output_dir: str | None = None,
        signing_key: str | None = None,
    ):
        assert signing_key is None
        raise ZipExportError("backup failed")

    monkeypatch.setattr(gradio_app_module, "export_run_bundle", _raise_backup_error)

    (
        status,
        backup_path,
        details,
        rows,
        _compare_a,
        _compare_b,
        _run_update,
        _confirm_update,
    ) = delete_history_run(
        repo=repo,
        run_id=run_id,
        confirm_run_id=run_id,
        create_backup_zip=True,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
    )

    assert "Delete failed." in status
    assert backup_path == ""
    assert "BACKUP_EXPORT_FAILED" in details
    assert repo.get_run(run_id) is not None
    assert len(rows) == 1


def test_restore_history_run_bundle_success_cycle(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-restore-ui")
    run_id = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="confirmed",
            ask="",
            gap="",
            question="",
        ),
        tokens=100,
        total_cost=0.05,
        total_time_ms=20.0,
    )

    export_status, zip_path, _download = export_history_run_bundle(
        repo=repo, run_id=run_id
    )
    assert "Export completed." in export_status
    assert zip_path

    (
        delete_status,
        _backup_path,
        _details,
        _rows,
        _a,
        _b,
        _run_update,
        _confirm_update,
    ) = delete_history_run(
        repo=repo,
        run_id=run_id,
        confirm_run_id=run_id,
        create_backup_zip=False,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
    )
    assert "Delete completed." in delete_status
    assert repo.get_run(run_id) is None

    (
        restore_status,
        restore_details,
        restored_run_id,
        restored_artifacts_root,
        rows,
        compare_a,
        compare_b,
        run_id_update,
    ) = restore_history_run_bundle(
        repo=repo,
        zip_file_path=zip_path,
        overwrite_existing=False,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
    )

    assert "Restore completed." in restore_status
    assert "manifest_verification=verified" in restore_details
    assert "files_checked=" in restore_details
    assert "signature_verification=unsigned" in restore_details
    assert "archive_signed=False" in restore_details
    assert "strict_mode=False" in restore_details
    assert "verify_only=False" in restore_details
    assert "rollback_attempted=False" in restore_details
    assert restored_run_id == run_id
    assert Path(restored_artifacts_root).is_dir()
    assert any(row[0] == run_id for row in rows)
    assert run_id in compare_a["choices"]
    assert run_id in compare_b["choices"]
    assert run_id_update["value"] == run_id
    assert repo.get_run(run_id) is not None


def test_restore_history_run_bundle_invalid_archive(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    invalid_zip = tmp_path / "invalid.zip"
    with ZipFile(invalid_zip, "w") as archive:
        archive.writestr("logs/run.log", "only log")

    (
        restore_status,
        restore_details,
        restored_run_id,
        restored_artifacts_root,
        rows,
        _compare_a,
        _compare_b,
        _run_update,
    ) = restore_history_run_bundle(
        repo=repo,
        zip_file_path=invalid_zip,
        overwrite_existing=False,
        session_id="",
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
    )

    assert restore_status.startswith("Restore failed.")
    assert "RESTORE_INVALID_ARCHIVE" in restore_details
    assert restored_run_id == ""
    assert restored_artifacts_root == ""
    assert rows == []


def test_restore_history_run_bundle_integrity_failure(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-restore-integrity-ui")
    run_id = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="confirmed",
            ask="",
            gap="",
            question="",
        ),
        tokens=15,
        total_cost=0.01,
        total_time_ms=8.0,
    )
    export_status, zip_path, _download = export_history_run_bundle(
        repo=repo,
        run_id=run_id,
    )
    assert "Export completed." in export_status
    assert zip_path

    tampered_zip = tmp_path / "tampered-ui.zip"
    with ZipFile(zip_path, "r") as source_archive:
        with ZipFile(tampered_zip, "w") as target_archive:
            for info in source_archive.infolist():
                payload = source_archive.read(info.filename)
                if info.filename == "logs/run.log":
                    payload = b"tampered\n"
                target_archive.writestr(info.filename, payload)

    repo.delete_run(run_id)
    (
        restore_status,
        restore_details,
        _restored_run_id,
        _restored_artifacts_root,
        rows,
        _compare_a,
        _compare_b,
        _run_update,
    ) = restore_history_run_bundle(
        repo=repo,
        zip_file_path=tampered_zip,
        overwrite_existing=False,
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
    )

    assert restore_status.startswith("Restore failed.")
    assert "RESTORE_INVALID_ARCHIVE" in restore_details
    assert "manifest_verification=failed" in restore_details
    assert rows == []


def test_restore_history_run_bundle_verify_only_signed(
    tmp_path: Path,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-verify-only-ui")
    run_id = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="confirmed",
            ask="",
            gap="",
            question="",
        ),
        tokens=22,
        total_cost=0.03,
        total_time_ms=11.0,
    )
    export_status, zip_path, _download = export_history_run_bundle(
        repo=repo,
        run_id=run_id,
        signing_key="ui-sign-key",
    )
    assert "Export completed." in export_status
    repo.delete_run(run_id)

    (
        restore_status,
        restore_details,
        restored_run_id,
        restored_artifacts_root,
        rows,
        compare_a,
        compare_b,
        run_id_update,
    ) = restore_history_run_bundle(
        repo=repo,
        zip_file_path=zip_path,
        overwrite_existing=False,
        verify_only=True,
        require_signature=True,
        signing_key="ui-sign-key",
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
    )

    assert "Verification completed." in restore_status
    assert restored_run_id == run_id
    assert "signature_verification=verified" in restore_details
    assert "archive_signed=True" in restore_details
    assert "strict_mode=True" in restore_details
    assert "verify_only=True" in restore_details
    assert not Path(restored_artifacts_root).exists()
    assert rows == []
    assert compare_a["choices"] == []
    assert compare_b["choices"] == []
    assert repo.get_run(run_id) is None


def test_restore_history_run_bundle_strict_rejects_unsigned(tmp_path: Path) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")
    session = repo.create_session("session-strict-unsigned-ui")
    run_id = _seed_history_run_for_compare(
        repo=repo,
        session_id=session.session_id,
        provider="openai",
        model="gpt-5.1",
        prompt_version="v001",
        payload=_comparison_payload(
            status="confirmed",
            ask="",
            gap="",
            question="",
        ),
        tokens=10,
        total_cost=0.01,
        total_time_ms=8.0,
    )
    export_status, zip_path, _download = export_history_run_bundle(
        repo=repo,
        run_id=run_id,
    )
    assert "Export completed." in export_status
    repo.delete_run(run_id)

    (
        restore_status,
        restore_details,
        _restored_run_id,
        _restored_artifacts_root,
        rows,
        _compare_a,
        _compare_b,
        _run_update,
    ) = restore_history_run_bundle(
        repo=repo,
        zip_file_path=zip_path,
        overwrite_existing=False,
        verify_only=False,
        require_signature=True,
        signing_key="ui-sign-key",
        session_id=session.session_id,
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
    )

    assert restore_status.startswith("Restore failed.")
    assert "RESTORE_INVALID_SIGNATURE" in restore_details
    assert "strict_mode=True" in restore_details
    assert rows == []


def test_restore_history_run_bundle_shows_rollback_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = StorageRepo(db_path=tmp_path / "kaucja.sqlite3")

    def _restore_stub(**_: Any) -> RestoreRunResult:
        return RestoreRunResult(
            status="failed",
            run_id="run-x",
            session_id="session-x",
            artifacts_root_path="/tmp/path",
            restored_paths=[],
            warnings=[],
            errors=["metadata failed"],
            error_code="RESTORE_DB_ERROR",
            error_message="metadata failed",
            manifest_verification_status="verified",
            files_checked=7,
            signature_verification_status="verified",
            archive_signed=True,
            signature_required=True,
            verify_only=False,
            rollback_attempted=True,
            rollback_succeeded=False,
        )

    monkeypatch.setattr(gradio_app_module, "restore_run_bundle", _restore_stub)

    (
        restore_status,
        restore_details,
        _restored_run_id,
        _restored_artifacts_root,
        _rows,
        _compare_a,
        _compare_b,
        _run_update,
    ) = restore_history_run_bundle(
        repo=repo,
        zip_file_path=tmp_path / "not-used.zip",
        overwrite_existing=False,
        session_id="",
        provider="",
        model="",
        prompt_version="",
        date_from="",
        date_to="",
        limit=20,
    )

    assert restore_status.startswith("Restore failed.")
    assert "manifest_verification=verified" in restore_details
    assert "rollback_attempted=True" in restore_details
    assert "rollback_succeeded=False" in restore_details


def test_run_full_pipeline_ui_reports_configuration_error_for_invalid_model(
    tmp_path: Path,
) -> None:
    file_one = tmp_path / "one.pdf"
    file_one.write_bytes(b"one")

    orchestrator = FakeOrchestrator()
    (status, *rest) = run_full_pipeline_ui(
        orchestrator=orchestrator,
        prompt_name="kaucja_gap_analysis",
        current_session_id="",
        uploaded_files=[file_one],
        provider="google",
        model="gpt-5.1",
        prompt_version="v001",
        ocr_model="mistral-ocr-latest",
        table_format="html",
        include_image_base64=True,
        openai_reasoning_effort="auto",
        gemini_thinking_level="auto",
        preflight_checker=lambda provider: None,
    )

    assert (
        "Configuration error: Model 'gpt-5.1' is not supported by provider 'google'."
        in status
    )


def test_build_model_choices_returns_all_models_when_provider_is_none() -> None:
    from app.ui.gradio_app import _build_model_choices
    from app.config.settings import Settings

    settings = Settings(
        env="test",
        openai_api_key="sk-test",
        google_api_key="AIzaSyTest",
        providers_config={
            "llm_providers": {
                "google": {"models": {"gemini-2.5-flash": {}}},
                "openai": {"models": {"gpt-5.1": {}}},
            }
        },
    )

    choices = _build_model_choices(settings=settings, provider=None)
    assert "gemini-2.5-flash" in choices
    assert "gpt-5.1" in choices
    assert len(choices) >= 2


def test_on_provider_change_ui_selects_default_model_from_provider() -> None:
    from app.ui.gradio_app import on_provider_change_ui

    result = on_provider_change_ui("google")
    assert "gemini-2.5-flash" in result["choices"]
    assert "gemini-2.5-pro" in result["choices"]
    assert result["value"] == "gemini-2.5-flash"
