"""Operator-driven batch runner for annotate_original."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .batch import (
    BatchClient,
    BatchResultItem,
    OpenAIResponsesBatchClient,
    build_batch_custom_id,
    build_batch_jsonl_item,
    deserialize_analysis_request_record,
    serialize_analysis_request_record,
)
from .batch_repository import MongoBatchStateRepository
from .costs import estimate_stage_cost
from .logging import JsonlPipelineLogger
from .pipeline import (
    AnalysisBusinessValidationError,
    AnnotationPipeline,
    PipelineRunOptions,
    _build_failed_llm_updates,
    _default_log_dir,
    _log,
    _log_failure,
)
from .prompts import build_analysis_fingerprint
from .repository import MongoDocumentRepository, RepositoryWriteError
from .router import RoutingInput
from .constants import DocumentFamily, PipelineMode
from .llm import LlmCallError, StructuredLlmRequest, StructuredLlmResponse
from .parser import MarkdownParseError
from .reader import ReadDocumentError
from .canonicalize import CanonicalizeDocumentError, build_canonical_text


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
    skipped_count: int = 0
    skipped_non_target_count: int = 0
    completed_count: int = 0
    partial_count: int = 0
    failed_count: int = 0
    direct_fallback_count: int = 0
    submitted_jobs_count: int = 0
    polled_jobs_count: int = 0
    applied_items_count: int = 0
    warnings: list[str] = Field(default_factory=list)


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
                outcome = self._prepare_and_queue_document(
                    document=document,
                    document_repository=document_repository,
                    batch_repository=batch_repository,
                    mode=options.mode.value,
                    run_id=run_id,
                    force_classifier_fallback=options.force_classifier_fallback,
                    logger=logger,
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
            if len(queued_items) < self.config.pipeline.batch_min_requests_to_submit:
                summary.warnings.append(
                    "Queued batch items are below batch_min_requests_to_submit."
                )
                return summary
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

    def poll(self, *, log_level: str = "INFO") -> BatchCommandSummary:
        run_id, logger, discovered, summary = self._initialize_batch_run(
            action="poll",
            options=BatchRunOptions(mode=PipelineMode.NEW, log_level=log_level),
        )
        summary.discovered_count = len(discovered)
        batch_repository = self._batch_repository_factory(self.config)
        try:
            jobs = batch_repository.get_inflight_jobs()
            for job in jobs:
                snapshot = self._batch_client.retrieve_job(str(job["_id"]))
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
        finally:
            batch_repository.close()
        return summary

    def apply(self, *, log_level: str = "INFO") -> BatchCommandSummary:
        run_id, logger, discovered, summary = self._initialize_batch_run(
            action="apply",
            options=BatchRunOptions(mode=PipelineMode.NEW, log_level=log_level),
        )
        summary.discovered_count = len(discovered)
        document_repository = self._document_repository_factory(self.config)
        batch_repository = self._batch_repository_factory(self.config)
        try:
            jobs = batch_repository.get_terminal_jobs_ready_for_apply()
            for job in jobs:
                summary = self._apply_one_job(
                    summary=summary,
                    job=job,
                    run_id=run_id,
                    logger=logger,
                    document_repository=document_repository,
                    batch_repository=batch_repository,
                )
                batch_repository.mark_job_applied(batch_job_id=str(job["_id"]))
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
        batch_job_id = str(job["_id"])
        items = batch_repository.list_items_for_job(batch_job_id)
        status = str(job.get("status", ""))
        success_items: dict[str, BatchResultItem] = {}
        error_items: dict[str, BatchResultItem] = {}
        if status == "completed":
            success_items = {
                item.custom_id: item
                for item in self._batch_client.download_results(
                    output_file_id=job.get("output_file_id")
                )
            }
            error_items = {
                item.custom_id: item
                for item in self._batch_client.download_errors(
                    error_file_id=job.get("error_file_id")
                )
            }
        for item in items:
            custom_id = str(item["custom_id"])
            if custom_id in success_items:
                result = success_items[custom_id]
                outcome = self._apply_success_item(
                    item=item,
                    result=result,
                    batch_job_id=batch_job_id,
                    run_id=run_id,
                    logger=logger,
                    document_repository=document_repository,
                    batch_repository=batch_repository,
                )
                self._record_outcome(summary, outcome)
                summary.applied_items_count += 1
                continue
            failure_item = error_items.get(custom_id)
            outcome = self._apply_failed_item(
                item=item,
                batch_job_id=batch_job_id,
                provider_failure=failure_item,
                run_id=run_id,
                logger=logger,
                document_repository=document_repository,
                batch_repository=batch_repository,
            )
            self._record_outcome(summary, outcome)
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
    ) -> str:
        custom_id = str(item["custom_id"])
        batch_repository.mark_item_status(
            custom_id=custom_id,
            status="completed",
            completed_at=result.response.completed_at if result.response else None,
        )
        document_repository.update_analysis_dispatch(
            doc_id=str(item["doc_id"]),
            dispatch_updates={
                "mode": "batch_analysis",
                "status": "completed",
                "custom_id": custom_id,
                "batch_job_id": batch_job_id,
            },
        )
        request = deserialize_analysis_request_record(dict(item["request_record"]))
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
            batch_repository.mark_item_applied(custom_id=custom_id)
        return outcome

    def _apply_failed_item(
        self,
        *,
        item: dict[str, Any],
        batch_job_id: str,
        provider_failure: BatchResultItem | None,
        run_id: str,
        logger: JsonlPipelineLogger,
        document_repository: MongoDocumentRepository,
        batch_repository: MongoBatchStateRepository,
    ) -> str:
        custom_id = str(item["custom_id"])
        status = "expired" if str(provider_failure.raw_payload.get("status", "")) == "expired" else "failed" if provider_failure else "failed"
        error_payload = (
            provider_failure.error_payload
            if provider_failure is not None
            else {"code": "batch_item_missing", "message": "Batch item result is missing."}
        )
        batch_repository.mark_item_status(
            custom_id=custom_id,
            status=status,
            error_payload=error_payload,
        )
        if not self.config.pipeline.batch_apply_direct_fallback:
            return "failed"
        summary_outcome = self._run_direct_fallback_for_item(
            item=item,
            batch_job_id=batch_job_id,
            error_payload=error_payload,
            run_id=run_id,
            logger=logger,
            document_repository=document_repository,
        )
        batch_repository.mark_item_applied(custom_id=custom_id)
        return summary_outcome

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
            cost_estimate=estimate_stage_cost(
                request=effective_request,
                response=effective_response,
                input_cost_per_1k_tokens_usd=self.config.model.input_cost_per_1k_tokens_usd,
                output_cost_per_1k_tokens_usd=self.config.model.output_cost_per_1k_tokens_usd,
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

    def _prepare_and_queue_document(
        self,
        *,
        document,
        document_repository: MongoDocumentRepository,
        batch_repository: MongoBatchStateRepository,
        mode: str,
        run_id: str,
        force_classifier_fallback: bool,
        logger: JsonlPipelineLogger,
    ) -> str:
        doc_id = document.relative_path.as_posix()
        try:
            read_result = self.pipeline.reader.read(document)
            document_repository.apply_read_result(doc_id=doc_id, read_result=read_result)
            parse_result = self.pipeline.parser.parse(
                file_name=document.file_name,
                normalized_text=read_result.normalized_text,
            )
            document_repository.apply_parse_result(
                doc_id=doc_id,
                parse_result=parse_result,
            )
            canonical_result = build_canonical_text(
                file_name=document.file_name,
                parse_result=parse_result,
                read_result=read_result,
            )
            language_result = self.pipeline.language_detector.detect(
                normalized_text=canonical_result.canonical_text,
                doc_metadata=parse_result.doc_metadata,
                relative_path=doc_id,
                title=parse_result.title or read_result.title,
            )
            document_repository.apply_canonical_result(
                doc_id=doc_id,
                canonical_result=canonical_result,
                language_result=language_result,
            )
        except (
            ReadDocumentError,
            MarkdownParseError,
            CanonicalizeDocumentError,
            RepositoryWriteError,
        ) as error:
            error_code = getattr(error, "code", "repository_write_error")
            error_message = getattr(error, "message", str(error))
            stage = "read"
            if isinstance(error, MarkdownParseError):
                stage = "parse"
            elif isinstance(error, CanonicalizeDocumentError):
                stage = "canonicalize"
            document_repository.mark_failed(
                doc_id=doc_id,
                stage=stage,
                error_code=error_code,
                error_message=error_message,
                mode=mode,
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="prepare",
                error_code=error_code,
                error_message=error_message,
            )
            return "failed"

        classification = self.pipeline.router.route(
            RoutingInput(
                relative_path=doc_id,
                file_name=document.file_name,
                title=parse_result.title or read_result.title,
                metadata=parse_result.doc_metadata,
                normalized_text=canonical_result.canonical_text,
            )
        )
        if classification.document_family is DocumentFamily.UNKNOWN:
            classification = self.pipeline._run_fallback_classifier(
                doc_id=doc_id,
                run_id=run_id,
                parse_result=parse_result,
                canonical_result=canonical_result,
                title=parse_result.title or read_result.title,
            )
        elif (
            force_classifier_fallback
            and classification.document_family is not DocumentFamily.CORPUS_README
        ):
            fallback = self.pipeline._run_fallback_classifier(
                doc_id=doc_id,
                run_id=run_id,
                parse_result=parse_result,
                canonical_result=canonical_result,
                title=parse_result.title or read_result.title,
            )
            if fallback is not None:
                self.pipeline._log_force_classifier_diagnostic(
                    logger=logger,
                    run_id=run_id,
                    doc_id=doc_id,
                    router_classification=classification,
                    fallback_classification=fallback,
                )
        if classification is None or classification.document_family is DocumentFamily.UNKNOWN:
            document_repository.mark_failed(
                doc_id=doc_id,
                stage="classify",
                error_code="classification_error",
                error_message="Document family could not be resolved.",
                mode=mode,
                annotation_status="failed",
            )
            return "failed"
        document_repository.apply_classification_result(
            doc_id=doc_id,
            classification_result=classification,
            mode=mode,
        )
        if not classification.annotatable:
            return "skipped_non_target"

        resolved_prompt = self.pipeline.prompt_resolver.resolve_analysis_prompt(
            classification.prompt_profile,
            source_language_code=language_result.language_code,
        )
        analysis_fingerprint = build_analysis_fingerprint(
            canonical_text_sha256=canonical_result.canonical_text_sha256,
            prompt_profile=classification.prompt_profile,
            prompt_pack_version=self.config.prompts.prompt_pack_version,
            prompt_hash=resolved_prompt.prompt_hash,
            model_id=self.config.model.model_id,
            reasoning_effort=self.config.model.reasoning_effort,
            text_verbosity=self.config.model.text_verbosity,
            output_schema_version=self.config.pipeline.schema_version,
            pipeline_version=self.config.pipeline.pipeline_version,
        )
        analysis_request = self.pipeline._build_analysis_request(
            run_id=run_id,
            doc_id=doc_id,
            classification=classification,
            language_code=language_result.language_code,
            parse_metadata=parse_result.doc_metadata,
            title=parse_result.title or read_result.title,
            canonical_result=canonical_result,
            resolved_prompt=resolved_prompt,
        )
        request_record = serialize_analysis_request_record(analysis_request)
        request_body = build_batch_jsonl_item(analysis_request)
        custom_id = build_batch_custom_id(
            doc_id=doc_id,
            stage=analysis_request.stage,
            request_hash=analysis_request.request_hash,
        )
        batch_repository.queue_item(
            custom_id=custom_id,
            doc_id=doc_id,
            stage=analysis_request.stage,
            request_hash=analysis_request.request_hash,
            prompt_hash=analysis_request.prompt_hash,
            source_language_code=language_result.language_code,
            request_record=request_record,
            request_body=request_body,
            analysis_fingerprint=analysis_fingerprint,
            cost_estimate=estimate_stage_cost(
                request=analysis_request,
                response=None,
                input_cost_per_1k_tokens_usd=self.config.model.input_cost_per_1k_tokens_usd,
                output_cost_per_1k_tokens_usd=self.config.model.output_cost_per_1k_tokens_usd,
            ),
        )
        document_repository.update_analysis_dispatch(
            doc_id=doc_id,
            dispatch_updates={
                "mode": "batch_analysis",
                "status": "queued",
                "custom_id": custom_id,
                "request_hash": analysis_request.request_hash,
                "prompt_hash": analysis_request.prompt_hash,
            },
        )
        return "queued"

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
    ) -> tuple[str, JsonlPipelineLogger, list[Any], BatchCommandSummary]:
        if self.config.config_path is None:
            raise ValueError("config_path must be set on PipelineConfig.")
        run_id = f"normadepo-batch-{uuid4().hex[:12]}"
        logger = JsonlPipelineLogger(
            run_id=run_id,
            log_dir=_default_log_dir(self.config.config_path),
            log_level=options.log_level,
        )
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
