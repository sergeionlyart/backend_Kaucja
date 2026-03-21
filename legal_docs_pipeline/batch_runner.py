"""Operator-driven batch runner for annotate_original."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from time import sleep
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .batch import (
    BatchClient,
    BatchResultItem,
    OpenAIResponsesBatchClient,
    deserialize_analysis_request_record,
)
from .batch_repository import MongoBatchStateRepository
from .logging import JsonlPipelineLogger
from .pipeline import (
    AnalysisBusinessValidationError,
    AnnotationPipeline,
    PipelineRunOptions,
    _build_failed_llm_updates,
    _default_log_dir,
    _log,
)
from .repository import MongoDocumentRepository
from .constants import LlmDispatchMode, PipelineMode
from .llm import LlmCallError, StructuredLlmRequest, StructuredLlmResponse


@dataclass(frozen=True, slots=True)
class BatchRunOptions:
    mode: PipelineMode
    limit: int | None = None
    only_doc_id: str | None = None
    from_relative_path: str | None = None
    force_classifier_fallback: bool = False
    log_level: str = "INFO"


class BatchCommandSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    config_path: Path
    run_id: str
    input_root: Path
    mongo_database: str
    mongo_collection: str
    log_path: Path
    discovered_count: int = 0
    queued_count: int = 0
    existing_item_count: int = 0
    skipped_count: int = 0
    skipped_non_target_count: int = 0
    completed_count: int = 0
    partial_count: int = 0
    failed_count: int = 0
    direct_fallback_count: int = 0
    batch_success_count: int = 0
    batch_failed_count: int = 0
    expired_count: int = 0
    stale_count: int = 0
    submitted_jobs_count: int = 0
    polled_jobs_count: int = 0
    applied_items_count: int = 0
    warnings: list[str] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class _ApplyItemResult:
    outcome: str
    provider_status: str
    via_fallback: bool = False
    from_batch_success: bool = False


class BatchAnalysisRunner:
    def __init__(
        self,
        *,
        config,
        pipeline: AnnotationPipeline | None = None,
        document_repository_factory=None,
        batch_repository_factory=None,
        batch_client: BatchClient | None = None,
    ) -> None:
        self.config = config
        self.pipeline = pipeline or AnnotationPipeline(config=config)
        self._document_repository_factory = (
            document_repository_factory or MongoDocumentRepository.from_config
        )
        self._batch_repository_factory = (
            batch_repository_factory or MongoBatchStateRepository.from_config
        )
        self._batch_client = batch_client or OpenAIResponsesBatchClient(
            timeout_seconds=config.model.request_timeout_seconds
        )

    def prepare(self, *, options: BatchRunOptions) -> BatchCommandSummary:
        run_id, logger, discovered, summary = self._initialize_batch_run(
            action="prepare",
            options=options,
        )
        self.pipeline.prompt_resolver.validate_prompt_pack()
        document_repository = self._document_repository_factory(self.config)
        batch_repository = self._batch_repository_factory(self.config)
        try:
            document_repository.ensure_indexes()
            batch_repository.ensure_indexes()
            for document in discovered:
                doc_id = document.relative_path.as_posix()
                existing = document_repository.get_document(doc_id)
                action = self.pipeline._select_document_action(
                    existing=existing,
                    document=document,
                    options=PipelineRunOptions(mode=options.mode),
                    rerun_scope=None,
                )
                if action == "skip_unchanged":
                    document_repository.touch_seen(doc_id=doc_id, run_id=run_id)
                    summary.skipped_count += 1
                    continue
                write_result = document_repository.upsert_discovered(
                    discovered=document,
                    input_root=self.config.input.root_path,
                    run_id=run_id,
                    mode=options.mode.value,
                )
                _ = write_result
                if action == "resume_translation":
                    outcome = self.pipeline._resume_translation(
                        repository=document_repository,
                        existing=existing,
                        doc_id=doc_id,
                        mode=options.mode.value,
                        run_id=run_id,
                        logger=logger,
                    )
                    self._record_outcome(summary, outcome)
                    continue
                outcome = self.pipeline._process_full_document(
                    repository=document_repository,
                    batch_repository=batch_repository,
                    document=document,
                    doc_id=doc_id,
                    mode=options.mode.value,
                    run_id=run_id,
                    force_classifier_fallback=options.force_classifier_fallback,
                    logger=logger,
                    dispatch_mode=LlmDispatchMode.BATCH_ANALYSIS,
                )
                self._record_outcome(summary, outcome)
        finally:
            batch_repository.close()
            document_repository.close()
        return summary

    def submit(self, *, log_level: str = "INFO") -> BatchCommandSummary:
        run_id, logger, discovered, summary = self._initialize_batch_run(
            action="submit",
            options=BatchRunOptions(mode=PipelineMode.NEW, log_level=log_level),
            discover_documents=False,
        )
        summary.discovered_count = len(discovered)
        batch_repository = self._batch_repository_factory(self.config)
        try:
            batch_repository.ensure_indexes()
            inflight_count = batch_repository.count_inflight_jobs()
            available_slots = max(
                0,
                self.config.pipeline.batch_inflight_jobs_limit - inflight_count,
            )
            if available_slots == 0:
                summary.warnings.append("Batch inflight jobs limit already reached.")
                return summary
            queued_items = batch_repository.list_queued_items()
            if not queued_items:
                return summary
            queued_count = len(queued_items)
            below_submit_threshold = (
                queued_count < self.config.pipeline.batch_min_requests_to_submit
            )
            should_flush_tail_batch = below_submit_threshold and inflight_count == 0
            if below_submit_threshold and not should_flush_tail_batch:
                summary.warnings.append(
                    "Queued batch items are below batch_min_requests_to_submit."
                )
                return summary
            if should_flush_tail_batch:
                _log(
                    logger,
                    run_id=run_id,
                    stage="batch",
                    event="batch_tail_flush_submitted",
                    level="info",
                    message=(
                        "Submitting trailing queued batch items below "
                        "batch_min_requests_to_submit because no inflight "
                        "jobs remain."
                    ),
                    details={
                        "queued_count": queued_count,
                        "batch_min_requests_to_submit": (
                            self.config.pipeline.batch_min_requests_to_submit
                        ),
                    },
                )
            chunks = _chunk_queued_items(
                queued_items=queued_items,
                max_requests=self.config.pipeline.batch_max_requests,
                max_input_file_bytes=self.config.pipeline.batch_max_input_file_bytes,
            )
            document_repository = self._document_repository_factory(self.config)
            try:
                for chunk in chunks[:available_slots]:
                    jsonl_items = [dict(item["request_body"]) for item in chunk]
                    batch_snapshot = self._batch_client.create_job(
                        jsonl_items=jsonl_items,
                        metadata={
                            "run_id": run_id,
                            "prompt_pack_version": self.config.prompts.prompt_pack_version,
                        },
                    )
                    custom_ids = [str(item["custom_id"]) for item in chunk]
                    batch_repository.mark_submitted(
                        batch_job_id=batch_snapshot.job_id,
                        custom_ids=custom_ids,
                        raw_payload=batch_snapshot.raw_payload,
                    )
                    for item in chunk:
                        document_repository.update_analysis_dispatch(
                            doc_id=str(item["doc_id"]),
                            dispatch_updates={
                                "mode": "batch_analysis",
                                "status": "submitted",
                                "custom_id": str(item["custom_id"]),
                                "batch_job_id": batch_snapshot.job_id,
                            },
                        )
                    summary.submitted_jobs_count += 1
            finally:
                document_repository.close()
        finally:
            batch_repository.close()
        return summary

    def poll(
        self,
        *,
        log_level: str = "INFO",
        wait: bool = False,
    ) -> BatchCommandSummary:
        run_id, logger, discovered, summary = self._initialize_batch_run(
            action="poll",
            options=BatchRunOptions(mode=PipelineMode.NEW, log_level=log_level),
            discover_documents=False,
        )
        summary.discovered_count = len(discovered)
        batch_repository = self._batch_repository_factory(self.config)
        try:
            while True:
                jobs = batch_repository.get_inflight_jobs()
                if not jobs:
                    break
                for job in jobs:
                    batch_job_id = str(job["batch_job_id"])
                    snapshot = self._batch_client.retrieve_job(batch_job_id)
                    batch_repository.update_job_status(
                        batch_job_id=snapshot.job_id,
                        status=snapshot.status,
                        raw_payload=snapshot.raw_payload,
                        output_file_id=snapshot.output_file_id,
                        error_file_id=snapshot.error_file_id,
                        completed_at=snapshot.completed_at,
                    )
                    summary.polled_jobs_count += 1
                    _log(
                        logger,
                        run_id=run_id,
                        stage="batch",
                        event="batch_job_polled",
                        level="info",
                        message=f"Polled batch job {snapshot.job_id}.",
                        details={"job_id": snapshot.job_id, "status": snapshot.status},
                    )
                if not wait:
                    break
                if not batch_repository.get_inflight_jobs():
                    break
                sleep(self.config.pipeline.batch_poll_interval_seconds)
        finally:
            batch_repository.close()
        return summary

    def apply(self, *, log_level: str = "INFO") -> BatchCommandSummary:
        run_id, logger, discovered, summary = self._initialize_batch_run(
            action="apply",
            options=BatchRunOptions(mode=PipelineMode.NEW, log_level=log_level),
            discover_documents=False,
        )
        summary.discovered_count = len(discovered)
        document_repository = self._document_repository_factory(self.config)
        batch_repository = self._batch_repository_factory(self.config)
        try:
            jobs = batch_repository.get_terminal_jobs_ready_for_apply()
            for job in jobs:
                batch_job_id = str(job["batch_job_id"])
                try:
                    summary = self._apply_one_job(
                        summary=summary,
                        job=job,
                        run_id=run_id,
                        logger=logger,
                        document_repository=document_repository,
                        batch_repository=batch_repository,
                    )
                    batch_repository.update_job_apply_status(
                        batch_job_id=batch_job_id,
                        apply_status=self._derive_job_apply_status(
                            batch_repository=batch_repository,
                            batch_job_id=batch_job_id,
                        ),
                    )
                except Exception as error:
                    batch_repository.update_job_apply_status(
                        batch_job_id=batch_job_id,
                        apply_status="apply_failed",
                    )
                    warning = f"Failed to apply batch job {batch_job_id}: {error}"
                    summary.warnings.append(warning)
                    _log(
                        logger,
                        run_id=run_id,
                        stage="batch",
                        event="batch_apply_failed",
                        level="error",
                        message=warning,
                        details={"batch_job_id": batch_job_id},
                    )
        finally:
            batch_repository.close()
            document_repository.close()
        return summary

    def _apply_one_job(
        self,
        *,
        summary: BatchCommandSummary,
        job: dict[str, Any],
        run_id: str,
        logger: JsonlPipelineLogger,
        document_repository: MongoDocumentRepository,
        batch_repository: MongoBatchStateRepository,
    ) -> BatchCommandSummary:
        batch_job_id = str(job["batch_job_id"])
        items = batch_repository.list_items_for_job(batch_job_id)
        provider_status = str(job.get("provider_status", job.get("status", "")))
        success_items: dict[str, BatchResultItem] = {}
        error_items: dict[str, BatchResultItem] = {}
        if job.get("output_file_id"):
            success_items = {
                item.custom_id: item
                for item in self._batch_client.download_results(
                    output_file_id=job.get("output_file_id")
                )
            }
        if job.get("error_file_id"):
            error_items = {
                item.custom_id: item
                for item in self._batch_client.download_errors(
                    error_file_id=job.get("error_file_id")
                )
            }
        for item in items:
            apply_status = str(item.get("apply_status", "pending"))
            if apply_status in {
                "applied_success",
                "applied_failed",
                "fallback_completed",
                "fallback_failed",
                "stale",
            }:
                continue
            custom_id = str(item["custom_id"])
            if custom_id in success_items:
                result = success_items[custom_id]
                apply_result = self._apply_success_item(
                    item=item,
                    result=result,
                    batch_job_id=batch_job_id,
                    run_id=run_id,
                    logger=logger,
                    document_repository=document_repository,
                    batch_repository=batch_repository,
                )
                self._update_apply_summary(summary=summary, result=apply_result)
                self._record_outcome(summary, apply_result.outcome)
                summary.applied_items_count += 1
                continue
            failure_item = error_items.get(custom_id)
            apply_result = self._apply_failed_item(
                item=item,
                batch_job_id=batch_job_id,
                job_provider_status=provider_status,
                provider_failure=failure_item,
                run_id=run_id,
                logger=logger,
                document_repository=document_repository,
                batch_repository=batch_repository,
            )
            self._update_apply_summary(summary=summary, result=apply_result)
            self._record_outcome(summary, apply_result.outcome)
            summary.applied_items_count += 1
        return summary

    def _apply_success_item(
        self,
        *,
        item: dict[str, Any],
        result: BatchResultItem,
        batch_job_id: str,
        run_id: str,
        logger: JsonlPipelineLogger,
        document_repository: MongoDocumentRepository,
        batch_repository: MongoBatchStateRepository,
    ) -> _ApplyItemResult:
        custom_id = str(item["custom_id"])
        provider_status = str(result.status or "completed")
        batch_repository.mark_item_provider_state(
            custom_id=custom_id,
            provider_status=provider_status,
            completed_at=result.response.completed_at if result.response else None,
        )
        if self._is_stale_item(item=item, document_repository=document_repository):
            batch_repository.mark_item_apply_state(
                custom_id=custom_id,
                apply_status="stale",
            )
            return _ApplyItemResult(outcome="stale", provider_status=provider_status)
        request = deserialize_analysis_request_record(dict(item["request_record"]))
        if result.response is None:
            return self._apply_failed_item(
                item=item,
                batch_job_id=batch_job_id,
                job_provider_status=provider_status,
                provider_failure=None,
                run_id=run_id,
                logger=logger,
                document_repository=document_repository,
                batch_repository=batch_repository,
                error_payload_override={
                    "code": "batch_success_missing_response",
                    "message": "Batch success item has no structured response payload.",
                },
            )
        outcome = self._finalize_analysis_success(
            doc_id=str(item["doc_id"]),
            source_language_code=str(item["source_language_code"]),
            analysis_fingerprint=str(item["analysis_fingerprint"]),
            request=request,
            response=result.response,
            mode="new",
            run_id=run_id,
            logger=logger,
            document_repository=document_repository,
            dispatch_updates={
                "mode": "batch_analysis",
                "status": "applied",
                "custom_id": custom_id,
                "batch_job_id": batch_job_id,
            },
        )
        if outcome in {"completed", "partial"}:
            batch_repository.mark_item_apply_state(
                custom_id=custom_id,
                apply_status="applied_success",
            )
            return _ApplyItemResult(
                outcome=outcome,
                provider_status=provider_status,
                from_batch_success=True,
            )
        if not self.config.pipeline.batch_apply_direct_fallback:
            batch_repository.mark_item_apply_state(
                custom_id=custom_id,
                apply_status="applied_failed",
                error_payload={
                    "code": "batch_apply_failed",
                    "message": "Batch success payload could not be applied.",
                },
            )
            return _ApplyItemResult(outcome="failed", provider_status=provider_status)
        fallback_outcome = self._run_direct_fallback_for_item(
            item=item,
            batch_job_id=batch_job_id,
            error_payload={
                "code": "batch_apply_failed",
                "message": "Batch success payload could not be applied.",
            },
            run_id=run_id,
            logger=logger,
            document_repository=document_repository,
        )
        batch_repository.mark_item_apply_state(
            custom_id=custom_id,
            apply_status=(
                "fallback_completed"
                if fallback_outcome in {"completed", "partial"}
                else "fallback_failed"
            ),
        )
        return _ApplyItemResult(
            outcome=fallback_outcome,
            provider_status=provider_status,
            via_fallback=True,
        )

    def _apply_failed_item(
        self,
        *,
        item: dict[str, Any],
        batch_job_id: str,
        job_provider_status: str,
        provider_failure: BatchResultItem | None,
        run_id: str,
        logger: JsonlPipelineLogger,
        document_repository: MongoDocumentRepository,
        batch_repository: MongoBatchStateRepository,
        error_payload_override: dict[str, Any] | None = None,
    ) -> _ApplyItemResult:
        custom_id = str(item["custom_id"])
        provider_status = (
            str(provider_failure.raw_payload.get("status", ""))
            if provider_failure is not None
            and isinstance(provider_failure.raw_payload, dict)
            and provider_failure.raw_payload.get("status")
            else job_provider_status
        )
        if provider_status not in {"completed", "failed", "expired", "cancelled"}:
            provider_status = "failed"
        error_payload = error_payload_override or (
            provider_failure.error_payload
            if provider_failure is not None and provider_failure.error_payload is not None
            else {
                "code": "batch_item_missing",
                "message": "Batch item result is missing from provider files.",
                "provider_failure": None,
            }
        )
        batch_repository.mark_item_provider_state(
            custom_id=custom_id,
            provider_status=provider_status,
            error_payload=error_payload,
        )
        if self._is_stale_item(item=item, document_repository=document_repository):
            batch_repository.mark_item_apply_state(
                custom_id=custom_id,
                apply_status="stale",
            )
            return _ApplyItemResult(
                outcome="stale",
                provider_status=provider_status,
            )
        if not self.config.pipeline.batch_apply_direct_fallback:
            batch_repository.mark_item_apply_state(
                custom_id=custom_id,
                apply_status="applied_failed",
                error_payload=error_payload,
            )
            return _ApplyItemResult(outcome="failed", provider_status=provider_status)
        summary_outcome = self._run_direct_fallback_for_item(
            item=item,
            batch_job_id=batch_job_id,
            error_payload=error_payload,
            run_id=run_id,
            logger=logger,
            document_repository=document_repository,
        )
        batch_repository.mark_item_apply_state(
            custom_id=custom_id,
            apply_status=(
                "fallback_completed"
                if summary_outcome in {"completed", "partial"}
                else "fallback_failed"
            ),
            error_payload=error_payload,
        )
        return _ApplyItemResult(
            outcome=summary_outcome,
            provider_status=provider_status,
            via_fallback=True,
        )

    def _run_direct_fallback_for_item(
        self,
        *,
        item: dict[str, Any],
        batch_job_id: str,
        error_payload: dict[str, Any],
        run_id: str,
        logger: JsonlPipelineLogger,
        document_repository: MongoDocumentRepository,
    ) -> str:
        doc_id = str(item["doc_id"])
        discovered_document = self._discover_required_document(doc_id)
        prepared = self.pipeline._prepare_annotatable_document(
            document=discovered_document,
            run_id=run_id,
            allow_classifier_fallback=False,
        )
        if prepared is None:
            return "failed"
        analysis_request = self.pipeline._build_analysis_request(
            run_id=run_id,
            doc_id=doc_id,
            classification=prepared.classification,
            language_code=prepared.language_result.language_code,
            parse_metadata=prepared.parse_result.doc_metadata,
            title=prepared.parse_result.title or prepared.read_result.title,
            canonical_result=prepared.canonical_result,
            resolved_prompt=prepared.resolved_prompt,
        )
        packed_request = self.pipeline._build_analysis_request(
            run_id=run_id,
            doc_id=doc_id,
            classification=prepared.classification,
            language_code=prepared.language_result.language_code,
            parse_metadata=prepared.parse_result.doc_metadata,
            title=prepared.parse_result.title or prepared.read_result.title,
            canonical_result=prepared.canonical_result,
            resolved_prompt=prepared.resolved_prompt,
            force_packed_input=True,
        )
        _log(
            logger,
            run_id=run_id,
            doc_id=doc_id,
            stage="annotate_original",
            event="batch_direct_fallback",
            level="warning",
            message="Falling back to direct analysis after batch item failure.",
            details={
                "batch_job_id": batch_job_id,
                "custom_id": item["custom_id"],
                "error_payload": error_payload,
            },
        )
        try:
            analysis_output, effective_request, effective_response = (
                self.pipeline._run_analysis_with_recovery(
                    run_id=run_id,
                    doc_id=doc_id,
                    logger=logger,
                    source_language_code=prepared.language_result.language_code,
                    analysis_request=analysis_request,
                    packed_analysis_request=packed_request,
                )
            )
        except LlmCallError as error:
            document_repository.mark_failed(
                doc_id=doc_id,
                stage="annotate_original",
                error_code=error.code,
                error_message=error.message,
                error_details=error.details,
                mode="new",
                llm_updates=_build_failed_llm_updates(
                    request=analysis_request,
                    error_code=error.code,
                    error_message=error.message,
                    error_details=error.details,
                ),
                annotation_status="failed",
                llm_block="analysis",
            )
            return "failed"
        return self._finalize_analysis_success(
            doc_id=doc_id,
            source_language_code=prepared.language_result.language_code,
            analysis_fingerprint=prepared.analysis_fingerprint,
            request=effective_request,
            response=effective_response,
            mode="new",
            run_id=run_id,
            logger=logger,
            document_repository=document_repository,
            dispatch_updates={
                "mode": "batch_analysis",
                "status": "fallback_direct_completed",
                "custom_id": item["custom_id"],
                "batch_job_id": batch_job_id,
                "fallback": "direct",
            },
        )

    def _finalize_analysis_success(
        self,
        *,
        doc_id: str,
        source_language_code: str,
        analysis_fingerprint: str,
        request: StructuredLlmRequest,
        response: StructuredLlmResponse,
        mode: str,
        run_id: str,
        logger: JsonlPipelineLogger,
        document_repository: MongoDocumentRepository,
        dispatch_updates: dict[str, Any],
    ) -> str:
        try:
            analysis_output, effective_request, effective_response = (
                self.pipeline._validate_or_repair_analysis_response(
                    run_id=run_id,
                    doc_id=doc_id,
                    logger=logger,
                    source_language_code=source_language_code,
                    analysis_request=request,
                    analysis_response=response,
                )
            )
        except ValidationError as error:
            document_repository.mark_failed(
                doc_id=doc_id,
                stage="annotate_original",
                error_code="llm_schema_validation_error",
                error_message="Analysis repair response failed schema validation.",
                mode=mode,
                llm_updates=_build_failed_llm_updates(
                    request=request,
                    error_code="llm_schema_validation_error",
                    error_message="Analysis repair response failed schema validation.",
                ),
                annotation_status="failed",
                validation_errors=[
                    issue["msg"] for issue in error.errors(include_url=False)
                ],
            )
            return "failed"
        except AnalysisBusinessValidationError as error:
            document_repository.mark_failed(
                doc_id=doc_id,
                stage="annotate_original",
                error_code="llm_schema_validation_error",
                error_message="Analysis repair response failed business validation.",
                mode=mode,
                llm_updates=_build_failed_llm_updates(
                    request=request,
                    error_code="llm_schema_validation_error",
                    error_message="Analysis repair response failed business validation.",
                ),
                annotation_status="failed",
                validation_errors=error.errors,
            )
            return "failed"
        document_repository.apply_analysis_result(
            doc_id=doc_id,
            annotation_output=analysis_output,
            analysis_fingerprint=analysis_fingerprint,
            llm_request=effective_request,
            llm_response=effective_response,
            mode=mode,
            dispatch_updates=dispatch_updates,
            cost_estimate=self.pipeline._estimate_stage_cost(
                request=effective_request,
                response=effective_response,
                dispatch_mode=LlmDispatchMode.BATCH_ANALYSIS,
            ),
        )
        return self.pipeline._run_translation_stage(
            repository=document_repository,
            doc_id=doc_id,
            analysis_output=analysis_output,
            mode=mode,
            run_id=run_id,
            logger=logger,
        )

    def _discover_required_document(self, doc_id: str):
        discovered = self.pipeline.scanner.scan(
            self.config.input.root_path,
            glob_pattern=self.config.input.glob,
            ignore_hidden=self.config.input.ignore_hidden,
            only_doc_id=doc_id,
            limit=1,
        )
        if not discovered:
            raise FileNotFoundError(f"Document not found under input root: {doc_id}")
        return discovered[0]

    def _initialize_batch_run(
        self,
        *,
        action: str,
        options: BatchRunOptions,
        discover_documents: bool = True,
    ) -> tuple[str, JsonlPipelineLogger, list[Any], BatchCommandSummary]:
        if self.config.config_path is None:
            raise ValueError("config_path must be set on PipelineConfig.")
        run_id = f"normadepo-batch-{uuid4().hex[:12]}"
        logger = JsonlPipelineLogger(
            run_id=run_id,
            log_dir=_default_log_dir(self.config.config_path),
            log_level=options.log_level,
        )
        discovered: list[Any] = []
        if discover_documents:
            discovered = self.pipeline.scanner.scan(
                self.config.input.root_path,
                glob_pattern=self.config.input.glob,
                ignore_hidden=self.config.input.ignore_hidden,
                only_doc_id=options.only_doc_id,
                from_relative_path=options.from_relative_path,
                limit=options.limit,
            )
        summary = BatchCommandSummary(
            action=action,
            config_path=self.config.config_path,
            run_id=run_id,
            input_root=self.config.input.root_path,
            mongo_database=self.config.mongo.database,
            mongo_collection=self.config.mongo.collection,
            log_path=logger.log_path,
            discovered_count=len(discovered),
        )
        return run_id, logger, discovered, summary

    @staticmethod
    def _record_outcome(summary: BatchCommandSummary, outcome: str) -> None:
        if outcome == "queued":
            summary.queued_count += 1
        elif outcome == "existing_item":
            summary.existing_item_count += 1
        elif outcome == "stale_replaced":
            summary.queued_count += 1
            summary.stale_count += 1
        elif outcome == "completed":
            summary.completed_count += 1
        elif outcome == "partial":
            summary.partial_count += 1
        elif outcome == "failed":
            summary.failed_count += 1
        elif outcome == "skipped_non_target":
            summary.skipped_non_target_count += 1
        elif outcome == "skipped":
            summary.skipped_count += 1
        elif outcome == "stale":
            summary.stale_count += 1

    @staticmethod
    def _update_apply_summary(
        *,
        summary: BatchCommandSummary,
        result: _ApplyItemResult,
    ) -> None:
        if result.from_batch_success:
            summary.batch_success_count += 1
        elif result.outcome != "stale":
            summary.batch_failed_count += 1
        if result.via_fallback:
            summary.direct_fallback_count += 1
        if result.provider_status == "expired":
            summary.expired_count += 1

    def _derive_job_apply_status(
        self,
        *,
        batch_repository: MongoBatchStateRepository,
        batch_job_id: str,
    ) -> str:
        items = batch_repository.list_items_for_job(batch_job_id)
        apply_statuses = {str(item.get("apply_status", "pending")) for item in items}
        if not items or apply_statuses == {"pending"}:
            return "pending"
        if apply_statuses.issubset(
            {"applied_success", "fallback_completed", "stale", "superseded"}
        ):
            return "fully_applied"
        if "pending" in apply_statuses:
            return "partially_applied"
        if "applied_failed" in apply_statuses or "fallback_failed" in apply_statuses:
            return "apply_failed"
        return "partially_applied"

    @staticmethod
    def _is_stale_item(
        *,
        item: dict[str, Any],
        document_repository: MongoDocumentRepository,
    ) -> bool:
        doc = document_repository.get_document(str(item["doc_id"]))
        if doc is None:
            return True
        dispatch = (
            doc.get("llm", {})
            .get("analysis", {})
            .get("dispatch", {})
        )
        if (
            dispatch.get("mode") == "batch_analysis"
            and dispatch.get("custom_id") == item.get("custom_id")
            and dispatch.get("request_hash") == item.get("request_hash")
            and dispatch.get("analysis_fingerprint") == item.get("analysis_fingerprint")
        ):
            return False
        return True


def _chunk_queued_items(
    *,
    queued_items: list[dict[str, Any]],
    max_requests: int,
    max_input_file_bytes: int,
) -> list[list[dict[str, Any]]]:
    chunks: list[list[dict[str, Any]]] = []
    current_chunk: list[dict[str, Any]] = []
    current_bytes = 0
    for item in queued_items:
        line = json.dumps(item["request_body"], ensure_ascii=False, separators=(",", ":"))
        line_bytes = len(line.encode("utf-8")) + 1
        if current_chunk and (
            len(current_chunk) >= max_requests
            or current_bytes + line_bytes > max_input_file_bytes
        ):
            chunks.append(current_chunk)
            current_chunk = []
            current_bytes = 0
        current_chunk.append(item)
        current_bytes += line_bytes
    if current_chunk:
        chunks.append(current_chunk)
    return chunks
