"""Discovery, routing, rerun, and two-stage annotation pipeline for NormaDepo."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
import os
from pathlib import Path
from time import sleep
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .canonicalize import (
    CanonicalTextResult,
    CanonicalizeDocumentError,
    build_canonical_text,
)
from .config import PipelineConfig
from .constants import (
    DEFAULT_TRANSLATION_RU_MAX_OUTPUT_TOKENS,
    DEFAULT_TRANSLATION_RU_MAX_OUTPUT_TOKENS_MAX,
    DocumentFamily,
    PACKED_INPUT_THRESHOLD_CHARS,
    PipelineMode,
    PromptProfile,
    RerunScope,
)
from .costs import estimate_stage_cost
from .language import HeuristicLanguageDetector, LanguageDetectionResult
from .llm import (
    AnnotationLlmClient,
    LlmCallError,
    OpenAIResponsesAnnotationLlmClient,
    StructuredLlmRequest,
    StructuredLlmResponse,
)
from .logging import JsonlPipelineLogger, PipelineLogEvent
from .parser import LegalMarkdownParser, MarkdownParseError, ParsedMarkdownDocument
from .prompts import (
    FilePromptResolver,
    ResolvedPrompt,
    build_analysis_fingerprint,
    build_request_hash,
    hash_prompt_text,
)
from .reader import MarkdownReader, ReadDocumentError, ReadDocumentResult
from .repository import MongoDocumentRepository, RepositoryWriteError
from .router import RoutingInput, RuleBasedDocumentRouter
from .scanner import DocumentScanner, DiscoveredDocument
from .schemas import (
    AnalysisAnnotationOutput,
    ClassificationResult,
    FallbackClassificationOutput,
    TranslationAnnotationOutput,
    export_analysis_json_schema,
    export_translation_json_schema,
    validate_analysis_business_rules,
    validate_translation_business_rules,
)

_RESUME_TRANSLATION_STAGE = "annotate_ru"
_FALLBACK_CLASSIFIER_MIN_CONFIDENCE = 0.6
_FALLBACK_CLASSIFIER_SYSTEM_PROMPT = (
    "Classify one legal markdown document into the allowed NormaDepo families. "
    "Use only provided metadata and excerpt. Return strict JSON only."
)
_TRANSPORT_RETRYABLE_LLM_ERROR_CODES = frozenset({"llm_timeout", "llm_rate_limit"})


@dataclass(frozen=True, slots=True)
class PipelineRunOptions:
    mode: PipelineMode
    limit: int | None = None
    only_doc_id: str | None = None
    from_relative_path: str | None = None
    force_classifier_fallback: bool = False
    log_level: str = "INFO"
    dry_run: bool = False


@dataclass(frozen=True, slots=True)
class PreparedAnnotatableDocument:
    read_result: ReadDocumentResult
    parse_result: ParsedMarkdownDocument
    canonical_result: CanonicalTextResult
    language_result: LanguageDetectionResult
    classification: ClassificationResult
    resolved_prompt: ResolvedPrompt
    analysis_fingerprint: str


class PipelineRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config_path: Path
    mode: PipelineMode
    dry_run: bool
    limit: int | None = None
    only_doc_id: str | None = None
    run_id: str
    input_root: Path
    mongo_uri: str
    mongo_database: str
    mongo_collection: str
    prompt_dir: Path
    prompt_pack_id: str
    prompt_pack_version: str
    pipeline_version: str
    log_path: Path
    discovered_count: int = 0
    processed_count: int = 0
    created_count: int = 0
    updated_count: int = 0
    completed_count: int = 0
    partial_count: int = 0
    skipped_non_target_count: int = 0
    skipped_unchanged_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    execution_status: str = "completed"
    message: str = ""
    warnings: list[str] = Field(default_factory=list)


class AnalysisBusinessValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("Analysis result failed business validation.")
        self.errors = errors


class TranslationBusinessValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("Translation result failed business validation.")
        self.errors = errors


class AnnotationPipeline:
    def __init__(
        self,
        *,
        config: PipelineConfig,
        scanner: DocumentScanner | None = None,
        reader: MarkdownReader | None = None,
        parser: LegalMarkdownParser | None = None,
        language_detector: HeuristicLanguageDetector | None = None,
        router: RuleBasedDocumentRouter | None = None,
        prompt_resolver: FilePromptResolver | None = None,
        repository_factory: Callable[[PipelineConfig], MongoDocumentRepository]
        | None = None,
        llm_client: AnnotationLlmClient | None = None,
    ) -> None:
        self.config = config
        self.scanner = scanner or DocumentScanner()
        self.reader = reader or MarkdownReader(
            max_file_size_bytes=config.input.max_file_size_bytes
        )
        self.parser = parser or LegalMarkdownParser()
        self.language_detector = language_detector or HeuristicLanguageDetector()
        self.router = router or RuleBasedDocumentRouter(
            router_version=config.pipeline.router_version
        )
        self.prompt_resolver = prompt_resolver or FilePromptResolver(
            config.prompts.prompt_dir
        )
        self._repository_factory = repository_factory or MongoDocumentRepository.from_config
        self._llm_client = llm_client

    def run(
        self,
        *,
        options: PipelineRunOptions,
        rerun_scope: RerunScope | None = None,
    ) -> PipelineRunSummary:
        if self.config.config_path is None:
            raise ValueError("config_path must be set on PipelineConfig.")
        if options.mode is PipelineMode.RERUN and rerun_scope is None:
            raise ValueError("rerun_scope is required for rerun mode.")
        if options.mode is not PipelineMode.RERUN and rerun_scope is not None:
            raise ValueError("rerun_scope is only valid in rerun mode.")

        self.prompt_resolver.validate_prompt_pack()
        run_id = f"normadepo-{uuid4().hex[:12]}"
        logger = JsonlPipelineLogger(
            run_id=run_id,
            log_dir=_default_log_dir(self.config.config_path),
            log_level=options.log_level,
        )
        discovered = self.scanner.scan(
            self.config.input.root_path,
            glob_pattern=self.config.input.glob,
            ignore_hidden=self.config.input.ignore_hidden,
            only_doc_id=options.only_doc_id,
            from_relative_path=options.from_relative_path,
            limit=options.limit,
        )
        if options.only_doc_id and not discovered:
            raise FileNotFoundError(
                f"Document not found under input root: {options.only_doc_id}"
            )

        summary = PipelineRunSummary(
            config_path=self.config.config_path,
            mode=options.mode,
            dry_run=options.dry_run,
            limit=options.limit,
            only_doc_id=options.only_doc_id,
            run_id=run_id,
            input_root=self.config.input.root_path,
            mongo_uri=self.config.mongo.uri,
            mongo_database=self.config.mongo.database,
            mongo_collection=self.config.mongo.collection,
            prompt_dir=self.config.prompts.prompt_dir,
            prompt_pack_id=self.config.prompts.prompt_pack_id,
            prompt_pack_version=self.config.prompts.prompt_pack_version,
            pipeline_version=self.config.pipeline.pipeline_version,
            log_path=logger.log_path,
            discovered_count=len(discovered),
            execution_status="dry_run_completed" if options.dry_run else "completed",
            message="Two-stage annotation pipeline finished.",
        )
        _log(
            logger,
            run_id=run_id,
            stage="run",
            event="run_started",
            level="info",
            message="Pipeline run started.",
            details={
                "mode": options.mode.value,
                "dry_run": options.dry_run,
                "force_classifier_fallback": options.force_classifier_fallback,
                "from_relative_path": options.from_relative_path,
                "rerun_scope": rerun_scope.value if rerun_scope else None,
                "discovered_count": len(discovered),
            },
        )

        _require_openai_api_key(
            config=self.config,
            llm_client=self._llm_client,
            dry_run=options.dry_run,
        )

        if options.dry_run and options.mode is not PipelineMode.RERUN:
            self._run_dry(
                discovered=discovered,
                summary=summary,
                logger=logger,
            )
            _log_summary(logger, summary)
            return summary

        repository: MongoDocumentRepository | None = None
        try:
            repository = self._repository_factory(self.config)
            if not options.dry_run:
                repository.ensure_indexes()
        except Exception as error:
            if options.dry_run and options.mode is PipelineMode.RERUN:
                warning = (
                    "Dry-run rerun selection skipped because repository lookup is "
                    f"unavailable: {error}"
                )
                summary.warnings.append(warning)
                _log(
                    logger,
                    run_id=run_id,
                    stage="rerun",
                    event="repository_unavailable",
                    level="warning",
                    message=warning,
                )
                _log_summary(logger, summary)
                return summary
            raise

        try:
            if options.dry_run:
                self._run_dry_with_repository(
                    repository=repository,
                    discovered=discovered,
                    options=options,
                    rerun_scope=rerun_scope,
                    summary=summary,
                    logger=logger,
                )
            else:
                self._run_with_repository(
                    repository=repository,
                    discovered=discovered,
                    options=options,
                    rerun_scope=rerun_scope,
                    summary=summary,
                    logger=logger,
                )
        finally:
            repository.close()

        _log_summary(logger, summary)
        return summary

    def _run_dry(
        self,
        *,
        discovered: list[DiscoveredDocument],
        summary: PipelineRunSummary,
        logger: JsonlPipelineLogger,
    ) -> None:
        for document in discovered:
            doc_id = document.relative_path.as_posix()
            try:
                prepared = self._prepare_annotatable_document(
                    document=document,
                    run_id=summary.run_id,
                    allow_classifier_fallback=False,
                )
                if prepared is None:
                    summary.skipped_non_target_count += 1
                    summary.processed_count += 1
                    _log(
                        logger,
                        run_id=summary.run_id,
                        doc_id=doc_id,
                        stage="classify",
                        event="non_target_dry_run",
                        level="info",
                        message="Dry-run classified document as non-target.",
                    )
                    continue
                summary.processed_count += 1
            except (ReadDocumentError, MarkdownParseError, ValueError) as error:
                summary.failed_count += 1
                summary.processed_count += 1
                _log(
                    logger,
                    run_id=summary.run_id,
                    doc_id=doc_id,
                    stage="dry_run",
                    event="dry_run_failed",
                    level="error",
                    message=str(error),
                )

    def _run_dry_with_repository(
        self,
        *,
        repository: MongoDocumentRepository,
        discovered: list[DiscoveredDocument],
        options: PipelineRunOptions,
        rerun_scope: RerunScope | None,
        summary: PipelineRunSummary,
        logger: JsonlPipelineLogger,
    ) -> None:
        for document in discovered:
            doc_id = document.relative_path.as_posix()
            existing = repository.get_document(doc_id)
            action = self._select_document_action(
                existing=existing,
                document=document,
                options=options,
                rerun_scope=rerun_scope,
            )
            if action == "skip_scope":
                continue
            if action == "skip_unchanged":
                summary.skipped_unchanged_count += 1
                summary.skipped_count += 1
                continue
            summary.processed_count += 1
            _log(
                logger,
                run_id=summary.run_id,
                doc_id=doc_id,
                stage="dry_run",
                event="doc_selected",
                level="info",
                message=f"Dry-run selected document via {action}.",
            )

    def _run_with_repository(
        self,
        *,
        repository: MongoDocumentRepository,
        discovered: list[DiscoveredDocument],
        options: PipelineRunOptions,
        rerun_scope: RerunScope | None,
        summary: PipelineRunSummary,
        logger: JsonlPipelineLogger,
    ) -> None:
        for document in discovered:
            doc_id = document.relative_path.as_posix()
            existing = repository.get_document(doc_id)
            action = self._select_document_action(
                existing=existing,
                document=document,
                options=options,
                rerun_scope=rerun_scope,
            )

            if action == "skip_scope":
                continue
            if action == "skip_unchanged":
                repository.touch_seen(doc_id=doc_id, run_id=summary.run_id)
                summary.skipped_unchanged_count += 1
                summary.skipped_count += 1
                _log(
                    logger,
                    run_id=summary.run_id,
                    doc_id=doc_id,
                    stage="select",
                    event="skipped_unchanged",
                    level="info",
                    message="Skipped unchanged completed document.",
                )
                continue

            write_result = repository.upsert_discovered(
                discovered=document,
                input_root=self.config.input.root_path,
                run_id=summary.run_id,
                mode=options.mode.value,
            )
            if write_result.created:
                summary.created_count += 1
            else:
                summary.updated_count += 1

            if action == "resume_translation":
                outcome = self._resume_translation(
                    repository=repository,
                    existing=existing,
                    doc_id=doc_id,
                    mode=options.mode.value,
                    run_id=summary.run_id,
                    logger=logger,
                )
                _record_outcome(summary, outcome)
                continue

            outcome = self._process_full_document(
                    repository=repository,
                    document=document,
                    doc_id=doc_id,
                    mode=options.mode.value,
                    run_id=summary.run_id,
                    force_classifier_fallback=options.force_classifier_fallback,
                    logger=logger,
                )
            _record_outcome(summary, outcome)

    def _process_full_document(
        self,
        *,
        repository: MongoDocumentRepository,
        document: DiscoveredDocument,
        doc_id: str,
        mode: str,
        run_id: str,
        force_classifier_fallback: bool,
        logger: JsonlPipelineLogger,
    ) -> str:
        try:
            read_result = self.reader.read(document)
            repository.apply_read_result(doc_id=doc_id, read_result=read_result)
        except (ReadDocumentError, RepositoryWriteError) as error:
            error_code = getattr(error, "code", "repository_write_error")
            error_message = str(error)
            repository.mark_failed(
                doc_id=doc_id,
                stage="read",
                error_code=error_code,
                error_message=error_message,
                mode=mode,
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="read",
                error_code=error_code,
                error_message=error_message,
            )
            return "failed"

        try:
            parse_result = self.parser.parse(
                file_name=document.file_name,
                normalized_text=read_result.normalized_text,
            )
            repository.apply_parse_result(
                doc_id=doc_id,
                parse_result=parse_result,
            )
        except (MarkdownParseError, RepositoryWriteError) as error:
            error_code = getattr(error, "code", "repository_write_error")
            error_message = str(error)
            repository.mark_failed(
                doc_id=doc_id,
                stage="parse",
                error_code=error_code,
                error_message=error_message,
                mode=mode,
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="parse",
                error_code=error_code,
                error_message=error_message,
            )
            return "failed"

        try:
            canonical_result = build_canonical_text(
                file_name=document.file_name,
                parse_result=parse_result,
                read_result=read_result,
            )
        except CanonicalizeDocumentError as error:
            repository.mark_failed(
                doc_id=doc_id,
                stage="canonicalize",
                error_code=error.code,
                error_message=error.message,
                mode=mode,
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="canonicalize",
                error_code=error.code,
                error_message=error.message,
            )
            return "failed"

        language_result = self.language_detector.detect(
            normalized_text=canonical_result.canonical_text,
            doc_metadata=parse_result.doc_metadata,
            relative_path=doc_id,
            title=parse_result.title or read_result.title,
        )
        try:
            repository.apply_canonical_result(
                doc_id=doc_id,
                canonical_result=canonical_result,
                language_result=language_result,
            )
        except RepositoryWriteError as error:
            repository.mark_failed(
                doc_id=doc_id,
                stage="canonicalize",
                error_code=error.code,
                error_message=error.message,
                mode=mode,
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="canonicalize",
                error_code=error.code,
                error_message=error.message,
            )
            return "failed"
        classification = self.router.route(
            RoutingInput(
                relative_path=doc_id,
                file_name=document.file_name,
                title=parse_result.title or read_result.title,
                metadata=parse_result.doc_metadata,
                normalized_text=canonical_result.canonical_text,
            )
        )
        if language_result.language_code == "und":
            if not classification.annotatable:
                try:
                    repository.apply_classification_result(
                        doc_id=doc_id,
                        classification_result=classification,
                        mode=mode,
                    )
                except RepositoryWriteError as error:
                    repository.mark_failed(
                        doc_id=doc_id,
                        stage="classify",
                        error_code=error.code,
                        error_message=error.message,
                        mode=mode,
                    )
                    _log_failure(
                        logger,
                        run_id=run_id,
                        doc_id=doc_id,
                        stage="classify",
                        error_code=error.code,
                        error_message=error.message,
                    )
                    return "failed"
                _log(
                    logger,
                    run_id=run_id,
                    doc_id=doc_id,
                    stage="classify",
                    event="skipped_non_target",
                    level="info",
                    message=(
                        "Document classified as non-target despite und "
                        "language signals."
                    ),
                )
                return "skipped_non_target"
            repository.mark_failed(
                doc_id=doc_id,
                stage="canonicalize",
                error_code="failed_language_detection",
                error_message="Unable to determine source language.",
                mode=mode,
                warnings=("language_undetermined",),
                source_updates={
                    "language_original": "und",
                },
                dedup_updates={
                    "canonical_doc_uid": parse_result.doc_metadata.get(
                        "canonical_doc_uid"
                    ),
                    "logical_doc_key": parse_result.doc_metadata.get(
                        "canonical_doc_uid"
                    )
                    or doc_id,
                },
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="canonicalize",
                error_code="failed_language_detection",
                error_message="Unable to determine source language.",
            )
            return "failed"
        if classification.document_family is DocumentFamily.UNKNOWN:
            classification = self._run_fallback_classifier(
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
            fallback_classification = self._run_fallback_classifier(
                doc_id=doc_id,
                run_id=run_id,
                parse_result=parse_result,
                canonical_result=canonical_result,
                title=parse_result.title or read_result.title,
            )
            self._log_force_classifier_diagnostic(
                logger=logger,
                run_id=run_id,
                doc_id=doc_id,
                router_classification=classification,
                fallback_classification=fallback_classification,
            )
        if classification is None or classification.document_family is DocumentFamily.UNKNOWN:
            repository.mark_failed(
                doc_id=doc_id,
                stage="classify",
                error_code="classification_error",
                error_message="Document family could not be resolved.",
                mode=mode,
                annotation_status="failed",
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="classify",
                error_code="classification_error",
                error_message="Document family could not be resolved.",
            )
            return "failed"

        try:
            repository.apply_classification_result(
                doc_id=doc_id,
                classification_result=classification,
                mode=mode,
            )
        except RepositoryWriteError as error:
            repository.mark_failed(
                doc_id=doc_id,
                stage="classify",
                error_code=error.code,
                error_message=error.message,
                mode=mode,
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="classify",
                error_code=error.code,
                error_message=error.message,
            )
            return "failed"
        if not classification.annotatable:
            _log(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="classify",
                event="skipped_non_target",
                level="info",
                message="Document classified as non-target.",
            )
            return "skipped_non_target"

        resolved_prompt = self.prompt_resolver.resolve_analysis_prompt(
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
        analysis_request = self._build_analysis_request(
            run_id=run_id,
            doc_id=doc_id,
            classification=classification,
            language_code=language_result.language_code,
            parse_metadata=parse_result.doc_metadata,
            title=parse_result.title or read_result.title,
            canonical_result=canonical_result,
            resolved_prompt=resolved_prompt,
        )
        packed_analysis_request = self._build_analysis_request(
            run_id=run_id,
            doc_id=doc_id,
            classification=classification,
            language_code=language_result.language_code,
            parse_metadata=parse_result.doc_metadata,
            title=parse_result.title or read_result.title,
            canonical_result=canonical_result,
            resolved_prompt=resolved_prompt,
            force_packed_input=True,
        )

        try:
            analysis_output, analysis_request, analysis_response = (
                self._run_analysis_with_recovery(
                    run_id=run_id,
                    doc_id=doc_id,
                    logger=logger,
                    source_language_code=language_result.language_code,
                    analysis_request=analysis_request,
                    packed_analysis_request=packed_analysis_request,
                )
            )
        except LlmCallError as error:
            repository.mark_failed(
                doc_id=doc_id,
                stage="annotate_original",
                error_code=error.code,
                error_message=error.message,
                error_details=error.details,
                mode=mode,
                llm_updates=_build_failed_llm_updates(
                    request=analysis_request,
                    error_code=error.code,
                    error_message=error.message,
                    error_details=error.details,
                ),
                annotation_status="failed",
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="annotate_original",
                error_code=error.code,
                error_message=error.message,
                error_details=error.details,
            )
            return "failed"
        except ValidationError as error:
            message = "Analysis repair response failed schema validation."
            repository.mark_failed(
                doc_id=doc_id,
                stage="annotate_original",
                error_code="llm_schema_validation_error",
                error_message=message,
                mode=mode,
                llm_updates=_build_failed_llm_updates(
                    request=analysis_request,
                    error_code="llm_schema_validation_error",
                    error_message=message,
                ),
                annotation_status="failed",
                validation_errors=[
                    issue["msg"] for issue in error.errors(include_url=False)
                ],
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="annotate_original",
                error_code="llm_schema_validation_error",
                error_message=message,
            )
            return "failed"
        except AnalysisBusinessValidationError as error:
            message = "Analysis repair response failed business validation."
            repository.mark_failed(
                doc_id=doc_id,
                stage="annotate_original",
                error_code="llm_schema_validation_error",
                error_message=message,
                mode=mode,
                llm_updates=_build_failed_llm_updates(
                    request=analysis_request,
                    error_code="llm_schema_validation_error",
                    error_message=message,
                ),
                annotation_status="failed",
                validation_errors=error.errors,
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="annotate_original",
                error_code="llm_schema_validation_error",
                error_message=message,
            )
            return "failed"

        try:
            repository.apply_analysis_result(
                doc_id=doc_id,
                annotation_output=analysis_output,
                analysis_fingerprint=analysis_fingerprint,
                llm_request=analysis_request,
                llm_response=analysis_response,
                mode=mode,
                cost_estimate=self._estimate_stage_cost(
                    request=analysis_request,
                    response=analysis_response,
                ),
            )
        except RepositoryWriteError as error:
            repository.mark_failed(
                doc_id=doc_id,
                stage="annotate_original",
                error_code=error.code,
                error_message=error.message,
                mode=mode,
                annotation_status="failed",
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="annotate_original",
                error_code=error.code,
                error_message=error.message,
            )
            return "failed"

        outcome = self._run_translation_stage(
            repository=repository,
            doc_id=doc_id,
            analysis_output=analysis_output,
            mode=mode,
            run_id=run_id,
            logger=logger,
        )
        return outcome

    def _resume_translation(
        self,
        *,
        repository: MongoDocumentRepository,
        existing: dict[str, Any] | None,
        doc_id: str,
        mode: str,
        run_id: str,
        logger: JsonlPipelineLogger,
    ) -> str:
        analysis_output = _load_existing_analysis_output(existing)
        if analysis_output is None:
            _log(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="annotate_ru",
                event="resume_unavailable",
                level="warning",
                message="Partial document could not resume translation; falling back to full processing.",
            )
            return "failed"
        return self._run_translation_stage(
            repository=repository,
            doc_id=doc_id,
            analysis_output=analysis_output,
            mode=mode,
            run_id=run_id,
            logger=logger,
        )

    def _run_translation_stage(
        self,
        *,
        repository: MongoDocumentRepository,
        doc_id: str,
        analysis_output: AnalysisAnnotationOutput,
        mode: str,
        run_id: str,
        logger: JsonlPipelineLogger,
    ) -> str:
        translation_prompt = self.prompt_resolver.resolve_translation_prompt()
        translation_request = self._build_translation_request(
            run_id=run_id,
            doc_id=doc_id,
            analysis_output=analysis_output,
            resolved_prompt=translation_prompt,
        )
        try:
            translation_request, translation_response = (
                self._run_translation_request_with_recovery(
                    run_id=run_id,
                    doc_id=doc_id,
                    logger=logger,
                    translation_request=translation_request,
                )
            )
            translation_output, translation_request, translation_response = (
                self._validate_or_repair_translation_response(
                    run_id=run_id,
                    doc_id=doc_id,
                    logger=logger,
                    translation_request=translation_request,
                    translation_response=translation_response,
                )
            )
        except LlmCallError as error:
            repository.mark_translation_partial(
                doc_id=doc_id,
                error_code=error.code,
                error_message=error.message,
                error_details=error.details,
                mode=mode,
                llm_updates=_build_failed_llm_updates(
                    request=translation_request,
                    error_code=error.code,
                    error_message=error.message,
                    error_details=error.details,
                ),
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="annotate_ru",
                error_code=error.code,
                error_message=error.message,
                error_details=error.details,
            )
            return "partial"
        except ValidationError as error:
            message = "Translation repair response failed schema validation."
            repository.mark_translation_partial(
                doc_id=doc_id,
                error_code="translation_validation_error",
                error_message=message,
                mode=mode,
                llm_updates=_build_failed_llm_updates(
                    request=translation_request,
                    error_code="translation_validation_error",
                    error_message=message,
                ),
                validation_errors=[
                    issue["msg"] for issue in error.errors(include_url=False)
                ],
                manual_review_required=True,
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="annotate_ru",
                error_code="translation_validation_error",
                error_message=message,
            )
            return "partial"
        except TranslationBusinessValidationError as error:
            message = "Translation repair response failed business validation."
            repository.mark_translation_partial(
                doc_id=doc_id,
                error_code="translation_validation_error",
                error_message=message,
                mode=mode,
                llm_updates=_build_failed_llm_updates(
                    request=translation_request,
                    error_code="translation_validation_error",
                    error_message=message,
                ),
                validation_errors=error.errors,
                manual_review_required=True,
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="annotate_ru",
                error_code="translation_validation_error",
                error_message=message,
            )
            return "partial"

        try:
            repository.apply_translation_result(
                doc_id=doc_id,
                translation_output=translation_output,
                llm_request=translation_request,
                llm_response=translation_response,
                mode=mode,
                cost_estimate=self._estimate_stage_cost(
                    request=translation_request,
                    response=translation_response,
                ),
            )
        except RepositoryWriteError as error:
            repository.mark_translation_partial(
                doc_id=doc_id,
                error_code=error.code,
                error_message=error.message,
                mode=mode,
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="annotate_ru",
                error_code=error.code,
                error_message=error.message,
            )
            return "partial"
        _log(
            logger,
            run_id=run_id,
            doc_id=doc_id,
            stage="annotate_ru",
            event="completed",
            level="info",
            message="Document reached completed state.",
        )
        return "completed"

    def _prepare_annotatable_document(
        self,
        *,
        document: DiscoveredDocument,
        run_id: str,
        allow_classifier_fallback: bool,
    ) -> PreparedAnnotatableDocument | None:
        read_result = self.reader.read(document)
        parse_result = self.parser.parse(
            file_name=document.file_name,
            normalized_text=read_result.normalized_text,
        )
        canonical_result = build_canonical_text(
            file_name=document.file_name,
            parse_result=parse_result,
            read_result=read_result,
        )
        language_result = self.language_detector.detect(
            normalized_text=canonical_result.canonical_text,
            doc_metadata=parse_result.doc_metadata,
            relative_path=document.relative_path.as_posix(),
            title=parse_result.title or read_result.title,
        )
        classification = self.router.route(
            RoutingInput(
                relative_path=document.relative_path.as_posix(),
                file_name=document.file_name,
                title=parse_result.title or read_result.title,
                metadata=parse_result.doc_metadata,
                normalized_text=canonical_result.canonical_text,
            )
        )
        if language_result.language_code == "und":
            if not classification.annotatable:
                return None
            raise ValueError("Unable to determine source language.")

        if classification.document_family is DocumentFamily.UNKNOWN and allow_classifier_fallback:
            classification = self._run_fallback_classifier(
                doc_id=document.relative_path.as_posix(),
                run_id=run_id,
                parse_result=parse_result,
                canonical_result=canonical_result,
                title=parse_result.title or read_result.title,
            )
        if classification is None or classification.document_family is DocumentFamily.UNKNOWN:
            raise ValueError("Document family could not be resolved.")
        if not classification.annotatable:
            return None

        resolved_prompt = self.prompt_resolver.resolve_analysis_prompt(
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
        return PreparedAnnotatableDocument(
            read_result=read_result,
            parse_result=parse_result,
            canonical_result=canonical_result,
            language_result=language_result,
            classification=classification,
            resolved_prompt=resolved_prompt,
            analysis_fingerprint=analysis_fingerprint,
        )

    def _run_fallback_classifier(
        self,
        *,
        doc_id: str,
        run_id: str,
        parse_result: ParsedMarkdownDocument,
        canonical_result: CanonicalTextResult,
        title: str | None,
    ) -> ClassificationResult | None:
        prompt_hash = hash_prompt_text(_FALLBACK_CLASSIFIER_SYSTEM_PROMPT)
        input_payload = {
            "doc_id": doc_id,
            "title": title,
            "doc_metadata": parse_result.doc_metadata,
            "excerpt": canonical_result.canonical_text[:2000],
        }
        request = StructuredLlmRequest(
            stage="classify_fallback",
            system_prompt=_FALLBACK_CLASSIFIER_SYSTEM_PROMPT,
            input_payload=input_payload,
            output_schema=FallbackClassificationOutput.model_json_schema(),
            output_model=FallbackClassificationOutput,
            metadata={
                "run_id": run_id,
                "doc_id": doc_id,
                "prompt_pack_version": self.config.prompts.prompt_pack_version,
                "prompt_profile": "classifier_fallback",
            },
            provider=self.config.model.provider,
            api=self.config.model.api,
            model_id=self.config.model.model_id,
            reasoning_effort=self.config.model.reasoning_effort,
            text_verbosity=self.config.model.text_verbosity,
            truncation=self.config.model.truncation,
            store=self.config.model.store,
            max_output_tokens=min(2000, self.config.model.analysis_max_output_tokens),
            prompt_pack_id=self.config.prompts.prompt_pack_id,
            prompt_pack_version=self.config.prompts.prompt_pack_version,
            prompt_profile="classifier_fallback",
            prompt_hash=prompt_hash,
            request_hash=build_request_hash(
                system_prompt=_FALLBACK_CLASSIFIER_SYSTEM_PROMPT,
                input_payload=input_payload,
                output_schema=FallbackClassificationOutput.model_json_schema(),
                model_id=self.config.model.model_id,
                reasoning_effort=self.config.model.reasoning_effort,
                text_verbosity=self.config.model.text_verbosity,
                max_output_tokens=min(2000, self.config.model.analysis_max_output_tokens),
            ),
        )
        try:
            response = self._run_llm_request(
                request=request,
                run_id=run_id,
                doc_id=doc_id,
                logger=None,
            )
            parsed = FallbackClassificationOutput.model_validate(response.output_payload)
        except (LlmCallError, ValidationError):
            return None

        if parsed.confidence < _FALLBACK_CLASSIFIER_MIN_CONFIDENCE:
            return None
        if not _fallback_family_prompt_is_consistent(
            document_family=parsed.document_family,
            prompt_profile=parsed.prompt_profile,
        ):
            return None
        return ClassificationResult(
            document_family=parsed.document_family,
            document_type_code=None,
            prompt_profile=parsed.prompt_profile,
            annotatable=parsed.prompt_profile is not PromptProfile.SKIP_NON_TARGET,
            classifier_method="llm_fallback",
            confidence=parsed.confidence,
            router_version=self.config.pipeline.router_version,
            signals={
                "fallback": True,
                "excerpt_chars": len(input_payload["excerpt"]),
            },
            skip_reason="fallback_non_target"
            if parsed.prompt_profile is PromptProfile.SKIP_NON_TARGET
            else None,
        )

    def _build_analysis_request(
        self,
        *,
        run_id: str,
        doc_id: str,
        classification: ClassificationResult,
        language_code: str,
        parse_metadata: dict[str, object],
        title: str | None,
        canonical_result: CanonicalTextResult,
        resolved_prompt: ResolvedPrompt,
        force_packed_input: bool = False,
    ) -> StructuredLlmRequest:
        output_schema = export_analysis_json_schema()
        input_payload = _build_analysis_input_payload(
            doc_id=doc_id,
            language_code=language_code,
            title=title,
            parse_metadata=parse_metadata,
            canonical_result=canonical_result,
            force_packed_input=force_packed_input,
        )
        return StructuredLlmRequest(
            stage="annotate_original",
            system_prompt=resolved_prompt.prompt_text,
            input_payload=input_payload,
            output_schema=output_schema,
            output_model=AnalysisAnnotationOutput,
            metadata={
                "run_id": run_id,
                "doc_id": doc_id,
                "prompt_pack_version": self.config.prompts.prompt_pack_version,
                "prompt_profile": classification.prompt_profile.value,
            },
            provider=self.config.model.provider,
            api=self.config.model.api,
            model_id=self.config.model.model_id,
            reasoning_effort=self.config.model.reasoning_effort,
            text_verbosity=self.config.model.text_verbosity,
            truncation=self.config.model.truncation,
            store=self.config.model.store,
            max_output_tokens=self.config.model.analysis_max_output_tokens,
            prompt_pack_id=self.config.prompts.prompt_pack_id,
            prompt_pack_version=self.config.prompts.prompt_pack_version,
            prompt_profile=classification.prompt_profile.value,
            prompt_hash=resolved_prompt.prompt_hash,
            request_hash=build_request_hash(
                system_prompt=resolved_prompt.prompt_text,
                input_payload=input_payload,
                output_schema=output_schema,
                model_id=self.config.model.model_id,
                reasoning_effort=self.config.model.reasoning_effort,
                text_verbosity=self.config.model.text_verbosity,
                max_output_tokens=self.config.model.analysis_max_output_tokens,
            ),
        )

    def _build_analysis_repair_request(
        self,
        *,
        run_id: str,
        doc_id: str,
        source_language_code: str,
        candidate_output: dict[str, Any],
        validation_errors: list[str],
    ) -> StructuredLlmRequest:
        resolved_prompt = self.prompt_resolver.resolve_analysis_repair_prompt(
            source_language_code=source_language_code
        )
        output_schema = export_analysis_json_schema()
        input_payload = {
            "doc_id": doc_id,
            "source_language_code": source_language_code,
            "validation_errors": validation_errors,
            "candidate_output": candidate_output,
        }
        return StructuredLlmRequest(
            stage="annotate_original",
            system_prompt=resolved_prompt.prompt_text,
            input_payload=input_payload,
            output_schema=output_schema,
            output_model=AnalysisAnnotationOutput,
            metadata={
                "run_id": run_id,
                "doc_id": doc_id,
                "prompt_pack_version": self.config.prompts.prompt_pack_version,
                "prompt_profile": "repair_analysis",
            },
            provider=self.config.model.provider,
            api=self.config.model.api,
            model_id=self.config.model.model_id,
            reasoning_effort=self.config.model.reasoning_effort,
            text_verbosity=self.config.model.text_verbosity,
            truncation=self.config.model.truncation,
            store=self.config.model.store,
            max_output_tokens=self.config.model.analysis_max_output_tokens,
            prompt_pack_id=self.config.prompts.prompt_pack_id,
            prompt_pack_version=self.config.prompts.prompt_pack_version,
            prompt_profile="repair_analysis",
            prompt_hash=resolved_prompt.prompt_hash,
            request_hash=build_request_hash(
                system_prompt=resolved_prompt.prompt_text,
                input_payload=input_payload,
                output_schema=output_schema,
                model_id=self.config.model.model_id,
                reasoning_effort=self.config.model.reasoning_effort,
                text_verbosity=self.config.model.text_verbosity,
                max_output_tokens=self.config.model.analysis_max_output_tokens,
            ),
        )

    def _build_translation_request(
        self,
        *,
        run_id: str,
        doc_id: str,
        analysis_output: AnalysisAnnotationOutput,
        resolved_prompt: ResolvedPrompt,
    ) -> StructuredLlmRequest:
        output_schema = export_translation_json_schema()
        input_payload = {
            "doc_id": doc_id,
            "semantic_context": analysis_output.semantic.model_dump(mode="json"),
            "annotation_original": analysis_output.annotation_original.model_dump(
                mode="json"
            ),
        }
        max_output_tokens = _select_translation_output_budget(
            input_payload=input_payload,
            configured_default=self.config.model.translation_ru_max_output_tokens,
        )
        return StructuredLlmRequest(
            stage="annotate_ru",
            system_prompt=resolved_prompt.prompt_text,
            input_payload=input_payload,
            output_schema=output_schema,
            output_model=TranslationAnnotationOutput,
            metadata={
                "run_id": run_id,
                "doc_id": doc_id,
                "prompt_pack_version": self.config.prompts.prompt_pack_version,
                "prompt_profile": "translate_to_ru",
            },
            provider=self.config.model.provider,
            api=self.config.model.api,
            model_id=self.config.model.model_id,
            reasoning_effort=self.config.model.reasoning_effort,
            text_verbosity=self.config.model.text_verbosity,
            truncation=self.config.model.truncation,
            store=self.config.model.store,
            max_output_tokens=max_output_tokens,
            prompt_pack_id=self.config.prompts.prompt_pack_id,
            prompt_pack_version=self.config.prompts.prompt_pack_version,
            prompt_profile="translate_to_ru",
            prompt_hash=resolved_prompt.prompt_hash,
            request_hash=build_request_hash(
                system_prompt=resolved_prompt.prompt_text,
                input_payload=input_payload,
                output_schema=output_schema,
                model_id=self.config.model.model_id,
                reasoning_effort=self.config.model.reasoning_effort,
                text_verbosity=self.config.model.text_verbosity,
                max_output_tokens=max_output_tokens,
            ),
        )

    def _build_translation_repair_request(
        self,
        *,
        run_id: str,
        doc_id: str,
        candidate_output: dict[str, Any],
        validation_errors: list[str],
    ) -> StructuredLlmRequest:
        resolved_prompt = self.prompt_resolver.resolve_translation_repair_prompt()
        output_schema = export_translation_json_schema()
        input_payload = {
            "doc_id": doc_id,
            "validation_errors": validation_errors,
            "candidate_output": candidate_output,
        }
        max_output_tokens = _select_translation_output_budget(
            input_payload=input_payload,
            configured_default=self.config.model.translation_ru_max_output_tokens,
        )
        return StructuredLlmRequest(
            stage="annotate_ru",
            system_prompt=resolved_prompt.prompt_text,
            input_payload=input_payload,
            output_schema=output_schema,
            output_model=TranslationAnnotationOutput,
            metadata={
                "run_id": run_id,
                "doc_id": doc_id,
                "prompt_pack_version": self.config.prompts.prompt_pack_version,
                "prompt_profile": "repair_translate_to_ru",
            },
            provider=self.config.model.provider,
            api=self.config.model.api,
            model_id=self.config.model.model_id,
            reasoning_effort=self.config.model.reasoning_effort,
            text_verbosity=self.config.model.text_verbosity,
            truncation=self.config.model.truncation,
            store=self.config.model.store,
            max_output_tokens=max_output_tokens,
            prompt_pack_id=self.config.prompts.prompt_pack_id,
            prompt_pack_version=self.config.prompts.prompt_pack_version,
            prompt_profile="repair_translate_to_ru",
            prompt_hash=resolved_prompt.prompt_hash,
            request_hash=build_request_hash(
                system_prompt=resolved_prompt.prompt_text,
                input_payload=input_payload,
                output_schema=output_schema,
                model_id=self.config.model.model_id,
                reasoning_effort=self.config.model.reasoning_effort,
                text_verbosity=self.config.model.text_verbosity,
                max_output_tokens=max_output_tokens,
            ),
        )

    def _run_analysis_with_recovery(
        self,
        *,
        run_id: str,
        doc_id: str,
        logger: JsonlPipelineLogger,
        source_language_code: str,
        analysis_request: StructuredLlmRequest,
        packed_analysis_request: StructuredLlmRequest,
    ) -> tuple[AnalysisAnnotationOutput, StructuredLlmRequest, StructuredLlmResponse]:
        active_request = analysis_request
        try:
            analysis_response = self._run_llm_request(
                request=active_request,
                run_id=run_id,
                doc_id=doc_id,
                logger=logger,
            )
        except LlmCallError as error:
            if not _should_retry_analysis_with_packed_input(error, analysis_request):
                raise
            _log(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="annotate_original",
                event="analysis_repacked_retry",
                level="warning",
                message=(
                    "Analysis request hit max_output_tokens; retrying with "
                    "packed canonical sections."
                ),
                error={"code": error.code, "message": error.message},
                details=error.details,
            )
            active_request = packed_analysis_request
            analysis_response = self._run_llm_request(
                request=active_request,
                run_id=run_id,
                doc_id=doc_id,
                logger=logger,
            )
        analysis_output, effective_request, effective_response = (
            self._validate_or_repair_analysis_response(
                run_id=run_id,
                doc_id=doc_id,
                logger=logger,
                source_language_code=source_language_code,
                analysis_request=active_request,
                analysis_response=analysis_response,
            )
        )
        return analysis_output, effective_request, effective_response

    def _run_translation_request_with_recovery(
        self,
        *,
        run_id: str,
        doc_id: str,
        logger: JsonlPipelineLogger,
        translation_request: StructuredLlmRequest,
    ) -> tuple[StructuredLlmRequest, StructuredLlmResponse]:
        active_request = translation_request
        try:
            translation_response = self._run_llm_request(
                request=active_request,
                run_id=run_id,
                doc_id=doc_id,
                logger=logger,
            )
        except LlmCallError as error:
            if not _should_retry_translation_compact(error):
                raise
            _log(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="annotate_ru",
                event="translation_compact_retry",
                level="warning",
                message=(
                    "Translation request returned a retryable incomplete result; "
                    "retrying compact structured payload once."
                ),
                error={"code": error.code, "message": error.message},
                details=error.details,
            )
            active_request = _build_translation_compact_retry_request(translation_request)
            translation_response = self._run_llm_request(
                request=active_request,
                run_id=run_id,
                doc_id=doc_id,
                logger=logger,
            )
        return active_request, translation_response

    def _validate_or_repair_analysis_response(
        self,
        *,
        run_id: str,
        doc_id: str,
        logger: JsonlPipelineLogger,
        source_language_code: str,
        analysis_request: StructuredLlmRequest,
        analysis_response: StructuredLlmResponse,
    ) -> tuple[AnalysisAnnotationOutput, StructuredLlmRequest, StructuredLlmResponse]:
        try:
            analysis_output = AnalysisAnnotationOutput.model_validate(
                analysis_response.output_payload
            )
        except ValidationError as error:
            validation_errors = [
                issue["msg"] for issue in error.errors(include_url=False)
            ]
            return self._repair_analysis_response(
                run_id=run_id,
                doc_id=doc_id,
                logger=logger,
                source_language_code=source_language_code,
                candidate_output=analysis_response.output_payload,
                validation_errors=validation_errors,
            )
        validation_errors = validate_analysis_business_rules(
            analysis_output,
            source_language=source_language_code,
        )
        if not validation_errors:
            return analysis_output, analysis_request, analysis_response
        return self._repair_analysis_response(
            run_id=run_id,
            doc_id=doc_id,
            logger=logger,
            source_language_code=source_language_code,
            candidate_output=analysis_response.output_payload,
            validation_errors=validation_errors,
        )

    def _repair_analysis_response(
        self,
        *,
        run_id: str,
        doc_id: str,
        logger: JsonlPipelineLogger,
        source_language_code: str,
        candidate_output: dict[str, Any],
        validation_errors: list[str],
    ) -> tuple[AnalysisAnnotationOutput, StructuredLlmRequest, StructuredLlmResponse]:
        _log(
            logger,
            run_id=run_id,
            doc_id=doc_id,
            stage="annotate_original",
            event="repair_requested",
            level="warning",
            message="Analysis output failed validation; requesting repair pass.",
            details={"validation_errors": validation_errors},
        )
        repair_request = self._build_analysis_repair_request(
            run_id=run_id,
            doc_id=doc_id,
            source_language_code=source_language_code,
            candidate_output=candidate_output,
            validation_errors=validation_errors,
        )
        repair_response = self._run_llm_request(
            request=repair_request,
            run_id=run_id,
            doc_id=doc_id,
            logger=logger,
        )
        repaired_output = AnalysisAnnotationOutput.model_validate(
            repair_response.output_payload
        )
        repair_errors = validate_analysis_business_rules(
            repaired_output,
            source_language=source_language_code,
        )
        if repair_errors:
            raise AnalysisBusinessValidationError(repair_errors)
        return repaired_output, repair_request, repair_response

    def _validate_or_repair_translation_response(
        self,
        *,
        run_id: str,
        doc_id: str,
        logger: JsonlPipelineLogger,
        translation_request: StructuredLlmRequest,
        translation_response: StructuredLlmResponse,
    ) -> tuple[
        TranslationAnnotationOutput,
        StructuredLlmRequest,
        StructuredLlmResponse,
    ]:
        try:
            translation_output = TranslationAnnotationOutput.model_validate(
                translation_response.output_payload
            )
        except ValidationError as error:
            validation_errors = [
                issue["msg"] for issue in error.errors(include_url=False)
            ]
            return self._repair_translation_response(
                run_id=run_id,
                doc_id=doc_id,
                logger=logger,
                candidate_output=translation_response.output_payload,
                validation_errors=validation_errors,
            )
        validation_errors = validate_translation_business_rules(translation_output)
        if not validation_errors:
            return translation_output, translation_request, translation_response
        return self._repair_translation_response(
            run_id=run_id,
            doc_id=doc_id,
            logger=logger,
            candidate_output=translation_response.output_payload,
            validation_errors=validation_errors,
        )

    def _repair_translation_response(
        self,
        *,
        run_id: str,
        doc_id: str,
        logger: JsonlPipelineLogger,
        candidate_output: dict[str, Any],
        validation_errors: list[str],
    ) -> tuple[
        TranslationAnnotationOutput,
        StructuredLlmRequest,
        StructuredLlmResponse,
    ]:
        _log(
            logger,
            run_id=run_id,
            doc_id=doc_id,
            stage="annotate_ru",
            event="repair_requested",
            level="warning",
            message="Translation output failed validation; requesting repair pass.",
            details={"validation_errors": validation_errors},
        )
        repair_request = self._build_translation_repair_request(
            run_id=run_id,
            doc_id=doc_id,
            candidate_output=candidate_output,
            validation_errors=validation_errors,
        )
        repair_response = self._run_llm_request(
            request=repair_request,
            run_id=run_id,
            doc_id=doc_id,
            logger=logger,
        )
        repaired_output = TranslationAnnotationOutput.model_validate(
            repair_response.output_payload
        )
        repair_errors = validate_translation_business_rules(repaired_output)
        if repair_errors:
            raise TranslationBusinessValidationError(repair_errors)
        return repaired_output, repair_request, repair_response

    def _select_document_action(
        self,
        *,
        existing: dict[str, Any] | None,
        document: DiscoveredDocument,
        options: PipelineRunOptions,
        rerun_scope: RerunScope | None,
    ) -> str:
        doc_sha = document.sha256_hex
        if options.mode is PipelineMode.FULL:
            return "process_full"

        if options.mode is PipelineMode.NEW:
            if existing is None:
                return "process_full"
            if _is_translation_resume_candidate(existing, doc_sha):
                return "resume_translation"
            if _is_non_target_skip_candidate(existing, doc_sha):
                return "skip_unchanged"
            if _is_completed_skip_candidate(existing, doc_sha):
                candidate = self._build_effective_completed_fingerprint(existing)
                if should_skip_existing_document_in_new_mode(
                    existing=existing,
                    discovered_sha256=doc_sha,
                    candidate_analysis_fingerprint=candidate,
                ):
                    return "skip_unchanged"
            return "process_full"

        if existing is None and rerun_scope in {RerunScope.ALL, RerunScope.DOC_ID}:
            return "process_full"
        if existing is None:
            return "skip_scope"
        if rerun_scope is RerunScope.ALL:
            if _is_translation_resume_candidate(existing, doc_sha):
                return "resume_translation"
            return "process_full"
        if rerun_scope is RerunScope.DOC_ID:
            if _is_translation_resume_candidate(existing, doc_sha):
                return "resume_translation"
            return "process_full"
        if rerun_scope is RerunScope.FAILED:
            if not _is_failed_rerun_candidate(existing):
                return "skip_scope"
            if _is_translation_resume_candidate(existing, doc_sha):
                return "resume_translation"
            return "process_full"
        if rerun_scope is RerunScope.STALE:
            if _is_file_changed(existing, doc_sha):
                return "process_full"
            if _is_completed_skip_candidate(existing, doc_sha):
                candidate = self._build_effective_completed_fingerprint(existing)
                if candidate is None:
                    return "process_full"
                if _analysis_fingerprint(existing) != candidate:
                    return "process_full"
            return "skip_scope"
        return "skip_scope"

    def _build_effective_completed_fingerprint(
        self,
        existing: dict[str, Any] | None,
    ) -> str | None:
        if existing is None:
            return None
        canonical_text_sha256 = _canonical_text_sha(existing)
        prompt_profile = _classification_prompt_profile(existing)
        source_language_code = _source_language(existing)
        if (
            not canonical_text_sha256
            or prompt_profile is None
            or not source_language_code
        ):
            return None
        if prompt_profile is PromptProfile.SKIP_NON_TARGET:
            return None
        try:
            resolved_prompt = self.prompt_resolver.resolve_analysis_prompt(
                prompt_profile,
                source_language_code=source_language_code,
            )
        except (FileNotFoundError, ValueError):
            return None
        return build_analysis_fingerprint(
            canonical_text_sha256=canonical_text_sha256,
            prompt_profile=prompt_profile,
            prompt_pack_version=self.config.prompts.prompt_pack_version,
            prompt_hash=resolved_prompt.prompt_hash,
            model_id=self.config.model.model_id,
            reasoning_effort=self.config.model.reasoning_effort,
            text_verbosity=self.config.model.text_verbosity,
            output_schema_version=self.config.pipeline.schema_version,
            pipeline_version=self.config.pipeline.pipeline_version,
        )

    def _llm(self) -> AnnotationLlmClient:
        if self._llm_client is None:
            self._llm_client = OpenAIResponsesAnnotationLlmClient(
                timeout_seconds=self.config.model.request_timeout_seconds
            )
        return self._llm_client

    def _log_force_classifier_diagnostic(
        self,
        *,
        logger: JsonlPipelineLogger,
        run_id: str,
        doc_id: str,
        router_classification: ClassificationResult,
        fallback_classification: ClassificationResult | None,
    ) -> None:
        if fallback_classification is None:
            _log(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="classify",
                event="force_classifier_fallback_ignored",
                level="warning",
                message=(
                    "Forced fallback classifier returned no usable verdict; "
                    "keeping rule-based classification."
                ),
                details={
                    "router_family": router_classification.document_family.value,
                    "router_prompt_profile": router_classification.prompt_profile.value,
                },
            )
            return
        if (
            fallback_classification.document_family
            is not router_classification.document_family
            or fallback_classification.prompt_profile
            is not router_classification.prompt_profile
        ):
            _log(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="classify",
                event="force_classifier_fallback_mismatch",
                level="warning",
                message=(
                    "Forced fallback classifier disagreed with rule-based route; "
                    "keeping rule-based classification."
                ),
                details={
                    "router_family": router_classification.document_family.value,
                    "router_prompt_profile": router_classification.prompt_profile.value,
                    "fallback_family": fallback_classification.document_family.value,
                    "fallback_prompt_profile": (
                        fallback_classification.prompt_profile.value
                    ),
                    "fallback_confidence": fallback_classification.confidence,
                },
            )
            return
        _log(
            logger,
            run_id=run_id,
            doc_id=doc_id,
            stage="classify",
            event="force_classifier_fallback_agreed",
            level="info",
            message=(
                "Forced fallback classifier agreed with rule-based route; "
                "keeping rule-based classification."
            ),
            details={
                "router_family": router_classification.document_family.value,
                "router_prompt_profile": router_classification.prompt_profile.value,
                "fallback_confidence": fallback_classification.confidence,
            },
        )

    def _run_llm_request(
        self,
        *,
        request: StructuredLlmRequest,
        run_id: str,
        doc_id: str,
        logger: JsonlPipelineLogger | None,
    ) -> StructuredLlmResponse:
        attempts = self.config.pipeline.retry_model_calls + 1
        timeout_seconds = self.config.model.request_timeout_seconds
        for attempt in range(1, attempts + 1):
            if logger is not None:
                _log(
                    logger,
                    run_id=run_id,
                    doc_id=doc_id,
                    stage=request.stage,
                    event="llm_request_started",
                    level="info",
                    message=(
                        f"Starting LLM request for {request.stage} "
                        f"(attempt {attempt}/{attempts})."
                    ),
                    details=_build_llm_log_details(
                        request=request,
                        doc_id=doc_id,
                        attempt=attempt,
                        max_attempts=attempts,
                        timeout_seconds=timeout_seconds,
                        cost_estimate=self._estimate_stage_cost(
                            request=request,
                            response=None,
                        ),
                    ),
                )
            try:
                response = self._llm().run(request)
            except LlmCallError as error:
                transient = _should_retry_llm_error(error)
                if logger is not None:
                    _log(
                        logger,
                        run_id=run_id,
                        doc_id=doc_id,
                        stage=request.stage,
                        event="llm_request_failed",
                        level="warning"
                        if transient and attempt < attempts
                        else "error",
                        message=(
                            f"LLM request for {request.stage} failed on "
                            f"attempt {attempt}/{attempts}."
                        ),
                        error={"code": error.code, "message": error.message},
                        details=_build_llm_log_details(
                            request=request,
                            doc_id=doc_id,
                            attempt=attempt,
                            max_attempts=attempts,
                            timeout_seconds=timeout_seconds,
                            cost_estimate=self._estimate_stage_cost(
                                request=request,
                                response=None,
                            ),
                            error_details=error.details,
                        ),
                    )
                if not transient or attempt >= attempts:
                    raise
                if logger is not None:
                    _log(
                        logger,
                        run_id=run_id,
                        doc_id=doc_id,
                        stage=request.stage,
                        event="llm_retry",
                        level="warning",
                        message=(
                            f"Retrying transient LLM error {error.code} "
                            f"(attempt {attempt + 1}/{attempts})."
                        ),
                        error={"code": error.code, "message": error.message},
                        details=_build_llm_log_details(
                            request=request,
                            doc_id=doc_id,
                            attempt=attempt + 1,
                            max_attempts=attempts,
                            timeout_seconds=timeout_seconds,
                            cost_estimate=self._estimate_stage_cost(
                                request=request,
                                response=None,
                            ),
                        ),
                    )
                sleep(_retry_backoff_seconds(attempt))
                continue
            if logger is not None:
                _log(
                    logger,
                    run_id=run_id,
                    doc_id=doc_id,
                    stage=request.stage,
                    event="llm_request_completed",
                    level="info",
                    message=(
                        f"LLM request for {request.stage} completed on "
                        f"attempt {attempt}/{attempts}."
                    ),
                    details=_build_llm_log_details(
                        request=request,
                        doc_id=doc_id,
                        attempt=attempt,
                        max_attempts=attempts,
                        timeout_seconds=timeout_seconds,
                        cost_estimate=self._estimate_stage_cost(
                            request=request,
                            response=response,
                        ),
                        response=response,
                    ),
                )
            return response
        raise RuntimeError("LLM retry loop exited unexpectedly.")

    def _estimate_stage_cost(
        self,
        *,
        request: StructuredLlmRequest,
        response: StructuredLlmResponse | None,
    ) -> dict[str, Any]:
        return estimate_stage_cost(
            request=request,
            response=response,
            input_cost_per_1k_tokens_usd=self.config.model.input_cost_per_1k_tokens_usd,
            output_cost_per_1k_tokens_usd=self.config.model.output_cost_per_1k_tokens_usd,
        )


def _build_analysis_input_payload(
    *,
    doc_id: str,
    language_code: str,
    title: str | None,
    parse_metadata: dict[str, object],
    canonical_result: CanonicalTextResult,
    force_packed_input: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "doc_id": doc_id,
        "relative_path": doc_id,
        "language_original": language_code,
        "title": title,
        "doc_metadata": parse_metadata,
        "text_preview": canonical_result.text_preview,
        "canonicalization_strategy": canonical_result.strategy,
    }
    use_packed_input = force_packed_input or (
        len(canonical_result.canonical_text) > PACKED_INPUT_THRESHOLD_CHARS
    )
    if use_packed_input:
        payload["document_sections"] = [
            {
                "section_id": section.section_id,
                "heading": section.heading,
                "text": section.text,
            }
            for section in canonical_result.sections
        ]
        payload["input_mode"] = "packed_sections"
        return payload
    payload["canonical_text"] = canonical_result.canonical_text
    payload["input_mode"] = "canonical_text"
    return payload


def should_skip_existing_document_in_new_mode(
    *,
    existing: dict[str, Any] | None,
    discovered_sha256: str,
    candidate_analysis_fingerprint: str | None = None,
) -> bool:
    if existing is None:
        return False
    if _source_sha(existing) != discovered_sha256:
        return False
    if _processing_status(existing) == "skipped_non_target":
        return True
    if _processing_status(existing) != "completed":
        return False
    if _annotation_status(existing) != "completed":
        return False
    if candidate_analysis_fingerprint is None:
        return False
    return _analysis_fingerprint(existing) == candidate_analysis_fingerprint


def _record_outcome(summary: PipelineRunSummary, outcome: str) -> None:
    if outcome == "completed":
        summary.completed_count += 1
        summary.processed_count += 1
    elif outcome == "partial":
        summary.partial_count += 1
        summary.processed_count += 1
    elif outcome == "failed":
        summary.failed_count += 1
        summary.processed_count += 1
    elif outcome == "skipped_non_target":
        summary.skipped_non_target_count += 1
        summary.processed_count += 1


def _build_failed_llm_updates(
    *,
    request: StructuredLlmRequest,
    error_code: str,
    error_message: str,
    error_details: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "provider": request.provider,
        "api": request.api,
        "model_id": request.model_id,
        "reasoning_effort": request.reasoning_effort,
        "text_format": "json_schema",
        "text_verbosity": request.text_verbosity,
        "max_output_tokens": request.max_output_tokens,
        "store": request.store,
        "truncation": request.truncation,
        "prompt_pack_id": request.prompt_pack_id,
        "prompt_pack_version": request.prompt_pack_version,
        "prompt_profile": request.prompt_profile,
        "prompt_hash": request.prompt_hash,
        "request_hash": request.request_hash,
        "status": "failed",
        "error": {"code": error_code, "message": error_message},
    }
    if error_details:
        if "response_id" in error_details:
            payload["response_id"] = error_details["response_id"]
        if "status" in error_details:
            payload["status"] = error_details["status"]
        if "usage" in error_details:
            payload["usage"] = error_details["usage"]
        if "incomplete_details" in error_details:
            payload["incomplete_details"] = error_details["incomplete_details"]
        payload["error"] = {
            "code": error_code,
            "message": error_message,
            "details": error_details,
        }
    return payload


def _build_llm_log_details(
    *,
    request: StructuredLlmRequest,
    doc_id: str,
    attempt: int,
    max_attempts: int,
    timeout_seconds: int,
    cost_estimate: dict[str, Any] | None = None,
    response: StructuredLlmResponse | None = None,
    error_details: dict[str, Any] | None = None,
) -> dict[str, object]:
    details: dict[str, object] = {
        "stage": request.stage,
        "doc_id": doc_id,
        "attempt": attempt,
        "max_attempts": max_attempts,
        "timeout_seconds": timeout_seconds,
        "model_id": request.model_id,
        "reasoning_effort": request.reasoning_effort,
        "max_output_tokens": request.max_output_tokens,
        "request_hash": request.request_hash,
    }
    if cost_estimate is not None:
        details.update(cost_estimate)
    if error_details:
        if "response_id" in error_details:
            details["response_id"] = error_details["response_id"]
        if "status" in error_details:
            details["status"] = error_details["status"]
        usage = error_details.get("usage")
        if isinstance(usage, dict):
            details["usage.input_tokens"] = usage.get("input_tokens")
            details["usage.output_tokens"] = usage.get("output_tokens")
            details["usage.reasoning_tokens"] = usage.get("reasoning_tokens")
        incomplete_details = error_details.get("incomplete_details")
        if isinstance(incomplete_details, dict):
            details["incomplete_details.reason"] = incomplete_details.get("reason")
    if response is None:
        return details
    details.update(
        {
            "response_id": response.response_id,
            "duration_ms": response.duration_ms,
            "usage.input_tokens": response.usage.input_tokens,
            "usage.output_tokens": response.usage.output_tokens,
            "usage.reasoning_tokens": response.usage.reasoning_tokens,
        }
    )
    return details


def _log(
    logger: JsonlPipelineLogger,
    *,
    run_id: str,
    stage: str,
    event: str,
    level: str,
    message: str,
    doc_id: str | None = None,
    error: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    logger.log(
        PipelineLogEvent(
            run_id=run_id,
            doc_id=doc_id,
            stage=stage,
            event=event,
            level=level,
            message=message,
            error=error,
            details=details or {},
        )
    )


def _log_failure(
    logger: JsonlPipelineLogger,
    *,
    run_id: str,
    doc_id: str,
    stage: str,
    error_code: str,
    error_message: str,
    error_details: dict[str, Any] | None = None,
) -> None:
    _log(
        logger,
        run_id=run_id,
        doc_id=doc_id,
        stage=stage,
        event="stage_failed",
        level="error",
        message=error_message,
        error={"code": error_code, "message": error_message},
        details=error_details,
    )


def _log_summary(logger: JsonlPipelineLogger, summary: PipelineRunSummary) -> None:
    _log(
        logger,
        run_id=summary.run_id,
        stage="run",
        event="run_completed",
        level="info",
        message="Pipeline run completed.",
        details={
            "discovered": summary.discovered_count,
            "processed": summary.processed_count,
            "completed": summary.completed_count,
            "partial": summary.partial_count,
            "failed": summary.failed_count,
            "skipped_non_target": summary.skipped_non_target_count,
            "skipped_unchanged": summary.skipped_unchanged_count,
        },
    )


def _load_existing_analysis_output(
    existing: dict[str, Any] | None,
) -> AnalysisAnnotationOutput | None:
    if existing is None:
        return None
    annotation = existing.get("annotation", {})
    if not isinstance(annotation, dict):
        return None
    semantic = annotation.get("semantic")
    original = annotation.get("original")
    if not isinstance(semantic, dict) or not isinstance(original, dict):
        return None
    try:
        return AnalysisAnnotationOutput.model_validate(
            {
                "semantic": semantic,
                "annotation_original": original,
            }
        )
    except ValidationError:
        return None


def _source_sha(existing: dict[str, Any]) -> str | None:
    source = existing.get("source", {})
    if not isinstance(source, dict):
        return None
    return source.get("file_sha256")


def _processing_status(existing: dict[str, Any]) -> str | None:
    processing = existing.get("processing", {})
    if not isinstance(processing, dict):
        return None
    return processing.get("status")


def _processing_stage(existing: dict[str, Any]) -> str | None:
    processing = existing.get("processing", {})
    if not isinstance(processing, dict):
        return None
    return processing.get("current_stage")


def _analysis_fingerprint(existing: dict[str, Any]) -> str | None:
    annotation = existing.get("annotation", {})
    if not isinstance(annotation, dict):
        return None
    value = annotation.get("analysis_fingerprint")
    return value if isinstance(value, str) else None


def _require_openai_api_key(
    *,
    config: PipelineConfig,
    llm_client: AnnotationLlmClient | None,
    dry_run: bool,
) -> None:
    if dry_run:
        return
    if llm_client is not None:
        return
    if config.model.provider != "openai" or config.model.api != "responses":
        return
    if os.getenv("OPENAI_API_KEY"):
        return
    raise RuntimeError(
        "OPENAI_API_KEY is not configured. "
        "Run preflight and export the key before live annotation."
    )


def _annotation_status(existing: dict[str, Any]) -> str | None:
    annotation = existing.get("annotation", {})
    if not isinstance(annotation, dict):
        return None
    value = annotation.get("status")
    return value if isinstance(value, str) else None


def _canonical_text_sha(existing: dict[str, Any]) -> str | None:
    source = existing.get("source", {})
    if not isinstance(source, dict):
        return None
    value = source.get("canonical_text_sha256")
    return value if isinstance(value, str) and value else None


def _source_language(existing: dict[str, Any]) -> str | None:
    source = existing.get("source", {})
    if not isinstance(source, dict):
        return None
    value = source.get("language_original")
    return value if isinstance(value, str) and value else None


def _should_retry_llm_error(error: LlmCallError) -> bool:
    if error.code in _TRANSPORT_RETRYABLE_LLM_ERROR_CODES:
        return True
    if error.code == "llm_http_error":
        status_code = None
        if error.details is not None:
            raw_status = error.details.get("status_code")
            if isinstance(raw_status, int):
                status_code = raw_status
        return _is_retryable_http_status(status_code)
    if error.code == "llm_incomplete":
        reason = _extract_incomplete_reason(error.details)
        return reason is None
    return False


def _should_retry_analysis_with_packed_input(
    error: LlmCallError,
    request: StructuredLlmRequest,
) -> bool:
    if error.code != "llm_incomplete":
        return False
    if _extract_incomplete_reason(error.details) != "max_output_tokens":
        return False
    return request.input_payload.get("input_mode") != "packed_sections"


def _should_retry_translation_compact(error: LlmCallError) -> bool:
    if error.code != "llm_incomplete":
        return False
    return _extract_incomplete_reason(error.details) == "max_output_tokens"


def _select_translation_output_budget(
    *,
    input_payload: dict[str, Any],
    configured_default: int,
) -> int:
    serialized = json.dumps(
        input_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if not serialized:
        return configured_default
    payload_chars = len(serialized)
    if payload_chars <= 8_000:
        return 8_000
    if payload_chars <= 16_000:
        return min(
            DEFAULT_TRANSLATION_RU_MAX_OUTPUT_TOKENS_MAX,
            max(configured_default, DEFAULT_TRANSLATION_RU_MAX_OUTPUT_TOKENS),
        )
    return min(DEFAULT_TRANSLATION_RU_MAX_OUTPUT_TOKENS_MAX, 16_000)


def _build_translation_compact_retry_request(
    request: StructuredLlmRequest,
) -> StructuredLlmRequest:
    compact_input_payload = _build_compact_translation_payload(request.input_payload)
    max_output_tokens = _select_translation_output_budget(
        input_payload=compact_input_payload,
        configured_default=DEFAULT_TRANSLATION_RU_MAX_OUTPUT_TOKENS,
    )
    return StructuredLlmRequest(
        stage=request.stage,
        system_prompt=request.system_prompt,
        input_payload=compact_input_payload,
        output_schema=request.output_schema,
        output_model=request.output_model,
        metadata=dict(request.metadata),
        provider=request.provider,
        api=request.api,
        model_id=request.model_id,
        reasoning_effort=request.reasoning_effort,
        text_verbosity=request.text_verbosity,
        truncation=request.truncation,
        store=request.store,
        max_output_tokens=max_output_tokens,
        prompt_pack_id=request.prompt_pack_id,
        prompt_pack_version=request.prompt_pack_version,
        prompt_profile=request.prompt_profile,
        prompt_hash=request.prompt_hash,
        request_hash=build_request_hash(
            system_prompt=request.system_prompt,
            input_payload=compact_input_payload,
            output_schema=request.output_schema,
            model_id=request.model_id,
            reasoning_effort=request.reasoning_effort,
            text_verbosity=request.text_verbosity,
            max_output_tokens=max_output_tokens,
        ),
    )


def _build_compact_translation_payload(
    input_payload: dict[str, Any],
) -> dict[str, Any]:
    semantic_context = input_payload.get("semantic_context")
    compact_semantic_context: dict[str, Any] = {}
    if isinstance(semantic_context, dict):
        compact_semantic_context = {
            "document_type_code": semantic_context.get("document_type_code"),
            "topic_codes": semantic_context.get("topic_codes"),
            "use_for_tasks_codes": semantic_context.get("use_for_tasks_codes"),
        }
    annotation_original = input_payload.get("annotation_original")
    compact_annotation: dict[str, Any] = {}
    if isinstance(annotation_original, dict):
        compact_annotation = {
            "language_code": annotation_original.get("language_code"),
            "document_type_label": _truncate_text(
                annotation_original.get("document_type_label"),
                limit=200,
            ),
            "summary": _truncate_text(
                annotation_original.get("summary"),
                limit=800,
            ),
            "practical_value": _truncate_list(
                annotation_original.get("practical_value"),
                item_limit=180,
                list_limit=3,
            ),
            "best_use_scenarios": _truncate_list(
                annotation_original.get("best_use_scenarios"),
                item_limit=180,
                list_limit=3,
            ),
            "use_for_tasks_labels": _truncate_list(
                annotation_original.get("use_for_tasks_labels"),
                item_limit=120,
                list_limit=4,
            ),
            "read_first": _truncate_list(
                annotation_original.get("read_first"),
                item_limit=160,
                list_limit=4,
            ),
            "limitations": _truncate_list(
                annotation_original.get("limitations"),
                item_limit=160,
                list_limit=4,
            ),
            "tags": _truncate_list(
                annotation_original.get("tags"),
                item_limit=80,
                list_limit=6,
            ),
        }
    compact_payload = {
        "doc_id": input_payload.get("doc_id"),
        "semantic_context": compact_semantic_context,
        "annotation_original": compact_annotation,
    }
    return compact_payload


def _truncate_text(value: Any, *, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(1, limit - 3)].rstrip() + "..."


def _truncate_list(
    value: Any,
    *,
    item_limit: int,
    list_limit: int,
) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for raw_item in value[:list_limit]:
        if not isinstance(raw_item, str):
            continue
        normalized = raw_item.strip()
        if not normalized:
            continue
        if len(normalized) > item_limit:
            normalized = normalized[: max(1, item_limit - 3)].rstrip() + "..."
        items.append(normalized)
    return items


def _extract_incomplete_reason(details: dict[str, Any] | None) -> str | None:
    if not isinstance(details, dict):
        return None
    incomplete_details = details.get("incomplete_details")
    if not isinstance(incomplete_details, dict):
        return None
    reason = incomplete_details.get("reason")
    return reason if isinstance(reason, str) else None


def _is_retryable_http_status(status_code: int | None) -> bool:
    if status_code is None:
        return False
    if status_code in {408, 409, 429}:
        return True
    return 500 <= status_code < 600


def _classification_prompt_profile(
    existing: dict[str, Any],
) -> PromptProfile | None:
    classification = existing.get("classification", {})
    if not isinstance(classification, dict):
        return None
    raw_value = classification.get("prompt_profile")
    if not isinstance(raw_value, str):
        return None
    try:
        return PromptProfile(raw_value)
    except ValueError:
        return None


def _is_file_changed(existing: dict[str, Any], discovered_sha: str) -> bool:
    return _source_sha(existing) != discovered_sha


def _is_non_target_skip_candidate(
    existing: dict[str, Any] | None,
    discovered_sha: str,
) -> bool:
    if existing is None:
        return False
    return _source_sha(existing) == discovered_sha and _processing_status(existing) == "skipped_non_target"


def _is_completed_skip_candidate(
    existing: dict[str, Any] | None,
    discovered_sha: str,
) -> bool:
    if existing is None:
        return False
    return _source_sha(existing) == discovered_sha and _processing_status(existing) == "completed"


def _is_translation_resume_candidate(
    existing: dict[str, Any] | None,
    discovered_sha: str,
) -> bool:
    if existing is None:
        return False
    if _source_sha(existing) != discovered_sha:
        return False
    if _processing_status(existing) != "partial":
        return False
    if _processing_stage(existing) != _RESUME_TRANSLATION_STAGE:
        return False
    return _load_existing_analysis_output(existing) is not None


def _is_failed_rerun_candidate(existing: dict[str, Any]) -> bool:
    return _processing_status(existing) in {"failed", "partial"}


def _fallback_family_prompt_is_consistent(
    *,
    document_family: DocumentFamily,
    prompt_profile: PromptProfile,
) -> bool:
    expected = {
        DocumentFamily.NORMATIVE_ACT: PromptProfile.ADDON_NORMATIVE,
        DocumentFamily.JUDICIAL_DECISION: PromptProfile.ADDON_CASE_LAW,
        DocumentFamily.CONSUMER_ADMIN: PromptProfile.ADDON_UOKIK,
        DocumentFamily.COMMENTARY_ARTICLE: PromptProfile.ADDON_COMMENTARY,
        DocumentFamily.DISCOVERY_REFERENCE: PromptProfile.ADDON_DISCOVERY,
        DocumentFamily.CORPUS_README: PromptProfile.SKIP_NON_TARGET,
    }.get(document_family)
    return expected is not None and expected is prompt_profile


def _default_log_dir(config_path: Path) -> Path:
    config_dir = config_path.resolve().parent
    if config_dir.name == "config":
        return config_dir.parent / "logs"
    return config_dir / "logs"


def _retry_backoff_seconds(attempt: int) -> float:
    return min(0.05 * (2 ** (attempt - 1)), 0.2)
