from __future__ import annotations

import json
import sqlite3

from app.utils.error_taxonomy import (
    ERROR_FRIENDLY_MESSAGES,
    ContextTooLargeError,
    OCRParseError,
    UnsupportedFileTypeError,
    classify_llm_api_error,
    classify_ocr_error,
    extract_http_status_code,
    is_retryable_llm_exception,
    is_retryable_ocr_exception,
)


class HttpError(RuntimeError):
    def __init__(self, status_code: int, message: str = "http error") -> None:
        super().__init__(message)
        self.status_code = status_code


def test_retry_classifier_for_ocr_and_llm_errors() -> None:
    assert is_retryable_ocr_exception(HttpError(429)) is True
    assert is_retryable_ocr_exception(HttpError(500)) is True
    assert is_retryable_ocr_exception(TimeoutError("timeout")) is True
    assert is_retryable_ocr_exception(ValueError("bad parse")) is False

    assert is_retryable_llm_exception(HttpError(429)) is True
    assert is_retryable_llm_exception(HttpError(503)) is True
    assert is_retryable_llm_exception(TimeoutError("timeout")) is False


def test_error_code_mapping() -> None:
    assert classify_ocr_error(UnsupportedFileTypeError("x")) == "FILE_UNSUPPORTED"
    assert classify_ocr_error(OCRParseError("x")) == "OCR_PARSE_ERROR"
    assert classify_ocr_error(TimeoutError("x")) == "OCR_API_ERROR"

    assert (
        classify_llm_api_error(json.JSONDecodeError("msg", "{}", 0))
        == "LLM_INVALID_JSON"
    )
    assert classify_llm_api_error(ContextTooLargeError("x")) == "CONTEXT_TOO_LARGE"
    assert classify_llm_api_error(HttpError(503)) == "LLM_API_ERROR"
    assert (
        classify_llm_api_error(sqlite3.OperationalError("db fail")) == "STORAGE_ERROR"
    )
    assert classify_ocr_error(PermissionError("disk denied")) == "STORAGE_ERROR"

    class WeirdError(Exception):
        pass

    assert classify_llm_api_error(WeirdError("boom")) == "UNKNOWN_ERROR"


def test_http_status_extraction_and_messages() -> None:
    error = HttpError(502)
    assert extract_http_status_code(error) == 502
    assert "LLM_API_ERROR" in ERROR_FRIENDLY_MESSAGES
    assert "OCR_API_ERROR" in ERROR_FRIENDLY_MESSAGES
    assert "UNKNOWN_ERROR" in ERROR_FRIENDLY_MESSAGES
