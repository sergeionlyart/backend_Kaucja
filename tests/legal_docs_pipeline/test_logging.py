from __future__ import annotations

import json

from legal_docs_pipeline.logging import JsonlPipelineLogger, PipelineLogEvent


def test_jsonl_logger_respects_minimum_log_level(tmp_path) -> None:
    logger = JsonlPipelineLogger(
        run_id="run-1",
        log_dir=tmp_path,
        log_level="WARNING",
    )

    logger.log(
        PipelineLogEvent(
            run_id="run-1",
            stage="run",
            event="started",
            level="info",
            message="should be filtered",
        )
    )
    logger.log(
        PipelineLogEvent(
            run_id="run-1",
            stage="run",
            event="failed",
            level="error",
            message="should stay",
        )
    )

    rows = [
        json.loads(line)
        for line in logger.log_path.read_text(encoding="utf-8").splitlines()
    ]

    assert len(rows) == 1
    assert rows[0]["event"] == "failed"
