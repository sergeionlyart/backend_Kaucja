import json
from pathlib import Path
from typing import Any

from app.ocr_client.mistral_ocr import MistralOCRClient
from app.ocr_client.types import OCROptions
from tests.test_orchestrator_full_pipeline import (
    SuccessLLMClient,
    _valid_llm_payload,
    _setup_orchestrator,
)


class MockUploadService:
    def __init__(self) -> None:
        self.uploaded_files: list[Path] = []

    def upload(self, *, file: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        self.uploaded_files.append(file["file_name"])
        return {"id": "mock-pdf-id"}


class MockProcessService:
    def process(self, *, document: Any, **kwargs: Any) -> dict[str, Any]:
        return {"pages": [{"markdown": "Dummy processed text from mock."}]}


def test_integration_txt_to_pdf_in_pipeline(tmp_path: Path, monkeypatch: Any) -> None:
    # 1. Arrange Mocks
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    src_txt = docs_dir / "sample.txt"
    src_txt.write_text("This is an integration test plain text file.", encoding="utf-8")

    upload_mock = MockUploadService()
    process_mock = MockProcessService()

    ocr_client = MistralOCRClient(
        api_key="dummy",
        upload_service=upload_mock,
        process_service=process_mock,
    )

    # Needs to bypass the canonical validation natively just like the previous tests.
    canonical_schema_text = Path("app/schemas/canonical_schema.json").read_text(
        encoding="utf-8"
    )

    llm_payload = _valid_llm_payload(json.loads(canonical_schema_text))
    llm_client = SuccessLLMClient(parsed_json=llm_payload)

    # 2. Setup Full Orchestrator (it will chdir and mock canonical prompt roots inside)
    orchestrator = _setup_orchestrator(
        tmp_path, monkeypatch=monkeypatch, llm_clients={"openai": llm_client}
    )

    # Override with our OCR client containing the mocked services
    orchestrator.ocr_client = ocr_client

    # 3. Act
    result = orchestrator.run_full_pipeline(
        input_files=[str(src_txt)],
        session_id=None,
        provider="openai",
        model="gpt-4.5",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        ocr_options=OCROptions(),
    )

    # 4. Assert
    assert result.run_status == "completed", (
        f"Pipeline failed on TXT: {result.error_message}"
    )
    assert result.error_code is None

    # Assert that TXT->PDF conversion fired and actual PDF was uploaded.
    assert len(upload_mock.uploaded_files) == 1
    uploaded_file = upload_mock.uploaded_files[0]
    assert Path(uploaded_file).suffix.lower() == ".pdf"
    assert Path(uploaded_file).stem == "sample_converted"

    # Validation that pipeline integrated correctly end to end through mocked states
    docs_scanned = result.documents
    assert len(docs_scanned) == 1
    assert docs_scanned[0].ocr_status == "ok"
    assert docs_scanned[0].combined_markdown_path is not None
    md_content = Path(docs_scanned[0].combined_markdown_path).read_text(
        encoding="utf-8"
    )
    assert "Dummy processed text from mock." in md_content

    # Validate that run.log captured the pre-processing
    run_logs = list(tmp_path.rglob("run.log"))
    assert len(run_logs) == 1, "Exactly one run.log should be created"
    log_content = run_logs[0].read_text(encoding="utf-8")
    assert "TXT pre-processed to PDF (size:" in log_content


def test_integration_txt_to_pdf_conversion_failure(
    tmp_path: Path, monkeypatch: Any
) -> None:
    # 1. Arrange Mocks
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    src_txt = docs_dir / "broken.txt"
    src_txt.write_text("This text won't convert.", encoding="utf-8")

    upload_mock = MockUploadService()
    process_mock = MockProcessService()

    ocr_client = MistralOCRClient(
        api_key="dummy",
        upload_service=upload_mock,
        process_service=process_mock,
    )

    canonical_schema_text = Path("app/schemas/canonical_schema.json").read_text(
        encoding="utf-8"
    )

    llm_payload = _valid_llm_payload(json.loads(canonical_schema_text))
    llm_client = SuccessLLMClient(parsed_json=llm_payload)

    orchestrator = _setup_orchestrator(
        tmp_path, monkeypatch=monkeypatch, llm_clients={"openai": llm_client}
    )
    orchestrator.ocr_client = ocr_client

    # Force the conversion to fail
    def _mock_fail_convert(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Mocked PDF conversion catastrophe")

    monkeypatch.setattr(
        "app.utils.pdf_converter.convert_txt_to_pdf", _mock_fail_convert
    )

    # 3. Act
    result = orchestrator.run_full_pipeline(
        input_files=[str(src_txt)],
        session_id=None,
        provider="openai",
        model="gpt-4.5",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        ocr_options=OCROptions(),
    )

    # 4. Assert
    assert result.run_status == "failed"
    assert result.error_code == "TXT_PDF_CONVERSION_ERROR"

    # Assert details
    error_msg = result.error_message
    assert error_msg is not None
    assert "Failed for doc_id" in error_msg
    assert "broken.txt" in error_msg
    assert "size=24 bytes" in error_msg  # "This text won't convert." is 24 bytes
    assert "Mocked PDF conversion catastrophe" in error_msg
