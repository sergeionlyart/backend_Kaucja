"""Discovery, routing, rerun, and two-stage annotation pipeline for NormaDepo."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from time import sleep
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .config import PipelineConfig
from .constants import DocumentFamily, PipelineMode, PromptProfile, RerunScope
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
from .repository import MongoDocumentRepository
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
_TRANSIENT_LLM_ERROR_CODES = frozenset({"llm_timeout", "llm_rate_limit"})


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
        self.reader = reader or MarkdownReader()
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
        except ReadDocumentError as error:
            repository.mark_failed(
                doc_id=doc_id,
                stage="read",
                error_code=error.code,
                error_message=error.message,
                mode=mode,
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="read",
                error_code=error.code,
                error_message=error.message,
            )
            return "failed"

        try:
            parse_result = self.parser.parse(
                file_name=document.file_name,
                normalized_text=read_result.normalized_text,
            )
        except MarkdownParseError as error:
            repository.mark_failed(
                doc_id=doc_id,
                stage="parse",
                error_code=error.code,
                error_message=error.message,
                mode=mode,
            )
            _log_failure(
                logger,
                run_id=run_id,
                doc_id=doc_id,
                stage="parse",
                error_code=error.code,
                error_message=error.message,
            )
            return "failed"

        language_result = self.language_detector.detect(
            normalized_text=read_result.normalized_text,
            doc_metadata=parse_result.doc_metadata,
            relative_path=doc_id,
            title=parse_result.title or read_result.title,
        )
        classification = self.router.route(
            RoutingInput(
                relative_path=doc_id,
                file_name=document.file_name,
                title=parse_result.title or read_result.title,
                metadata=parse_result.doc_metadata,
                normalized_text=read_result.normalized_text,
            )
        )
        if language_result.language_code == "und":
            if not classification.annotatable:
                repository.apply_parse_result(
                    doc_id=doc_id,
                    parse_result=parse_result,
                    language_result=language_result,
                )
                repository.apply_classification_result(
                    doc_id=doc_id,
                    classification_result=classification,
                    mode=mode,
                )
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
                stage="parse",
                error_code="failed_language_detection",
                error_message="Unable to determine source language.",
                mode=mode,
                warnings=("language_undetermined",),
                source_updates={
                    "language_original": "und",
                    "doc_metadata": dict(parse_result.doc_metadata),
                    "content_markdown": parse_result.content_markdown,
                    "title": parse_result.title or read_result.title,
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
                stage="parse",
                error_code="failed_language_detection",
                error_message="Unable to determine source language.",
            )
            return "failed"

        repository.apply_parse_result(
            doc_id=doc_id,
            parse_result=parse_result,
            language_result=language_result,
        )
        if classification.document_family is DocumentFamily.UNKNOWN:
            classification = self._run_fallback_classifier(
                doc_id=doc_id,
                run_id=run_id,
                parse_result=parse_result,
                read_result=read_result,
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
                read_result=read_result,
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

        repository.apply_classification_result(
            doc_id=doc_id,
            classification_result=classification,
            mode=mode,
        )
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
            classification.prompt_profile
        )
        analysis_fingerprint = build_analysis_fingerprint(
            normalized_text_sha256=read_result.normalized_text_sha256,
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
            read_result=read_result,
            resolved_prompt=resolved_prompt,
        )

        try:
            analysis_response = self._run_llm_request(
                request=analysis_request,
                run_id=run_id,
                doc_id=doc_id,
                logger=logger,
            )
            analysis_output = AnalysisAnnotationOutput.model_validate(
                analysis_response.output_payload
            )
            validation_errors = validate_analysis_business_rules(
                analysis_output,
                source_language=language_result.language_code,
            )
            if validation_errors:
                raise AnalysisBusinessValidationError(validation_errors)
        except LlmCallError as error:
            repository.mark_failed(
                doc_id=doc_id,
                stage="annotate_original",
                error_code=error.code,
                error_message=error.message,
                mode=mode,
                llm_updates=_build_failed_llm_updates(
                    request=analysis_request,
                    error_code=error.code,
                    error_message=error.message,
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
            )
            return "failed"
        except ValidationError as error:
            message = "Analysis response failed schema validation."
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
            message = "Analysis response failed business validation."
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

        repository.apply_analysis_result(
            doc_id=doc_id,
            annotation_output=analysis_output,
            analysis_fingerprint=analysis_fingerprint,
            llm_request=analysis_request,
            llm_response=analysis_response,
            mode=mode,
        )

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
            translation_response = self._run_llm_request(
                request=translation_request,
                run_id=run_id,
                doc_id=doc_id,
                logger=logger,
            )
            translation_output = TranslationAnnotationOutput.model_validate(
                translation_response.output_payload
            )
            validation_errors = validate_translation_business_rules(
                translation_output,
                expected_semantic=analysis_output.semantic,
            )
            if validation_errors:
                raise TranslationBusinessValidationError(validation_errors)
        except LlmCallError as error:
            repository.mark_translation_partial(
                doc_id=doc_id,
                error_code=error.code,
                error_message=error.message,
                mode=mode,
                llm_updates=_build_failed_llm_updates(
                    request=translation_request,
                    error_code=error.code,
                    error_message=error.message,
                ),
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
        except ValidationError as error:
            message = "Translation response failed schema validation."
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
            message = "Translation response failed business validation."
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

        repository.apply_translation_result(
            doc_id=doc_id,
            translation_output=translation_output,
            llm_request=translation_request,
            llm_response=translation_response,
            mode=mode,
        )
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
        language_result = self.language_detector.detect(
            normalized_text=read_result.normalized_text,
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
                normalized_text=read_result.normalized_text,
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
                read_result=read_result,
                title=parse_result.title or read_result.title,
            )
        if classification is None or classification.document_family is DocumentFamily.UNKNOWN:
            raise ValueError("Document family could not be resolved.")
        if not classification.annotatable:
            return None

        resolved_prompt = self.prompt_resolver.resolve_analysis_prompt(
            classification.prompt_profile
        )
        analysis_fingerprint = build_analysis_fingerprint(
            normalized_text_sha256=read_result.normalized_text_sha256,
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
        read_result: ReadDocumentResult,
        title: str | None,
    ) -> ClassificationResult | None:
        prompt_hash = hash_prompt_text(_FALLBACK_CLASSIFIER_SYSTEM_PROMPT)
        input_payload = {
            "doc_id": doc_id,
            "title": title,
            "doc_metadata": parse_result.doc_metadata,
            "excerpt": read_result.normalized_text[:2000],
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
        read_result: ReadDocumentResult,
        resolved_prompt: ResolvedPrompt,
    ) -> StructuredLlmRequest:
        output_schema = export_analysis_json_schema()
        input_payload = {
            "doc_id": doc_id,
            "relative_path": doc_id,
            "language_original": language_code,
            "title": read_result.title,
            "doc_metadata": parse_metadata,
            "markdown_document": read_result.normalized_text,
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
            "analysis_result": analysis_output.model_dump(mode="json"),
        }
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
            max_output_tokens=self.config.model.translation_ru_max_output_tokens,
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
                max_output_tokens=self.config.model.translation_ru_max_output_tokens,
            ),
        )

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
        normalized_text_sha256 = _normalized_text_sha(existing)
        prompt_profile = _classification_prompt_profile(existing)
        if not normalized_text_sha256 or prompt_profile is None:
            return None
        if prompt_profile is PromptProfile.SKIP_NON_TARGET:
            return None
        try:
            resolved_prompt = self.prompt_resolver.resolve_analysis_prompt(prompt_profile)
        except (FileNotFoundError, ValueError):
            return None
        return build_analysis_fingerprint(
            normalized_text_sha256=normalized_text_sha256,
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
        for attempt in range(1, attempts + 1):
            try:
                return self._llm().run(request)
            except LlmCallError as error:
                if (
                    error.code not in _TRANSIENT_LLM_ERROR_CODES
                    or attempt >= attempts
                ):
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
                        details={"attempt": attempt + 1, "max_attempts": attempts},
                    )
                sleep(_retry_backoff_seconds(attempt))
        raise RuntimeError("LLM retry loop exited unexpectedly.")


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
) -> dict[str, object]:
    return {
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


def _annotation_status(existing: dict[str, Any]) -> str | None:
    annotation = existing.get("annotation", {})
    if not isinstance(annotation, dict):
        return None
    value = annotation.get("status")
    return value if isinstance(value, str) else None


def _normalized_text_sha(existing: dict[str, Any]) -> str | None:
    source = existing.get("source", {})
    if not isinstance(source, dict):
        return None
    value = source.get("normalized_text_sha256")
    return value if isinstance(value, str) and value else None


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
