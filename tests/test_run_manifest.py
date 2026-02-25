from __future__ import annotations

from pathlib import Path

from app.storage.run_manifest import (
    get_manifest_path,
    init_run_manifest,
    read_run_manifest,
    update_run_manifest,
)


def test_run_manifest_init_and_update(tmp_path: Path) -> None:
    run_root = tmp_path / "data" / "sessions" / "s-1" / "runs" / "r-1"

    path = init_run_manifest(
        artifacts_root_path=run_root,
        session_id="s-1",
        run_id="r-1",
        inputs={
            "provider": "openai",
            "model": "gpt-5.1",
            "prompt_name": "kaucja_gap_analysis",
            "prompt_version": "v001",
            "schema_version": "v001",
            "ocr_params": {"model": "mistral-ocr-latest"},
            "llm_params": {"openai_reasoning_effort": "auto"},
        },
        artifacts={
            "root": str(run_root),
            "run_log": str(run_root / "logs" / "run.log"),
            "documents": [],
            "llm": {},
        },
        status="running",
    )

    assert path == get_manifest_path(run_root)
    assert path.is_file()

    initial = read_run_manifest(artifacts_root_path=run_root)
    assert initial["session_id"] == "s-1"
    assert initial["run_id"] == "r-1"
    assert initial["stages"]["init"]["status"] == "completed"
    assert initial["stages"]["ocr"]["status"] == "pending"

    update_run_manifest(
        artifacts_root_path=run_root,
        updates={
            "status": "completed",
            "stages": {
                "ocr": {"status": "completed"},
                "llm": {"status": "completed"},
                "finalize": {"status": "completed"},
            },
            "metrics": {
                "timings": {"t_total_ms": 100.0},
                "usage": {"input_tokens": 10},
                "usage_normalized": {"total_tokens": 15},
                "cost": {"total_cost_usd": 0.001},
            },
            "validation": {"valid": True, "errors": []},
        },
    )

    updated = read_run_manifest(artifacts_root_path=run_root)
    assert updated["status"] == "completed"
    assert updated["stages"]["ocr"]["status"] == "completed"
    assert updated["stages"]["llm"]["status"] == "completed"
    assert updated["stages"]["finalize"]["status"] == "completed"
    assert updated["metrics"]["timings"]["t_total_ms"] == 100.0
    assert updated["validation"]["valid"] is True
    assert updated["updated_at"] != updated["created_at"]
