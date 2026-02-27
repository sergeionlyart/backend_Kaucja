import json
from pathlib import Path

from app.ocr_client.mistral_ocr import MistralOCRClient
from app.ocr_client.types import OCROptions, OCRResult
from tests.test_orchestrator_full_pipeline import (
    SuccessLLMClient,
    _valid_llm_payload,
    _setup_orchestrator,
)


# Re-use the existing pipeline Mocks for isolated tests
class _MockTXTInterceptorMistralOCRClient(MistralOCRClient):
    """
    Simulates Mistral OCR Client intercepting a .txt file.
    Instead of actually calling Mistral APIs, it fakes the filesystem outputs
    that the orchestrator relies upon to proceed.
    """

    def process_document(
        self,
        *,
        input_path: Path,
        doc_id: str,
        options: OCROptions,
        output_dir: Path,
    ) -> OCRResult:
        output_dir.mkdir(parents=True, exist_ok=True)

        if input_path.suffix.lower() == ".txt":
            from app.utils.pdf_converter import convert_txt_to_pdf

            pdf_path = output_dir / f"{input_path.stem}_converted.pdf"
            try:
                convert_txt_to_pdf(input_path, pdf_path)
            except Exception as error:
                from app.utils.error_taxonomy import TXTPDFConversionError

                raise TXTPDFConversionError(
                    f"TXT conversion failed: {error}"
                ) from error
            input_path = pdf_path
        combined_path = output_dir / "combined.md"
        raw_response_path = output_dir / "raw_response.json"
        quality_path = output_dir / "quality.json"

        combined_path.write_text(
            "Dummy processed text from interceptor.", encoding="utf-8"
        )
        raw_response_path.write_text('{"pages": []}', encoding="utf-8")
        quality_path.write_text('{"warnings": [], "bad_pages": []}', encoding="utf-8")

        return OCRResult(
            doc_id=doc_id,
            ocr_model="mistral-ocr-latest",
            pages_count=1,
            combined_markdown_path=str(combined_path.resolve()),
            raw_response_path=str(raw_response_path.resolve()),
            tables_dir=str((output_dir / "tables").resolve()),
            images_dir=str((output_dir / "images").resolve()),
            page_renders_dir=str((output_dir / "page_renders").resolve()),
            quality_path=str(quality_path.resolve()),
            quality_warnings=[],
            converted_pdf_path=str(pdf_path.resolve())
            if "pdf_path" in locals()
            else None,
        )


def test_integration_txt_to_pdf_in_pipeline(tmp_path: Path) -> None:
    # 1. Arrange Mocks
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    src_txt = docs_dir / "sample.txt"
    src_txt.write_text("This is an integration test plain text file.", encoding="utf-8")

    # 2. Setup Valid Context constraints
    prompt_root = tmp_path / "prompts"
    prompt_dir = prompt_root / "default_analyzer" / "v1.0.0"
    prompt_dir.mkdir(parents=True)
    canonical_prompt_text = Path("app/prompts/canonical_prompt.txt").read_text(
        encoding="utf-8"
    )
    canonical_schema_text = Path("app/schemas/canonical_schema.json").read_text(
        encoding="utf-8"
    )

    (prompt_dir / "system_prompt.txt").write_text(
        canonical_prompt_text, encoding="utf-8"
    )
    (prompt_dir / "schema.json").write_text(canonical_schema_text, encoding="utf-8")

    # Mock OCR and LLM setup
    ocr_client = _MockTXTInterceptorMistralOCRClient(
        api_key="dummy",
        process_service=None,
        upload_service=None,  # type: ignore
    )
    llm_payload = _valid_llm_payload(json.loads(canonical_schema_text))
    llm_client = SuccessLLMClient(parsed_json=llm_payload)


    orchestrator = _setup_orchestrator(tmp_path, {"openai": llm_client})

    # Patch the orchestrator mocks with our custom ones designed to explicitly pass TXT through Interceptor
    orchestrator.ocr_client = ocr_client
    orchestrator.prompt_root = prompt_root

    # 3. Act
    result = orchestrator.run_full_pipeline(
        input_files=[str(src_txt)],
        session_id=None,
        provider="openai",
        model="gpt-4o",
        prompt_name="default_analyzer",
        prompt_version="v1.0.0",
        ocr_options=OCROptions(),
    )

    # 4. Assert
    assert result.run_status == "completed", (
        f"Pipeline failed on TXT: {result.error_message}"
    )
    assert result.error_code is None

    # Validation that the converted PDF is the one supplied to OCR
    docs_scanned = result.documents
    assert len(docs_scanned) == 1
    assert docs_scanned[0].ocr_status == "ok"
    assert docs_scanned[0].combined_markdown_path is not None
    md_content = Path(docs_scanned[0].combined_markdown_path).read_text(
        encoding="utf-8"
    )
    assert "Dummy processed text from interceptor." in md_content
