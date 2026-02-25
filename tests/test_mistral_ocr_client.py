from __future__ import annotations

import base64
import json
from pathlib import Path

from app.ocr_client.mistral_ocr import MistralOCRClient
from app.ocr_client.types import OCROptions


class FakeProcessService:
    def process(self, **kwargs: object) -> dict[str, object]:
        assert kwargs["model"] == "mistral-ocr-latest"
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
    client = MistralOCRClient(process_service=FakeProcessService())

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
