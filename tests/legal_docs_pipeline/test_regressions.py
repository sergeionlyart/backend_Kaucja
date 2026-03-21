from __future__ import annotations

from bson import BSON
import pytest

from legal_docs_pipeline.pipeline import AnnotationPipeline, PipelineRunOptions
from legal_docs_pipeline.constants import PipelineMode
from legal_docs_pipeline.repository import MongoDocumentRepository
from tests.fake_mongo_runtime import FakeMongoCollection
from tests.legal_docs_pipeline.test_pipeline import (
    PROJECT_ROOT,
    ScriptedLlmClient,
    _analysis_payload_en,
    _build_config,
    _invalid_analysis_payload_missing_summary,
    _translation_payload_en,
)


EU_HEAVY_DOC_IDS = [
    "eu_acts/28_eu_eurlex_eli_reg_2007_861_oj_eng.md",
    "eu_acts/29_eu_eurlex_eli_reg_2006_1896_oj_eng.md",
    "eu_acts/30_eu_eurlex_eli_reg_2004_805_oj_eng.md",
]

EU_REPAIR_DOC_IDS = [
    "eu_acts/26_eu_eurlex_31993l0013_en_html.md",
    "eu_acts/27_eu_eurlex_52019xc0927_01.md",
]


@pytest.mark.parametrize("doc_id", EU_HEAVY_DOC_IDS)
def test_heavy_eurlex_docs_persist_compact_mongo_shape(doc_id: str) -> None:
    input_root = PROJECT_ROOT / "docs/legal/cas_law_v2_2_md"
    config = _build_config(tmp_path=PROJECT_ROOT, input_root=input_root)
    repository = _build_repository()
    pipeline = AnnotationPipeline(
        config=config,
        repository_factory=lambda _config: repository,
        llm_client=ScriptedLlmClient(script=[]),
    )

    discovered = pipeline.scanner.scan(
        input_root,
        glob_pattern="**/*.md",
        ignore_hidden=True,
        only_doc_id=doc_id,
        limit=1,
    )[0]
    repository.upsert_discovered(
        discovered=discovered,
        input_root=input_root,
        run_id="run-regression",
        mode="full",
    )
    read_result = pipeline.reader.read(discovered)
    repository.apply_read_result(doc_id=doc_id, read_result=read_result)
    parse_result = pipeline.parser.parse(
        file_name=discovered.file_name,
        normalized_text=read_result.normalized_text,
    )
    repository.apply_parse_result(doc_id=doc_id, parse_result=parse_result)
    canonical_result = pipeline._prepare_annotatable_document(
        document=discovered,
        run_id="run-regression",
        allow_classifier_fallback=False,
    )
    assert canonical_result is not None
    repository.apply_canonical_result(
        doc_id=doc_id,
        canonical_result=canonical_result.canonical_result,
        language_result=canonical_result.language_result,
    )
    stored = repository.get_document(doc_id)

    assert stored is not None
    assert "raw_markdown" not in stored["source"]
    assert "normalized_text" not in stored["source"]
    assert "content_markdown" not in stored["source"]
    assert stored["source"]["text_stats_canonical"]["chars"] < read_result.text_stats.chars
    assert len(BSON.encode(stored)) < 16 * 1024 * 1024


@pytest.mark.parametrize("doc_id", EU_REPAIR_DOC_IDS)
def test_en_regression_docs_complete_via_analysis_repair(doc_id: str) -> None:
    input_root = PROJECT_ROOT / "docs/legal/cas_law_v2_2_md"
    repository = _build_repository()
    llm_client = ScriptedLlmClient(
        script=[
            _invalid_analysis_payload_missing_summary(),
            _analysis_payload_en(),
            _translation_payload_en(),
        ]
    )
    pipeline = AnnotationPipeline(
        config=_build_config(tmp_path=PROJECT_ROOT, input_root=input_root),
        repository_factory=lambda _config: repository,
        llm_client=llm_client,
    )

    summary = pipeline.run(
        options=PipelineRunOptions(
            mode=PipelineMode.FULL,
            only_doc_id=doc_id,
        )
    )
    stored = repository.get_document(doc_id)

    assert summary.completed_count == 1
    assert stored is not None
    assert stored["annotation"]["status"] == "completed"
    assert stored["annotation"]["qa"]["manual_review_required"] is False
    assert "raw_markdown" not in stored["source"]


def _build_repository() -> MongoDocumentRepository:
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
