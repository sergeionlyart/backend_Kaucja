import json
from pathlib import Path
from typing import Any

from app.pipeline.orchestrator import OCRPipelineOrchestrator
from app.storage.repo import StorageRepo
from app.storage.artifacts import ArtifactsManager
from app.ocr_client.types import OCROptions, OCRResult
from tests.test_orchestrator_full_pipeline import SuccessLLMClient, _valid_llm_payload

# We will create a base orchestrator setup factory that we can precisely manipulate for lock testing.


def _create_orchestrator_with_drift(
    tmp_path: Path,
    monkeypatch: Any,
    missing_canonical_prompt: bool = False,
    missing_canonical_schema: bool = False,
    invalid_canonical_schema: bool = False,
    requested_prompt_override: str | None = None,
    requested_schema_override: str | None = None,
) -> OCRPipelineOrchestrator:
    # 1. Boilerplate DB & Artifacts
    artifacts_manager = ArtifactsManager(tmp_path / "data")
    repo = StorageRepo(
        db_path=tmp_path / "kaucja.sqlite3", artifacts_manager=artifacts_manager
    )

    # 2. Setup the "Requested" Prompts the Orchestrator points to at runtime
    prompt_root = tmp_path / "prompts"
    prompt_dir = prompt_root / "default_analyzer" / "v1.0.0"
    prompt_dir.mkdir(parents=True, exist_ok=True)

    canonical_prompt_text = Path("app/prompts/canonical_prompt.txt").read_text(
        encoding="utf-8"
    )
    canonical_schema_text = Path("app/schemas/canonical_schema.json").read_text(
        encoding="utf-8"
    )

    # Write requested prompt & schema (with overrides if provided)
    req_prompt = (
        requested_prompt_override
        if requested_prompt_override is not None
        else canonical_prompt_text
    )
    req_schema = (
        requested_schema_override
        if requested_schema_override is not None
        else canonical_schema_text
    )

    (prompt_dir / "system_prompt.txt").write_text(req_prompt, encoding="utf-8")
    (prompt_dir / "schema.json").write_text(req_schema, encoding="utf-8")

    # 3. Setup the "Canonical" assets which Orchestrator expects at app/prompts and app/schemas
    app_prompts = tmp_path / "app" / "prompts"
    app_schemas = tmp_path / "app" / "schemas"
    app_prompts.mkdir(parents=True, exist_ok=True)
    app_schemas.mkdir(parents=True, exist_ok=True)

    if not missing_canonical_prompt:
        (app_prompts / "canonical_prompt.txt").write_text(
            canonical_prompt_text, encoding="utf-8"
        )

    if not missing_canonical_schema:
        if invalid_canonical_schema:
            (app_schemas / "canonical_schema.json").write_text(
                "{invalid json", encoding="utf-8"
            )
        else:
            (app_schemas / "canonical_schema.json").write_text(
                canonical_schema_text, encoding="utf-8"
            )

    monkeypatch.chdir(tmp_path)

    # 4. Mock OCR client (skip actual OCR since TechSpec drift check happens at LLM stage anyway)
    class MockOCRClient:
        def process_document(
            self,
            *,
            input_path: Path,
            doc_id: str,
            options: OCROptions,
            output_dir: Path,
        ) -> OCRResult:
            (output_dir / "combined.md").write_text("Dummy content")
            return OCRResult(
                doc_id=doc_id,
                ocr_model="mock",
                pages_count=1,
                combined_markdown_path=str((output_dir / "combined.md").resolve()),
                raw_response_path=str((output_dir / "raw.json").resolve()),
                tables_dir=str((output_dir / "tables").resolve()),
                images_dir=str((output_dir / "images").resolve()),
                page_renders_dir=str((output_dir / "page_renders").resolve()),
                quality_path=str((output_dir / "quality.json").resolve()),
                quality_warnings=[],
                converted_pdf_path=None,
            )

    llm_payload = _valid_llm_payload(json.loads(canonical_schema_text))
    llm_client = SuccessLLMClient(parsed_json=llm_payload)

    return OCRPipelineOrchestrator(
        repo=repo,
        artifacts_manager=artifacts_manager,
        ocr_client=MockOCRClient(),
        llm_clients={"openai": llm_client},
        prompt_root=prompt_root,
    )


def _create_dummy_txt(tmp_path: Path) -> str:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(exist_ok=True)
    src_txt = docs_dir / "sample.txt"
    src_txt.write_text("This is an integration test plain text file.", encoding="utf-8")
    return str(src_txt)


# ==================== TESTS ====================


def test_techspec_fail_closed_missing_canonical_prompt(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _create_orchestrator_with_drift(
        tmp_path, monkeypatch, missing_canonical_prompt=True
    )
    result = orchestrator.run_full_pipeline(
        input_files=[_create_dummy_txt(tmp_path)],
        session_id=None,
        provider="openai",
        model="gpt-4o",
        prompt_name="default_analyzer",
        prompt_version="v1.0.0",
        ocr_options=OCROptions(),
    )
    assert result.run_status == "failed"
    assert result.error_code == "TECHSPEC_DRIFT"
    assert "missing" in result.error_message.lower()


def test_techspec_fail_closed_missing_canonical_schema(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _create_orchestrator_with_drift(
        tmp_path, monkeypatch, missing_canonical_schema=True
    )
    result = orchestrator.run_full_pipeline(
        input_files=[_create_dummy_txt(tmp_path)],
        session_id=None,
        provider="openai",
        model="gpt-4o",
        prompt_name="default_analyzer",
        prompt_version="v1.0.0",
        ocr_options=OCROptions(),
    )
    assert result.run_status == "failed"
    assert result.error_code == "TECHSPEC_DRIFT"
    assert "missing" in result.error_message.lower()


def test_techspec_fail_closed_invalid_canonical_schema(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _create_orchestrator_with_drift(
        tmp_path, monkeypatch, invalid_canonical_schema=True
    )
    result = orchestrator.run_full_pipeline(
        input_files=[_create_dummy_txt(tmp_path)],
        session_id=None,
        provider="openai",
        model="gpt-4o",
        prompt_name="default_analyzer",
        prompt_version="v1.0.0",
        ocr_options=OCROptions(),
    )
    assert result.run_status == "failed"
    assert result.error_code == "TECHSPEC_DRIFT"
    assert (
        "invalid" in result.error_message.lower()
        or "decode" in result.error_message.lower()
    )


def test_techspec_fail_closed_requested_prompt_drift(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _create_orchestrator_with_drift(
        tmp_path, monkeypatch, requested_prompt_override="This a hacked prompt"
    )
    result = orchestrator.run_full_pipeline(
        input_files=[_create_dummy_txt(tmp_path)],
        session_id=None,
        provider="openai",
        model="gpt-4o",
        prompt_name="default_analyzer",
        prompt_version="v1.0.0",
        ocr_options=OCROptions(),
    )
    assert result.run_status == "failed"
    assert result.error_code == "TECHSPEC_DRIFT"
    assert (
        "drift" in result.error_message.lower()
        or "violate" in result.error_message.lower()
    )


def test_techspec_fail_closed_requested_schema_drift(
    tmp_path: Path, monkeypatch: Any
) -> None:
    orchestrator = _create_orchestrator_with_drift(
        tmp_path, monkeypatch, requested_schema_override='{"hacked": true}'
    )
    result = orchestrator.run_full_pipeline(
        input_files=[_create_dummy_txt(tmp_path)],
        session_id=None,
        provider="openai",
        model="gpt-4o",
        prompt_name="default_analyzer",
        prompt_version="v1.0.0",
        ocr_options=OCROptions(),
    )
    assert result.run_status == "failed"
    assert result.error_code == "TECHSPEC_DRIFT"
    assert (
        "drift" in result.error_message.lower()
        or "violate" in result.error_message.lower()
    )
