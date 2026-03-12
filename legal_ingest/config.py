from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_COLLECTIONS = (
    "documents",
    "pages",
    "nodes",
    "citations",
    "document_sources",
    "ingest_runs",
)
DEFAULT_ARTIFACT_ROOT = Path("artifacts/legal_ingest")
DEFAULT_MIGRATION_MAP_PATH = Path("legal_ingest/data/migration_map_v3_1.json")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def utc_timestamp_token() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def _default_mongo_uri() -> str:
    return os.environ.get("LEGAL_INGEST_MONGO_URI", "mongodb://localhost:27017")


def _default_mongo_db() -> str:
    return os.environ.get("LEGAL_INGEST_MONGO_DB", "legal_rag_runtime")


def _default_artifact_root() -> Path:
    value = os.environ.get("LEGAL_INGEST_ARTIFACT_DIR")
    if value:
        return Path(value)
    return DEFAULT_ARTIFACT_ROOT


@dataclass(frozen=True, slots=True)
class MongoConfig:
    uri: str = field(default_factory=_default_mongo_uri)
    db_name: str = field(default_factory=_default_mongo_db)


@dataclass(frozen=True, slots=True)
class ArtifactConfig:
    root_dir: Path = field(default_factory=_default_artifact_root)

    @property
    def resolved_root_dir(self) -> Path:
        return resolve_path(self.root_dir)

    def backup_dir(self, timestamp: str) -> Path:
        return self.resolved_root_dir / "backups" / timestamp

    def audit_dir(self, timestamp: str) -> Path:
        return self.resolved_root_dir / "audits" / timestamp

    def report_dir(self, command_name: str, timestamp: str) -> Path:
        return self.resolved_root_dir / command_name / timestamp

    def corpus_docs_dir(self) -> Path:
        return self.resolved_root_dir / "corpus" / "docs"
