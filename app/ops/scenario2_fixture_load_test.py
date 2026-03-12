from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from app.config.settings import Settings, get_settings
from app.ops.scenario2_openai_threading_smoke import _build_orchestrator
from app.ocr_client.types import OCROptions
from app.pipeline.scenario_router import SCENARIO_2_ID


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run repeated Scenario 2 load tests on a fixture batch."
    )
    parser.add_argument(
        "--fixtures-dir",
        default="fixtures/1",
        help="Directory with fixture documents for the Scenario 2 batch run.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of batch runs to execute (max 5).",
    )
    parser.add_argument(
        "--session-prefix",
        default=None,
        help="Optional session prefix. Defaults to a timestamped load-test id.",
    )
    args = parser.parse_args()

    if args.iterations < 1 or args.iterations > 5:
        raise SystemExit("--iterations must be between 1 and 5")

    settings = get_settings()
    fixtures_dir = settings.project_root / args.fixtures_dir
    input_files = _collect_input_files(fixtures_dir)
    orchestrator = _build_orchestrator(settings=settings)
    session_prefix = args.session_prefix or _default_session_prefix()

    iteration_log: list[dict[str, object]] = []
    stable_successes = 0
    for iteration in range(1, args.iterations + 1):
        session_id = f"{session_prefix}-iter{iteration}"
        case_id = f"{session_id}-case"
        result = orchestrator.run_full_pipeline(
            input_files=input_files,
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
        )
        summary = _build_iteration_summary(
            settings=settings,
            session_id=result.session_id,
            run_id=result.run_id,
            iteration=iteration,
            input_files=input_files,
        )
        iteration_log.append(summary)
        if summary["run_status"] == "completed":
            stable_successes += 1
            continue
        break

    report = {
        "fixtures_dir": str(fixtures_dir),
        "input_files": [str(path) for path in input_files],
        "iterations_requested": args.iterations,
        "iterations_executed": len(iteration_log),
        "stable_successes_in_row": stable_successes,
        "all_completed": stable_successes == args.iterations,
        "iteration_log": iteration_log,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["all_completed"] else 1


def _collect_input_files(fixtures_dir: Path) -> list[Path]:
    if not fixtures_dir.is_dir():
        raise FileNotFoundError(f"Fixture directory not found: {fixtures_dir}")
    files = sorted(path for path in fixtures_dir.iterdir() if path.is_file())
    if not files:
        raise RuntimeError(f"No fixture files found: {fixtures_dir}")
    return files


def _default_session_prefix() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"scenario2-fixture-load-{stamp}"


def _build_iteration_summary(
    *,
    settings: Settings,
    session_id: str,
    run_id: str,
    iteration: int,
    input_files: list[Path],
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
    metrics = manifest.get("metrics", {})
    timings = metrics.get("timings", {}) if isinstance(metrics, dict) else {}
    tool_trace = trace_payload.get("tool_trace", [])
    return {
        "iteration": iteration,
        "session_id": session_id,
        "run_id": run_id,
        "run_status": manifest.get("status"),
        "error_code": manifest.get("error_code"),
        "error_message": manifest.get("error_message"),
        "tool_names": [
            entry.get("tool") for entry in tool_trace if isinstance(entry, dict)
        ],
        "tool_round_count": trace_payload.get("tool_round_count"),
        "fetch_fragments_called": diagnostics.get("fetch_fragments_called"),
        "usable_fragments": diagnostics.get(
            "fetch_fragments_returned_usable_fragments"
        ),
        "final_text_present": bool(str(trace_payload.get("final_text") or "").strip()),
        "review_status": manifest.get("review_status"),
        "verifier_gate_status": manifest.get("verifier_gate_status"),
        "t_ocr_total_ms": timings.get("t_ocr_total_ms"),
        "t_total_ms": timings.get("t_total_ms"),
        "trace_path": str(trace_path.resolve()) if trace_path.is_file() else None,
        "input_files": [path.name for path in input_files],
    }


if __name__ == "__main__":
    raise SystemExit(main())
