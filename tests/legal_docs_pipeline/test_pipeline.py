from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from legal_docs_pipeline.canonicalize import CanonicalSection, CanonicalTextResult
from legal_docs_pipeline.config import PipelineConfig
from legal_docs_pipeline.constants import PipelineMode, PromptProfile, RerunScope
from legal_docs_pipeline.llm import (
    LlmCallError,
    StructuredLlmRequest,
    StructuredLlmResponse,
    StructuredLlmUsage,
)
from legal_docs_pipeline.pipeline import (
    AnnotationPipeline,
    PipelineRunOptions,
    should_skip_existing_document_in_new_mode,
)
from legal_docs_pipeline.repository import MongoDocumentRepository
from legal_docs_pipeline.reader import TextStats
from legal_docs_pipeline.schemas import AnalysisAnnotationOutput, ClassificationResult
from tests.fake_mongo_runtime import FakeMongoCollection


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ScriptedLlmClient:
    def __init__(self, script: list[dict[str, Any] | Exception]) -> None:
        self.calls: list[StructuredLlmRequest] = []
        self._script = list(script)

    def run(self, request: StructuredLlmRequest) -> StructuredLlmResponse:
        self.calls.append(request)
        if not self._script:
            raise AssertionError(f"Unexpected LLM call for stage {request.stage}.")

        outcome = self._script.pop(0)
        if isinstance(outcome, Exception):
            raise outcome

        return StructuredLlmResponse(
            response_id=f"resp_{len(self.calls)}",
            output_payload=outcome,
            raw_json=json.dumps(outcome, ensure_ascii=False, sort_keys=True),
            status="completed",
            completed_at=datetime.now(tz=timezone.utc),
            duration_ms=1200,
            usage=StructuredLlmUsage(
                input_tokens=100,
                output_tokens=200,
                reasoning_tokens=40,
            ),
        )


def test_should_skip_new_mode_only_for_valid_terminal_records() -> None:
    unchanged_partial = _build_existing(status="partial", file_sha256="same-sha")
    unchanged_failed = _build_existing(status="failed", file_sha256="same-sha")
    unchanged_pending = _build_existing(
        status="pending_annotate_original",
        file_sha256="same-sha",
    )
    unchanged_skipped = _build_existing(
        status="skipped_non_target",
        file_sha256="same-sha",
        annotation_status="skipped",
    )
    unchanged_completed = _build_existing(
        status="completed",
        file_sha256="same-sha",
        analysis_fingerprint="fp-1",
        annotation_status="completed",
    )
    invalid_completed = _build_existing(
        status="completed",
        file_sha256="same-sha",
        analysis_fingerprint="fp-1",
        annotation_status="partial",
    )

    assert (
        should_skip_existing_document_in_new_mode(
            existing=unchanged_partial,
            discovered_sha256="same-sha",
        )
        is False
    )
    assert (
        should_skip_existing_document_in_new_mode(
            existing=unchanged_failed,
            discovered_sha256="same-sha",
        )
        is False
    )
    assert (
        should_skip_existing_document_in_new_mode(
            existing=unchanged_pending,
            discovered_sha256="same-sha",
        )
        is False
    )
    assert (
        should_skip_existing_document_in_new_mode(
            existing=unchanged_skipped,
            discovered_sha256="same-sha",
        )
        is True
    )
    assert (
        should_skip_existing_document_in_new_mode(
            existing=unchanged_completed,
            discovered_sha256="same-sha",
            candidate_analysis_fingerprint="fp-1",
        )
        is True
    )
    assert (
        should_skip_existing_document_in_new_mode(
            existing=unchanged_completed,
            discovered_sha256="same-sha",
        )
        is False
    )
    assert (
        should_skip_existing_document_in_new_mode(
            existing=invalid_completed,
            discovered_sha256="same-sha",
            candidate_analysis_fingerprint="fp-1",
        )
        is False
    )


def test_pipeline_skips_non_target_without_llm(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    (input_root / "README.md").write_text(
        "# cas_law markdown export\n\nGenerated at: 2026-03-16\n",
        encoding="utf-8",
    )

    repository = _build_repository()
    llm_client = ScriptedLlmClient(script=[])
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    stored = repository.get_document("README.md")

    assert summary.processed_count == 1
    assert summary.skipped_non_target_count == 1
    assert llm_client.calls == []
    assert stored is not None
    assert stored["classification"]["document_family"] == "corpus_readme"
    assert stored["classification"]["prompt_profile"] == "skip_non_target"
    assert stored["annotation"]["status"] == "skipped"
    assert stored["processing"]["status"] == "skipped_non_target"


def test_pipeline_dry_run_allows_und_non_target_discovery(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    (input_root / "pl_saos").mkdir(parents=True)
    _write_discovery_search_doc(
        input_root / "pl_saos" / "search_snapshot.md",
    )

    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: _build_repository(),
        llm_client=ScriptedLlmClient(script=[]),
    )

    summary = pipeline.run(
        options=PipelineRunOptions(mode=PipelineMode.FULL, dry_run=True)
    )

    assert summary.processed_count == 1
    assert summary.skipped_non_target_count == 0
    assert summary.failed_count == 0


def test_pipeline_completes_discovery_search_snapshot(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    (input_root / "pl_saos").mkdir(parents=True)
    _write_discovery_search_doc(
        input_root / "pl_saos" / "search_snapshot.md",
    )

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[_analysis_payload_en(), _translation_payload_en()]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    stored = repository.get_document("pl_saos/search_snapshot.md")

    assert summary.processed_count == 1
    assert summary.completed_count == 1
    assert summary.failed_count == 0
    assert [request.stage for request in llm_client.calls] == [
        "annotate_original",
        "annotate_ru",
    ]
    assert stored is not None
    assert stored["source"]["language_original"] == "en"
    assert stored["classification"]["document_family"] == "discovery_reference"
    assert stored["classification"]["prompt_profile"] == "addon_discovery"
    assert stored["annotation"]["status"] == "completed"
    assert stored["processing"]["status"] == "completed"


def test_pipeline_completes_document_with_translation(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[
            _analysis_payload(),
            _translation_payload(),
        ]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    stored = repository.get_document("doc.md")
    log_rows = [
        json.loads(line)
        for line in summary.log_path.read_text(encoding="utf-8").splitlines()
    ]

    assert summary.processed_count == 1
    assert summary.completed_count == 1
    assert summary.partial_count == 0
    assert summary.failed_count == 0
    assert [request.stage for request in llm_client.calls] == [
        "annotate_original",
        "annotate_ru",
    ]
    assert stored is not None
    assert stored["annotation"]["status"] == "completed"
    assert stored["annotation"]["ru"]["summary"].startswith("Документ")
    assert stored["processing"]["status"] == "completed"
    assert stored["processing"]["last_success_at"] is not None
    assert stored["search"]["authority_level"] == "high"
    assert stored["search"]["tags_original"] == ["kaucja", "wyrok"]
    assert stored["search"]["tags_ru"] == ["кауция", "решение"]
    assert stored["llm"]["translation_ru"]["prompt_profile"] == "translate_to_ru"
    assert any(row["event"] == "run_started" for row in log_rows)
    assert any(row["event"] == "run_completed" for row in log_rows)
    assert _stage_events(log_rows, "annotate_original") == [
        "llm_request_started",
        "llm_request_completed",
    ]
    assert _stage_events(log_rows, "annotate_ru") == [
        "llm_request_started",
        "llm_request_completed",
        "completed",
    ]
    assert _find_event(log_rows, "annotate_original", "llm_request_completed")[
        "details"
    ]["usage.reasoning_tokens"] == 40
    assert _find_event(log_rows, "annotate_ru", "llm_request_completed")["details"][
        "timeout_seconds"
    ] == 120


def test_translation_request_uses_configured_translation_budget(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: _build_repository(),
        llm_client=ScriptedLlmClient(script=[]),
    )
    analysis_output = AnalysisAnnotationOutput.model_validate(_analysis_payload())
    resolved_prompt = pipeline.prompt_resolver.resolve_translation_prompt()

    request = pipeline._build_translation_request(
        run_id="run-translation-floor",
        doc_id="doc.md",
        analysis_output=analysis_output,
        resolved_prompt=resolved_prompt,
    )

    assert request.max_output_tokens == 8_000


def test_analysis_request_uses_packed_sections_for_large_canonical_text(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: _build_repository(),
        llm_client=ScriptedLlmClient(script=[]),
    )
    request = pipeline._build_analysis_request(
        run_id="run-packed",
        doc_id="doc.md",
        classification=_build_classification_result(),
        language_code="pl",
        parse_metadata={"canonical_doc_uid": "saos_pl:123"},
        title="WYROK",
        canonical_result=_build_large_canonical_result(),
        resolved_prompt=pipeline.prompt_resolver.resolve_analysis_prompt(
            _build_classification_result().prompt_profile,
            source_language_code="pl",
        ),
    )

    assert request.input_payload["input_mode"] == "packed_sections"
    assert "document_sections" in request.input_payload
    assert "canonical_text" not in request.input_payload


def test_pipeline_requires_openai_api_key_for_default_live_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: _build_repository(),
    )

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not configured"):
        pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))


def test_pipeline_rerun_failed_resumes_translation_for_partial_document(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    first_client = ScriptedLlmClient(
        script=[
            _analysis_payload(),
            LlmCallError(code="llm_timeout", message="Translation timed out."),
        ]
    )
    initial_pipeline = AnnotationPipeline(
        config=_build_config(
            tmp_path=tmp_path,
            input_root=input_root,
            retry_model_calls=0,
        ),
        repository_factory=lambda _config: repository,
        llm_client=first_client,
    )
    initial_summary = initial_pipeline.run(
        options=PipelineRunOptions(mode=PipelineMode.FULL)
    )

    resumed_client = ScriptedLlmClient(script=[_translation_payload()])
    rerun_pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=resumed_client,
    )
    rerun_summary = rerun_pipeline.run(
        options=PipelineRunOptions(mode=PipelineMode.RERUN),
        rerun_scope=RerunScope.FAILED,
    )
    stored = repository.get_document("doc.md")

    assert initial_summary.partial_count == 1
    assert [request.stage for request in first_client.calls] == [
        "annotate_original",
        "annotate_ru",
    ]
    assert rerun_summary.processed_count == 1
    assert rerun_summary.completed_count == 1
    assert [request.stage for request in resumed_client.calls] == ["annotate_ru"]
    assert stored is not None
    assert stored["annotation"]["status"] == "completed"
    assert stored["annotation"]["original"]["summary"].startswith("Dokument")
    assert stored["annotation"]["ru"]["summary"].startswith("Документ")
    assert stored["processing"]["status"] == "completed"


def test_pipeline_rerun_doc_id_resumes_translation_for_partial_document(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    first_client = ScriptedLlmClient(
        script=[
            _analysis_payload(),
            LlmCallError(code="llm_timeout", message="Translation timed out."),
        ]
    )
    initial_pipeline = AnnotationPipeline(
        config=_build_config(
            tmp_path=tmp_path,
            input_root=input_root,
            retry_model_calls=0,
        ),
        repository_factory=lambda _config: repository,
        llm_client=first_client,
    )
    initial_pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))

    resumed_client = ScriptedLlmClient(script=[_translation_payload()])
    rerun_pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=resumed_client,
    )
    rerun_summary = rerun_pipeline.run(
        options=PipelineRunOptions(
            mode=PipelineMode.RERUN,
            only_doc_id="doc.md",
        ),
        rerun_scope=RerunScope.DOC_ID,
    )
    stored = repository.get_document("doc.md")

    assert rerun_summary.processed_count == 1
    assert rerun_summary.completed_count == 1
    assert [request.stage for request in resumed_client.calls] == ["annotate_ru"]
    assert stored is not None
    assert stored["annotation"]["status"] == "completed"
    assert stored["processing"]["status"] == "completed"


def test_pipeline_new_skips_completed_document_when_fingerprint_matches(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    full_pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=ScriptedLlmClient(
            script=[_analysis_payload(), _translation_payload()]
        ),
    )
    full_pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    before = repository.get_document("doc.md")

    skip_client = ScriptedLlmClient(script=[])
    new_pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=skip_client,
    )
    summary = new_pipeline.run(options=PipelineRunOptions(mode=PipelineMode.NEW))
    after = repository.get_document("doc.md")

    assert summary.processed_count == 0
    assert summary.skipped_unchanged_count == 1
    assert summary.skipped_count == 1
    assert skip_client.calls == []
    assert before is not None
    assert after is not None
    assert after["processing"]["last_success_at"] == before["processing"]["last_success_at"]


def test_pipeline_new_skips_completed_fallback_classified_document(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_unknown_doc(input_root / "unknown.md")

    repository = _build_repository()
    _run_completed_fallback_pipeline(
        tmp_path=tmp_path,
        input_root=input_root,
        repository=repository,
    )

    skip_client = ScriptedLlmClient(script=[])
    new_pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=skip_client,
    )
    summary = new_pipeline.run(options=PipelineRunOptions(mode=PipelineMode.NEW))

    assert summary.processed_count == 0
    assert summary.skipped_unchanged_count == 1
    assert skip_client.calls == []


def test_pipeline_rerun_stale_skips_completed_fallback_classified_document(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_unknown_doc(input_root / "unknown.md")

    repository = _build_repository()
    _run_completed_fallback_pipeline(
        tmp_path=tmp_path,
        input_root=input_root,
        repository=repository,
    )

    stale_client = ScriptedLlmClient(script=[])
    stale_pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=stale_client,
    )
    summary = stale_pipeline.run(
        options=PipelineRunOptions(mode=PipelineMode.RERUN),
        rerun_scope=RerunScope.STALE,
    )

    assert summary.processed_count == 0
    assert summary.completed_count == 0
    assert stale_client.calls == []


@pytest.mark.parametrize(
    ("change_kind", "config_updates"),
    [
        ("prompt_pack", {"prompt_pack_version": "2026-03-17"}),
        ("model", {"model_id": "gpt-5.5"}),
        ("schema", {"schema_version": "1.0.1"}),
        ("file_content", {}),
    ],
)
def test_pipeline_rerun_stale_reprocesses_fallback_completed_document_when_inputs_change(
    tmp_path: Path,
    change_kind: str,
    config_updates: dict[str, str],
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    document_path = input_root / "unknown.md"
    _write_unknown_doc(document_path)

    repository = _build_repository()
    _run_completed_fallback_pipeline(
        tmp_path=tmp_path,
        input_root=input_root,
        repository=repository,
    )

    if change_kind == "file_content":
        document_path.write_text(
            document_path.read_text(encoding="utf-8")
            + "\nDodatkowy akapit o mediacji lokatora.\n",
            encoding="utf-8",
        )

    rerun_client = ScriptedLlmClient(
        script=[
            _fallback_classification_payload(),
            _analysis_payload(
                document_type_code="commentary_article",
                document_type_label="komentarz",
            ),
            _translation_payload(
                semantic_document_type_code="commentary_article",
                document_type_label="комментарий",
            ),
        ]
    )
    stale_pipeline = AnnotationPipeline(
        config=_build_config(
            tmp_path=tmp_path,
            input_root=input_root,
            **config_updates,
        ),
        repository_factory=lambda _config: repository,
        llm_client=rerun_client,
    )
    summary = stale_pipeline.run(
        options=PipelineRunOptions(mode=PipelineMode.RERUN),
        rerun_scope=RerunScope.STALE,
    )

    assert summary.processed_count == 1
    assert summary.completed_count == 1
    assert [request.stage for request in rerun_client.calls] == [
        "classify_fallback",
        "annotate_original",
        "annotate_ru",
    ]


def test_pipeline_rerun_stale_reprocesses_when_fingerprint_changes(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    first_pipeline = AnnotationPipeline(
        config=_build_config(
            tmp_path=tmp_path,
            input_root=input_root,
            prompt_pack_version="2026-03-16",
        ),
        repository_factory=lambda _config: repository,
        llm_client=ScriptedLlmClient(
            script=[_analysis_payload(), _translation_payload()]
        ),
    )
    first_pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))

    rerun_client = ScriptedLlmClient(
        script=[_analysis_payload(), _translation_payload()]
    )
    stale_pipeline = AnnotationPipeline(
        config=_build_config(
            tmp_path=tmp_path,
            input_root=input_root,
            prompt_pack_version="2026-03-17",
        ),
        repository_factory=lambda _config: repository,
        llm_client=rerun_client,
    )
    summary = stale_pipeline.run(
        options=PipelineRunOptions(mode=PipelineMode.RERUN),
        rerun_scope=RerunScope.STALE,
    )

    assert summary.processed_count == 1
    assert summary.completed_count == 1
    assert [request.stage for request in rerun_client.calls] == [
        "annotate_original",
        "annotate_ru",
    ]


def test_pipeline_retries_transient_llm_errors_using_config_surface(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[
            LlmCallError(code="llm_timeout", message="Temporary timeout."),
            _analysis_payload(),
            _translation_payload(),
        ]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(
            tmp_path=tmp_path,
            input_root=input_root,
            retry_model_calls=1,
        ),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    log_rows = [
        json.loads(line)
        for line in summary.log_path.read_text(encoding="utf-8").splitlines()
    ]

    assert summary.completed_count == 1
    assert [request.stage for request in llm_client.calls] == [
        "annotate_original",
        "annotate_original",
        "annotate_ru",
    ]
    assert _stage_events(log_rows, "annotate_original") == [
        "llm_request_started",
        "llm_request_failed",
        "llm_retry",
        "llm_request_started",
        "llm_request_completed",
    ]


def test_pipeline_marks_original_timeout_failed_and_logs_llm_failure(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[LlmCallError(code="llm_timeout", message="Analysis timed out.")]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(
            tmp_path=tmp_path,
            input_root=input_root,
            retry_model_calls=0,
        ),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    stored = repository.get_document("doc.md")
    log_rows = [
        json.loads(line)
        for line in summary.log_path.read_text(encoding="utf-8").splitlines()
    ]

    assert summary.failed_count == 1
    assert summary.partial_count == 0
    assert [request.stage for request in llm_client.calls] == ["annotate_original"]
    assert stored is not None
    assert stored["annotation"]["status"] == "failed"
    assert stored["processing"]["status"] == "failed"
    assert stored["processing"]["error"]["code"] == "llm_timeout"
    assert _stage_events(log_rows, "annotate_original") == [
        "llm_request_started",
        "llm_request_failed",
        "stage_failed",
    ]
    failure_event = _find_event(log_rows, "annotate_original", "llm_request_failed")
    assert failure_event["error"]["code"] == "llm_timeout"
    assert failure_event["details"]["timeout_seconds"] == 120
    assert failure_event["details"]["attempt"] == 1


def test_pipeline_marks_translation_timeout_partial_and_keeps_original(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[
            _analysis_payload(),
            LlmCallError(code="llm_timeout", message="Translation timed out."),
        ]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(
            tmp_path=tmp_path,
            input_root=input_root,
            retry_model_calls=0,
        ),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    stored = repository.get_document("doc.md")
    log_rows = [
        json.loads(line)
        for line in summary.log_path.read_text(encoding="utf-8").splitlines()
    ]

    assert summary.partial_count == 1
    assert summary.failed_count == 0
    assert [request.stage for request in llm_client.calls] == [
        "annotate_original",
        "annotate_ru",
    ]
    assert stored is not None
    assert stored["annotation"]["status"] == "partial"
    assert stored["annotation"]["original"]["summary"].startswith("Dokument")
    assert "ru" not in stored["annotation"]
    assert stored["processing"]["status"] == "partial"
    assert stored["processing"]["error"]["code"] == "llm_timeout"
    assert _stage_events(log_rows, "annotate_original") == [
        "llm_request_started",
        "llm_request_completed",
    ]
    assert _stage_events(log_rows, "annotate_ru") == [
        "llm_request_started",
        "llm_request_failed",
        "stage_failed",
    ]
    failure_event = _find_event(log_rows, "annotate_ru", "llm_request_failed")
    assert failure_event["error"]["code"] == "llm_timeout"
    assert failure_event["details"]["request_hash"]


def test_pipeline_persists_incomplete_reason_for_translation_partial(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[
            _analysis_payload(),
            LlmCallError(
                code="llm_incomplete",
                message="Responses API returned an incomplete result.",
                details={
                    "response_id": "resp_incomplete_1",
                    "status": "incomplete",
                    "usage": {
                        "input_tokens": 400,
                        "output_tokens": 24000,
                        "reasoning_tokens": 1200,
                    },
                    "incomplete_details": {
                        "reason": "max_output_tokens",
                    },
                },
            ),
            LlmCallError(
                code="llm_incomplete",
                message="Responses API returned an incomplete result.",
                details={
                    "response_id": "resp_incomplete_1",
                    "status": "incomplete",
                    "usage": {
                        "input_tokens": 400,
                        "output_tokens": 24000,
                        "reasoning_tokens": 1200,
                    },
                    "incomplete_details": {
                        "reason": "max_output_tokens",
                    },
                },
            ),
        ]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(
            tmp_path=tmp_path,
            input_root=input_root,
            retry_model_calls=0,
        ),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    stored = repository.get_document("doc.md")
    log_rows = [
        json.loads(line)
        for line in summary.log_path.read_text(encoding="utf-8").splitlines()
    ]

    assert summary.partial_count == 1
    assert [request.stage for request in llm_client.calls] == [
        "annotate_original",
        "annotate_ru",
        "annotate_ru",
    ]
    assert stored is not None
    assert stored["processing"]["status"] == "partial"
    assert stored["processing"]["error"]["code"] == "llm_incomplete"
    assert stored["processing"]["error"]["details"]["incomplete_details"]["reason"] == (
        "max_output_tokens"
    )
    assert stored["llm"]["translation_ru"]["response_id"] == "resp_incomplete_1"
    assert stored["llm"]["translation_ru"]["status"] == "incomplete"
    assert stored["llm"]["translation_ru"]["usage"]["output_tokens"] == 24000
    assert stored["llm"]["translation_ru"]["incomplete_details"]["reason"] == (
        "max_output_tokens"
    )
    failure_event = _find_event(log_rows, "annotate_ru", "llm_request_failed")
    assert failure_event["details"]["response_id"] == "resp_incomplete_1"
    assert failure_event["details"]["status"] == "incomplete"
    assert failure_event["details"]["incomplete_details.reason"] == "max_output_tokens"


def test_pipeline_translation_compact_retry_uses_reduced_payload(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[
            _analysis_payload(),
            LlmCallError(
                code="llm_incomplete",
                message="Responses API returned an incomplete result.",
                details={
                    "response_id": "resp_incomplete_1",
                    "status": "incomplete",
                    "usage": {
                        "input_tokens": 400,
                        "output_tokens": 12000,
                        "reasoning_tokens": 1200,
                    },
                    "incomplete_details": {
                        "reason": "max_output_tokens",
                    },
                },
            ),
            _translation_payload(),
        ]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(
            tmp_path=tmp_path,
            input_root=input_root,
            retry_model_calls=0,
        ),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))

    assert summary.completed_count == 1
    assert [request.stage for request in llm_client.calls] == [
        "annotate_original",
        "annotate_ru",
        "annotate_ru",
    ]
    first_request = llm_client.calls[1]
    second_request = llm_client.calls[2]
    assert json.dumps(second_request.input_payload, ensure_ascii=False) != json.dumps(
        first_request.input_payload,
        ensure_ascii=False,
    )
    assert len(json.dumps(second_request.input_payload, ensure_ascii=False)) < len(
        json.dumps(first_request.input_payload, ensure_ascii=False)
    )
    assert second_request.max_output_tokens <= first_request.max_output_tokens


def test_pipeline_analysis_repair_pass_recovers_structured_output(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[
            _invalid_analysis_payload_missing_summary(),
            _analysis_payload(),
            _translation_payload(),
        ]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    log_rows = [
        json.loads(line)
        for line in summary.log_path.read_text(encoding="utf-8").splitlines()
    ]

    assert summary.completed_count == 1
    assert _find_event(log_rows, "annotate_original", "repair_requested")["details"][
        "validation_errors"
    ]


def test_pipeline_translation_repair_pass_recovers_business_validation(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[
            _analysis_payload(),
            _invalid_translation_payload_wrong_language(),
            _translation_payload(),
        ]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    log_rows = [
        json.loads(line)
        for line in summary.log_path.read_text(encoding="utf-8").splitlines()
    ]

    assert summary.completed_count == 1
    assert _find_event(log_rows, "annotate_ru", "repair_requested")["details"][
        "validation_errors"
    ]


def test_pipeline_force_classifier_fallback_keeps_rule_based_route_when_it_agrees(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[
            _fallback_classification_payload(
                document_family="judicial_decision",
                prompt_profile="addon_case_law",
            ),
            _analysis_payload(),
            _translation_payload(),
        ]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(
        options=PipelineRunOptions(
            mode=PipelineMode.FULL,
            force_classifier_fallback=True,
        )
    )
    stored = repository.get_document("doc.md")

    assert summary.completed_count == 1
    assert [request.stage for request in llm_client.calls] == [
        "classify_fallback",
        "annotate_original",
        "annotate_ru",
    ]
    assert stored is not None
    assert stored["classification"]["classifier_method"] == "rule_based"
    assert stored["classification"]["document_family"] == "judicial_decision"
    assert stored["classification"]["prompt_profile"] == "addon_case_law"


def test_pipeline_force_classifier_fallback_timeout_keeps_rule_based_route(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[
            LlmCallError(code="llm_timeout", message="Fallback timed out."),
            _analysis_payload(),
            _translation_payload(),
        ]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(
            tmp_path=tmp_path,
            input_root=input_root,
            retry_model_calls=0,
        ),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(
        options=PipelineRunOptions(
            mode=PipelineMode.FULL,
            force_classifier_fallback=True,
        )
    )
    stored = repository.get_document("doc.md")

    assert summary.completed_count == 1
    assert [request.stage for request in llm_client.calls] == [
        "classify_fallback",
        "annotate_original",
        "annotate_ru",
    ]
    assert stored is not None
    assert stored["classification"]["classifier_method"] == "rule_based"
    assert stored["processing"]["status"] == "completed"


def test_pipeline_force_classifier_fallback_low_confidence_keeps_rule_based_route(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "doc.md", canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[
            _fallback_classification_payload(confidence=0.4),
            _analysis_payload(),
            _translation_payload(),
        ]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(
        options=PipelineRunOptions(
            mode=PipelineMode.FULL,
            force_classifier_fallback=True,
        )
    )
    stored = repository.get_document("doc.md")

    assert summary.completed_count == 1
    assert [request.stage for request in llm_client.calls] == [
        "classify_fallback",
        "annotate_original",
        "annotate_ru",
    ]
    assert stored is not None
    assert stored["classification"]["classifier_method"] == "rule_based"
    assert stored["processing"]["status"] == "completed"


def test_pipeline_rerun_stale_reprocesses_when_file_changes(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    document_path = input_root / "doc.md"
    _write_judicial_doc(document_path, canonical_doc_uid="saos_pl:123")

    repository = _build_repository()
    first_pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=ScriptedLlmClient(
            script=[_analysis_payload(), _translation_payload()]
        ),
    )
    first_pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))

    document_path.write_text(
        document_path.read_text(encoding="utf-8") + "\nDodatkowy akapit o odsetkach.\n",
        encoding="utf-8",
    )
    rerun_client = ScriptedLlmClient(
        script=[_analysis_payload(), _translation_payload()]
    )
    stale_pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=rerun_client,
    )
    summary = stale_pipeline.run(
        options=PipelineRunOptions(mode=PipelineMode.RERUN),
        rerun_scope=RerunScope.STALE,
    )
    stored = repository.get_document("doc.md")

    assert summary.processed_count == 1
    assert summary.completed_count == 1
    assert [request.stage for request in rerun_client.calls] == [
        "annotate_original",
        "annotate_ru",
    ]
    assert stored is not None
    assert stored["source"]["revision_no"] == 2


def test_pipeline_rerun_doc_id_processes_only_selected_document(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_judicial_doc(input_root / "a.md", canonical_doc_uid="saos_pl:111")
    _write_judicial_doc(input_root / "b.md", canonical_doc_uid="saos_pl:222")

    repository = _build_repository()
    initial_pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=ScriptedLlmClient(
            script=[
                _analysis_payload(),
                _translation_payload(),
                _analysis_payload(),
                _translation_payload(),
            ]
        ),
    )
    initial_pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    before_a = repository.get_document("a.md")
    before_b = repository.get_document("b.md")

    rerun_client = ScriptedLlmClient(
        script=[_analysis_payload(), _translation_payload()]
    )
    rerun_pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=rerun_client,
    )
    summary = rerun_pipeline.run(
        options=PipelineRunOptions(
            mode=PipelineMode.RERUN,
            only_doc_id="b.md",
        ),
        rerun_scope=RerunScope.DOC_ID,
    )
    after_a = repository.get_document("a.md")
    after_b = repository.get_document("b.md")

    assert summary.discovered_count == 1
    assert summary.processed_count == 1
    assert [request.stage for request in rerun_client.calls] == [
        "annotate_original",
        "annotate_ru",
    ]
    assert before_a is not None
    assert before_b is not None
    assert after_a is not None
    assert after_b is not None
    assert after_a["processing"]["run_id"] == before_a["processing"]["run_id"]
    assert after_b["processing"]["run_id"] == summary.run_id


def test_pipeline_uses_fallback_classifier_for_unknown_document(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_unknown_doc(input_root / "unknown.md")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[
            _fallback_classification_payload(),
            _analysis_payload(
                document_type_code="commentary_article",
                document_type_label="komentarz",
            ),
            _translation_payload(
                semantic_document_type_code="commentary_article",
                document_type_label="комментарий",
            ),
        ]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    stored = repository.get_document("unknown.md")

    assert summary.completed_count == 1
    assert [request.stage for request in llm_client.calls] == [
        "classify_fallback",
        "annotate_original",
        "annotate_ru",
    ]
    assert stored is not None
    assert stored["classification"]["classifier_method"] == "llm_fallback"
    assert stored["classification"]["document_family"] == "commentary_article"
    assert stored["classification"]["prompt_profile"] == "addon_commentary"


def test_pipeline_fails_when_fallback_classifier_is_not_confident(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    _write_unknown_doc(input_root / "unknown.md")

    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[_fallback_classification_payload(confidence=0.4)]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))
    stored = repository.get_document("unknown.md")

    assert summary.failed_count == 1
    assert [request.stage for request in llm_client.calls] == ["classify_fallback"]
    assert stored is not None
    assert stored["processing"]["status"] == "failed"
    assert stored["processing"]["error"]["code"] == "classification_error"


def _build_config(
    *,
    tmp_path: Path,
    input_root: Path,
    prompt_pack_version: str = "2026-03-16",
    model_id: str = "gpt-5.4",
    schema_version: str = "1.0.0",
    retry_model_calls: int = 2,
) -> PipelineConfig:
    config = PipelineConfig.model_validate(
        {
            "input": {
                "root_path": input_root,
                "glob": "**/*.md",
                "ignore_hidden": True,
                "max_file_size_bytes": 64 * 1024 * 1024,
            },
            "mongo": {
                "uri": "mongodb://localhost:27017",
                "database": "kaucja_legal_corpus",
                "collection": "documents",
            },
            "model": {
                "provider": "openai",
                "api": "responses",
                "model_id": model_id,
                "reasoning_effort": "xhigh",
                "text_verbosity": "low",
                "truncation": "disabled",
                "store": False,
                "analysis_max_output_tokens": 32000,
                "translation_ru_max_output_tokens": 12000,
            },
            "prompts": {
                "prompt_pack_id": "kaucja-prompt-pack",
                "prompt_pack_version": prompt_pack_version,
                "prompt_dir": PROJECT_ROOT / "prompts/kaucja",
            },
            "pipeline": {
                "schema_version": schema_version,
                "pipeline_version": "1.0.0",
                "workers": 1,
                "dedup_version": "1.0.0",
                "router_version": "1.0.0",
                "history_tail_size": 10,
                "retry_model_calls": retry_model_calls,
                "retry_mongo_writes": 2,
                "llm_dispatch_mode": "direct",
                "batch_max_requests": 25,
                "batch_max_input_file_bytes": 8 * 1024 * 1024,
                "batch_poll_interval_seconds": 30,
                "batch_inflight_jobs_limit": 2,
                "batch_min_requests_to_submit": 5,
                "batch_apply_direct_fallback": True,
            },
        }
    )
    return config.model_copy(update={"config_path": tmp_path / "pipeline.yaml"})


def _build_repository() -> MongoDocumentRepository:
    repository = MongoDocumentRepository(
        collection=FakeMongoCollection(),
        schema_version="1.0.0",
        pipeline_version="1.0.0",
        dedup_version="1.0.0",
        router_version="1.0.0",
        history_tail_size=10,
    )
    repository.ensure_indexes()
    return repository


def _write_judicial_doc(path: Path, *, canonical_doc_uid: str) -> None:
    path.write_text(
        "\n".join(
            [
                "## Metadata",
                "",
                "- Original source system: saos_pl",
                f"- Canonical doc UID: {canonical_doc_uid}",
                "",
                "## Content",
                "",
                "# WYROK",
                "",
                "Sygn. akt I C 1/20",
                "Spór o zwrot kaucji.",
            ]
        ),
        encoding="utf-8",
    )


def _write_unknown_doc(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "## Metadata",
                "",
                "- Original source system: local_manual",
                "",
                "## Content",
                "",
                "# Analiza depozytu",
                "",
                (
                    "Materiał opisuje kaucję mieszkaniową, obowiązki lokatora "
                    "i zasady najem po zakończeniu umowy."
                ),
            ]
        ),
        encoding="utf-8",
    )


def _write_discovery_search_doc(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# SAOS Search Snapshot",
                "",
                "## Metadata",
                "",
                "- Original source system: saos_pl",
                "- Canonical doc UID: saos_pl:search:kaucja_mieszkaniowa",
                "- Original URL: https://www.saos.org.pl/search?keywords=kaucja+mieszkaniowa",
                "",
                "## Content",
                "",
                "# SAOS Search Snapshot",
                "",
                "Query URL: https://www.saos.org.pl/search?keywords=kaucja+mieszkaniowa",
                "",
                "This entry is a search/discovery page, not a primary legal document.",
                "",
                "## Result Links",
                "",
                "- II Ca 1527/23 - https://www.saos.org.pl/judgments/535713",
                "- V C 1874/22 - https://www.saos.org.pl/judgments/521555",
                "- I C 733/21 - https://www.saos.org.pl/judgments/486542",
            ]
        ),
        encoding="utf-8",
    )


def _analysis_payload(
    *,
    document_type_code: str = "pl_judgment",
    document_type_label: str = "wyrok",
) -> dict[str, Any]:
    return {
        "semantic": {
            "document_type_code": document_type_code,
            "authority_level": "high",
            "relevance": "core",
            "usually_supports": "depends",
            "topic_codes": ["deposit_return_term"],
            "use_for_tasks_codes": ["claim", "legal_position"],
        },
        "annotation_original": {
            "language_code": "pl",
            "document_type_label": document_type_label,
            "summary": "Dokument porządkuje argumentację o zwrocie kaucji.",
            "practical_value": ["Pomaga w pozwie."],
            "best_use_scenarios": ["Zwrot kaucji po zakończeniu najmu."],
            "use_for_tasks_labels": ["pozew", "pozycja prawna"],
            "read_first": ["Sentencja.", "Uzasadnienie o potrąceniu."],
            "limitations": ["Dotyczy konkretnego stanu faktycznego."],
            "tags": ["kaucja", "wyrok"],
        },
    }


def _stage_events(
    log_rows: list[dict[str, Any]],
    stage: str,
) -> list[str]:
    return [row["event"] for row in log_rows if row["stage"] == stage]


def _find_event(
    log_rows: list[dict[str, Any]],
    stage: str,
    event: str,
) -> dict[str, Any]:
    for row in log_rows:
        if row["stage"] == stage and row["event"] == event:
            return row
    raise AssertionError(f"Event {event} for stage {stage} was not logged.")


def _analysis_payload_en() -> dict[str, Any]:
    return {
        "semantic": {
            "document_type_code": "discovery_page",
            "authority_level": "reference_only",
            "relevance": "discovery_only",
            "usually_supports": "depends",
            "topic_codes": ["discovery_navigation"],
            "use_for_tasks_codes": ["internal_analysis"],
        },
        "annotation_original": {
            "language_code": "en",
            "document_type_label": "discovery page",
            "summary": "This search snapshot helps navigate relevant decisions.",
            "practical_value": ["Useful for locating candidate case-law quickly."],
            "best_use_scenarios": ["Initial discovery before reviewing judgments."],
            "use_for_tasks_labels": ["internal analysis"],
            "read_first": ["Query URL.", "Result links section."],
            "limitations": ["It is not a primary legal source."],
            "tags": ["discovery", "saos"],
        },
    }


def _invalid_analysis_payload_missing_summary() -> dict[str, Any]:
    payload = _analysis_payload()
    payload["annotation_original"].pop("summary")
    return payload


def _translation_payload(
    *,
    semantic_document_type_code: str = "pl_judgment",
    document_type_label: str = "решение суда",
) -> dict[str, Any]:
    del semantic_document_type_code
    return {
        "annotation_ru": {
            "language_code": "ru",
            "document_type_label": document_type_label,
            "summary": "Документ систематизирует аргументацию по возврату кауции.",
            "practical_value": ["Помогает при подготовке иска."],
            "best_use_scenarios": ["Спор о возврате кауции после окончания найма."],
            "use_for_tasks_labels": ["иск", "правовая позиция"],
            "read_first": ["Резолютивная часть.", "Мотивировка о зачёте."],
            "limitations": ["Связано с конкретной фактической ситуацией."],
            "tags": ["кауция", "решение"],
        },
    }


def _invalid_translation_payload_wrong_language() -> dict[str, Any]:
    payload = _translation_payload()
    payload["annotation_ru"]["language_code"] = "pl"
    return payload


def _translation_payload_en() -> dict[str, Any]:
    return {
        "annotation_ru": {
            "language_code": "ru",
            "document_type_label": "страница поиска",
            "summary": "Этот снимок поиска помогает найти релевантные судебные решения.",
            "practical_value": ["Ускоряет первичный поиск подходящей практики."],
            "best_use_scenarios": ["Предварительный обзор корпуса перед чтением решений."],
            "use_for_tasks_labels": ["внутренний анализ"],
            "read_first": ["Query URL.", "Список Result Links."],
            "limitations": ["Это не первичный правовой источник."],
            "tags": ["поиск", "saos"],
        },
    }


def _fallback_classification_payload(
    *,
    confidence: float = 0.81,
    document_family: str = "commentary_article",
    prompt_profile: str = "addon_commentary",
) -> dict[str, Any]:
    return {
        "document_family": document_family,
        "prompt_profile": prompt_profile,
        "confidence": confidence,
    }


def _build_classification_result() -> ClassificationResult:
    return ClassificationResult(
        document_family="judicial_decision",
        document_type_code="pl_judgment",
        prompt_profile=PromptProfile.ADDON_CASE_LAW,
        annotatable=True,
        classifier_method="rule_based",
        confidence=0.95,
        router_version="2.0.0",
        signals={"matched_rules": ["judicial_decision"]},
        skip_reason=None,
    )


def _build_large_canonical_result() -> CanonicalTextResult:
    section_text = "Artykuł o zwrocie kaucji.\n" * 500
    sections = tuple(
        CanonicalSection(
            section_id=f"s{index:03d}",
            heading=f"Sekcja {index}",
            text=section_text[:2000],
            char_count=len(section_text[:2000]),
        )
        for index in range(1, 4)
    )
    return CanonicalTextResult(
        canonical_text=section_text * 5,
        canonical_text_sha256="large-canonical-sha",
        text_preview=section_text[:200],
        text_stats_raw=TextStats(chars=50000, lines=1000, words=7000),
        text_stats_canonical=TextStats(chars=50000, lines=1000, words=7000),
        strategy="plain_markdown",
        sections=sections,
    )


def _run_completed_fallback_pipeline(
    *,
    tmp_path: Path,
    input_root: Path,
    repository: MongoDocumentRepository,
) -> None:
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=tmp_path, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=ScriptedLlmClient(
            script=[
                _fallback_classification_payload(),
                _analysis_payload(
                    document_type_code="commentary_article",
                    document_type_label="komentarz",
                ),
                _translation_payload(
                    semantic_document_type_code="commentary_article",
                    document_type_label="комментарий",
                ),
            ]
        ),
    )
    summary = pipeline.run(options=PipelineRunOptions(mode=PipelineMode.FULL))

    assert summary.completed_count == 1


def _build_existing(
    *,
    status: str,
    file_sha256: str,
    analysis_fingerprint: str = "",
    annotation_status: str = "pending",
) -> dict[str, object]:
    return {
        "source": {"file_sha256": file_sha256},
        "processing": {"status": status},
        "annotation": {
            "analysis_fingerprint": analysis_fingerprint,
            "status": annotation_status,
        },
    }
