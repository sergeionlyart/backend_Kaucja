from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from legal_docs_pipeline.config import PipelineConfig
from legal_docs_pipeline.config import load_pipeline_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_example_pipeline_config_loads_and_resolves_paths() -> None:
    config = load_pipeline_config(PROJECT_ROOT / "config/pipeline.yaml")

    assert config.input.root_path == (PROJECT_ROOT / "docs/legal/cas_law_v2_2_md").resolve()
    assert config.input.max_file_size_bytes == 64 * 1024 * 1024
    assert config.prompts.prompt_dir == (PROJECT_ROOT / "prompts/kaucja").resolve()
    assert config.mongo.collection == "documents_cas_law_v2_2_prod_v2"
    assert config.pipeline.workers == 1
    assert config.model.model_id == "gpt-5.4"
    assert config.model.translation_ru_max_output_tokens == 24_000
    assert config.model.request_timeout_seconds == 600


def test_probe_pipeline_config_loads_with_diagnostic_overrides() -> None:
    config = load_pipeline_config(PROJECT_ROOT / "config/pipeline.llm_probe.yaml")

    assert config.input.root_path == (PROJECT_ROOT / "docs/legal/cas_law_v2_2_md").resolve()
    assert config.prompts.prompt_dir == (PROJECT_ROOT / "prompts/kaucja").resolve()
    assert config.mongo.collection == "documents_cas_law_v2_2_llm_probe_v1"
    assert config.model.model_id == "gpt-5.4"
    assert config.model.request_timeout_seconds == 600
    assert config.pipeline.retry_model_calls == 0


def test_translation_budget_rejects_values_below_explicit_minimum(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        PipelineConfig.model_validate(
            {
                "input": {
                    "root_path": tmp_path,
                    "glob": "**/*.md",
                    "ignore_hidden": True,
                },
                "mongo": {
                    "uri": "mongodb://localhost:27017",
                    "database": "kaucja_legal_corpus",
                    "collection": "documents",
                },
                "model": {
                    "provider": "openai",
                    "api": "responses",
                    "model_id": "gpt-5.4",
                    "reasoning_effort": "xhigh",
                    "text_verbosity": "low",
                    "truncation": "disabled",
                    "store": False,
                    "analysis_max_output_tokens": 32000,
                    "translation_ru_max_output_tokens": 16000,
                },
                "prompts": {
                    "prompt_pack_id": "kaucja-prompt-pack",
                    "prompt_pack_version": "2026-03-20",
                    "prompt_dir": PROJECT_ROOT / "prompts/kaucja",
                },
                "pipeline": {
                    "schema_version": "2.0.0",
                    "pipeline_version": "2.0.0",
                    "workers": 1,
                    "dedup_version": "2.0.0",
                    "router_version": "2.0.0",
                    "history_tail_size": 10,
                    "retry_model_calls": 2,
                    "retry_mongo_writes": 2,
                },
            }
        )
