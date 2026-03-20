"""Deterministic markdown scanner for the NormaDepo pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Protocol


@dataclass(frozen=True, slots=True)
class DiscoveredDocument:
    absolute_path: Path
    relative_path: PurePosixPath
    file_name: str
    size_bytes: int
    modified_at: datetime
    sha256_hex: str
    top_level_dir: str


class Scanner(Protocol):
    def scan(
        self,
        input_root: Path,
        *,
        glob_pattern: str = "**/*.md",
        ignore_hidden: bool = True,
        only_doc_id: str | None = None,
        from_relative_path: str | None = None,
        limit: int | None = None,
    ) -> list[DiscoveredDocument]:
        """Return documents in deterministic order."""


class DocumentScanner:
    def scan(
        self,
        input_root: Path,
        *,
        glob_pattern: str = "**/*.md",
        ignore_hidden: bool = True,
        only_doc_id: str | None = None,
        from_relative_path: str | None = None,
        limit: int | None = None,
    ) -> list[DiscoveredDocument]:
        input_root = input_root.expanduser().resolve()
        requested_doc_id = (
            PurePosixPath(only_doc_id).as_posix() if only_doc_id else None
        )
        start_relative_path = (
            PurePosixPath(from_relative_path).as_posix()
            if from_relative_path
            else None
        )

        relative_paths = [
            PurePosixPath(path.relative_to(input_root).as_posix())
            for path in input_root.glob(glob_pattern)
            if path.is_file()
            and (not ignore_hidden or _is_allowed_relative_path(path.relative_to(input_root)))
        ]
        relative_paths.sort(key=lambda path: path.as_posix())

        if requested_doc_id is not None:
            relative_paths = [
                path for path in relative_paths if path.as_posix() == requested_doc_id
            ]
        elif start_relative_path is not None:
            relative_paths = [
                path
                for path in relative_paths
                if path.as_posix() >= start_relative_path
            ]
        if limit is not None:
            relative_paths = relative_paths[:limit]

        return [
            _build_discovered_document(input_root=input_root, relative_path=relative_path)
            for relative_path in relative_paths
        ]


def _build_discovered_document(
    *,
    input_root: Path,
    relative_path: PurePosixPath,
) -> DiscoveredDocument:
    absolute_path = (input_root / Path(relative_path)).resolve()
    stat_result = absolute_path.stat()
    top_level_dir = relative_path.parts[0] if len(relative_path.parts) > 1 else ""
    return DiscoveredDocument(
        absolute_path=absolute_path,
        relative_path=relative_path,
        file_name=absolute_path.name,
        size_bytes=stat_result.st_size,
        modified_at=datetime.fromtimestamp(
            stat_result.st_mtime,
            tz=timezone.utc,
        ),
        sha256_hex=_compute_sha256(absolute_path),
        top_level_dir=top_level_dir,
    )


def _compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _is_allowed_relative_path(relative_path: Path) -> bool:
    parts = relative_path.parts
    if any(part.startswith(".") for part in parts):
        return False

    file_name = relative_path.name
    if file_name in {".DS_Store"}:
        return False
    if file_name.startswith("~$"):
        return False
    if file_name.endswith(("~", ".tmp", ".swp", ".swo")):
        return False

    return True
