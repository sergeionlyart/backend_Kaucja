from pathlib import Path
from unittest.mock import MagicMock

from app.utils.pdf_converter import convert_txt_to_pdf
from app.ocr_client.mistral_ocr import MistralOCRClient
from app.ocr_client.types import OCROptions


def test_pdf_converter(tmp_path: Path) -> None:
    txt_path = tmp_path / "test.txt"
    txt_path.write_text(
        "Hello World!\nThis is a test of the TXT to PDF converter.\n" * 50
    )
    pdf_path = tmp_path / "output.pdf"

    convert_txt_to_pdf(txt_path, pdf_path)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0

    # We can also load it with PyMuPDF to check page count
    import fitz

    doc = fitz.open(str(pdf_path))
    assert len(doc) > 0
    text = doc[0].get_text()
    assert "Hello World!" in text
    doc.close()


def test_mistral_client_intercepts_txt(tmp_path: Path) -> None:
    # Prepare mock text
    txt_path = tmp_path / "input.txt"
    txt_path.write_text("Mock txt file")

    output_dir = tmp_path / "output"

    # Mock processes
    mock_process = MagicMock()
    mock_process.process.return_value = {
        "model": "mock",
        "pages": [{"markdown": "mock markdown"}],
    }

    mock_upload = MagicMock()
    mock_upload.upload.return_value = {"id": "mock_file_id"}

    client = MistralOCRClient(process_service=mock_process, upload_service=mock_upload)

    options = OCROptions(model="mock_model")

    # Execute
    result = client.process_document(
        input_path=txt_path,
        doc_id="0001",
        options=options,
        output_dir=output_dir,
    )

    # Validation
    assert result.ocr_model == "mock"
    assert "mock markdown" in Path(result.combined_markdown_path).read_text()

    # The crucial part: what did it upload?
    # It should have uploaded the converted PDF instead of the TXT file.
    call_args = mock_upload.upload.call_args
    assert call_args is not None

    uploaded_file_name = call_args[1]["file"]["file_name"]
    assert uploaded_file_name.endswith(".pdf")
    assert "input_converted" in uploaded_file_name
