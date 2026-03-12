from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from app.agentic.case_workspace_store import Scenario2CaseMetadata
from app.agentic.scenario2_runtime_factory import build_scenario2_runtime
from app.config.settings import Settings, get_settings
from app.llm_client.gemini_client import GeminiLLMClient
from app.llm_client.openai_client import OpenAILLMClient
from app.ocr_client.mistral_ocr import MistralOCRClient
from app.ocr_client.types import OCROptions
from app.pipeline.orchestrator import OCRPipelineOrchestrator
from app.pipeline.scenario_router import SCENARIO_2_ID
from app.storage.artifacts import ArtifactsManager
from app.storage.repo import StorageRepo


_DEFAULT_INPUT_TEXT = """\
Najemca żąda zwrotu kaucji po wyprowadzce.
Wynajmujący twierdzi, że zatrzymuje kaucję za uszkodzenia i niedopłaty za media.
Potrzebna jest analiza, czy potrącenie jest zgodne z prawem i jakie dowody są potrzebne.
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a real Scenario 2 OpenAI threading smoke check."
    )
    parser.add_argument(
        "--input-text",
        default=_DEFAULT_INPUT_TEXT,
        help="Plain-text case description that will be OCR-processed via TXT->PDF.",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Optional explicit session id. Defaults to a timestamped smoke id.",
    )
    parser.add_argument(
        "--case-id",
        default=None,
        help="Optional explicit Scenario 2 case workspace id.",
    )
    args = parser.parse_args()

    settings = get_settings()
    orchestrator = _build_orchestrator(settings=settings)
    session_id = args.session_id or _default_session_id()
    case_id = args.case_id or f"{session_id}-case"

    with TemporaryDirectory(prefix="scenario2-threading-smoke-") as temp_dir:
        input_path = Path(temp_dir) / "scenario2_smoke.txt"
        input_path.write_text(args.input_text, encoding="utf-8")
        result = orchestrator.run_full_pipeline(
            input_files=[input_path],
            session_id=session_id,
            provider=settings.default_provider,
            model=settings.default_model,
            prompt_name=settings.default_prompt_name,
            prompt_version=settings.default_prompt_version,
            scenario_id=SCENARIO_2_ID,
            ocr_options=OCROptions(
                model=settings.default_ocr_model,
                table_format=settings.default_ocr_table_format,
                include_image_base64=settings.default_ocr_include_image_base64,
            ),
            scenario2_case_workspace_id=case_id,
            scenario2_case_metadata=Scenario2CaseMetadata(),
        )

    summary = _build_summary(
        settings=settings,
        session_id=result.session_id,
        run_id=result.run_id,
        run_status=result.run_status,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    error_text = " ".join(
        [
            str(summary.get("error_code") or ""),
            str(summary.get("error_message") or ""),
            str(summary.get("trace_stage_error") or ""),
        ]
    )
    if "No tool call found for function call output with call_id" in error_text:
        return 2
    if "Unknown parameter:" in error_text:
        return 3
    if bool(summary.get("threading_blocker_cleared")):
        return 0
    if str(summary.get("run_status")) != "completed":
        return 1
    return 0


def _build_orchestrator(*, settings: Settings) -> OCRPipelineOrchestrator:
    repo = StorageRepo(db_path=str(settings.resolved_sqlite_path))
    artifacts = ArtifactsManager(data_dir=settings.resolved_data_dir)
    scenario2_runtime = build_scenario2_runtime(settings=settings)

    return OCRPipelineOrchestrator(
        repo=repo,
        artifacts_manager=artifacts,
        ocr_client=MistralOCRClient(api_key=settings.mistral_api_key),
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


def _default_session_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"scenario2-threading-smoke-{stamp}"


def _build_summary(
    *,
    settings: Settings,
    session_id: str,
    run_id: str,
    run_status: str,
) -> dict[str, object]:
    run_dir = settings.resolved_data_dir / "sessions" / session_id / "runs" / run_id
    manifest_path = run_dir / "run.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    trace_path = Path(
        manifest.get("artifacts", {}).get("llm", {}).get("trace_path")
        or run_dir / "llm" / "scenario2_trace.json"
    )
    trace_payload = (
        json.loads(trace_path.read_text(encoding="utf-8"))
        if trace_path.is_file()
        else {}
    )
    diagnostics = trace_payload.get("diagnostics", {})
    tool_trace = trace_payload.get("tool_trace", [])
    return {
        "session_id": session_id,
        "run_id": run_id,
        "run_status": run_status,
        "scenario_id": manifest.get("inputs", {}).get("scenario_id"),
        "case_workspace_id": manifest.get("inputs", {}).get("case_workspace_id"),
        "review_status": manifest.get("review_status"),
        "verifier_gate_status": manifest.get("verifier_gate_status"),
        "error_code": manifest.get("error_code"),
        "error_message": manifest.get("error_message"),
        "tool_names": [entry.get("tool") for entry in tool_trace],
        "fetch_fragments_alias_normalized": _fetch_fragments_alias_normalized(
            tool_trace
        ),
        "fetch_fragments_called": diagnostics.get("fetch_fragments_called"),
        "fetch_fragments_returned_usable_fragments": diagnostics.get(
            "fetch_fragments_returned_usable_fragments"
        ),
        "tool_round_count": trace_payload.get("tool_round_count"),
        "final_text_present": bool(str(trace_payload.get("final_text") or "").strip()),
        "threading_trace_rounds": len(diagnostics.get("openai_threading_trace", [])),
        "last_previous_response_id": _last_previous_response_id(
            diagnostics.get("openai_threading_trace")
        ),
        "threading_blocker_cleared": _threading_blocker_cleared(
            tool_names=[entry.get("tool") for entry in tool_trace],
            diagnostics=diagnostics,
            final_text=str(trace_payload.get("final_text") or ""),
        ),
        "trace_stage_error": diagnostics.get("error_message"),
    }


def _last_previous_response_id(value: object) -> str | None:
    if not isinstance(value, list) or not value:
        return None
    last_entry = value[-1]
    if not isinstance(last_entry, dict):
        return None
    result = last_entry.get("previous_response_id")
    if result is None:
        return None
    text = str(result).strip()
    return text or None


def _threading_blocker_cleared(
    *,
    tool_names: list[object],
    diagnostics: dict[str, object],
    final_text: str,
) -> bool:
    if any(str(tool_name) == "fetch_fragments" for tool_name in tool_names):
        return True
    if bool(str(final_text).strip()):
        return True
    trace = diagnostics.get("openai_threading_trace")
    return isinstance(trace, list) and len(trace) >= 2


def _fetch_fragments_alias_normalized(tool_trace: object) -> bool:
    if not isinstance(tool_trace, list):
        return False
    for entry in tool_trace:
        if not isinstance(entry, dict):
            continue
        if entry.get("tool") != "fetch_fragments":
            continue
        aliases = entry.get("request_aliases_applied")
        if not isinstance(aliases, dict):
            continue
        if aliases.get("machine_ref") == "refs":
            return True
        if aliases.get("references") == "refs":
            return True
        if aliases.get("machine_refs") == "refs":
            return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
