from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    openai_reasoning_effort TEXT,
    gemini_thinking_level TEXT,
    prompt_name TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('created', 'running', 'completed', 'failed')),
    error_code TEXT,
    error_message TEXT,
    timings_json TEXT NOT NULL DEFAULT '{}',
    usage_json TEXT NOT NULL DEFAULT '{}',
    usage_normalized_json TEXT NOT NULL DEFAULT '{}',
    cost_json TEXT NOT NULL DEFAULT '{}',
    artifacts_root_path TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    original_mime TEXT,
    original_path TEXT NOT NULL,
    ocr_status TEXT NOT NULL CHECK (ocr_status IN ('pending', 'ok', 'failed')),
    ocr_model TEXT,
    pages_count INTEGER,
    ocr_artifacts_path TEXT,
    ocr_error TEXT,
    FOREIGN KEY (run_id) REFERENCES runs (run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS llm_outputs (
    run_id TEXT PRIMARY KEY,
    response_json_path TEXT NOT NULL,
    response_valid INTEGER NOT NULL CHECK (response_valid IN (0, 1)),
    schema_validation_errors_path TEXT,
    FOREIGN KEY (run_id) REFERENCES runs (run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_runs_session_id ON runs (session_id);
CREATE INDEX IF NOT EXISTS idx_documents_run_id ON documents (run_id);
"""


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


@contextmanager
def connection(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
