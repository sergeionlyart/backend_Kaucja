"""Unified API error handling for /api/v2 endpoints.

TechSpec error format (applied to ALL errors, including framework 422):
    {
        "error": {
            "code": "UPPER_SNAKE_CASE",
            "message": "human-readable",
            "details": { ... },
            "request_id": "uuid"
        }
    }
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    """Application-level error that maps to an HTTP response."""

    def __init__(
        self,
        *,
        status_code: int,
        error_code: str,
        detail: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail
        self.details = details


def _error_body(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": uuid.uuid4().hex,
        }
    }
    if details:
        body["error"]["details"] = details
    return body


# ---------------------------------------------------------------------------
# HTTP status -> error code mapping
# ---------------------------------------------------------------------------

_HTTP_STATUS_TO_CODE: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
}


def _code_for_status(status_code: int) -> str:
    return _HTTP_STATUS_TO_CODE.get(status_code, "INTERNAL_ERROR")


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


async def _api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.error_code, exc.detail, exc.details),
    )


async def _request_validation_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert FastAPI's framework 422 into unified error format."""
    raw_errors = exc.errors()
    field_details: dict[str, Any] = {}
    messages: list[str] = []
    for err in raw_errors:
        loc = ".".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "invalid")
        field_details[loc] = msg
        messages.append(f"{loc}: {msg}")
    return JSONResponse(
        status_code=422,
        content=_error_body(
            "VALIDATION_ERROR",
            "; ".join(messages) if messages else "Validation failed",
            field_details if field_details else None,
        ),
    )


async def _http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Convert Starlette HTTPException into unified error format.

    Maps status codes to appropriate error codes instead of always
    using INTERNAL_ERROR.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(
            _code_for_status(exc.status_code),
            str(exc.detail),
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _request_validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Convenience helpers  (codes are UPPER_SNAKE_CASE per TechSpec)
# ---------------------------------------------------------------------------


def validation_error(detail: str, details: dict[str, Any] | None = None) -> ApiError:
    return ApiError(
        status_code=422,
        error_code="VALIDATION_ERROR",
        detail=detail,
        details=details,
    )


def files_validation_error(
    detail: str, details: dict[str, Any] | None = None
) -> ApiError:
    return ApiError(
        status_code=422,
        error_code="FILES_VALIDATION_ERROR",
        detail=detail,
        details=details,
    )


def unsupported_media_type(detail: str) -> ApiError:
    return ApiError(
        status_code=415,
        error_code="UNSUPPORTED_MEDIA_TYPE",
        detail=detail,
    )


def payload_too_large(detail: str) -> ApiError:
    return ApiError(
        status_code=413,
        error_code="PAYLOAD_TOO_LARGE",
        detail=detail,
    )


def not_found(detail: str) -> ApiError:
    return ApiError(
        status_code=404,
        error_code="NOT_FOUND",
        detail=detail,
    )


def internal_error(detail: str) -> ApiError:
    return ApiError(
        status_code=500,
        error_code="INTERNAL_ERROR",
        detail=detail,
    )


def ocr_failed(detail: str) -> ApiError:
    return ApiError(
        status_code=502,
        error_code="OCR_FAILED",
        detail=detail,
    )


def llm_failed(detail: str) -> ApiError:
    return ApiError(
        status_code=502,
        error_code="LLM_FAILED",
        detail=detail,
    )


def pipeline_validation_failed(
    detail: str, details: dict[str, Any] | None = None
) -> ApiError:
    return ApiError(
        status_code=422,
        error_code="PIPELINE_VALIDATION_FAILED",
        detail=detail,
        details=details,
    )


def case_not_found(case_id: str) -> ApiError:
    return ApiError(
        status_code=404,
        error_code="CASE_NOT_FOUND",
        detail=f"Case '{case_id}' not found.",
    )


def no_stored_documents(case_id: str) -> ApiError:
    return ApiError(
        status_code=422,
        error_code="NO_STORED_DOCUMENTS",
        detail=f"Case '{case_id}' has no stored documents for reanalysis.",
    )


def case_busy(case_id: str) -> ApiError:
    return ApiError(
        status_code=409,
        error_code="CASE_BUSY",
        detail=f"Case '{case_id}' is currently being processed. Please wait.",
    )
