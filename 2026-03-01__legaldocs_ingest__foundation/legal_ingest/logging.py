import logging
import json
import sys
from datetime import datetime
from threading import local

_log_ctx = local()


def set_log_context(**kwargs):
    for k, v in kwargs.items():
        setattr(_log_ctx, k, v)


def get_log_context() -> dict:
    return {k: v for k, v in _log_ctx.__dict__.items() if not k.startswith("_")}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ctx = get_log_context()
        data = {
            "ts": datetime.utcfromtimestamp(record.created).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "level": record.levelname,
            "run_id": ctx.get("run_id"),
            "source_id": ctx.get("source_id"),
            "doc_uid": ctx.get("doc_uid"),
            "stage": ctx.get("stage"),
            "msg": record.getMessage(),
        }

        if hasattr(record, "duration_ms"):
            data["duration_ms"] = record.duration_ms
        if hasattr(record, "metrics"):
            data["metrics"] = record.metrics

        # Clean nulls
        data = {k: v for k, v in data.items() if v is not None}
        return json.dumps(data)


def setup_logging(level=logging.INFO, log_file: str = None) -> logging.Logger:
    logger = logging.getLogger("legal_ingest")
    logger.setLevel(level)
    logger.handlers.clear()

    formatter = JsonFormatter()

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
