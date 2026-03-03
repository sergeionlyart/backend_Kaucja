"""Map FullPipelineResult (canonical schema) -> UI v2 contract.

Converts checklist items to summary_fields/fields_meta,
next_questions_to_user to questions, and builds analyzed_documents +
missing_docs from the pipeline output.
"""

from __future__ import annotations

from typing import Any

from .models import (
    AnalyzedDocument,
    ClarificationQuestion,
    FieldMeta,
    MissingDoc,
    SummaryField,
)

# ---------------------------------------------------------------------------
# Canonical item_id -> UI v2 summary field mapping
# ---------------------------------------------------------------------------

# All 22 item_ids from canonical_schema.json checklist_item.item_id enum
ALL_ITEM_IDS: list[str] = [
    "CONTRACT_EXISTS",
    "CONTRACT_SIGNED_AND_DATED",
    "PROPERTY_ADDRESS_CONFIRMED",
    "LEASE_TYPE_CONFIRMED",
    "KAUCJA_CLAUSE_PRESENT",
    "KAUCJA_AMOUNT_STATED",
    "KAUCJA_PAYMENT_PROOF",
    "CZYNSZ_AT_DEPOSIT_DATE",
    "CZYNSZ_AT_RETURN_DATE",
    "MOVE_IN_PROTOCOL",
    "MOVE_OUT_PROTOCOL",
    "VACATE_DATE_PROOF",
    "KEY_HANDOVER_PROOF",
    "METER_READINGS_AT_EXIT",
    "UTILITIES_SETTLEMENT",
    "RENT_AND_FEES_PAID",
    "LANDLORD_DEDUCTIONS_EXPLAINED",
    "PHOTOS_VIDEOS_CONDITION",
    "PRECOURT_DEMAND_LETTER",
    "DELIVERY_PROOF",
    "LANDLORD_RESPONSE",
    "TENANT_BANK_ACCOUNT_FOR_RETURN",
]

# Map item_id -> (summary_field_id, doc_type)
# summary_field_id is the UI v2 field; doc_type is for missing_docs
ITEM_ID_TO_FIELD: dict[str, tuple[str, str]] = {
    "CONTRACT_EXISTS": ("lease_agreement", "lease"),
    "CONTRACT_SIGNED_AND_DATED": ("lease_agreement", "lease"),
    "PROPERTY_ADDRESS_CONFIRMED": ("lease_agreement", "lease"),
    "LEASE_TYPE_CONFIRMED": ("lease_agreement", "lease"),
    "KAUCJA_CLAUSE_PRESENT": ("deposit_amount", "lease"),
    "KAUCJA_AMOUNT_STATED": ("deposit_amount", "lease"),
    "KAUCJA_PAYMENT_PROOF": ("deposit_payment_method", "deposit_payment"),
    "CZYNSZ_AT_DEPOSIT_DATE": ("deposit_amount", "lease"),
    "CZYNSZ_AT_RETURN_DATE": ("deposit_amount", "lease"),
    "MOVE_IN_PROTOCOL": ("handover_protocol", "handover_protocol"),
    "MOVE_OUT_PROTOCOL": ("handover_protocol", "handover_protocol"),
    "VACATE_DATE_PROOF": ("move_out_date", "handover_protocol"),
    "KEY_HANDOVER_PROOF": ("handover_protocol", "handover_protocol"),
    "METER_READINGS_AT_EXIT": ("handover_protocol", "handover_protocol"),
    "UTILITIES_SETTLEMENT": ("handover_protocol", "handover_protocol"),
    "RENT_AND_FEES_PAID": ("deposit_amount", "deposit_payment"),
    "LANDLORD_DEDUCTIONS_EXPLAINED": ("withholding_reason", "correspondence"),
    "PHOTOS_VIDEOS_CONDITION": ("handover_protocol", "handover_protocol"),
    "PRECOURT_DEMAND_LETTER": ("withholding_reason", "correspondence"),
    "DELIVERY_PROOF": ("withholding_reason", "correspondence"),
    "LANDLORD_RESPONSE": ("withholding_reason", "correspondence"),
    "TENANT_BANK_ACCOUNT_FOR_RETURN": ("deposit_payment_method", "deposit_payment"),
}

# UI v2 summary field definitions
SUMMARY_FIELD_IDS: list[str] = [
    "lease_agreement",
    "deposit_amount",
    "deposit_payment_method",
    "handover_protocol",
    "move_out_date",
    "withholding_reason",
]

FIELD_LABELS: dict[str, str] = {
    "lease_agreement": "Umowa najmu",
    "deposit_amount": "Suma kaucji",
    "deposit_payment_method": "Sposob platnosci",
    "handover_protocol": "Protokol zdawczo-odbiorczy",
    "move_out_date": "Data wyprowadzki",
    "withholding_reason": "Powod zatrzymania",
}

# canonical status -> UI status
_STATUS_MAP: dict[str, str] = {
    "confirmed": "ok",
    "missing": "muted",
    "ambiguous": "warn",
    "conflict": "warn",
}

# canonical importance -> UI question priority
_IMPORTANCE_MAP: dict[str, str] = {
    "critical": "high",
    "recommended": "medium",
}


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------


def map_pipeline_to_ui(
    parsed_json: dict[str, Any],
    *,
    case_id: str,
    run_id: str,
    documents_info: list[dict[str, Any]],
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Convert canonical parsed_json + pipeline metadata to UI v2 contract."""
    checklist: list[dict[str, Any]] = parsed_json.get("checklist", [])

    # --- Build summary_fields + fields_meta ---
    # Aggregate best status per summary field from all checklist items
    field_best_status: dict[str, str] = {fid: "muted" for fid in SUMMARY_FIELD_IDS}
    field_values: dict[str, str] = {fid: "" for fid in SUMMARY_FIELD_IDS}
    field_sources: dict[str, list[dict[str, Any]]] = {
        fid: [] for fid in SUMMARY_FIELD_IDS
    }
    field_confidence: dict[str, str | None] = {fid: None for fid in SUMMARY_FIELD_IDS}

    for item in checklist:
        item_id = item.get("item_id", "")
        mapping = ITEM_ID_TO_FIELD.get(item_id)
        if not mapping:
            continue
        field_id, _doc_type = mapping
        raw_status = item.get("status", "missing")
        ui_status = _STATUS_MAP.get(raw_status, "muted")

        # Take the best (most informative) status
        current = field_best_status[field_id]
        priority = {"ok": 3, "warn": 2, "muted": 1}
        if priority.get(ui_status, 0) > priority.get(current, 0):
            field_best_status[field_id] = ui_status

        # Collect a value from findings
        findings = item.get("findings", [])
        if findings and not field_values[field_id]:
            first_quote = findings[0].get("quote", "")
            if first_quote:
                field_values[field_id] = (
                    first_quote[:80] + "..." if len(first_quote) > 80 else first_quote
                )

        # Track sources for fields_meta
        for f in findings:
            field_sources[field_id].append(
                {
                    "doc_id": f.get("doc_id"),
                    "quote": f.get("quote", ""),
                }
            )

        # Confidence
        conf = item.get("confidence")
        if conf and not field_confidence[field_id]:
            field_confidence[field_id] = conf

    summary_fields: list[SummaryField] = []
    fields_meta: dict[str, FieldMeta] = {}
    for fid in SUMMARY_FIELD_IDS:
        status = field_best_status[fid]
        value = field_values.get(fid, "")
        # If status is ok but no value, provide a generic
        if status == "ok" and not value:
            value = "potwierdzone"

        summary_fields.append(
            SummaryField(
                id=fid,
                label=FIELD_LABELS.get(fid, fid),
                value=value,
                status=status,
            )
        )

        sources = field_sources.get(fid, [])
        first_source = sources[0] if sources else None
        conf_val = field_confidence.get(fid)
        conf_float = (
            {"high": 0.95, "medium": 0.75, "low": 0.45}.get(conf_val, None)
            if conf_val
            else None
        )

        fields_meta[fid] = FieldMeta(
            source_type="document" if first_source else "unknown",
            source_label="z dokumentu" if first_source else "brak danych",
            document_id=first_source.get("doc_id") if first_source else None,
            confidence=conf_float,
        )

    # --- Build questions from next_questions_to_user + checklist requests ---
    questions: list[ClarificationQuestion] = []
    next_qs: list[str] = parsed_json.get("next_questions_to_user", [])
    for idx, q_text in enumerate(next_qs[:8]):
        questions.append(
            ClarificationQuestion(
                id=f"q_pipeline_{idx}",
                text=q_text,
                priority="high",
            )
        )

    # Add checklist request_from_user items for missing items
    for item in checklist:
        if item.get("status") == "missing":
            req = item.get("request_from_user", {})
            ask = req.get("ask", "")
            if ask and len(questions) < 10:
                mapping = ITEM_ID_TO_FIELD.get(item.get("item_id", ""))
                doc_types = [mapping[1]] if mapping else []
                questions.append(
                    ClarificationQuestion(
                        id=f"q_item_{item.get('item_id', 'unknown')}",
                        text=ask,
                        priority=_IMPORTANCE_MAP.get(
                            item.get("importance", "recommended"), "medium"
                        ),
                        related_doc_types=doc_types,
                    )
                )

    # --- Build missing_docs ---
    present_doc_types: set[str] = set()
    for item in checklist:
        if item.get("status") == "confirmed":
            mapping = ITEM_ID_TO_FIELD.get(item.get("item_id", ""))
            if mapping:
                present_doc_types.add(mapping[1])

    required_types = ["lease", "deposit_payment", "handover_protocol", "correspondence"]
    missing_docs: list[MissingDoc] = []
    for dt in required_types:
        if dt not in present_doc_types:
            missing_docs.append(
                MissingDoc(
                    doc_type=dt,
                    priority="high" if dt in ("lease", "deposit_payment") else "medium",
                    reason=f"Brak dokumentu: {dt}",
                )
            )

    # --- Build analyzed_documents ---
    analyzed_documents: list[AnalyzedDocument] = []
    for di in documents_info:
        # Determine extracted fields from checklist items that have findings with this doc
        extracted: set[str] = set()
        doc_id_str = di.get("doc_id", "")
        for item in checklist:
            for f in item.get("findings", []):
                if f.get("doc_id") == doc_id_str:
                    mapping = ITEM_ID_TO_FIELD.get(item.get("item_id", ""))
                    if mapping:
                        extracted.add(mapping[0])

        analyzed_documents.append(
            AnalyzedDocument(
                id=di.get("doc_id", ""),
                categoryId=di.get("category_id", "lease"),
                name=di.get("name", ""),
                sizeMb=di.get("size_mb", 0.0),
                status="done",
                progress=100,
                extracted_fields=sorted(extracted),
                analyzed_at=di.get("analyzed_at"),
                client_doc_id=di.get("client_doc_id"),
            )
        )

    result: dict[str, Any] = {
        "case_id": case_id,
        "analyzed_documents": analyzed_documents,
        "summary_fields": summary_fields,
        "fields_meta": fields_meta,
        "questions": questions,
        "missing_docs": missing_docs,
        "analysis_run_id": run_id,
    }

    if warnings:
        result["warnings"] = warnings

    return result
