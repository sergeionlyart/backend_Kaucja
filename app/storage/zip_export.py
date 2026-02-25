from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

_BUNDLE_MANIFEST_FILE = "bundle_manifest.json"
_MANIFEST_SIGNATURE_ALGORITHM = "hmac-sha256"


class ZipExportError(RuntimeError):
    """Raised when run bundle export cannot be completed safely."""


def export_run_bundle(
    *,
    artifacts_root_path: Path | str,
    output_dir: Path | str | None = None,
    signing_key: str | None = None,
) -> Path:
    root = Path(artifacts_root_path)
    if not root.exists():
        raise FileNotFoundError(f"Artifacts root not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Artifacts root is not a directory: {root}")

    resolved_root = root.resolve()
    run_id = resolved_root.name
    destination_dir = (
        Path(output_dir) if output_dir is not None else resolved_root.parent
    )
    destination_dir.mkdir(parents=True, exist_ok=True)

    zip_path = destination_dir / f"{run_id}_bundle.zip"
    file_paths = _collect_artifact_files(resolved_root)
    archive_files = _collect_archive_files(resolved_root, file_paths)
    session_id, manifest_run_id = _resolve_bundle_identifiers(resolved_root)
    manifest_payload = _build_bundle_manifest(
        run_id=manifest_run_id,
        session_id=session_id,
        archive_files=archive_files,
        signing_key=signing_key,
    )
    manifest_bytes = _json_dumps_bytes(manifest_payload)
    archive_entries = [
        *archive_files,
        (_BUNDLE_MANIFEST_FILE, manifest_bytes),
    ]

    with ZipFile(zip_path, mode="w") as archive:
        for relative_path, data in sorted(archive_entries, key=lambda item: item[0]):
            zip_info = ZipInfo(filename=relative_path)
            zip_info.date_time = (1980, 1, 1, 0, 0, 0)
            zip_info.compress_type = ZIP_DEFLATED
            archive.writestr(zip_info, data)

    return zip_path


def _collect_archive_files(
    root_path: Path,
    file_paths: list[Path],
) -> list[tuple[str, bytes]]:
    archive_files: list[tuple[str, bytes]] = []
    for file_path in file_paths:
        relative_path = _safe_relative_path(
            base_path=root_path,
            target_path=file_path,
        )
        archive_files.append((relative_path.as_posix(), file_path.read_bytes()))
    return archive_files


def _collect_artifact_files(root_path: Path) -> list[Path]:
    if root_path.is_symlink():
        raise ZipExportError(f"Artifacts root must not be a symlink: {root_path}")

    files: list[Path] = []
    for candidate in sorted(root_path.rglob("*"), key=lambda item: item.as_posix()):
        if not candidate.is_file() and not candidate.is_symlink():
            continue

        if candidate.is_symlink():
            raise ZipExportError(f"Refusing to export symlinked path: {candidate}")

        resolved_candidate = candidate.resolve()
        _safe_relative_path(base_path=root_path, target_path=resolved_candidate)
        files.append(resolved_candidate)

    if not files:
        raise ZipExportError(f"Artifacts root contains no files to export: {root_path}")

    return files


def _safe_relative_path(*, base_path: Path, target_path: Path) -> Path:
    resolved_base = base_path.resolve()
    resolved_target = target_path.resolve()
    try:
        relative_path = resolved_target.relative_to(resolved_base)
    except ValueError as error:
        raise ZipExportError(
            f"Path traversal attempt detected: {resolved_target}"
        ) from error

    if ".." in relative_path.parts:
        raise ZipExportError(f"Path traversal attempt detected: {resolved_target}")
    return relative_path


def _resolve_bundle_identifiers(root_path: Path) -> tuple[str, str]:
    run_id = root_path.name
    session_id = "unknown"

    run_manifest_path = root_path / "run.json"
    if run_manifest_path.exists():
        try:
            payload = json.loads(run_manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}

        if isinstance(payload, dict):
            payload_session_id = str(payload.get("session_id") or "").strip()
            payload_run_id = str(payload.get("run_id") or "").strip()
            if payload_session_id:
                session_id = payload_session_id
            if payload_run_id:
                run_id = payload_run_id

    if session_id == "unknown":
        path_parts = root_path.parts
        if len(path_parts) >= 3 and path_parts[-2] == "runs":
            session_id = path_parts[-3]

    return session_id, run_id


def _build_bundle_manifest(
    *,
    run_id: str,
    session_id: str,
    archive_files: list[tuple[str, bytes]],
    signing_key: str | None,
) -> dict[str, Any]:
    files_payload: list[dict[str, Any]] = []
    for relative_path, data in sorted(archive_files, key=lambda item: item[0]):
        files_payload.append(
            {
                "relative_path": relative_path,
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )

    manifest_payload: dict[str, Any] = {
        "version": "v1",
        "run_id": run_id,
        "session_id": session_id,
        "files": files_payload,
    }
    normalized_key = _normalize_signing_key(signing_key)
    if normalized_key is not None:
        signature_value = _compute_manifest_signature(
            manifest_payload=manifest_payload,
            signing_key=normalized_key,
        )
        manifest_payload["signature"] = {
            "algorithm": _MANIFEST_SIGNATURE_ALGORITHM,
            "hmac_sha256": signature_value,
        }
    return manifest_payload


def _json_dumps_bytes(payload: dict[str, Any]) -> bytes:
    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return f"{text}\n".encode("utf-8")


def _canonical_manifest_bytes(manifest_payload: dict[str, Any]) -> bytes:
    canonical_json = json.dumps(
        manifest_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return canonical_json.encode("utf-8")


def _compute_manifest_signature(
    *,
    manifest_payload: dict[str, Any],
    signing_key: str,
) -> str:
    message = _canonical_manifest_bytes(manifest_payload)
    return hmac.new(
        signing_key.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()


def _normalize_signing_key(signing_key: str | None) -> str | None:
    if signing_key is None:
        return None
    normalized = signing_key.strip()
    if not normalized:
        return None
    return normalized
