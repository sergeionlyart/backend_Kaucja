import json
import logging
import io
from legal_ingest.logging import setup_logging, set_log_context, clear_log_context


def test_json_formatter_extra_fields():
    log_stream = io.StringIO()
    logger = setup_logging(level=logging.INFO)
    logger.handlers[0].stream = log_stream

    set_log_context(run_id="test-run", doc_uid="test-doc")

    # Test fallback to context
    logger.info("Test message 1", extra={"stage": "init"})

    # Test override in extra
    logger.info("Test message 2", extra={"stage": "custom_stage", "duration_ms": 150})

    # Test clearing context
    clear_log_context(["doc_uid"])
    logger.info("Test message 3")

    log_lines = log_stream.getvalue().strip().split("\n")

    assert len(log_lines) == 3

    d1 = json.loads(log_lines[0])
    assert d1["msg"] == "Test message 1"
    assert d1["run_id"] == "test-run"
    assert d1["doc_uid"] == "test-doc"
    assert d1["stage"] == "init"
    assert "duration_ms" not in d1

    d2 = json.loads(log_lines[1])
    assert d2["msg"] == "Test message 2"
    assert d2["doc_uid"] == "test-doc"
    assert d2["stage"] == "custom_stage"
    assert d2["duration_ms"] == 150

    d3 = json.loads(log_lines[2])
    assert d3["msg"] == "Test message 3"
    assert "doc_uid" not in d3
    assert d3["run_id"] == "test-run"
