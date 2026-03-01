from unittest.mock import patch, MagicMock
from legal_ingest.parsers.pdf import _run_mistral_ocr
from legal_ingest.config import OcrConfig


@patch("legal_ingest.parsers.pdf.httpx.post")
@patch("legal_ingest.parsers.pdf.os.getenv")
def test_ocr_payload_structure(mock_getenv, mock_post):
    mock_getenv.return_value = "fake-key"

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"pages": [{"markdown": "OCR Output"}]}
    mock_post.return_value = mock_resp

    ocr_config = OcrConfig(
        enabled=True,
        endpoint="https://api.mistral.ai/v1/ocr",
        model="mistral-ocr-latest",
        api_key_env="MISTRAL_API_KEY",
        provider="mistral",
    )

    _run_mistral_ocr("doc1", "hash1", ocr_config, "https://test.com/file.pdf")

    # Assert payload shape explicitly
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer fake-key"
    assert "json" in kwargs

    payload = kwargs["json"]
    assert payload["model"] == "mistral-ocr-latest"
    assert payload["document"]["type"] == "document_url"
    assert payload["document"]["documentUrl"] == "https://test.com/file.pdf"
    assert payload["table_format"] == "markdown"
    assert payload["include_image_base64"] is False
