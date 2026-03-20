from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from pymongo.errors import AutoReconnect

from legal_docs_pipeline.constants import PromptProfile
from legal_docs_pipeline.language import LanguageDetectionResult
from legal_docs_pipeline.llm import (
    StructuredLlmRequest,
    StructuredLlmResponse,
    StructuredLlmUsage,
)
from legal_docs_pipeline.parser import ParsedMarkdownDocument
from legal_docs_pipeline.reader import ReadDocumentResult, TextStats
from legal_docs_pipeline.repository import MongoDocumentRepository
from legal_docs_pipeline.scanner import DiscoveredDocument
from legal_docs_pipeline.schemas import (
    AnalysisAnnotationOutput,
    ClassificationResult,
    TranslationAnnotationOutput,
)
from tests.fake_mongo_runtime import FakeMongoCollection


def test_repository_parse_stage_does_not_set_last_success_at(tmp_path: Path) -> None:
    repository = _build_repository()
    discovered = _build_discovered(tmp_path=tmp_path, file_name="doc.md", sha256="sha-v1")

    repository.upsert_discovered(
        discovered=discovered,
        input_root=tmp_path,
        run_id="run-1",
        mode="new",
    )
    repository.apply_read_result(doc_id="doc.md", read_result=_build_read_result())
    repository.apply_parse_result(
        doc_id="doc.md",
        parse_result=_build_parse_result(),
        language_result=_build_language_result(),
    )

    stored = repository.get_document("doc.md")

    assert stored is not None
    assert stored["processing"]["status"] == "pending_classification"
    assert stored["processing"]["last_success_at"] is None


def test_repository_marks_non_target_as_terminal_success(tmp_path: Path) -> None:
    repository = _build_repository()
    discovered = _build_discovered(
        tmp_path=tmp_path,
        file_name="README.md",
        sha256="sha-readme",
    )

    repository.upsert_discovered(
        discovered=discovered,
        input_root=tmp_path,
        run_id="run-readme",
        mode="full",
    )
    repository.apply_read_result(doc_id="README.md", read_result=_build_read_result())
    repository.apply_parse_result(
        doc_id="README.md",
        parse_result=_build_parse_result(title="Corpus README"),
        language_result=LanguageDetectionResult(
            language_code="en",
            confidence=0.9,
            strategy="heuristic",
            signals=("service_readme_export_markers",),
        ),
    )
    repository.apply_classification_result(
        doc_id="README.md",
        classification_result=ClassificationResult(
            document_family="corpus_readme",
            document_type_code=None,
            prompt_profile="skip_non_target",
            annotatable=False,
            classifier_method="rule_based",
            confidence=0.99,
            router_version="1.0.0",
            signals={"matched_rules": ["file_name:corpus_readme"]},
            skip_reason="service_readme",
        ),
        mode="full",
    )

    stored = repository.get_document("README.md")

    assert stored is not None
    assert stored["annotation"]["status"] == "skipped"
    assert stored["processing"]["status"] == "skipped_non_target"
    assert stored["processing"]["last_success_at"] is not None


def test_repository_translation_success_sets_completed_terminal_state(
    tmp_path: Path,
) -> None:
    repository = _build_repository()
    _persist_partial_annotation(repository=repository, tmp_path=tmp_path)

    repository.apply_translation_result(
        doc_id="doc.md",
        translation_output=_build_translation_output(),
        llm_request=_build_llm_request(stage="annotate_ru", prompt_profile="translate_to_ru"),
        llm_response=_build_llm_response(
            output_payload=_build_translation_output().model_dump(mode="json")
        ),
        mode="new",
    )

    stored = repository.get_document("doc.md")

    assert stored is not None
    assert stored["annotation"]["status"] == "completed"
    assert stored["processing"]["status"] == "completed"
    assert stored["processing"]["last_success_at"] is not None
    assert stored["search"]["tags_ru"] == ["кауция", "решение"]
    assert stored["llm"]["translation_ru"]["prompt_profile"] == "translate_to_ru"


def test_repository_translation_failure_keeps_partial_progress(tmp_path: Path) -> None:
    repository = _build_repository()
    _persist_partial_annotation(repository=repository, tmp_path=tmp_path)

    repository.mark_translation_partial(
        doc_id="doc.md",
        error_code="translation_validation_error",
        error_message="Translation semantic block diverged.",
        mode="rerun",
        llm_updates={
            "prompt_profile": "translate_to_ru",
            "status": "failed",
            "error": {
                "code": "translation_validation_error",
                "message": "Translation semantic block diverged.",
            },
        },
        validation_errors=["translation semantic block must match analysis semantic block."],
        manual_review_required=True,
    )

    stored = repository.get_document("doc.md")

    assert stored is not None
    assert stored["annotation"]["status"] == "partial"
    assert stored["annotation"]["original"]["summary"] == "Dokument porządkuje linię orzeczniczą."
    assert stored["processing"]["status"] == "partial"
    assert stored["processing"]["current_stage"] == "annotate_ru"
    assert stored["annotation"]["qa"]["manual_review_required"] is True
    assert stored["llm"]["translation_ru"]["status"] == "failed"


def test_repository_retries_transient_mongo_write_failures(tmp_path: Path) -> None:
    collection = FlakyMongoCollection(failures_before_success=1)
    repository = MongoDocumentRepository(
        collection=collection,
        schema_version="1.0.0",
        pipeline_version="1.0.0",
        dedup_version="1.0.0",
        router_version="1.0.0",
        history_tail_size=10,
        retry_mongo_writes=1,
    )

    repository.upsert_discovered(
        discovered=_build_discovered(tmp_path=tmp_path, file_name="doc.md", sha256="sha-v1"),
        input_root=tmp_path,
        run_id="run-retry",
        mode="new",
    )

    stored = repository.get_document("doc.md")

    assert stored is not None
    assert collection.update_attempts == 2


def test_repository_ensure_indexes_does_not_request_unique_id_index() -> None:
    collection = FakeMongoCollection()
    repository = MongoDocumentRepository(
        collection=collection,
        schema_version="1.0.0",
        pipeline_version="1.0.0",
        dedup_version="1.0.0",
        router_version="1.0.0",
        history_tail_size=10,
    )

    repository.ensure_indexes()

    id_indexes = [
        index for index in collection.indexes if index["keys"] == [("_id", 1)]
    ]

    assert id_indexes == [{"keys": [("_id", 1)], "kwargs": {}}]


def _persist_partial_annotation(
    *,
    repository: MongoDocumentRepository,
    tmp_path: Path,
) -> None:
    discovered = _build_discovered(tmp_path=tmp_path, file_name="doc.md", sha256="sha-v1")
    repository.upsert_discovered(
        discovered=discovered,
        input_root=tmp_path,
        run_id="run-1",
        mode="new",
    )
    repository.apply_read_result(doc_id="doc.md", read_result=_build_read_result())
    repository.apply_parse_result(
        doc_id="doc.md",
        parse_result=_build_parse_result(),
        language_result=_build_language_result(),
    )
    repository.apply_classification_result(
        doc_id="doc.md",
        classification_result=_build_classification_result(),
        mode="new",
    )
    repository.apply_analysis_result(
        doc_id="doc.md",
        annotation_output=_build_analysis_output(),
        analysis_fingerprint="analysis-fingerprint",
        llm_request=_build_llm_request(
            stage="annotate_original",
            prompt_profile="addon_case_law",
        ),
        llm_response=_build_llm_response(
            output_payload=_build_analysis_output().model_dump(mode="json")
        ),
        mode="new",
    )


def _build_repository() -> MongoDocumentRepository:
    collection = FakeMongoCollection()
    repository = MongoDocumentRepository(
        collection=collection,
        schema_version="1.0.0",
        pipeline_version="1.0.0",
        dedup_version="1.0.0",
        router_version="1.0.0",
        history_tail_size=10,
        retry_mongo_writes=2,
    )
    repository.ensure_indexes()
    return repository


class FlakyMongoCollection(FakeMongoCollection):
    def __init__(self, *, failures_before_success: int) -> None:
        super().__init__()
        self.failures_before_success = failures_before_success
        self.update_attempts = 0

    def update_one(
        self,
        query: dict[str, object],
        update: dict[str, object],
        *,
        upsert: bool = False,
    ) -> None:
        self.update_attempts += 1
        if self.failures_before_success > 0:
            self.failures_before_success -= 1
            raise AutoReconnect("temporary reconnect")
        super().update_one(query, update, upsert=upsert)


def _build_discovered(
    *,
    tmp_path: Path,
    file_name: str,
    sha256: str,
) -> DiscoveredDocument:
    file_path = tmp_path / file_name
    file_path.write_text("content", encoding="utf-8")
    return DiscoveredDocument(
        absolute_path=file_path,
        relative_path=PurePosixPath(file_name),
        file_name=file_name,
        size_bytes=file_path.stat().st_size,
        modified_at=datetime.now(tz=timezone.utc),
        sha256_hex=sha256,
        top_level_dir="",
    )


def _build_read_result() -> ReadDocumentResult:
    return ReadDocumentResult(
        raw_markdown="## Content\n\nWYROK\n",
        normalized_text="## Content\n\nWYROK\n",
        normalized_text_sha256="normalized-sha",
        title="WYROK",
        text_stats=TextStats(chars=10, lines=2, words=1),
    )


def _build_parse_result(*, title: str = "WYROK") -> ParsedMarkdownDocument:
    return ParsedMarkdownDocument(
        doc_metadata={
            "canonical_doc_uid": "saos_pl:123",
            "original_source_system": "saos_pl",
        },
        content_markdown="WYROK\nSygn. akt I C 1/20",
        title=title,
        had_metadata_block=True,
        had_content_block=True,
        warnings=(),
    )


def _build_language_result() -> LanguageDetectionResult:
    return LanguageDetectionResult(
        language_code="pl",
        confidence=1.0,
        strategy="heuristic",
        signals=("text_markers_pl=3",),
    )


def _build_classification_result() -> ClassificationResult:
    return ClassificationResult(
        document_family="judicial_decision",
        document_type_code="pl_judgment",
        prompt_profile=PromptProfile.ADDON_CASE_LAW,
        annotatable=True,
        classifier_method="rule_based",
        confidence=0.95,
        router_version="1.0.0",
        signals={"matched_rules": ["judicial_decision"]},
        skip_reason=None,
    )


def _build_analysis_output() -> AnalysisAnnotationOutput:
    return AnalysisAnnotationOutput.model_validate(
        {
            "semantic": {
                "document_type_code": "pl_judgment",
                "authority_level": "high",
                "relevance": "core",
                "usually_supports": "depends",
                "topic_codes": ["deposit_return_term"],
                "use_for_tasks_codes": ["claim", "legal_position"],
            },
            "annotation_original": {
                "language_code": "pl",
                "document_type_label": "wyrok",
                "summary": "Dokument porządkuje linię orzeczniczą.",
                "practical_value": ["Pomaga ocenić potrącenie i termin zwrotu."],
                "best_use_scenarios": ["Spór o zwrot kaucji po zakończeniu najmu."],
                "use_for_tasks_labels": ["pozew", "pozycja prawna"],
                "read_first": ["Sentencja.", "Fragmenty uzasadnienia o potrąceniu."],
                "limitations": ["Dotyczy konkretnego stanu faktycznego."],
                "tags": ["kaucja", "wyrok"],
            },
        }
    )


def _build_translation_output() -> TranslationAnnotationOutput:
    return TranslationAnnotationOutput.model_validate(
        {
            "semantic": _build_analysis_output().semantic.model_dump(mode="json"),
            "annotation_ru": {
                "language_code": "ru",
                "document_type_label": "решение суда",
                "summary": "Документ систематизирует аргументацию по возврату кауции.",
                "practical_value": ["Помогает при подготовке иска."],
                "best_use_scenarios": ["Спор о возврате кауции после окончания найма."],
                "use_for_tasks_labels": ["иск", "правовая позиция"],
                "read_first": ["Резолютивная часть.", "Фрагменты мотивировки о зачёте."],
                "limitations": ["Связано с конкретной фактической ситуацией."],
                "tags": ["кауция", "решение"],
            },
        }
    )


def _build_llm_request(*, stage: str, prompt_profile: str) -> StructuredLlmRequest:
    output_model = (
        AnalysisAnnotationOutput if stage == "annotate_original" else TranslationAnnotationOutput
    )
    return StructuredLlmRequest(
        stage=stage,
        system_prompt="system prompt",
        input_payload={"doc_id": "doc.md"},
        output_schema={"type": "object"},
        output_model=output_model,
        metadata={
            "run_id": "run-1",
            "doc_id": "doc.md",
            "prompt_pack_version": "2026-03-16",
            "prompt_profile": prompt_profile,
        },
        provider="openai",
        api="responses",
        model_id="gpt-5.4",
        reasoning_effort="xhigh",
        text_verbosity="low",
        truncation="disabled",
        store=False,
        max_output_tokens=32000 if stage == "annotate_original" else 12000,
        prompt_pack_id="kaucja-prompt-pack",
        prompt_pack_version="2026-03-16",
        prompt_profile=prompt_profile,
        prompt_hash="prompt-hash",
        request_hash="request-hash",
    )


def _build_llm_response(*, output_payload: dict[str, object]) -> StructuredLlmResponse:
    return StructuredLlmResponse(
        response_id="resp_123",
        output_payload=output_payload,
        raw_json="{}",
        status="completed",
        completed_at=datetime.now(tz=timezone.utc),
        duration_ms=1234,
        usage=StructuredLlmUsage(
            input_tokens=10,
            output_tokens=20,
            reasoning_tokens=5,
        ),
    )
