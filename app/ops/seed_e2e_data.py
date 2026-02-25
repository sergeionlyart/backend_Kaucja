from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config.settings import get_settings
from app.storage.artifacts import ArtifactsManager
from app.storage.repo import StorageRepo

DEFAULT_SESSION_ID = "e2e-session-001"
DEFAULT_DOC_ID = "0000001"


@dataclass(frozen=True, slots=True)
class SeedRunSpec:
    run_id: str
    created_at: str
    provider: str
    model: str
    prompt_version: str
    prompt_name: str
    schema_version: str
    parsed_payload: dict[str, Any]
    metrics: dict[str, dict[str, Any]]
    log_lines: list[str]
    combined_markdown: str


def seed_e2e_data(
    *,
    db_path: Path,
    data_dir: Path,
    session_id: str = DEFAULT_SESSION_ID,
) -> dict[str, Any]:
    repo = StorageRepo(
        db_path=db_path,
        artifacts_manager=ArtifactsManager(data_dir),
    )
    seeded_runs: list[dict[str, Any]] = []
    warnings: list[str] = []

    repo.create_session(session_id=session_id)
    for spec in _seed_specs():
        existing = repo.get_run(spec.run_id)
        if existing is not None:
            delete_result = repo.delete_run(spec.run_id)
            if not delete_result.deleted:
                raise RuntimeError(
                    "Failed to reset seeded run before insert: "
                    f"run_id={spec.run_id} "
                    f"error_code={delete_result.error_code} "
                    f"error_message={delete_result.error_message}"
                )

        seeded_runs.append(
            _seed_single_run(
                repo=repo,
                session_id=session_id,
                spec=spec,
            )
        )

    return {
        "status": "ok",
        "session_id": session_id,
        "db_path": str(db_path.resolve()),
        "data_dir": str(data_dir.resolve()),
        "seeded_runs": seeded_runs,
        "warnings": warnings,
    }


def _seed_single_run(
    *,
    repo: StorageRepo,
    session_id: str,
    spec: SeedRunSpec,
) -> dict[str, Any]:
    run = repo.create_run(
        session_id=session_id,
        provider=spec.provider,
        model=spec.model,
        prompt_name=spec.prompt_name,
        prompt_version=spec.prompt_version,
        schema_version=spec.schema_version,
        status="completed",
        openai_reasoning_effort="low",
        gemini_thinking_level="low",
        run_id=spec.run_id,
        created_at=spec.created_at,
    )
    run_root = Path(run.artifacts_root_path)

    document_artifacts = repo.artifacts_manager.create_document_artifacts(
        artifacts_root_path=run_root,
        doc_id=DEFAULT_DOC_ID,
    )
    llm_artifacts = repo.artifacts_manager.create_llm_artifacts(
        artifacts_root_path=run_root
    )

    original_file = document_artifacts.original_dir / "contract.pdf"
    original_file.write_bytes(b"%PDF-1.4\n% deterministic-e2e-seed\n")

    (document_artifacts.pages_dir / "0001.md").write_text(
        spec.combined_markdown,
        encoding="utf-8",
    )
    document_artifacts.combined_markdown_path.write_text(
        spec.combined_markdown,
        encoding="utf-8",
    )
    document_artifacts.raw_response_path.write_text(
        json.dumps(
            {
                "model": "mistral-ocr-latest",
                "pages": [{"index": 1, "markdown": spec.combined_markdown}],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    document_artifacts.quality_path.write_text(
        json.dumps({"warnings": [], "bad_pages": []}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    llm_artifacts.request_path.write_text(
        (
            "<BEGIN_DOCUMENTS>\n"
            f"[DOC {DEFAULT_DOC_ID}]\n"
            f"{spec.combined_markdown}\n"
            "<END_DOCUMENTS>\n"
        ),
        encoding="utf-8",
    )
    llm_artifacts.response_raw_path.write_text(
        json.dumps(spec.parsed_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    llm_artifacts.response_parsed_path.write_text(
        json.dumps(spec.parsed_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    llm_artifacts.validation_path.write_text(
        json.dumps(
            {"valid": True, "schema_errors": [], "invariant_errors": []},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    run_log_path = run_root / "logs" / "run.log"
    run_log_path.write_text("\n".join(spec.log_lines) + "\n", encoding="utf-8")

    repo.create_document(
        run_id=run.run_id,
        doc_id=DEFAULT_DOC_ID,
        original_filename="contract.pdf",
        original_mime="application/pdf",
        original_path=str(original_file.resolve()),
        ocr_status="ok",
        ocr_model="mistral-ocr-latest",
        pages_count=1,
        ocr_artifacts_path=str(document_artifacts.ocr_dir.resolve()),
        ocr_error=None,
    )
    repo.upsert_llm_output(
        run_id=run.run_id,
        response_json_path=str(llm_artifacts.response_parsed_path.resolve()),
        response_valid=True,
        schema_validation_errors_path=None,
    )
    repo.update_run_metrics(
        run_id=run.run_id,
        timings_json=_dict_or_empty(spec.metrics.get("timings")),
        usage_json=_dict_or_empty(spec.metrics.get("usage")),
        usage_normalized_json=_dict_or_empty(spec.metrics.get("usage_normalized")),
        cost_json=_dict_or_empty(spec.metrics.get("cost")),
    )
    repo.update_run_status(run_id=run.run_id, status="completed")

    run_manifest = {
        "session_id": session_id,
        "run_id": run.run_id,
        "status": "completed",
        "inputs": {
            "provider": spec.provider,
            "model": spec.model,
            "prompt_name": spec.prompt_name,
            "prompt_version": spec.prompt_version,
            "schema_version": spec.schema_version,
            "ocr_params": {
                "model": "mistral-ocr-latest",
                "table_format": "none",
                "include_image_base64": False,
            },
            "llm_params": {
                "openai_reasoning_effort": "low",
                "gemini_thinking_level": "low",
            },
        },
        "stages": {
            "init": {"status": "completed", "updated_at": spec.created_at},
            "ocr": {"status": "completed", "updated_at": spec.created_at},
            "llm": {"status": "completed", "updated_at": spec.created_at},
            "finalize": {"status": "completed", "updated_at": spec.created_at},
        },
        "artifacts": {
            "root": str(run_root.resolve()),
            "run_log": str(run_log_path.resolve()),
            "documents": [
                {
                    "doc_id": DEFAULT_DOC_ID,
                    "ocr_status": "ok",
                    "pages_count": 1,
                    "combined_markdown_path": str(
                        document_artifacts.combined_markdown_path.resolve()
                    ),
                    "ocr_artifacts_path": str(document_artifacts.ocr_dir.resolve()),
                    "ocr_error": None,
                }
            ],
            "llm": {
                "request_path": str(llm_artifacts.request_path.resolve()),
                "response_raw_path": str(llm_artifacts.response_raw_path.resolve()),
                "response_parsed_path": str(
                    llm_artifacts.response_parsed_path.resolve()
                ),
                "validation_path": str(llm_artifacts.validation_path.resolve()),
            },
        },
        "metrics": {
            "timings": _dict_or_empty(spec.metrics.get("timings")),
            "usage": _dict_or_empty(spec.metrics.get("usage")),
            "usage_normalized": _dict_or_empty(spec.metrics.get("usage_normalized")),
            "cost": _dict_or_empty(spec.metrics.get("cost")),
        },
        "validation": {"valid": True, "errors": []},
        "error_code": None,
        "error_message": None,
        "created_at": spec.created_at,
        "updated_at": spec.created_at,
    }
    (run_root / "run.json").write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "run_id": run.run_id,
        "session_id": session_id,
        "provider": spec.provider,
        "model": spec.model,
        "prompt_version": spec.prompt_version,
        "artifacts_root_path": str(run_root.resolve()),
        "run_manifest_path": str((run_root / "run.json").resolve()),
        "created_at": spec.created_at,
    }


def _seed_specs() -> list[SeedRunSpec]:
    payload_a = {
        "checklist": [
            _checklist_item(
                item_id="KAUCJA_PAYMENT_PROOF",
                importance="critical",
                status="missing",
                confidence="low",
                ask="Upload transfer confirmation for deposit payment.",
                quote="No payment confirmation was found in the provided document.",
            ),
            _checklist_item(
                item_id="CONTRACT_EXISTS",
                importance="critical",
                status="confirmed",
                confidence="high",
                ask="",
                quote="Signed lease contract is present and legible.",
            ),
        ],
        "critical_gaps_summary": ["Deposit transfer proof is missing."],
        "next_questions_to_user": ["Please upload deposit payment confirmation."],
    }
    payload_b = {
        "checklist": [
            _checklist_item(
                item_id="KAUCJA_PAYMENT_PROOF",
                importance="critical",
                status="confirmed",
                confidence="high",
                ask="",
                quote="Bank transfer confirmation explicitly references kaucja payment.",
            ),
            _checklist_item(
                item_id="CONTRACT_EXISTS",
                importance="critical",
                status="confirmed",
                confidence="high",
                ask="",
                quote="Signed lease contract is present and legible.",
            ),
        ],
        "critical_gaps_summary": [],
        "next_questions_to_user": [
            "Do you want to include utility invoices as evidence?"
        ],
    }

    return [
        SeedRunSpec(
            run_id="e2e-run-a",
            created_at="2026-02-20T10:00:00+00:00",
            provider="openai",
            model="gpt-5.1",
            prompt_version="v001",
            prompt_name="kaucja_gap_analysis",
            schema_version="v001",
            parsed_payload=payload_a,
            metrics={
                "timings": {"t_total_ms": 1650.0},
                "usage": {"input_tokens": 620, "output_tokens": 210},
                "usage_normalized": {"total_tokens": 830},
                "cost": {"total_cost_usd": 0.19},
            },
            log_lines=[
                "seed run: init completed",
                "seed run: ocr completed",
                "seed run: llm completed",
                "seed run: finalize completed",
            ],
            combined_markdown="# Lease Agreement\n\nDeposit clause found, payment proof missing.",
        ),
        SeedRunSpec(
            run_id="e2e-run-b",
            created_at="2026-02-21T10:00:00+00:00",
            provider="google",
            model="gemini-3.1-pro-preview",
            prompt_version="v002",
            prompt_name="kaucja_gap_analysis",
            schema_version="v002",
            parsed_payload=payload_b,
            metrics={
                "timings": {"t_total_ms": 1430.0},
                "usage": {"input_tokens": 590, "output_tokens": 180},
                "usage_normalized": {"total_tokens": 770},
                "cost": {"total_cost_usd": 0.16},
            },
            log_lines=[
                "seed run: init completed",
                "seed run: ocr completed",
                "seed run: llm completed",
                "seed run: finalize completed",
            ],
            combined_markdown="# Lease Agreement\n\nDeposit clause found with payment evidence.",
        ),
    ]


def _checklist_item(
    *,
    item_id: str,
    importance: str,
    status: str,
    confidence: str,
    ask: str,
    quote: str,
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "importance": importance,
        "status": status,
        "confidence": confidence,
        "what_it_supports": "Deposit settlement evidence",
        "missing_what_exactly": "" if status == "confirmed" else "Payment confirmation",
        "request_from_user": {
            "type": "upload_document" if ask else "none",
            "ask": ask,
            "examples": ["bank transfer confirmation"] if ask else [],
        },
        "findings": [
            {
                "doc_id": DEFAULT_DOC_ID,
                "quote": quote,
                "why_this_quote_matters": "Used for deterministic browser smoke diff.",
            }
        ],
    }


def _dict_or_empty(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return value


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Seed deterministic local data for browser/e2e tests."
    )
    parser.add_argument(
        "--db-path",
        default=str(settings.resolved_data_dir / "e2e" / "kaucja_e2e.sqlite3"),
        help="SQLite path for deterministic e2e seed database.",
    )
    parser.add_argument(
        "--data-dir",
        default=str(settings.resolved_data_dir / "e2e"),
        help="Artifacts data directory for deterministic e2e runs.",
    )
    parser.add_argument(
        "--session-id",
        default=DEFAULT_SESSION_ID,
        help="Session identifier used for seeded runs.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    db_path = Path(args.db_path)
    data_dir = Path(args.data_dir)

    report = seed_e2e_data(
        db_path=db_path,
        data_dir=data_dir,
        session_id=str(args.session_id),
    )
    print(_json_text(report))


if __name__ == "__main__":
    main()
