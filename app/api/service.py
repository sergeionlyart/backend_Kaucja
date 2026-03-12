"""MVP case service with FS-based storage, PIPELINE_STUB, and real pipeline.

Storage layout:
    data/v2_cases/{case_id}/case.json    - serialised case state
    data/v2_cases/{case_id}/uploads/     - uploaded files for pipeline
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.agentic.case_workspace_store import Scenario2CaseMetadata
from .models import (
    AnalyzedDocument,
    ClarificationQuestion,
    FieldMeta,
    MissingDoc,
    SummaryField,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PIPELINE_STUB = os.environ.get("PIPELINE_STUB", "true").lower() in (
    "1",
    "true",
    "yes",
)

_DATA_DIR = Path(os.environ.get("KAUCJA_DATA_DIR", "data"))
_CASES_DIR = _DATA_DIR / "v2_cases"

SUMMARY_FIELD_IDS: list[str] = [
    "lease_agreement",
    "deposit_amount",
    "deposit_payment_method",
    "handover_protocol",
    "move_out_date",
    "withholding_reason",
]

FIELD_LABELS: dict[str, dict[str, str]] = {
    "pl": {
        "lease_agreement": "Umowa najmu",
        "deposit_amount": "Suma kaucji",
        "deposit_payment_method": "Sposob platnosci",
        "handover_protocol": "Protokol zdawczo-odbiorczy",
        "move_out_date": "Data wyprowadzki",
        "withholding_reason": "Powod zatrzymania (wg wlasciciela)",
    },
    "ru": {
        "lease_agreement": "Dogovor arendy",
        "deposit_amount": "Summa zaloga",
        "deposit_payment_method": "Sposob oplaty",
        "handover_protocol": "Protokol peredachi",
        "move_out_date": "Data vyezda",
        "withholding_reason": "Prichina uderzhaniya (po versii vladeltsa)",
    },
}

REQUIRED_DOC_TYPES = [
    "lease",
    "deposit_payment",
    "handover_protocol",
    "correspondence",
]

ALLOWED_MIME_TYPES: set[str] = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}

MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024
MAX_TOTAL_SIZE_BYTES: int = 50 * 1024 * 1024
MAX_FILES_PER_REQUEST: int = 10

VALID_CATEGORIES: set[str] = {
    "lease",
    "deposit_payment",
    "handover_protocol",
    "correspondence",
}


# ---------------------------------------------------------------------------
# Locale helpers
# ---------------------------------------------------------------------------


def _normalize_locale(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if raw.startswith("ru"):
        return "ru"
    if raw.startswith("uk"):
        return "uk"
    if raw.startswith("be"):
        return "be"
    return "pl"


def _field_label(locale: str, field_id: str) -> str:
    labels = FIELD_LABELS.get(locale, FIELD_LABELS["pl"])
    return labels.get(field_id, FIELD_LABELS["pl"].get(field_id, field_id))


# ---------------------------------------------------------------------------
# Case ID
# ---------------------------------------------------------------------------


def _create_case_id() -> str:
    year = datetime.now(tz=timezone.utc).year
    chunk = secrets.token_hex(2).upper()
    return f"KJ-{year}-{chunk}"


# ---------------------------------------------------------------------------
# FS persistence (MVP)
# ---------------------------------------------------------------------------


def _case_path(case_id: str) -> Path:
    return _CASES_DIR / case_id / "case.json"


def _uploads_dir(case_id: str) -> Path:
    return _CASES_DIR / case_id / "uploads"


def _load_case(case_id: str) -> dict[str, Any] | None:
    p = _case_path(case_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _save_case(case_id: str, state: dict[str, Any]) -> None:
    p = _case_path(case_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def save_upload(case_id: str, filename: str, content: bytes) -> dict[str, Any]:
    """Save an uploaded file to case storage.

    Dedup Policy
    ─────────────
    PHYSICAL dedup: two uploads with the same sha256 share one file on disk.
    LOGICAL identity reuse: when catalog contains a matching sha256, the
        existing doc_id is returned so the router can reuse it.  This keeps
        doc_ids stable across repeated uploads of the same content.
    Scan fallback: if catalog is empty/stale but a matching file exists on
        disk, physical dedup is applied (no doc_id reuse — the caller
        generates a fresh doc_id for the new logical document).

    Returns a structured SaveResult dict:
        saved_path  (Path)       – where the file lives on disk
        sha256      (str)        – content hash
        is_dedup_hit (bool)      – True if an existing file was reused
        existing_doc_id (str|None) – doc_id from catalog on catalog-hit
    """
    upload_dir = _uploads_dir(case_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    content_hash = hashlib.sha256(content).hexdigest()

    # 1. Fast path: catalog-based dedup
    catalog = _load_documents_catalog(case_id)
    for entry in catalog:
        if entry.get("sha256") == content_hash:
            existing = Path(entry["saved_path"])
            if existing.is_file():
                logger.info(
                    "Dedup (catalog): %s matches %s in case %s",
                    filename,
                    existing.name,
                    case_id,
                )
                return {
                    "saved_path": existing,
                    "sha256": content_hash,
                    "is_dedup_hit": True,
                    "existing_doc_id": entry.get("doc_id"),
                }

    # 2. Slow fallback: scan existing files (in case catalog is stale)
    for existing in upload_dir.iterdir():
        if existing.is_file():
            existing_hash = hashlib.sha256(existing.read_bytes()).hexdigest()
            if existing_hash == content_hash:
                logger.info(
                    "Dedup (scan): %s matches %s in case %s",
                    filename,
                    existing.name,
                    case_id,
                )
                return {
                    "saved_path": existing,
                    "sha256": content_hash,
                    "is_dedup_hit": True,
                    "existing_doc_id": None,  # scan-only, no catalog doc_id
                }

    dest = upload_dir / filename
    dest.write_bytes(content)
    return {
        "saved_path": dest,
        "sha256": content_hash,
        "is_dedup_hit": False,
        "existing_doc_id": None,
    }


# ---------------------------------------------------------------------------
# File-based case lock (cross-process safe)
# ---------------------------------------------------------------------------

_lock_fds: dict[str, int] = {}
_lock_guard = threading.Lock()


def acquire_case_lock(case_id: str) -> None:
    """Acquire a file-based lock per case. Raises CASE_BUSY if already held."""
    import fcntl

    case_dir = _case_path(case_id).parent
    case_dir.mkdir(parents=True, exist_ok=True)
    lock_file = case_dir / ".lock"

    fd = os.open(str(lock_file), os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        os.close(fd)
        from .errors import case_busy

        raise case_busy(case_id)

    with _lock_guard:
        # Close any stale fd for this case
        old_fd = _lock_fds.get(case_id)
        if old_fd is not None:
            try:
                os.close(old_fd)
            except OSError:
                pass
        _lock_fds[case_id] = fd


def release_case_lock(case_id: str) -> None:
    """Release the file-based lock."""
    with _lock_guard:
        fd = _lock_fds.pop(case_id, None)
    if fd is not None:
        try:
            os.close(fd)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Documents catalog (documents.json)
# ---------------------------------------------------------------------------


def _documents_catalog_path(case_id: str) -> Path:
    return _case_path(case_id).parent / "documents.json"


def _load_documents_catalog(case_id: str) -> list[dict[str, Any]]:
    """Load documents.json, with legacy stored_files migration."""
    cat_path = _documents_catalog_path(case_id)
    if cat_path.is_file():
        try:
            return json.loads(cat_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            logger.warning("Corrupt documents.json for case %s", case_id)
            return []

    # Legacy migration: read stored_files from case.json
    state = _load_case(case_id)
    if state and "stored_files" in state:
        legacy = state["stored_files"]
        logger.info(
            "Migrating %d stored_files to documents.json for case %s",
            len(legacy),
            case_id,
        )
        _save_documents_catalog(case_id, legacy)
        return legacy

    return []


def _save_documents_catalog(case_id: str, catalog: list[dict[str, Any]]) -> None:
    """Atomic write of documents.json (tmp + rename)."""
    cat_path = _documents_catalog_path(case_id)
    cat_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cat_path.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    tmp_path.replace(cat_path)


def _deduplicate_catalog(catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove catalog entries with duplicate (sha256, saved_path), keeping first."""
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, Any]] = []
    for entry in catalog:
        key = (entry.get("sha256", ""), entry.get("saved_path", ""))
        if key == ("", ""):
            result.append(entry)  # keep entries without identity info
            continue
        if key not in seen:
            seen.add(key)
            result.append(entry)
    return result


def _persist_files_info(
    case_id: str,
    files_info: list[dict[str, Any]],
    saved_paths: list[Path],
) -> None:
    """Merge/upsert file metadata into documents.json catalog.

    Existing entries are keyed by doc_id: re-analyzing the same doc_id
    updates the entry in-place; new doc_ids are appended.
    Also updates case.json status.
    """
    catalog = _load_documents_catalog(case_id)
    by_doc_id = {e["doc_id"]: e for e in catalog}

    now_iso = datetime.now(tz=timezone.utc).isoformat()
    for fi, sp in zip(files_info, saved_paths):
        content_hash = ""
        if sp.is_file():
            content_hash = hashlib.sha256(sp.read_bytes()).hexdigest()
        by_doc_id[fi["doc_id"]] = {
            "doc_id": fi["doc_id"],
            "original_name": fi["name"],
            "categoryId": fi["category_id"],
            "sha256": content_hash,
            "uploaded_at": now_iso,
            "size_bytes": fi.get("content_length", 0),
            "saved_path": str(sp),
            "client_doc_id": fi.get("client_doc_id"),
        }

    _save_documents_catalog(case_id, _deduplicate_catalog(list(by_doc_id.values())))

    # Also update case.json status
    state = _load_case(case_id) or {}
    state["status"] = "analyzed"
    state["updated_at"] = now_iso
    _save_case(case_id, state)


def list_stored_documents(case_id: str) -> list[dict[str, Any]]:
    """Return stored file metadata from documents.json, filtering to safe + existing files.

    Safety: resolved path must be strictly inside the case uploads directory.
    Uses Path.relative_to() to prevent prefix-bypass attacks.
    Reads from documents.json (with legacy stored_files auto-migration).
    """
    catalog = _load_documents_catalog(case_id)
    if not catalog:
        return []

    safe_root = _uploads_dir(case_id).resolve()
    result: list[dict[str, Any]] = []
    for entry in catalog:
        try:
            resolved = Path(entry["saved_path"]).resolve()
        except (TypeError, ValueError):
            logger.warning(
                "Invalid saved_path in case %s: %s", case_id, entry.get("saved_path")
            )
            continue
        try:
            resolved.relative_to(safe_root)
        except ValueError:
            logger.warning(
                "Path containment blocked in case %s: %s not under %s",
                case_id,
                resolved,
                safe_root,
            )
            continue
        if resolved.is_file():
            result.append(entry)
    return result


# ---------------------------------------------------------------------------
# Intake parsing (regex-based, mirrors Node.js deriveV2SummaryFromIntake)
# ---------------------------------------------------------------------------


def _status_for_value(value: str) -> str:
    return "ok" if value.strip() else "muted"


def parse_intake(
    intake_text: str,
    locale: str | None = None,
) -> dict[str, Any]:
    """Parse free-form text and return structured summary fields + metadata."""
    loc = _normalize_locale(locale)
    normalized = intake_text.lower()

    deposit_match = re.search(r"(\d{2,6})\s*(pln|zl)", normalized)
    deposit_amount = f"{deposit_match.group(1)} PLN" if deposit_match else ""

    iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", normalized)
    slash_match = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", normalized)
    if iso_match:
        move_out_date = iso_match.group(1)
    elif slash_match:
        move_out_date = (
            f"{slash_match.group(3)}-{slash_match.group(2)}-{slash_match.group(1)}"
        )
    else:
        move_out_date = ""

    lease_mentioned = "umow" in normalized or "najem" in normalized
    protocol_mentioned = "protok" in normalized or "akt" in normalized
    payment_method = (
        "przelew"
        if "przelew" in normalized
        else "gotowka"
        if "gotow" in normalized
        else ""
    )
    withholding_reason = (
        "opisane w zgloszeniu"
        if ("zatrzym" in normalized or "potrac" in normalized)
        else ""
    )

    values_by_id: dict[str, str] = {
        "lease_agreement": "wspomniana" if lease_mentioned else "",
        "deposit_amount": deposit_amount,
        "deposit_payment_method": payment_method,
        "handover_protocol": "wspomniany" if protocol_mentioned else "",
        "move_out_date": move_out_date,
        "withholding_reason": withholding_reason,
    }

    summary_fields: list[SummaryField] = []
    fields_meta: dict[str, FieldMeta] = {}

    for field_id in SUMMARY_FIELD_IDS:
        value = values_by_id.get(field_id, "")
        has_value = bool(value.strip())
        status = _status_for_value(value)

        summary_fields.append(
            SummaryField(
                id=field_id,
                label=_field_label(loc, field_id),
                value=value,
                status=status,
            )
        )
        fields_meta[field_id] = FieldMeta(
            source_type="intake" if has_value else "unknown",
            source_label="z opisu" if has_value else "brak danych",
            confidence=0.78 if has_value else None,
        )

    return {
        "summary_fields": summary_fields,
        "fields_meta": fields_meta,
    }


def _parse_claim_amount_summary(value: str) -> tuple[float | None, str | None]:
    raw = value.strip()
    if not raw:
        return None, None
    match = re.fullmatch(r"(\d+(?:[.,]\d{1,2})?)\s*([A-Za-z]{3})", raw)
    if match is None:
        return None, None
    amount_raw, currency = match.groups()
    try:
        amount = float(amount_raw.replace(",", "."))
    except ValueError:
        return None, None
    return amount, currency.upper()


def _summary_field_value(
    summary_fields: list[SummaryField],
    field_id: str,
) -> str | None:
    for field in summary_fields:
        if field.id == field_id:
            value = field.value.strip()
            return value or None
    return None


def build_scenario2_case_metadata(
    *,
    intake_text: str | None,
    locale: str | None,
) -> Scenario2CaseMetadata:
    if not intake_text or not intake_text.strip():
        return Scenario2CaseMetadata()
    parsed = parse_intake(intake_text, locale)
    summary_fields: list[SummaryField] = parsed["summary_fields"]
    deposit_amount = _summary_field_value(summary_fields, "deposit_amount") or ""
    move_out_date = _summary_field_value(summary_fields, "move_out_date")
    claim_amount, currency = _parse_claim_amount_summary(deposit_amount)
    return Scenario2CaseMetadata(
        claim_amount=claim_amount,
        currency=currency,
        move_out_date=move_out_date,
    )


# ---------------------------------------------------------------------------
# Missing docs / questions derivation
# ---------------------------------------------------------------------------


def _build_missing_docs(
    documents: list[dict[str, Any]],
) -> list[MissingDoc]:
    present_categories: set[str] = set()
    for doc in documents:
        cat = doc.get("category_id", "")
        if cat:
            present_categories.add(cat)

    reasons = {
        "lease": "Brak umowy najmu.",
        "deposit_payment": "Brak potwierdzenia wplaty kaucji.",
        "handover_protocol": "Brak protokolu lub rozliczenia po wyprowadzce.",
        "correspondence": "Brak korespondencji z wlascicielem.",
    }

    result: list[MissingDoc] = []
    for doc_type in REQUIRED_DOC_TYPES:
        if doc_type not in present_categories:
            priority = "high" if doc_type in ("lease", "deposit_payment") else "medium"
            result.append(
                MissingDoc(
                    doc_type=doc_type,
                    priority=priority,
                    reason=reasons.get(doc_type, ""),
                )
            )
    return result


def _build_questions(
    summary_fields: list[SummaryField],
    missing_docs: list[MissingDoc],
) -> list[ClarificationQuestion]:
    fields_by_id = {f.id: f for f in summary_fields}
    missing_types = {d.doc_type for d in missing_docs}
    questions: list[ClarificationQuestion] = []

    deposit_f = fields_by_id.get("deposit_amount")
    if not deposit_f or deposit_f.status != "ok":
        questions.append(
            ClarificationQuestion(
                id="q_deposit_amount",
                text="Czy mozesz potwierdzic dokladna kwote kaucji (PLN)?",
                priority="high",
                related_doc_types=["deposit_payment"],
            )
        )

    move_out_f = fields_by_id.get("move_out_date")
    if not move_out_f or move_out_f.status != "ok":
        questions.append(
            ClarificationQuestion(
                id="q_move_out_date",
                text="Czy mozesz podac date wyprowadzki?",
                priority="high",
                related_doc_types=["handover_protocol"],
            )
        )

    lease_f = fields_by_id.get("lease_agreement")
    if not lease_f or lease_f.status != "ok" or "lease" in missing_types:
        questions.append(
            ClarificationQuestion(
                id="q_lease_copy",
                text="Czy masz kopie umowy najmu?",
                priority="high",
                related_doc_types=["lease"],
            )
        )

    protocol_f = fields_by_id.get("handover_protocol")
    if (
        not protocol_f
        or protocol_f.status != "ok"
        or "handover_protocol" in missing_types
    ):
        questions.append(
            ClarificationQuestion(
                id="q_protocol",
                text="Czy podpisaliscie protokol zdawczo-odbiorczy przy wyprowadzce?",
                priority="medium",
                related_doc_types=["handover_protocol"],
            )
        )

    if "correspondence" in missing_types:
        questions.append(
            ClarificationQuestion(
                id="q_refusal_messages",
                text="Czy masz korespondencje, w ktorej wlasciciel odmawia zwrotu kaucji?",
                priority="medium",
                related_doc_types=["correspondence"],
            )
        )

    return questions[:8]


# ---------------------------------------------------------------------------
# Public service methods
# ---------------------------------------------------------------------------


def handle_intake(
    intake_text: str,
    case_id: str | None = None,
    locale: str | None = None,
) -> dict[str, Any]:
    """Process intake text and return TechSpec-compatible response."""
    cid = case_id.strip() if case_id else _create_case_id()
    parsed = parse_intake(intake_text, locale)
    summary_fields: list[SummaryField] = parsed["summary_fields"]
    fields_meta: dict[str, FieldMeta] = parsed["fields_meta"]
    missing_docs = _build_missing_docs([])
    questions = _build_questions(summary_fields, missing_docs)

    _save_case(
        cid,
        {
            "case_id": cid,
            "locale": _normalize_locale(locale),
            "intake_text": intake_text,
            "status": "parsed",
            "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        },
    )

    return {
        "case_id": cid,
        "case_status": "parsed",
        "summary_fields": summary_fields,
        "fields_meta": fields_meta,
        "questions": questions,
        "missing_docs": missing_docs,
    }


def handle_documents_analyze_stub(
    case_id: str,
    files_info: list[dict[str, Any]],
    saved_paths: list[Path],
    locale: str | None = None,
    intake_text: str | None = None,
) -> dict[str, Any]:
    """Stub analyze: deterministic response without OCR/LLM."""
    loc = _normalize_locale(locale)
    now_iso = datetime.now(tz=timezone.utc).isoformat()

    extracted_by_cat: dict[str, list[str]] = {
        "lease": ["lease_agreement", "deposit_amount"],
        "deposit_payment": ["deposit_amount", "deposit_payment_method"],
        "handover_protocol": ["handover_protocol", "move_out_date"],
        "correspondence": ["withholding_reason"],
    }

    analyzed_documents: list[AnalyzedDocument] = []
    for fi in files_info:
        cat = fi["category_id"]
        analyzed_documents.append(
            AnalyzedDocument(
                id=fi["doc_id"],
                categoryId=cat,
                name=fi["name"],
                sizeMb=fi["size_mb"],
                status="done",
                progress=100,
                extracted_fields=extracted_by_cat.get(cat, []),
                analyzed_at=now_iso,
                client_doc_id=fi.get("client_doc_id"),
            )
        )

    summary_fields: list[SummaryField] = []
    fields_meta: dict[str, FieldMeta] = {}
    present_categories = {fi["category_id"] for fi in files_info}

    stub_values: dict[str, tuple[str, str, str]] = {
        "lease_agreement": (
            "rozpoznano" if "lease" in present_categories else "",
            "lease" if "lease" in present_categories else "unknown",
            "z umowy" if "lease" in present_categories else "brak danych",
        ),
        "deposit_amount": (
            "potwierdzona dokumentem"
            if "deposit_payment" in present_categories
            else "",
            "deposit_payment" if "deposit_payment" in present_categories else "unknown",
            "z potwierdzenia wplaty"
            if "deposit_payment" in present_categories
            else "brak danych",
        ),
        "deposit_payment_method": (
            "przelew" if "deposit_payment" in present_categories else "",
            "deposit_payment" if "deposit_payment" in present_categories else "unknown",
            "z potwierdzenia wplaty"
            if "deposit_payment" in present_categories
            else "brak danych",
        ),
        "handover_protocol": (
            "dodano protokol" if "handover_protocol" in present_categories else "",
            "handover_protocol"
            if "handover_protocol" in present_categories
            else "unknown",
            "z protokolu"
            if "handover_protocol" in present_categories
            else "brak danych",
        ),
        "move_out_date": (
            "potwierdzona w dokumencie"
            if "handover_protocol" in present_categories
            else "",
            "handover_protocol"
            if "handover_protocol" in present_categories
            else "unknown",
            "z protokolu"
            if "handover_protocol" in present_categories
            else "brak danych",
        ),
        "withholding_reason": (
            "wskazany w korespondencji"
            if "correspondence" in present_categories
            else "",
            "correspondence" if "correspondence" in present_categories else "unknown",
            "z korespondencji"
            if "correspondence" in present_categories
            else "brak danych",
        ),
    }

    for field_id in SUMMARY_FIELD_IDS:
        val, src_type, src_label = stub_values.get(
            field_id, ("", "unknown", "brak danych")
        )
        summary_fields.append(
            SummaryField(
                id=field_id,
                label=_field_label(loc, field_id),
                value=val,
                status=_status_for_value(val),
            )
        )
        fields_meta[field_id] = FieldMeta(
            source_type=src_type,
            source_label=src_label,
            confidence=0.85 if val else None,
        )

    docs_list = [{"category_id": fi["category_id"]} for fi in files_info]
    missing_docs = _build_missing_docs(docs_list)
    questions = _build_questions(summary_fields, missing_docs)

    result = {
        "case_id": case_id,
        "analyzed_documents": analyzed_documents,
        "summary_fields": summary_fields,
        "fields_meta": fields_meta,
        "questions": questions,
        "missing_docs": missing_docs,
        "analysis_run_id": f"stub-{secrets.token_hex(4)}",
    }

    # Persist files_info using actual saved_paths from router
    _persist_files_info(case_id, files_info, saved_paths)

    return result


def handle_documents_analyze_real(
    case_id: str,
    files_info: list[dict[str, Any]],
    saved_paths: list[Path],
    locale: str | None = None,
    intake_text: str | None = None,
) -> dict[str, Any]:
    """Real pipeline analyze: runs OCRPipelineOrchestrator.run_full_pipeline.

    Imports are done lazily to avoid import-time deps on heavy modules.
    """
    from app.agentic.scenario2_runtime_factory import build_scenario2_runtime
    from app.config.settings import Settings
    from app.llm_client.gemini_client import GeminiLLMClient
    from app.llm_client.openai_client import OpenAILLMClient
    from app.pipeline.orchestrator import OCRPipelineOrchestrator
    from app.storage.artifacts import ArtifactsManager
    from app.storage.repo import StorageRepo

    try:
        from app.ocr_client.mistral_ocr import MistralOCRClient
        from app.ocr_client.types import OCROptions
    except ImportError:
        logger.exception("OCR client not available")
        raise

    settings = Settings()
    case_state = _load_case(case_id)
    effective_intake_text = intake_text or (
        str(case_state.get("intake_text") or "") if case_state else None
    )
    scenario2_case_metadata = build_scenario2_case_metadata(
        intake_text=effective_intake_text,
        locale=locale,
    )
    # Backward-compatible settings resolution for real pipeline mode.
    # Current Settings exposes resolved_sqlite_path/resolved_data_dir and
    # mistral_api_key (with OCR_API_KEY alias).
    db_path = getattr(settings, "db_path", None) or settings.resolved_sqlite_path
    data_root = getattr(settings, "storage_root", None) or settings.resolved_data_dir
    ocr_api_key = getattr(settings, "ocr_api_key", None) or settings.mistral_api_key

    repo = StorageRepo(db_path=str(db_path))
    artifacts = ArtifactsManager(data_dir=data_root)

    ocr_client = MistralOCRClient(api_key=ocr_api_key)
    scenario2_runtime = build_scenario2_runtime(settings=settings)

    orchestrator = OCRPipelineOrchestrator(
        repo=repo,
        artifacts_manager=artifacts,
        ocr_client=ocr_client,
        llm_clients={
            "openai": OpenAILLMClient(
                api_key=settings.openai_api_key,
                pricing_config=settings.pricing_config,
            ),
            "google": GeminiLLMClient(
                api_key=settings.google_api_key,
                pricing_config=settings.pricing_config,
            ),
        },
        prompt_root=settings.project_root / "app" / "prompts",
        scenario2_runner=scenario2_runtime.runner,
        legal_corpus_tool=scenario2_runtime.legal_corpus_tool,
        scenario2_case_workspace_store=getattr(
            scenario2_runtime, "case_workspace_store", None
        ),
        scenario2_runner_mode=settings.scenario2_runner_mode,
        scenario2_verifier_policy=settings.scenario2_verifier_policy,
        scenario2_bootstrap_error=scenario2_runtime.bootstrap_error,
    )

    result = orchestrator.run_full_pipeline(
        input_files=saved_paths,
        session_id=case_id,
        provider=settings.default_provider,
        model=settings.default_model,
        prompt_name=settings.default_prompt_name,
        prompt_version=settings.default_prompt_version,
        ocr_options=OCROptions(),
        scenario2_case_metadata=scenario2_case_metadata,
    )

    # Classify known pipeline errors for caller
    if result.error_code:
        from .errors import (
            internal_error,
            llm_failed,
            ocr_failed,
            pipeline_validation_failed,
        )

        error_msg = result.error_message or "Pipeline error"
        # Normalize to lowercase for comparison (pipeline may return
        # UPPER_SNAKE_CASE like OCR_API_ERROR or lowercase like ocr_failed)
        code = result.error_code.lower()

        _OCR_CODES = {
            "ocr_failed",
            "ocr_all_failed",
            "ocr_timeout",
            "ocr_api_error",
        }
        _LLM_CODES = {
            "llm_failed",
            "llm_refused",
            "llm_api_error",
            "llm_invalid_json",
            "context_too_large",
        }
        _VALIDATION_CODES = {
            "validation_failed",
            "json_parse_failed",
            "pipeline_validation_failed",
        }

        if code in _OCR_CODES:
            raise ocr_failed(error_msg)
        if code in _LLM_CODES:
            raise llm_failed(error_msg)
        if code in _VALIDATION_CODES:
            raise pipeline_validation_failed(
                error_msg,
                {"validation_errors": result.validation_errors[:5]}
                if result.validation_errors
                else None,
            )
        # Fail-closed: unknown error_code must NOT return 200
        raise internal_error(f"Pipeline error ({result.error_code}): {error_msg}")

    # Use mapper to convert pipeline output to UI contract
    from .mapper import map_pipeline_to_ui

    if result.parsed_json:
        warnings = []
        if result.validation_errors:
            warnings.extend(result.validation_errors)
        if result.error_message:
            warnings.append(result.error_message)

        mapped = map_pipeline_to_ui(
            result.parsed_json,
            case_id=case_id,
            run_id=result.run_id,
            documents_info=files_info,
            warnings=warnings or None,
        )

        # Persist files_info for server-side reanalyze
        _persist_files_info(case_id, files_info, saved_paths)

        return mapped

    # No error_code but also no parsed_json —
    # fail-closed: treat as internal error
    from .errors import internal_error

    raise internal_error("Pipeline returned no results and no error code")


def handle_submit(
    case_id: str,
    locale: str | None = None,
    email: str | None = None,
    consents: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Submit the case - set case_status to report_sent."""
    # Validate email
    if not email or "@" not in email or len(email) < 5:
        from .errors import validation_error

        raise validation_error(
            "Valid email address is required.",
            {"email": "invalid"},
        )

    # Validate consents
    if not consents or not consents.get("terms") or not consents.get("privacy"):
        from .errors import validation_error

        raise validation_error(
            "Both 'terms' and 'privacy' consents must be accepted.",
            {"consents": "missing_required"},
        )

    case = _load_case(case_id)
    if case is None:
        case = {
            "case_id": case_id,
            "locale": _normalize_locale(locale),
            "status": "draft",
            "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        }

    now_iso = datetime.now(tz=timezone.utc).isoformat()
    case["status"] = "report_sent"
    case["submitted_at"] = now_iso
    case["updated_at"] = now_iso
    case["email"] = email
    case["consents"] = consents
    _save_case(case_id, case)

    return {
        "case_id": case_id,
        "case_status": "report_sent",
        "submitted_at": now_iso,
    }


# ---------------------------------------------------------------------------
# Reanalyze from stored files
# ---------------------------------------------------------------------------


def handle_reanalyze(
    case_id: str,
    locale: str | None = None,
    document_ids: list[str] | None = None,
    client_document_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Re-run analysis using previously stored files (no new upload required).

    Selectors (mutually exclusive, at most one may be provided):
    - ``document_ids``: select by server-side doc_id
    - ``client_document_ids``: select by frontend client_doc_id
    If neither is provided, all stored documents are re-analyzed.
    """
    # Mutual exclusivity check
    if document_ids is not None and client_document_ids is not None:
        from .errors import validation_error

        raise validation_error(
            "Provide either document_ids or client_document_ids, not both.",
            {"selectors": "mutually_exclusive"},
        )

    stored = list_stored_documents(case_id)
    if not stored:
        # Distinguish: case doesn't exist vs. no stored files
        if _load_case(case_id) is None:
            from .errors import case_not_found

            raise case_not_found(case_id)
        from .errors import no_stored_documents

        raise no_stored_documents(case_id)

    # Selective filtering by document_ids (server ids)
    if document_ids is not None:
        _validate_selector(document_ids, "document_ids")
        stored_by_id = {e["doc_id"]: e for e in stored}
        unknown = [did for did in document_ids if did not in stored_by_id]
        if unknown:
            from .errors import validation_error

            raise validation_error(
                f"Unknown document_ids: {', '.join(unknown)}.",
                {"document_ids": "unknown", "unknown_ids": unknown},
            )
        stored = [stored_by_id[did] for did in document_ids]

    # Selective filtering by client_document_ids (frontend local ids)
    elif client_document_ids is not None:
        _validate_selector(client_document_ids, "client_document_ids")
        stored_by_client = {
            e["client_doc_id"]: e for e in stored if e.get("client_doc_id")
        }
        unknown = [cid for cid in client_document_ids if cid not in stored_by_client]
        if unknown:
            from .errors import validation_error

            raise validation_error(
                f"Unknown client_document_ids: {', '.join(unknown)}.",
                {"client_document_ids": "unknown", "unknown_ids": unknown},
            )
        stored = [stored_by_client[cid] for cid in client_document_ids]

    if not stored:
        from .errors import no_stored_documents

        raise no_stored_documents(case_id)

    # Rebuild files_info + saved_paths from stored metadata
    files_info: list[dict[str, Any]] = []
    saved_paths: list[Path] = []
    for entry in stored:
        size_mb = (
            round(entry.get("size_bytes", 0) / (1024 * 1024), 2)
            if entry.get("size_bytes")
            else entry.get("size_mb", 0)
        )
        files_info.append(
            {
                "doc_id": entry["doc_id"],
                "category_id": entry.get("categoryId") or entry.get("category_id", ""),
                "name": entry.get("original_name") or entry.get("name", ""),
                "size_mb": size_mb,
                "client_doc_id": entry.get("client_doc_id"),
            }
        )
        saved_paths.append(Path(entry["saved_path"]))

    # Load intake_text from case state (if available)
    case_state = _load_case(case_id)
    intake_text = case_state.get("intake_text") if case_state else None

    if PIPELINE_STUB:
        return handle_documents_analyze_stub(
            case_id=case_id,
            files_info=files_info,
            saved_paths=saved_paths,
            locale=locale,
            intake_text=intake_text,
        )
    else:
        return handle_documents_analyze_real(
            case_id=case_id,
            files_info=files_info,
            saved_paths=saved_paths,
            locale=locale,
            intake_text=intake_text,
        )


def _validate_selector(ids: list[str], field_name: str) -> None:
    """Validate a selector list: no empty strings, no duplicates."""
    if not ids:
        from .errors import validation_error

        raise validation_error(
            f"{field_name} must not be empty when provided.",
            {field_name: "empty"},
        )
    blanks = [i for i in ids if not i or not i.strip()]
    if blanks:
        from .errors import validation_error

        raise validation_error(
            f"{field_name} contains empty values.",
            {field_name: "blank_values"},
        )
    if len(ids) != len(set(ids)):
        from .errors import validation_error

        raise validation_error(
            f"{field_name} contains duplicates.",
            {field_name: "duplicates"},
        )
