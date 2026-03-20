from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/annotate_legal_docs.py", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--config" in result.stdout
    assert "--mode" in result.stdout
    assert "--only-doc-id" in result.stdout
    assert "--from-relative-path" in result.stdout
    assert "--force-classifier-fallback" in result.stdout
    assert "--log-level" in result.stdout
    assert "--doc-id" not in result.stdout


def test_cli_dry_run_new_limit_outputs_summary(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    (input_root / "A.md").write_text(
        "# README\n\n## Content\n\nThis entry is a search/discovery page.\nResult Links\n",
        encoding="utf-8",
    )
    (input_root / "b.md").write_text(
        "## Metadata\n\n- Original source system: saos_pl\n\n## Content\n\nWYROK\nSygn. akt I C 1/20\n",
        encoding="utf-8",
    )
    (input_root / "c.md").write_text(
        "## Metadata\n\n- Original source system: eurlex_eu\n\n## Content\n\nCOUNCIL DIRECTIVE 93/13/EEC\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "pipeline.yaml"
    config_path.write_text(
        "\n".join(
            [
                "input:",
                f'  root_path: "{input_root}"',
                '  glob: "**/*.md"',
                "  ignore_hidden: true",
                "mongo:",
                '  uri: "mongodb://localhost:27017"',
                '  database: "kaucja_legal_corpus"',
                '  collection: "documents"',
                "model:",
                '  provider: "openai"',
                '  api: "responses"',
                '  model_id: "gpt-5.4"',
                '  reasoning_effort: "xhigh"',
                '  text_verbosity: "low"',
                '  truncation: "disabled"',
                "  store: false",
                "  analysis_max_output_tokens: 32000",
                "  translation_ru_max_output_tokens: 24000",
                "prompts:",
                '  prompt_pack_id: "kaucja-prompt-pack"',
                '  prompt_pack_version: "2026-03-16"',
                f'  prompt_dir: "{(PROJECT_ROOT / "prompts/kaucja").resolve()}"',
                "pipeline:",
                '  schema_version: "1.0.0"',
                '  pipeline_version: "1.0.0"',
                "  workers: 1",
                '  dedup_version: "1.0.0"',
                '  router_version: "1.0.0"',
                "  history_tail_size: 10",
                "  retry_model_calls: 2",
                "  retry_mongo_writes: 2",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/annotate_legal_docs.py",
            "--config",
            str(config_path),
            "--mode",
            "new",
            "--from-relative-path",
            "b.md",
            "--limit",
            "2",
            "--dry-run",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["execution_status"] == "dry_run_completed"
    assert payload["mode"] == "new"
    assert payload["dry_run"] is True
    assert payload["discovered_count"] == 2
    assert payload["processed_count"] == 2
    assert payload["failed_count"] == 0


def test_cli_dry_run_rerun_failed_outputs_summary(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    (input_root / "doc.md").write_text(
        "## Metadata\n\n- Original source system: saos_pl\n\n## Content\n\nWYROK\nSygn. akt I C 1/20\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "pipeline.yaml"
    config_path.write_text(
        "\n".join(
            [
                "input:",
                f'  root_path: "{input_root}"',
                '  glob: "**/*.md"',
                "  ignore_hidden: true",
                "mongo:",
                '  uri: "mongodb://localhost:27017"',
                '  database: "kaucja_legal_corpus"',
                '  collection: "documents"',
                "model:",
                '  provider: "openai"',
                '  api: "responses"',
                '  model_id: "gpt-5.4"',
                '  reasoning_effort: "xhigh"',
                '  text_verbosity: "low"',
                '  truncation: "disabled"',
                "  store: false",
                "  analysis_max_output_tokens: 32000",
                "  translation_ru_max_output_tokens: 24000",
                "prompts:",
                '  prompt_pack_id: "kaucja-prompt-pack"',
                '  prompt_pack_version: "2026-03-16"',
                f'  prompt_dir: "{(PROJECT_ROOT / "prompts/kaucja").resolve()}"',
                "pipeline:",
                '  schema_version: "1.0.0"',
                '  pipeline_version: "1.0.0"',
                "  workers: 1",
                '  dedup_version: "1.0.0"',
                '  router_version: "1.0.0"',
                "  history_tail_size: 10",
                "  retry_model_calls: 2",
                "  retry_mongo_writes: 2",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/annotate_legal_docs.py",
            "--config",
            str(config_path),
            "--mode",
            "rerun",
            "--rerun-scope",
            "failed",
            "--dry-run",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["execution_status"] == "dry_run_completed"
    assert payload["mode"] == "rerun"
    assert payload["dry_run"] is True
    assert payload["discovered_count"] == 1
    assert isinstance(payload["warnings"], list)


def test_cli_rejects_dry_run_with_force_classifier_fallback(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    (input_root / "doc.md").write_text(
        "## Metadata\n\n- Original source system: saos_pl\n\n## Content\n\nWYROK\nSygn. akt I C 1/20\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "pipeline.yaml"
    config_path.write_text(
        "\n".join(
            [
                "input:",
                f'  root_path: "{input_root}"',
                '  glob: "**/*.md"',
                "  ignore_hidden: true",
                "mongo:",
                '  uri: "mongodb://localhost:27017"',
                '  database: "kaucja_legal_corpus"',
                '  collection: "documents"',
                "model:",
                '  provider: "openai"',
                '  api: "responses"',
                '  model_id: "gpt-5.4"',
                '  reasoning_effort: "xhigh"',
                '  text_verbosity: "low"',
                '  truncation: "disabled"',
                "  store: false",
                "  analysis_max_output_tokens: 32000",
                "  translation_ru_max_output_tokens: 24000",
                "prompts:",
                '  prompt_pack_id: "kaucja-prompt-pack"',
                '  prompt_pack_version: "2026-03-16"',
                f'  prompt_dir: "{(PROJECT_ROOT / "prompts/kaucja").resolve()}"',
                "pipeline:",
                '  schema_version: "1.0.0"',
                '  pipeline_version: "1.0.0"',
                "  workers: 1",
                '  dedup_version: "1.0.0"',
                '  router_version: "1.0.0"',
                "  history_tail_size: 10",
                "  retry_model_calls: 2",
                "  retry_mongo_writes: 2",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/annotate_legal_docs.py",
            "--config",
            str(config_path),
            "--mode",
            "new",
            "--dry-run",
            "--force-classifier-fallback",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--dry-run cannot be combined with --force-classifier-fallback" in result.stderr
