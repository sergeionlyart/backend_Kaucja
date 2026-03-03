"""FastAPI router for /api/v2 endpoints."""

from __future__ import annotations

import logging
import secrets
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from . import service
from .errors import (
    ApiError,
    files_validation_error,
    internal_error,
    payload_too_large,
    unsupported_media_type,
    validation_error,
)
from .models import (
    DocumentAnalyzeResponse,
    HealthResponse,
    IntakeRequest,
    IntakeResponse,
    ReanalyzeRequest,
    SubmitRequest,
    SubmitResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2")


# ---------------------------------------------------------------------------
# GET /api/v2/health
# ---------------------------------------------------------------------------


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


# ---------------------------------------------------------------------------
# POST /api/v2/case/intake
# ---------------------------------------------------------------------------


@router.post("/case/intake", response_model=IntakeResponse)
async def case_intake(body: IntakeRequest) -> IntakeResponse:
    result = service.handle_intake(
        intake_text=body.intake_text,
        case_id=body.case_id,
        locale=body.locale,
    )
    return IntakeResponse(**result)


# ---------------------------------------------------------------------------
# POST /api/v2/case/documents/analyze  (multipart/form-data)
# ---------------------------------------------------------------------------


@router.post("/case/documents/analyze", response_model=DocumentAnalyzeResponse)
async def case_documents_analyze(
    case_id: Annotated[str, Form()],
    files_category: Annotated[list[str], Form()],
    locale: Annotated[str | None, Form()] = None,
    intake_text: Annotated[str | None, Form()] = None,
    client_doc_id: Annotated[list[str] | None, Form()] = None,
    files: list[UploadFile] = File(...),  # noqa: B008
) -> DocumentAnalyzeResponse:
    # --- Validation: files present ---
    if not files:
        raise files_validation_error(
            "At least one file is required.",
            {"files": "required"},
        )

    # --- Validation: files <-> categories count match ---
    if len(files) != len(files_category):
        raise files_validation_error(
            f"files ({len(files)}) and files_category "
            f"({len(files_category)}) counts must match.",
            {"files_category": "length_mismatch"},
        )

    # --- Validation: client_doc_id length (if provided) ---
    if client_doc_id is not None and len(client_doc_id) != len(files):
        raise files_validation_error(
            f"client_doc_id ({len(client_doc_id)}) and files "
            f"({len(files)}) counts must match.",
            {"client_doc_id": "length_mismatch"},
        )

    # --- Validation: client_doc_id uniqueness (if provided) ---
    if client_doc_id is not None:
        seen: set[str] = set()
        dupes: list[str] = []
        for cid in client_doc_id:
            if cid in seen:
                dupes.append(cid)
            seen.add(cid)
        if dupes:
            raise files_validation_error(
                f"Duplicate client_doc_id values: {', '.join(dupes)}. "
                "Each client_doc_id must be unique within a single request.",
                {"client_doc_id": "duplicate", "duplicates": dupes},
            )

    # --- Validation: max files ---
    if len(files) > service.MAX_FILES_PER_REQUEST:
        raise files_validation_error(
            f"Maximum {service.MAX_FILES_PER_REQUEST} files per request.",
            {"files": "too_many"},
        )

    # --- Validate each file (buffer content, defer FS writes to lock) ---
    pending_uploads: list[dict] = []
    total_bytes = 0
    for idx, (upload, category) in enumerate(zip(files, files_category)):
        cat_clean = category.strip().lower()
        if cat_clean not in service.VALID_CATEGORIES:
            raise validation_error(
                f"Invalid category '{category}' for file #{idx + 1}. "
                f"Allowed: {', '.join(sorted(service.VALID_CATEGORIES))}.",
                {"files_category": f"invalid_at_{idx}"},
            )

        mime = (upload.content_type or "").lower()
        if mime not in service.ALLOWED_MIME_TYPES:
            raise unsupported_media_type(
                f"File '{upload.filename}' has unsupported type '{mime}'. "
                f"Allowed: {', '.join(sorted(service.ALLOWED_MIME_TYPES))}."
            )

        content = await upload.read()
        if len(content) > service.MAX_FILE_SIZE_BYTES:
            raise payload_too_large(
                f"File '{upload.filename}' exceeds "
                f"{service.MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit."
            )

        total_bytes += len(content)
        if total_bytes > service.MAX_TOTAL_SIZE_BYTES:
            raise payload_too_large(
                f"Total upload size exceeds "
                f"{service.MAX_TOTAL_SIZE_BYTES // (1024 * 1024)} MB limit."
            )

        size_mb = round(len(content) / (1024 * 1024), 2)
        doc_id = f"doc_{secrets.token_hex(4)}"
        filename = upload.filename or f"file_{idx}"
        c_doc_id = client_doc_id[idx] if client_doc_id else None

        # Buffer upload data — actual FS write deferred until lock acquired
        pending_uploads.append({
            "doc_id": doc_id,
            "filename": f"{doc_id}_{filename}",
            "content": content,
            "info": {
                "doc_id": doc_id,
                "category_id": cat_clean,
                "name": filename,
                "size_mb": size_mb,
                "content_length": len(content),
                "client_doc_id": c_doc_id,
            },
        })

    # --- Lock wraps ALL FS writes + pipeline ---
    service.acquire_case_lock(case_id)
    try:
        # Save files to disk (inside lock)
        files_info: list[dict] = []
        saved_paths: list[Path] = []
        for pu in pending_uploads:
            result = service.save_upload(case_id, pu["filename"], pu["content"])
            saved_path = result["saved_path"]

            # Reuse doc_id from catalog on dedup hit (same file re-uploaded)
            effective_doc_id = pu["info"]["doc_id"]
            if result["is_dedup_hit"] and result.get("existing_doc_id"):
                effective_doc_id = result["existing_doc_id"]

            info = {**pu["info"], "doc_id": effective_doc_id}
            saved_paths.append(saved_path)
            files_info.append(info)

        # Run either stub or real pipeline
        if service.PIPELINE_STUB:
            result = service.handle_documents_analyze_stub(
                case_id=case_id,
                files_info=files_info,
                saved_paths=saved_paths,
                locale=locale,
                intake_text=intake_text,
            )
        else:
            try:
                result = service.handle_documents_analyze_real(
                    case_id=case_id,
                    files_info=files_info,
                    saved_paths=saved_paths,
                    locale=locale,
                    intake_text=intake_text,
                )
            except ApiError:
                raise  # OCR_FAILED / LLM_FAILED / PIPELINE_VALIDATION_FAILED
            except Exception:
                logger.exception("Pipeline failed for case %s", case_id)
                raise internal_error("Document analysis failed. Please try again.")
    finally:
        service.release_case_lock(case_id)

    return DocumentAnalyzeResponse(**result)


# ---------------------------------------------------------------------------
# POST /api/v2/case/documents/reanalyze  (JSON body, server-side files)
# ---------------------------------------------------------------------------


@router.post("/case/documents/reanalyze", response_model=DocumentAnalyzeResponse)
async def case_documents_reanalyze(body: ReanalyzeRequest) -> DocumentAnalyzeResponse:
    service.acquire_case_lock(body.case_id)
    try:
        result = service.handle_reanalyze(
            case_id=body.case_id,
            locale=body.locale,
            document_ids=body.document_ids,
            client_document_ids=body.client_document_ids,
        )
    except ApiError:
        raise
    except Exception:
        logger.exception("Reanalyze failed for case %s", body.case_id)
        raise internal_error("Document reanalysis failed. Please try again.")
    finally:
        service.release_case_lock(body.case_id)

    return DocumentAnalyzeResponse(**result)


# ---------------------------------------------------------------------------
# POST /api/v2/case/submit
# ---------------------------------------------------------------------------


@router.post("/case/submit", response_model=SubmitResponse)
async def case_submit(body: SubmitRequest) -> SubmitResponse:
    result = service.handle_submit(
        case_id=body.case_id,
        locale=body.locale,
        email=body.email,
        consents=body.consents.model_dump(),
    )
    return SubmitResponse(**result)
