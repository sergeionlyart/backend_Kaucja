from __future__ import annotations

import base64
import inspect
import json
from pathlib import Path

from mistralai import Mistral
from mistralai.models.ocrrequest import Document

from app.ocr_client.mistral_ocr import MistralOCRClient
from app.ocr_client.types import OCROptions


class FakeUploadService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def upload(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(kwargs)
        return {"id": "file-123"}


class FakeProcessService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def process(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(kwargs)
        return {
            "model": "mistral-ocr-latest",
            "pages": [
                {
                    "markdown": "Page one [tbl-0.html](tbl-0.html) ![img-0.png](img-0.png)",
                    "tables": [{"html": "<table><tr><td>A</td></tr></table>"}],
                    "images": [
                        {
                            "image_base64": base64.b64encode(b"fake-image").decode(
                                "ascii"
                            ),
                            "mime_type": "image/png",
                        }
                    ],
                },
                {
                    "markdown": "Second page markdown",
                    "tables": [],
                    "images": [],
                },
            ],
        }


def test_mistral_ocr_client_saves_expected_artifacts(tmp_path: Path) -> None:
    input_path = tmp_path / "doc.pdf"
    input_path.write_bytes(b"pdf-bytes")

    output_dir = tmp_path / "ocr"
    upload_service = FakeUploadService()
    process_service = FakeProcessService()
    client = MistralOCRClient(
        process_service=process_service,
        upload_service=upload_service,
    )

    result = client.process_document(
        input_path=input_path,
        doc_id="0000001",
        options=OCROptions(model="mistral-ocr-latest", table_format="html"),
        output_dir=output_dir,
    )

    assert result.pages_count == 2
    assert Path(result.raw_response_path).is_file()
    assert Path(result.combined_markdown_path).is_file()
    assert (output_dir / "pages" / "0001.md").is_file()
    assert (output_dir / "pages" / "0002.md").is_file()
    assert (output_dir / "tables" / "tbl-0.html").is_file()
    assert (output_dir / "images" / "img-0.png").is_file()
    assert Path(result.quality_path).is_file()

    combined_markdown = Path(result.combined_markdown_path).read_text(encoding="utf-8")
    assert "[tbl-0.html](tbl-0.html)" in combined_markdown
    assert "![img-0.png](img-0.png)" in combined_markdown

    raw_payload = json.loads(Path(result.raw_response_path).read_text(encoding="utf-8"))
    assert len(raw_payload["pages"]) == 2


def test_mistral_ocr_uses_uploaded_file_id_for_request(tmp_path: Path) -> None:
    input_path = tmp_path / "doc.pdf"
    input_path.write_bytes(b"pdf-bytes")

    upload_service = FakeUploadService()
    process_service = FakeProcessService()
    client = MistralOCRClient(
        process_service=process_service,
        upload_service=upload_service,
    )

    client.process_document(
        input_path=input_path,
        doc_id="0000001",
        options=OCROptions(model="mistral-ocr-latest", table_format="html"),
        output_dir=tmp_path / "ocr",
    )

    assert len(upload_service.calls) == 1
    upload_call = upload_service.calls[0]
    assert upload_call["purpose"] == "ocr"

    assert len(process_service.calls) == 1
    process_call = process_service.calls[0]
    assert process_call["document"] == {"type": "file", "file_id": "file-123"}


def test_mistral_ocr_table_format_none_does_not_create_table_files(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "doc.pdf"
    input_path.write_bytes(b"pdf-bytes")

    upload_service = FakeUploadService()
    process_service = FakeProcessService()
    client = MistralOCRClient(
        process_service=process_service,
        upload_service=upload_service,
    )

    client.process_document(
        input_path=input_path,
        doc_id="0000001",
        options=OCROptions(model="mistral-ocr-latest", table_format="none"),
        output_dir=tmp_path / "ocr",
    )

    process_call = process_service.calls[0]
    assert "table_format" not in process_call
    table_files = list((tmp_path / "ocr" / "tables").glob("tbl-*"))
    assert table_files == []


def test_mistral_sdk_ocr_contract_supports_file_document() -> None:
    signature = inspect.signature(Mistral(api_key="test").ocr.process)
    document_parameter = signature.parameters["document"]
    annotation_repr = str(document_parameter.annotation)
    document_union_repr = str(Document.__value__)

    assert "Document" in annotation_repr
    assert "FileChunk" in document_union_repr
    assert "DocumentURLChunk" in document_union_repr
