from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from legal_docs_pipeline.batch import (
    BatchJobSnapshot,
    BatchResultItem,
    build_batch_custom_id,
    build_batch_jsonl_item,
    parse_batch_output_line,
)
from legal_docs_pipeline.batch_repository import MongoBatchStateRepository
from legal_docs_pipeline.batch_runner import BatchAnalysisRunner, BatchRunOptions
from legal_docs_pipeline.constants import PipelineMode
from legal_docs_pipeline.llm import StructuredLlmResponse, StructuredLlmUsage
from tests.fake_mongo_runtime import FakeMongoCollection
from tests.legal_docs_pipeline.test_pipeline import (
    PROJECT_ROOT,
    ScriptedLlmClient,
    _analysis_payload,
    _build_classification_result,
    _build_config,
    _translation_payload,
    _write_judicial_doc,
)
from legal_docs_pipeline.repository import MongoDocumentRepository
from legal_docs_pipeline.pipeline import AnnotationPipeline, PipelineRunOptions


class FakeBatchClient:
    def __init__(
        self,
        *,
        output_payloads: dict[str, dict[str, Any]] | None = None,
        error_payloads: dict[str, dict[str, Any]] | None = None,
        job_status: str = "completed",
        output_file_id: str | None = "file_out_1",
        error_file_id: str | None = "file_err_1",
    ) -> None:
        self.created_jobs: list[dict[str, Any]] = []
        self.output_payloads = output_payloads or {}
        self.error_payloads = error_payloads or {}
        self.job_status = job_status
        self.output_file_id = output_file_id
        self.error_file_id = error_file_id

    def create_job(
        self,
        *,
        jsonl_items: list[dict[str, Any]],
        metadata: dict[str, str],
    ) -> BatchJobSnapshot:
        job_id = f"batch_{len(self.created_jobs) + 1}"
        self.created_jobs.append(
            {
                "job_id": job_id,
                "jsonl_items": jsonl_items,
                "metadata": metadata,
            }
        )
        return BatchJobSnapshot(
            job_id=job_id,
            status="submitted",
            input_file_id="file_in_1",
            output_file_id=None,
            error_file_id=None,
            submitted_at=datetime.now(tz=timezone.utc),
            completed_at=None,
            raw_payload={"id": job_id, "status": "submitted"},
        )

    def retrieve_job(self, job_id: str) -> BatchJobSnapshot:
        return BatchJobSnapshot(
            job_id=job_id,
            status=self.job_status,
            input_file_id="file_in_1",
            output_file_id=self.output_file_id,
            error_file_id=self.error_file_id,
            submitted_at=datetime.now(tz=timezone.utc),
            completed_at=datetime.now(tz=timezone.utc),
            raw_payload={"id": job_id, "status": self.job_status},
        )

    def download_results(self, *, output_file_id: str | None) -> list[BatchResultItem]:
        if not self.created_jobs:
            return []
        items = self.created_jobs[-1]["jsonl_items"]
        results: list[BatchResultItem] = []
        for item in items:
            custom_id = item["custom_id"]
            if custom_id not in self.output_payloads:
                continue
            response = StructuredLlmResponse(
                response_id=f"resp_{custom_id}",
                output_payload=self.output_payloads[custom_id],
                raw_json=json.dumps(self.output_payloads[custom_id], ensure_ascii=False),
                status="completed",
                completed_at=datetime.now(tz=timezone.utc),
                duration_ms=0,
                usage=StructuredLlmUsage(
                    input_tokens=100,
                    output_tokens=200,
                    reasoning_tokens=20,
                ),
            )
            results.append(
                BatchResultItem(
                    custom_id=custom_id,
                    status="completed",
                    response=response,
                    error_payload=None,
                    raw_payload={"custom_id": custom_id},
                )
            )
        return results

    def download_errors(self, *, error_file_id: str | None) -> list[BatchResultItem]:
        if not self.created_jobs:
            return []
        items = self.created_jobs[-1]["jsonl_items"]
        results: list[BatchResultItem] = []
        for item in items:
            custom_id = item["custom_id"]
            if custom_id not in self.error_payloads:
                continue
            results.append(
                BatchResultItem(
                    custom_id=custom_id,
                    status="failed",
                    response=None,
                    error_payload=self.error_payloads[custom_id],
                    raw_payload={"custom_id": custom_id},
                )
            )
        return results


def test_build_batch_jsonl_item_has_stable_custom_id() -> None:
    request = _build_configured_analysis_request()

    item = build_batch_jsonl_item(request)

    assert item["custom_id"] == build_batch_custom_id(
        doc_id="doc.md",
        stage="annotate_original",
        request_hash=request.request_hash,
    )
    assert item["method"] == "POST"
    assert item["url"] == "/v1/responses"
    assert item["body"]["text"]["format"]["type"] == "json_schema"


def test_parse_batch_output_line_extracts_structured_json() -> None:
    line = json.dumps(
        {
            "custom_id": "doc.md::annotate_original::hash-1",
            "response": {
                "body": {
                    "id": "resp_1",
                    "status": "completed",
                    "completed_at": 1_763_500_000,
                    "usage": {
                        "input_tokens": 10,
                        "output_tokens": 20,
                        "output_tokens_details": {"reasoning_tokens": 3},
                    },
                    "output": [
                        {
                            "type": "message",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": json.dumps(_analysis_payload()),
                                }
                            ],
                        }
                    ],
                }
            },
        }
    )

    parsed = parse_batch_output_line(line)

    assert parsed.status == "completed"
    assert parsed.response is not None
    assert parsed.response.output_payload["semantic"]["document_type_code"] == "pl_judgment"


def test_batch_runner_prepare_submit_poll_apply_success(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    config = _build_config(tmp_path=tmp_path, input_root=input_root).model_copy(
        update={
            "pipeline": _build_config(tmp_path=tmp_path, input_root=input_root).pipeline.model_copy(
                update={"batch_min_requests_to_submit": 1}
            )
        }
    )
    document_repository = _build_document_repository()
    batch_repository = _build_batch_repository()
    prepare_pipeline = AnnotationPipeline(
        config=config,
        repository_factory=lambda _config: document_repository,
        llm_client=ScriptedLlmClient(script=[_translation_payload()]),
    )
    batch_client = FakeBatchClient()
    runner = BatchAnalysisRunner(
        config=config,
        pipeline=prepare_pipeline,
        document_repository_factory=lambda _config: document_repository,
        batch_repository_factory=lambda _config: batch_repository,
        batch_client=batch_client,
    )

    prepare_summary = runner.prepare(
        options=BatchRunOptions(mode=PipelineMode.FULL)
    )
    queued_items = batch_repository.list_queued_items()
    assert len(queued_items) == 1
    batch_client.output_payloads = {
        str(queued_items[0]["custom_id"]): _analysis_payload()
    }
    submit_summary = runner.submit()
    poll_summary = runner.poll()
    apply_summary = runner.apply()
    stored = document_repository.get_document("doc.md")

    assert prepare_summary.queued_count == 1
    assert submit_summary.submitted_jobs_count == 1
    assert poll_summary.polled_jobs_count == 1
    assert apply_summary.completed_count == 1
    assert apply_summary.batch_success_count == 1
    assert stored is not None
    assert stored["annotation"]["status"] == "completed"
    assert stored["llm"]["analysis"]["dispatch"]["mode"] == "batch_analysis"
    assert stored["llm"]["analysis"]["dispatch"]["status"] == "applied"


def test_batch_runner_failed_item_falls_back_to_direct_analysis(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    config = _build_config(tmp_path=tmp_path, input_root=input_root).model_copy(
        update={
            "pipeline": _build_config(tmp_path=tmp_path, input_root=input_root).pipeline.model_copy(
                update={"batch_min_requests_to_submit": 1}
            )
        }
    )
    document_repository = _build_document_repository()
    batch_repository = _build_batch_repository()
    pipeline = AnnotationPipeline(
        config=config,
        repository_factory=lambda _config: document_repository,
        llm_client=ScriptedLlmClient(script=[_analysis_payload(), _translation_payload()]),
    )
    batch_client = FakeBatchClient()
    runner = BatchAnalysisRunner(
        config=config,
        pipeline=pipeline,
        document_repository_factory=lambda _config: document_repository,
        batch_repository_factory=lambda _config: batch_repository,
        batch_client=batch_client,
    )

    runner.prepare(options=BatchRunOptions(mode=PipelineMode.FULL))
    queued_items = batch_repository.list_queued_items()
    assert len(queued_items) == 1
    batch_client.error_payloads = {
        str(queued_items[0]["custom_id"]): {
            "code": "provider_error",
            "message": "Malformed provider output.",
        }
    }
    runner.submit()
    runner.poll()
    apply_summary = runner.apply()
    stored = document_repository.get_document("doc.md")

    assert apply_summary.completed_count == 1
    assert apply_summary.direct_fallback_count == 1
    assert apply_summary.batch_failed_count == 1
    assert stored is not None
    assert stored["annotation"]["status"] == "completed"
    assert stored["llm"]["analysis"]["dispatch"]["fallback"] == "direct"


def test_pipeline_run_honors_batch_dispatch_mode(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    base_config = _build_config(tmp_path=tmp_path, input_root=input_root)
    config = base_config.model_copy(
        update={
            "pipeline": base_config.pipeline.model_copy(
                update={
                    "llm_dispatch_mode": "batch_analysis",
                    "batch_min_requests_to_submit": 1,
                }
            )
        }
    )
    document_repository = _build_document_repository()
    batch_repository = _build_batch_repository(config=config)
    pipeline = AnnotationPipeline(
        config=config,
        repository_factory=lambda _config: document_repository,
        batch_repository_factory=lambda _config: batch_repository,
        llm_client=ScriptedLlmClient(script=[]),
    )

    summary = pipeline.run(
        options=PipelineRunOptions(
            mode=PipelineMode.FULL,
            only_doc_id="doc.md",
        )
    )
    stored = document_repository.get_document("doc.md")
    queued_items = batch_repository.list_queued_items()

    assert summary.queued_count == 1
    assert summary.completed_count == 0
    assert stored is not None
    assert stored["processing"]["status"] == "awaiting_batch_analysis"
    assert stored["llm"]["analysis"]["dispatch"]["mode"] == "batch_analysis"
    assert len(queued_items) == 1
    assert queued_items[0]["cost_estimate"]["dispatch_mode"] == "batch_analysis"
    assert queued_items[0]["cost_estimate"]["batch_discount_factor"] == 0.5


def test_batch_runner_prepare_reports_existing_item_on_repeat(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    base_config = _build_config(tmp_path=tmp_path, input_root=input_root)
    config = base_config.model_copy(
        update={
            "pipeline": base_config.pipeline.model_copy(
                update={"batch_min_requests_to_submit": 1}
            )
        }
    )
    document_repository = _build_document_repository()
    batch_repository = _build_batch_repository(config=config)
    runner = BatchAnalysisRunner(
        config=config,
        pipeline=AnnotationPipeline(
            config=config,
            repository_factory=lambda _config: document_repository,
            batch_repository_factory=lambda _config: batch_repository,
            llm_client=ScriptedLlmClient(script=[]),
        ),
        document_repository_factory=lambda _config: document_repository,
        batch_repository_factory=lambda _config: batch_repository,
        batch_client=FakeBatchClient(),
    )

    first_summary = runner.prepare(options=BatchRunOptions(mode=PipelineMode.FULL))
    second_summary = runner.prepare(options=BatchRunOptions(mode=PipelineMode.FULL))

    assert first_summary.queued_count == 1
    assert second_summary.queued_count == 0
    assert second_summary.existing_item_count == 1


def test_batch_runner_apply_marks_stale_item_without_overwrite(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    base_config = _build_config(tmp_path=tmp_path, input_root=input_root)
    config = base_config.model_copy(
        update={
            "pipeline": base_config.pipeline.model_copy(
                update={"batch_min_requests_to_submit": 1}
            )
        }
    )
    document_repository = _build_document_repository()
    batch_repository = _build_batch_repository(config=config)
    runner = BatchAnalysisRunner(
        config=config,
        pipeline=AnnotationPipeline(
            config=config,
            repository_factory=lambda _config: document_repository,
            batch_repository_factory=lambda _config: batch_repository,
            llm_client=ScriptedLlmClient(script=[_translation_payload()]),
        ),
        document_repository_factory=lambda _config: document_repository,
        batch_repository_factory=lambda _config: batch_repository,
        batch_client=FakeBatchClient(),
    )

    runner.prepare(options=BatchRunOptions(mode=PipelineMode.FULL))
    queued_items = batch_repository.list_queued_items()
    assert len(queued_items) == 1
    queued_item = queued_items[0]
    runner._batch_client.output_payloads = {
        str(queued_item["custom_id"]): _analysis_payload()
    }
    runner.submit()
    runner.poll()
    document_repository.update_analysis_dispatch(
        doc_id="doc.md",
        dispatch_updates={
            "mode": "batch_analysis",
            "status": "queued",
            "custom_id": "doc.md::annotate_original::newer-request",
            "request_hash": "newer-request",
            "analysis_fingerprint": "newer-fingerprint",
        },
    )
    apply_summary = runner.apply()
    stored = document_repository.get_document("doc.md")
    stale_item = batch_repository.get_item(str(queued_item["custom_id"]))

    assert apply_summary.stale_count == 1
    assert apply_summary.completed_count == 0
    assert stale_item is not None
    assert stale_item["apply_status"] == "stale"
    assert stored is not None
    assert stored["llm"]["analysis"]["dispatch"]["custom_id"] == (
        "doc.md::annotate_original::newer-request"
    )


def test_batch_runner_missing_error_line_falls_back_to_direct(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    base_config = _build_config(tmp_path=tmp_path, input_root=input_root)
    config = base_config.model_copy(
        update={
            "pipeline": base_config.pipeline.model_copy(
                update={"batch_min_requests_to_submit": 1}
            )
        }
    )
    document_repository = _build_document_repository()
    batch_repository = _build_batch_repository(config=config)
    pipeline = AnnotationPipeline(
        config=config,
        repository_factory=lambda _config: document_repository,
        batch_repository_factory=lambda _config: batch_repository,
        llm_client=ScriptedLlmClient(script=[_analysis_payload(), _translation_payload()]),
    )
    runner = BatchAnalysisRunner(
        config=config,
        pipeline=pipeline,
        document_repository_factory=lambda _config: document_repository,
        batch_repository_factory=lambda _config: batch_repository,
        batch_client=FakeBatchClient(
            job_status="failed",
            output_file_id=None,
            error_file_id=None,
        ),
    )

    runner.prepare(options=BatchRunOptions(mode=PipelineMode.FULL))
    runner.submit()
    runner.poll()
    apply_summary = runner.apply()
    stored = document_repository.get_document("doc.md")

    assert apply_summary.completed_count == 1
    assert apply_summary.direct_fallback_count == 1
    assert apply_summary.batch_failed_count == 1
    assert stored is not None
    assert stored["annotation"]["status"] == "completed"


def _build_document_repository() -> MongoDocumentRepository:
    repository = MongoDocumentRepository(
        collection=FakeMongoCollection(),
        schema_version="2.0.0",
        pipeline_version="2.0.0",
        dedup_version="2.0.0",
        router_version="2.0.0",
        history_tail_size=10,
    )
    repository.ensure_indexes()
    return repository

def _build_batch_repository(*, config=None) -> MongoBatchStateRepository:
    repository = MongoBatchStateRepository(
        jobs_collection=FakeMongoCollection(),
        items_collection=FakeMongoCollection(),
        target_database=(
            config.mongo.database if config is not None else "kaucja_legal_corpus"
        ),
        target_collection=(
            config.mongo.collection if config is not None else "documents"
        ),
        schema_version="2.0.0",
        jobs_collection_name="analysis_batch_jobs_v2",
        items_collection_name="analysis_batch_items_v2",
    )
    repository.ensure_indexes()
    return repository


def _build_configured_analysis_request():
    input_root = PROJECT_ROOT / "docs/legal/cas_law_v2_2_md"
    config = _build_config(tmp_path=PROJECT_ROOT / "tmp", input_root=input_root)
    pipeline = AnnotationPipeline(
        config=config,
        repository_factory=lambda _config: _build_document_repository(),
        llm_client=ScriptedLlmClient(script=[]),
    )
    return pipeline._build_analysis_request(
        run_id="run-1",
        doc_id="doc.md",
        classification=_build_classification_result(),
        language_code="pl",
        parse_metadata={"canonical_doc_uid": "saos_pl:123"},
        title="WYROK",
        canonical_result=_build_canonical_result_for_batch(),
        resolved_prompt=pipeline.prompt_resolver.resolve_analysis_prompt(
            _build_classification_result().prompt_profile,
            source_language_code="pl",
        ),
    )


def _build_canonical_result_for_batch():
    from legal_docs_pipeline.canonicalize import CanonicalTextResult
    from legal_docs_pipeline.reader import TextStats

    return CanonicalTextResult(
        canonical_text="WYROK\nSygn. akt I C 1/20",
        canonical_text_sha256="canonical-sha",
        text_preview="WYROK\nSygn. akt I C 1/20",
        text_stats_raw=TextStats(chars=24, lines=2, words=6),
        text_stats_canonical=TextStats(chars=24, lines=2, words=6),
        strategy="plain_markdown",
        sections=(),
    )
