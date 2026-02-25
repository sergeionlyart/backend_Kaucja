from __future__ import annotations

import json
import sqlite3
import socket
from typing import Any, Literal

ErrorCode = Literal[
    "FILE_UNSUPPORTED",
    "OCR_API_ERROR",
    "OCR_PARSE_ERROR",
    "LLM_API_ERROR",
    "LLM_INVALID_JSON",
    "LLM_SCHEMA_INVALID",
    "CONTEXT_TOO_LARGE",
    "STORAGE_ERROR",
    "UNKNOWN_ERROR",
    "RESTORE_INVALID_ARCHIVE",
    "RESTORE_INVALID_SIGNATURE",
    "RESTORE_RUN_EXISTS",
    "RESTORE_FS_ERROR",
    "RESTORE_DB_ERROR",
]

ERROR_FRIENDLY_MESSAGES: dict[ErrorCode, str] = {
    "FILE_UNSUPPORTED": "Uploaded file format is not supported.",
    "OCR_API_ERROR": "OCR service request failed. Please retry.",
    "OCR_PARSE_ERROR": "OCR service response could not be parsed.",
    "LLM_API_ERROR": "LLM provider request failed. Please retry or switch model.",
    "LLM_INVALID_JSON": "Model returned invalid JSON output.",
    "LLM_SCHEMA_INVALID": "Model output failed schema validation.",
    "CONTEXT_TOO_LARGE": "Input content is too large for selected model.",
    "STORAGE_ERROR": "Storage operation failed while saving run data.",
    "UNKNOWN_ERROR": "Unexpected error occurred during pipeline run.",
    "RESTORE_INVALID_ARCHIVE": (
        "Restore bundle is invalid or unsafe. Verify archive source and try again."
    ),
    "RESTORE_INVALID_SIGNATURE": (
        "Restore bundle signature verification failed or signature is required."
    ),
    "RESTORE_RUN_EXISTS": (
        "Run already exists in local storage. Enable overwrite to restore it."
    ),
    "RESTORE_FS_ERROR": "Restore failed due to filesystem access error.",
    "RESTORE_DB_ERROR": "Restore failed while writing metadata into SQLite.",
}


class UnsupportedFileTypeError(ValueError):
    """Raised when OCR input file type is unsupported."""


class OCRParseError(ValueError):
    """Raised when OCR provider response cannot be parsed."""


class ContextTooLargeError(ValueError):
    """Raised before LLM call when packed input exceeds configured threshold."""


def classify_ocr_error(error: Exception) -> ErrorCode:
    if isinstance(error, UnsupportedFileTypeError):
        return "FILE_UNSUPPORTED"
    if isinstance(error, OCRParseError | json.JSONDecodeError):
        return "OCR_PARSE_ERROR"

    if is_retryable_ocr_exception(error):
        return "OCR_API_ERROR"

    if is_storage_error_exception(error):
        return "STORAGE_ERROR"

    if isinstance(error, (ConnectionError, TimeoutError, socket.timeout)):
        return "OCR_API_ERROR"

    if isinstance(error, ValueError | TypeError):
        return "OCR_PARSE_ERROR"

    if isinstance(error, RuntimeError):
        return "OCR_API_ERROR"

    return "UNKNOWN_ERROR"


def classify_llm_api_error(error: Exception) -> ErrorCode:
    if isinstance(error, ContextTooLargeError):
        return "CONTEXT_TOO_LARGE"
    if isinstance(error, json.JSONDecodeError):
        return "LLM_INVALID_JSON"
    if is_storage_error_exception(error):
        return "STORAGE_ERROR"
    if is_retryable_llm_exception(error):
        return "LLM_API_ERROR"
    if extract_http_status_code(error) is not None:
        return "LLM_API_ERROR"
    if isinstance(error, (ConnectionError, TimeoutError, socket.timeout, RuntimeError)):
        return "LLM_API_ERROR"
    return "UNKNOWN_ERROR"


def is_retryable_ocr_exception(error: Exception) -> bool:
    status_code = extract_http_status_code(error)
    if status_code is not None and is_retryable_status_code(status_code):
        return True

    if isinstance(error, (ConnectionError, TimeoutError, socket.timeout)):
        return True

    class_name = error.__class__.__name__.lower()
    message = str(error).lower()
    if "timeout" in class_name or "timed out" in message:
        return True
    if "connection" in class_name or "connection" in message:
        return True
    if "network" in class_name or "network" in message:
        return True
    return False


def is_retryable_llm_exception(error: Exception) -> bool:
    status_code = extract_http_status_code(error)
    return status_code is not None and is_retryable_status_code(status_code)


def is_retryable_status_code(status_code: int) -> bool:
    return status_code == 429 or 500 <= status_code <= 599


def extract_http_status_code(error: Exception) -> int | None:
    for field_name in ("status_code", "status", "http_status"):
        value = getattr(error, field_name, None)
        parsed = _to_int_or_none(value)
        if parsed is not None:
            return parsed

    response = getattr(error, "response", None)
    if response is not None:
        parsed = _to_int_or_none(getattr(response, "status_code", None))
        if parsed is not None:
            return parsed

    return None


def build_error_details(error: Exception) -> str:
    details: list[str] = [f"{error.__class__.__name__}: {error}"]
    status_code = extract_http_status_code(error)
    if status_code is not None:
        details.append(f"status_code={status_code}")

    for field_name in ("body", "response_body", "payload"):
        value = getattr(error, field_name, None)
        if value is None:
            continue
        details.append(f"{field_name}={value}")
    return "\n".join(details)


def is_storage_error_exception(error: Exception) -> bool:
    if isinstance(error, sqlite3.Error):
        return True
    if isinstance(error, OSError):
        return True
    return False


def _to_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
