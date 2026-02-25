from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import mimetypes
import shutil
import tempfile
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import BadZipFile, ZipFile, ZipInfo

from app.storage.artifacts import ArtifactsManager
from app.storage.db import connection
from app.storage.models import RestoreRunResult
from app.storage.repo import StorageRepo

_REQUIRED_MANIFEST_FILE = "run.json"
_BUNDLE_MANIFEST_FILE = "bundle_manifest.json"
_MANIFEST_SIGNATURE_ALGORITHM = "hmac-sha256"
_VALID_RUN_STATUSES = {"created", "running", "completed", "failed"}
_VALID_OCR_STATUSES = {"pending", "ok", "failed"}
_LAYOUT_ROOTS = {"logs", "documents", "llm"}
_ZIP_BOMB_DEFAULT_MAX_ENTRIES = 1_000
_ZIP_BOMB_DEFAULT_MAX_TOTAL_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
_ZIP_BOMB_DEFAULT_MAX_SINGLE_FILE_BYTES = 128 * 1024 * 1024
_ZIP_BOMB_DEFAULT_MAX_COMPRESSION_RATIO = 200.0


@dataclass(frozen=True, slots=True)
class RestoreSafetyLimits:
    max_entries: int = _ZIP_BOMB_DEFAULT_MAX_ENTRIES
    max_total_uncompressed_bytes: int = _ZIP_BOMB_DEFAULT_MAX_TOTAL_UNCOMPRESSED_BYTES
    max_single_file_bytes: int = _ZIP_BOMB_DEFAULT_MAX_SINGLE_FILE_BYTES
    max_compression_ratio: float = _ZIP_BOMB_DEFAULT_MAX_COMPRESSION_RATIO


@dataclass(frozen=True, slots=True)
class ArchiveInspection:
    file_entries: list[ZipInfo]
    has_bundle_manifest: bool


@dataclass(frozen=True, slots=True)
class BundleVerification:
    files_checked: int
    run_id: str | None
    session_id: str | None
    signed: bool
    signature_verification_status: str
    warnings: list[str]


class RestoreArchiveError(RuntimeError):
    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def restore_run_bundle(
    *,
    repo: StorageRepo,
    zip_path: Path | str,
    data_dir: Path | str | None = None,
    overwrite_existing: bool = False,
    rollback_on_metadata_failure: bool = True,
    safety_limits: RestoreSafetyLimits | None = None,
    signing_key: str | None = None,
    require_signature: bool = False,
    verify_only: bool = False,
) -> RestoreRunResult:
    archive_path = Path(zip_path)
    data_root = (
        Path(data_dir).resolve()
        if data_dir is not None
        else repo.artifacts_manager.data_dir.resolve()
    )
    limits = safety_limits or RestoreSafetyLimits()
    manifest_verification_status = "not_checked"
    signature_verification_status = "not_checked"
    files_checked = 0
    archive_signed = False
    bundle_manifest_run_id: str | None = None
    bundle_manifest_session_id: str | None = None
    normalized_signing_key = _normalize_signing_key(signing_key)

    if not archive_path.exists() or not archive_path.is_file():
        return _restore_error(
            error_code="RESTORE_INVALID_ARCHIVE",
            error_message=f"Archive file not found: {archive_path}",
            manifest_verification_status=manifest_verification_status,
            files_checked=files_checked,
            signature_verification_status=signature_verification_status,
            archive_signed=archive_signed,
            signature_required=require_signature,
            verify_only=verify_only,
        )

    warnings: list[str] = []

    try:
        with ZipFile(archive_path, "r") as archive:
            inspection = _validate_archive_entries(archive, limits=limits)
            file_entries = inspection.file_entries

            if inspection.has_bundle_manifest:
                manifest_verification_status = "verifying"
                signature_verification_status = "verifying"
                bundle_verification = _verify_bundle_manifest(
                    archive=archive,
                    file_entries=file_entries,
                    signing_key=normalized_signing_key,
                    require_signature=require_signature,
                )
                files_checked = bundle_verification.files_checked
                bundle_manifest_run_id = bundle_verification.run_id
                bundle_manifest_session_id = bundle_verification.session_id
                manifest_verification_status = "verified"
                archive_signed = bundle_verification.signed
                signature_verification_status = (
                    bundle_verification.signature_verification_status
                )
                warnings.extend(bundle_verification.warnings)
            else:
                manifest_verification_status = "legacy_missing_manifest"
                signature_verification_status = "missing_manifest_unsigned_legacy"
                warnings.append(
                    "bundle_manifest.json is missing; legacy archive restored "
                    "without integrity verification."
                )
                if require_signature:
                    return _restore_error(
                        error_code="RESTORE_INVALID_SIGNATURE",
                        error_message=(
                            "Archive signature is required in strict mode, but "
                            "bundle_manifest.json is missing."
                        ),
                        manifest_verification_status=manifest_verification_status,
                        files_checked=files_checked,
                        signature_verification_status=signature_verification_status,
                        archive_signed=False,
                        signature_required=require_signature,
                        verify_only=verify_only,
                    )

            manifest = _load_run_manifest_from_archive(
                archive=archive,
                file_entries=file_entries,
            )

            run_id = str(manifest.get("run_id") or "").strip()
            session_id = str(manifest.get("session_id") or "").strip()
            if not run_id or not session_id:
                raise RestoreArchiveError(
                    code="RESTORE_INVALID_ARCHIVE",
                    message="run.json must contain non-empty session_id and run_id.",
                )
            _validate_bundle_identity(
                run_id=run_id,
                session_id=session_id,
                bundle_run_id=bundle_manifest_run_id,
                bundle_session_id=bundle_manifest_session_id,
            )

            target_root = _build_target_root(
                data_root=data_root,
                session_id=session_id,
                run_id=run_id,
            )
            if verify_only:
                return RestoreRunResult(
                    status="verified",
                    run_id=run_id,
                    session_id=session_id,
                    artifacts_root_path=str(target_root),
                    restored_paths=[],
                    warnings=warnings,
                    errors=[],
                    error_code=None,
                    error_message=None,
                    manifest_verification_status=manifest_verification_status,
                    files_checked=files_checked,
                    signature_verification_status=signature_verification_status,
                    archive_signed=archive_signed,
                    signature_required=require_signature,
                    verify_only=True,
                    rollback_attempted=False,
                    rollback_succeeded=None,
                )

            with tempfile.TemporaryDirectory() as temp_dir:
                extract_root = Path(temp_dir) / "run_bundle"
                extract_root.mkdir(parents=True, exist_ok=True)
                _extract_archive_entries(
                    archive=archive,
                    file_entries=file_entries,
                    extract_root=extract_root,
                )
                if target_root.exists():
                    if not overwrite_existing:
                        return _restore_error(
                            error_code="RESTORE_RUN_EXISTS",
                            error_message=f"Run already exists: {run_id}",
                            run_id=run_id,
                            session_id=session_id,
                            artifacts_root_path=str(target_root),
                            manifest_verification_status=manifest_verification_status,
                            files_checked=files_checked,
                            signature_verification_status=signature_verification_status,
                            archive_signed=archive_signed,
                            signature_required=require_signature,
                            verify_only=verify_only,
                        )

                    delete_result = repo.delete_run(run_id)
                    if not delete_result.deleted:
                        return _restore_error(
                            error_code="RESTORE_FS_ERROR",
                            error_message=(
                                "Failed to remove existing run before restore: "
                                f"{delete_result.error_code or ''} "
                                f"{delete_result.error_message or ''}"
                            ).strip(),
                            run_id=run_id,
                            session_id=session_id,
                            artifacts_root_path=str(target_root),
                            manifest_verification_status=manifest_verification_status,
                            files_checked=files_checked,
                            signature_verification_status=signature_verification_status,
                            archive_signed=archive_signed,
                            signature_required=require_signature,
                            verify_only=verify_only,
                        )

                _move_extracted_tree(extract_root=extract_root, target_root=target_root)

                metadata_warnings, metadata_errors = _restore_metadata(
                    repo=repo,
                    manifest=manifest,
                    target_root=target_root,
                    session_id=session_id,
                    run_id=run_id,
                )
                warnings.extend(metadata_warnings)
                restored_paths = _restored_paths(target_root)

                if metadata_errors:
                    rollback_attempted = False
                    rollback_succeeded: bool | None = None
                    if rollback_on_metadata_failure:
                        rollback_attempted = True
                        rollback_succeeded = _rollback_restored_tree(
                            target_root=target_root,
                            data_root=data_root,
                        )
                        if not rollback_succeeded:
                            warnings.append(
                                "Rollback failed after metadata restore failure; "
                                "restored files may remain on disk."
                            )
                    return RestoreRunResult(
                        status="failed",
                        run_id=run_id,
                        session_id=session_id,
                        artifacts_root_path=str(target_root),
                        restored_paths=restored_paths,
                        warnings=warnings,
                        errors=metadata_errors,
                        error_code="RESTORE_DB_ERROR",
                        error_message="Metadata restore failed for one or more entities.",
                        manifest_verification_status=manifest_verification_status,
                        files_checked=files_checked,
                        signature_verification_status=signature_verification_status,
                        archive_signed=archive_signed,
                        signature_required=require_signature,
                        verify_only=False,
                        rollback_attempted=rollback_attempted,
                        rollback_succeeded=rollback_succeeded,
                    )

                return RestoreRunResult(
                    status="restored",
                    run_id=run_id,
                    session_id=session_id,
                    artifacts_root_path=str(target_root),
                    restored_paths=restored_paths,
                    warnings=warnings,
                    errors=[],
                    error_code=None,
                    error_message=None,
                    manifest_verification_status=manifest_verification_status,
                    files_checked=files_checked,
                    signature_verification_status=signature_verification_status,
                    archive_signed=archive_signed,
                    signature_required=require_signature,
                    verify_only=False,
                    rollback_attempted=False,
                    rollback_succeeded=None,
                )

    except RestoreArchiveError as error:
        if manifest_verification_status in {"verifying", "verified"}:
            manifest_verification_status = "failed"
        if signature_verification_status in {"verifying", "verified"}:
            signature_verification_status = "failed"
        return _restore_error(
            error_code=error.code,
            error_message=error.message,
            manifest_verification_status=manifest_verification_status,
            files_checked=files_checked,
            signature_verification_status=signature_verification_status,
            archive_signed=archive_signed,
            signature_required=require_signature,
            verify_only=verify_only,
        )
    except BadZipFile as error:
        return _restore_error(
            error_code="RESTORE_INVALID_ARCHIVE",
            error_message=f"Invalid ZIP archive: {error}",
            manifest_verification_status=manifest_verification_status,
            files_checked=files_checked,
            signature_verification_status=signature_verification_status,
            archive_signed=archive_signed,
            signature_required=require_signature,
            verify_only=verify_only,
        )
    except OSError as error:
        return _restore_error(
            error_code="RESTORE_FS_ERROR",
            error_message=f"Filesystem restore error: {error}",
            manifest_verification_status=manifest_verification_status,
            files_checked=files_checked,
            signature_verification_status=signature_verification_status,
            archive_signed=archive_signed,
            signature_required=require_signature,
            verify_only=verify_only,
        )
    except Exception as error:  # noqa: BLE001
        return _restore_error(
            error_code="RESTORE_DB_ERROR",
            error_message=f"Restore failed: {error.__class__.__name__}: {error}",
            manifest_verification_status=manifest_verification_status,
            files_checked=files_checked,
            signature_verification_status=signature_verification_status,
            archive_signed=archive_signed,
            signature_required=require_signature,
            verify_only=verify_only,
        )


def _validate_archive_entries(
    archive: ZipFile,
    *,
    limits: RestoreSafetyLimits,
) -> ArchiveInspection:
    infos = sorted(archive.infolist(), key=lambda item: item.filename)
    if not infos:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message="Archive is empty.",
        )
    if len(infos) > limits.max_entries:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=(
                f"Archive has too many entries ({len(infos)}), limit is "
                f"{limits.max_entries}."
            ),
        )

    file_entries: list[ZipInfo] = []
    has_manifest = False
    has_bundle_manifest = False
    layout_roots_seen: set[str] = set()
    seen_paths: set[str] = set()
    total_uncompressed_bytes = 0
    for info in infos:
        path = _validate_archive_path(info)
        normalized_name = path.as_posix()
        if normalized_name in seen_paths:
            raise RestoreArchiveError(
                code="RESTORE_INVALID_ARCHIVE",
                message=f"Archive contains duplicated entry path: {info.filename}",
            )
        seen_paths.add(normalized_name)

        if info.is_dir():
            continue
        if path.as_posix() == _REQUIRED_MANIFEST_FILE:
            has_manifest = True
        if path.as_posix() == _BUNDLE_MANIFEST_FILE:
            has_bundle_manifest = True
        if path.parts and path.parts[0] in _LAYOUT_ROOTS:
            layout_roots_seen.add(path.parts[0])
        if _is_symlink_entry(info):
            raise RestoreArchiveError(
                code="RESTORE_INVALID_ARCHIVE",
                message=f"Archive contains symlink entry: {info.filename}",
            )
        _validate_zip_bomb_limits(info=info, limits=limits)
        total_uncompressed_bytes += info.file_size
        file_entries.append(info)

    if total_uncompressed_bytes > limits.max_total_uncompressed_bytes:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=(
                "Archive uncompressed size exceeds allowed limit: "
                f"{total_uncompressed_bytes} > "
                f"{limits.max_total_uncompressed_bytes}."
            ),
        )

    if not has_manifest:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message="Archive does not contain run.json.",
        )
    if not layout_roots_seen:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=(
                "Archive must contain at least one layout root from logs/documents/llm."
            ),
        )

    return ArchiveInspection(
        file_entries=file_entries,
        has_bundle_manifest=has_bundle_manifest,
    )


def _validate_zip_bomb_limits(*, info: ZipInfo, limits: RestoreSafetyLimits) -> None:
    if info.file_size > limits.max_single_file_bytes:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=(
                f"Archive entry '{info.filename}' exceeds max_single_file_bytes: "
                f"{info.file_size} > {limits.max_single_file_bytes}."
            ),
        )

    compressed_size = max(info.compress_size, 1)
    compression_ratio = info.file_size / compressed_size
    if compression_ratio > limits.max_compression_ratio:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=(
                f"Archive entry '{info.filename}' exceeds max_compression_ratio: "
                f"{compression_ratio:.2f} > {limits.max_compression_ratio:.2f}."
            ),
        )


def _validate_archive_path(info: ZipInfo) -> PurePosixPath:
    name = info.filename
    if not name:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message="Archive entry has empty name.",
        )

    path = PurePosixPath(name)
    if path.is_absolute() or path.anchor:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=f"Archive entry uses absolute path: {name}",
        )

    if any(part in {"", ".", ".."} for part in path.parts):
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=f"Archive entry has invalid path: {name}",
        )

    drive_like = path.parts[0]
    if ":" in drive_like:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=f"Archive entry has invalid drive-style path: {name}",
        )

    return path


def _is_symlink_entry(info: ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0o170000
    return mode == 0o120000


def _extract_archive_entries(
    *,
    archive: ZipFile,
    file_entries: list[ZipInfo],
    extract_root: Path,
) -> None:
    resolved_root = extract_root.resolve()

    for info in file_entries:
        relative = _validate_archive_path(info)
        if relative.as_posix() == _BUNDLE_MANIFEST_FILE:
            continue
        target_path = extract_root / relative.as_posix()
        resolved_target = target_path.resolve()
        try:
            resolved_target.relative_to(resolved_root)
        except ValueError as error:
            raise RestoreArchiveError(
                code="RESTORE_INVALID_ARCHIVE",
                message=f"Path traversal detected in archive entry: {info.filename}",
            ) from error

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(info, "r") as source, target_path.open("wb") as destination:
            shutil.copyfileobj(source, destination)


def _verify_bundle_manifest(
    *,
    archive: ZipFile,
    file_entries: list[ZipInfo],
    signing_key: str | None,
    require_signature: bool,
) -> BundleVerification:
    bundle_entry: ZipInfo | None = None
    for info in file_entries:
        if _validate_archive_path(info).as_posix() == _BUNDLE_MANIFEST_FILE:
            bundle_entry = info
            break

    if bundle_entry is None:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message="bundle_manifest.json is not present.",
        )

    try:
        manifest_payload = json.loads(archive.read(bundle_entry).decode("utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=f"Failed to parse bundle_manifest.json: {error}",
        ) from error

    if not isinstance(manifest_payload, dict):
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message="bundle_manifest.json root must be a JSON object.",
        )

    expected_files = manifest_payload.get("files")
    if not isinstance(expected_files, list):
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message="bundle_manifest.json must contain files[] list.",
        )

    expected_map: dict[str, tuple[int, str]] = {}
    for file_item in expected_files:
        if not isinstance(file_item, dict):
            raise RestoreArchiveError(
                code="RESTORE_INVALID_ARCHIVE",
                message="bundle_manifest.json files[] contains non-object item.",
            )
        relative_path = str(file_item.get("relative_path") or "").strip()
        if not relative_path:
            raise RestoreArchiveError(
                code="RESTORE_INVALID_ARCHIVE",
                message="bundle_manifest.json files[] item has empty relative_path.",
            )
        if relative_path == _BUNDLE_MANIFEST_FILE:
            raise RestoreArchiveError(
                code="RESTORE_INVALID_ARCHIVE",
                message="bundle_manifest.json must not include itself in files[] list.",
            )
        try:
            size_bytes = int(file_item.get("size_bytes"))
        except (TypeError, ValueError) as error:
            raise RestoreArchiveError(
                code="RESTORE_INVALID_ARCHIVE",
                message=(
                    "bundle_manifest.json files[] item has invalid size_bytes for "
                    f"path '{relative_path}'."
                ),
            ) from error

        if size_bytes < 0:
            raise RestoreArchiveError(
                code="RESTORE_INVALID_ARCHIVE",
                message=(
                    "bundle_manifest.json files[] item has negative size_bytes for "
                    f"path '{relative_path}'."
                ),
            )

        sha256_hex = str(file_item.get("sha256") or "").strip().lower()
        if len(sha256_hex) != 64 or any(
            char not in "0123456789abcdef" for char in sha256_hex
        ):
            raise RestoreArchiveError(
                code="RESTORE_INVALID_ARCHIVE",
                message=(
                    "bundle_manifest.json files[] item has invalid sha256 for "
                    f"path '{relative_path}'."
                ),
            )

        if relative_path in expected_map:
            raise RestoreArchiveError(
                code="RESTORE_INVALID_ARCHIVE",
                message=f"bundle_manifest.json has duplicate path: {relative_path}",
            )
        expected_map[relative_path] = (size_bytes, sha256_hex)

    actual_map: dict[str, ZipInfo] = {}
    for info in file_entries:
        relative_path = _validate_archive_path(info).as_posix()
        if relative_path == _BUNDLE_MANIFEST_FILE:
            continue
        actual_map[relative_path] = info

    expected_paths = set(expected_map)
    actual_paths = set(actual_map)
    missing_paths = sorted(expected_paths - actual_paths)
    extra_paths = sorted(actual_paths - expected_paths)
    if missing_paths or extra_paths:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=(
                "bundle_manifest.json paths mismatch. "
                f"missing={missing_paths} extra={extra_paths}"
            ),
        )

    for relative_path in sorted(expected_map):
        expected_size, expected_sha = expected_map[relative_path]
        entry = actual_map[relative_path]
        payload = archive.read(entry)

        if len(payload) != expected_size:
            raise RestoreArchiveError(
                code="RESTORE_INVALID_ARCHIVE",
                message=(
                    f"Integrity mismatch for '{relative_path}': "
                    f"size {len(payload)} != {expected_size}."
                ),
            )

        actual_sha = hashlib.sha256(payload).hexdigest()
        if actual_sha != expected_sha:
            raise RestoreArchiveError(
                code="RESTORE_INVALID_ARCHIVE",
                message=(
                    f"Integrity mismatch for '{relative_path}': sha256 does not match."
                ),
            )

    signature_warnings: list[str] = []
    signed, signature_status = _verify_bundle_manifest_signature(
        manifest_payload=manifest_payload,
        signing_key=signing_key,
        require_signature=require_signature,
        warnings=signature_warnings,
    )

    return BundleVerification(
        files_checked=len(expected_map),
        run_id=_to_optional_str(manifest_payload.get("run_id")),
        session_id=_to_optional_str(manifest_payload.get("session_id")),
        signed=signed,
        signature_verification_status=signature_status,
        warnings=signature_warnings,
    )


def _verify_bundle_manifest_signature(
    *,
    manifest_payload: dict[str, Any],
    signing_key: str | None,
    require_signature: bool,
    warnings: list[str],
) -> tuple[bool, str]:
    signature_payload = manifest_payload.get("signature")
    if signature_payload is None:
        if require_signature:
            raise RestoreArchiveError(
                code="RESTORE_INVALID_SIGNATURE",
                message=(
                    "Archive signature is required in strict mode, but "
                    "bundle_manifest.json has no signature section."
                ),
            )
        warnings.append(
            "Archive is unsigned (bundle_manifest.json has no signature). "
            "Strict mode is disabled, continuing restore."
        )
        return False, "unsigned"

    if not isinstance(signature_payload, dict):
        raise RestoreArchiveError(
            code="RESTORE_INVALID_SIGNATURE",
            message="bundle_manifest.json signature must be a JSON object.",
        )

    algorithm = str(signature_payload.get("algorithm") or "").strip().lower()
    provided_signature = str(signature_payload.get("hmac_sha256") or "").strip().lower()
    if algorithm != _MANIFEST_SIGNATURE_ALGORITHM:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_SIGNATURE",
            message=(
                "Unsupported signature algorithm in bundle_manifest.json: "
                f"{algorithm or '<empty>'}."
            ),
        )

    if len(provided_signature) != 64 or any(
        char not in "0123456789abcdef" for char in provided_signature
    ):
        raise RestoreArchiveError(
            code="RESTORE_INVALID_SIGNATURE",
            message="bundle_manifest.json signature value has invalid format.",
        )

    if signing_key is None:
        if require_signature:
            raise RestoreArchiveError(
                code="RESTORE_INVALID_SIGNATURE",
                message=(
                    "Archive signature is present, but verification key is not "
                    "configured."
                ),
            )
        warnings.append(
            "Archive is signed, but BUNDLE_SIGNING_KEY is not configured. "
            "Signature was not verified."
        )
        return True, "signed_unverified_missing_key"

    canonical_payload = _manifest_payload_without_signature(manifest_payload)
    expected_signature = _compute_manifest_signature(
        manifest_payload=canonical_payload,
        signing_key=signing_key,
    )
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise RestoreArchiveError(
            code="RESTORE_INVALID_SIGNATURE",
            message="bundle_manifest.json signature mismatch.",
        )

    return True, "verified"


def _manifest_payload_without_signature(
    manifest_payload: dict[str, Any],
) -> dict[str, Any]:
    filtered_payload: dict[str, Any] = {}
    for key in sorted(manifest_payload):
        if key == "signature":
            continue
        filtered_payload[key] = manifest_payload[key]
    return filtered_payload


def _compute_manifest_signature(
    *,
    manifest_payload: dict[str, Any],
    signing_key: str,
) -> str:
    canonical_json = json.dumps(
        manifest_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hmac.new(
        signing_key.encode("utf-8"),
        canonical_json.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _validate_bundle_identity(
    *,
    run_id: str,
    session_id: str,
    bundle_run_id: str | None,
    bundle_session_id: str | None,
) -> None:
    if bundle_run_id is not None and bundle_run_id != run_id:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=(
                "bundle_manifest.json run_id does not match run.json. "
                f"bundle={bundle_run_id} run={run_id}."
            ),
        )
    if bundle_session_id is not None and bundle_session_id != session_id:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=(
                "bundle_manifest.json session_id does not match run.json. "
                f"bundle={bundle_session_id} run={session_id}."
            ),
        )


def _load_run_manifest_from_archive(
    *,
    archive: ZipFile,
    file_entries: list[ZipInfo],
) -> dict[str, Any]:
    manifest_entry: ZipInfo | None = None
    for info in file_entries:
        if _validate_archive_path(info).as_posix() == _REQUIRED_MANIFEST_FILE:
            manifest_entry = info
            break

    if manifest_entry is None:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message="Archive does not contain run.json.",
        )

    try:
        payload_text = archive.read(manifest_entry).decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=f"Failed to read run.json: {error}",
        ) from error

    return _load_manifest_payload(payload_text)


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload_text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=f"Failed to read run.json: {error}",
        ) from error
    return _load_manifest_payload(payload_text)


def _load_manifest_payload(payload_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as error:
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message=f"Failed to parse run.json: {error}",
        ) from error

    if not isinstance(payload, dict):
        raise RestoreArchiveError(
            code="RESTORE_INVALID_ARCHIVE",
            message="run.json root must be a JSON object.",
        )
    return payload


def _build_target_root(*, data_root: Path, session_id: str, run_id: str) -> Path:
    target_root = (data_root / "sessions" / session_id / "runs" / run_id).resolve()
    try:
        target_root.relative_to(data_root)
    except ValueError as error:
        raise RestoreArchiveError(
            code="RESTORE_FS_ERROR",
            message=f"Resolved target path is outside data root: {target_root}",
        ) from error
    return target_root


def _move_extracted_tree(*, extract_root: Path, target_root: Path) -> None:
    if target_root.exists():
        raise RestoreArchiveError(
            code="RESTORE_RUN_EXISTS",
            message=f"Target run path already exists: {target_root}",
        )

    target_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(extract_root, target_root)


def _restore_metadata(
    *,
    repo: StorageRepo,
    manifest: dict[str, Any],
    target_root: Path,
    session_id: str,
    run_id: str,
) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    inputs = manifest.get("inputs") if isinstance(manifest.get("inputs"), dict) else {}
    metrics = (
        manifest.get("metrics") if isinstance(manifest.get("metrics"), dict) else {}
    )

    provider = str(inputs.get("provider") or "unknown")
    model = str(inputs.get("model") or "unknown")
    prompt_name = str(inputs.get("prompt_name") or "unknown")
    prompt_version = str(inputs.get("prompt_version") or "unknown")
    schema_version = str(inputs.get("schema_version") or prompt_version)

    llm_params = (
        inputs.get("llm_params") if isinstance(inputs.get("llm_params"), dict) else {}
    )
    openai_reasoning_effort = _to_optional_str(
        llm_params.get("openai_reasoning_effort")
    )
    gemini_thinking_level = _to_optional_str(llm_params.get("gemini_thinking_level"))

    status = str(manifest.get("status") or "completed")
    if status not in _VALID_RUN_STATUSES:
        warnings.append(
            f"Invalid run status '{status}' in run.json. Fallback to 'completed'."
        )
        status = "completed"

    created_at = str(manifest.get("created_at") or _utc_now())

    try:
        with connection(repo.db_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sessions (session_id, created_at)
                VALUES (?, ?)
                """,
                (session_id, created_at),
            )

            conn.execute(
                """
                INSERT INTO runs (
                    run_id,
                    session_id,
                    created_at,
                    provider,
                    model,
                    openai_reasoning_effort,
                    gemini_thinking_level,
                    prompt_name,
                    prompt_version,
                    schema_version,
                    status,
                    error_code,
                    error_message,
                    timings_json,
                    usage_json,
                    usage_normalized_json,
                    cost_json,
                    artifacts_root_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    session_id = excluded.session_id,
                    created_at = excluded.created_at,
                    provider = excluded.provider,
                    model = excluded.model,
                    openai_reasoning_effort = excluded.openai_reasoning_effort,
                    gemini_thinking_level = excluded.gemini_thinking_level,
                    prompt_name = excluded.prompt_name,
                    prompt_version = excluded.prompt_version,
                    schema_version = excluded.schema_version,
                    status = excluded.status,
                    error_code = excluded.error_code,
                    error_message = excluded.error_message,
                    timings_json = excluded.timings_json,
                    usage_json = excluded.usage_json,
                    usage_normalized_json = excluded.usage_normalized_json,
                    cost_json = excluded.cost_json,
                    artifacts_root_path = excluded.artifacts_root_path
                """,
                (
                    run_id,
                    session_id,
                    created_at,
                    provider,
                    model,
                    openai_reasoning_effort,
                    gemini_thinking_level,
                    prompt_name,
                    prompt_version,
                    schema_version,
                    status,
                    _to_optional_str(manifest.get("error_code")),
                    _to_optional_str(manifest.get("error_message")),
                    _json_text(metrics.get("timings")),
                    _json_text(metrics.get("usage")),
                    _json_text(metrics.get("usage_normalized")),
                    _json_text(metrics.get("cost")),
                    str(target_root),
                ),
            )

            conn.execute("DELETE FROM documents WHERE run_id = ?", (run_id,))
            for document_payload in _collect_document_payloads(
                target_root=target_root,
                manifest=manifest,
                ocr_model_hint=str(
                    (
                        (inputs.get("ocr_params") or {}).get("model")
                        if isinstance(inputs.get("ocr_params"), dict)
                        else ""
                    )
                    or "mistral-ocr-latest"
                ),
                warnings=warnings,
            ):
                conn.execute(
                    """
                    INSERT INTO documents (
                        run_id,
                        doc_id,
                        original_filename,
                        original_mime,
                        original_path,
                        ocr_status,
                        ocr_model,
                        pages_count,
                        ocr_artifacts_path,
                        ocr_error
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        document_payload["doc_id"],
                        document_payload["original_filename"],
                        document_payload["original_mime"],
                        document_payload["original_path"],
                        document_payload["ocr_status"],
                        document_payload["ocr_model"],
                        document_payload["pages_count"],
                        document_payload["ocr_artifacts_path"],
                        document_payload["ocr_error"],
                    ),
                )

            conn.execute("DELETE FROM llm_outputs WHERE run_id = ?", (run_id,))
            llm_payload, llm_warning = _llm_output_payload(target_root=target_root)
            if llm_warning is not None:
                warnings.append(llm_warning)
            if llm_payload is not None:
                conn.execute(
                    """
                    INSERT INTO llm_outputs (
                        run_id,
                        response_json_path,
                        response_valid,
                        schema_validation_errors_path
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        llm_payload["response_json_path"],
                        1 if llm_payload["response_valid"] else 0,
                        llm_payload["schema_validation_errors_path"],
                    ),
                )
    except Exception as error:  # noqa: BLE001
        errors.append(f"{error.__class__.__name__}: {error}")

    return warnings, errors


def _collect_document_payloads(
    *,
    target_root: Path,
    manifest: dict[str, Any],
    ocr_model_hint: str,
    warnings: list[str],
) -> list[dict[str, Any]]:
    artifacts = (
        manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
    )
    manifest_documents = artifacts.get("documents")

    payloads: list[dict[str, Any]] = []
    if isinstance(manifest_documents, list):
        mapped: dict[str, dict[str, Any]] = {}
        for item in manifest_documents:
            if not isinstance(item, dict):
                continue
            doc_id = str(item.get("doc_id") or "").strip()
            if doc_id:
                mapped[doc_id] = item

        for doc_id in sorted(mapped.keys()):
            payloads.append(
                _build_document_payload(
                    target_root=target_root,
                    doc_id=doc_id,
                    manifest_document=mapped[doc_id],
                    ocr_model_hint=ocr_model_hint,
                    warnings=warnings,
                )
            )
        return payloads

    docs_root = target_root / "documents"
    if not docs_root.exists():
        return payloads

    for doc_dir in sorted(docs_root.iterdir(), key=lambda item: item.name):
        if not doc_dir.is_dir():
            continue
        payloads.append(
            _build_document_payload(
                target_root=target_root,
                doc_id=doc_dir.name,
                manifest_document={},
                ocr_model_hint=ocr_model_hint,
                warnings=warnings,
            )
        )

    return payloads


def _build_document_payload(
    *,
    target_root: Path,
    doc_id: str,
    manifest_document: dict[str, Any],
    ocr_model_hint: str,
    warnings: list[str],
) -> dict[str, Any]:
    document_root = target_root / "documents" / doc_id
    original_dir = document_root / "original"
    ocr_dir = document_root / "ocr"

    original_files = []
    if original_dir.exists():
        original_files = sorted(
            [path for path in original_dir.iterdir() if path.is_file()],
            key=lambda item: item.name,
        )

    if original_files:
        original_file = original_files[0]
        original_filename = original_file.name
        original_path = str(original_file)
        guessed_mime, _ = mimetypes.guess_type(original_file.name)
        original_mime = guessed_mime
    else:
        original_filename = f"{doc_id}.bin"
        original_path = str(original_dir / original_filename)
        original_mime = None
        warnings.append(f"Original file not found for doc_id={doc_id}")

    pages_count = _to_optional_int(manifest_document.get("pages_count"))
    if pages_count is None and (ocr_dir / "pages").exists():
        pages_count = len(
            [path for path in (ocr_dir / "pages").iterdir() if path.suffix == ".md"]
        )

    ocr_status = str(manifest_document.get("ocr_status") or "ok")
    if ocr_status not in _VALID_OCR_STATUSES:
        warnings.append(
            f"Invalid ocr_status '{ocr_status}' for doc_id={doc_id}. Fallback to 'ok'."
        )
        ocr_status = "ok"

    return {
        "doc_id": doc_id,
        "original_filename": original_filename,
        "original_mime": original_mime,
        "original_path": original_path,
        "ocr_status": ocr_status,
        "ocr_model": ocr_model_hint,
        "pages_count": pages_count,
        "ocr_artifacts_path": str(ocr_dir),
        "ocr_error": _to_optional_str(manifest_document.get("ocr_error")),
    }


def _llm_output_payload(
    *,
    target_root: Path,
) -> tuple[dict[str, Any] | None, str | None]:
    parsed_path = target_root / "llm" / "response_parsed.json"
    validation_path = target_root / "llm" / "validation.json"

    if not parsed_path.exists():
        return None, "LLM parsed response file is missing."

    response_valid = False
    schema_errors_path: str | None = str(validation_path)
    if validation_path.exists():
        try:
            payload = json.loads(validation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return (
                {
                    "response_json_path": str(parsed_path),
                    "response_valid": False,
                    "schema_validation_errors_path": str(validation_path),
                },
                "Validation artifact is unreadable; response_valid set to false.",
            )

        if isinstance(payload, dict):
            response_valid = bool(payload.get("valid"))
            schema_errors_path = None if response_valid else str(validation_path)

    return (
        {
            "response_json_path": str(parsed_path),
            "response_valid": response_valid,
            "schema_validation_errors_path": schema_errors_path,
        },
        None,
    )


def _restored_paths(target_root: Path) -> list[str]:
    interesting_paths = [
        target_root,
        target_root / "run.json",
        target_root / "logs" / "run.log",
        target_root / "llm" / "response_parsed.json",
        target_root / "llm" / "validation.json",
    ]

    existing = [str(path) for path in interesting_paths if path.exists()]
    if str(target_root) not in existing:
        existing.insert(0, str(target_root))
    return existing


def _rollback_restored_tree(*, target_root: Path, data_root: Path) -> bool:
    if not target_root.exists():
        return True

    resolved_data_root = data_root.resolve()
    resolved_target = target_root.resolve()
    try:
        resolved_target.relative_to(resolved_data_root)
    except ValueError:
        return False

    try:
        shutil.rmtree(resolved_target)
    except OSError:
        return False
    return True


def _normalize_signing_key(signing_key: str | None) -> str | None:
    if signing_key is None:
        return None
    normalized = signing_key.strip()
    if not normalized:
        return None
    return normalized


def _to_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def _to_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _json_text(value: Any) -> str:
    payload = value if isinstance(value, dict) else {}
    return json.dumps(payload, ensure_ascii=False)


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _restore_error(
    *,
    error_code: str,
    error_message: str,
    run_id: str | None = None,
    session_id: str | None = None,
    artifacts_root_path: str | None = None,
    manifest_verification_status: str,
    files_checked: int,
    signature_verification_status: str,
    archive_signed: bool,
    signature_required: bool,
    verify_only: bool,
) -> RestoreRunResult:
    return RestoreRunResult(
        status="failed",
        run_id=run_id,
        session_id=session_id,
        artifacts_root_path=artifacts_root_path,
        restored_paths=[],
        warnings=[],
        errors=[error_message],
        error_code=error_code,
        error_message=error_message,
        manifest_verification_status=manifest_verification_status,
        files_checked=files_checked,
        signature_verification_status=signature_verification_status,
        archive_signed=archive_signed,
        signature_required=signature_required,
        verify_only=verify_only,
        rollback_attempted=False,
        rollback_succeeded=None,
    )


def main() -> None:
    from app.config.settings import get_settings

    parser = argparse.ArgumentParser(
        description="Restore run artifacts and metadata from a backup ZIP bundle."
    )
    parser.add_argument("--zip-path", required=True, help="Path to backup ZIP file.")
    parser.add_argument(
        "--db-path",
        default="data/kaucja.sqlite3",
        help="Path to SQLite database file.",
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Artifacts data directory.",
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Allow overwrite for already existing run_id.",
    )
    parser.add_argument(
        "--no-rollback-on-metadata-failure",
        action="store_true",
        help=(
            "Disable filesystem rollback when metadata restore fails after files were "
            "copied."
        ),
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help=(
            "Only verify archive safety/integrity/signature and print report "
            "without filesystem or DB writes."
        ),
    )
    parser.add_argument(
        "--require-signature",
        action="store_true",
        help=(
            "Require bundle signature validation; unsigned archives are rejected "
            "(strict mode)."
        ),
    )

    args = parser.parse_args()
    settings = get_settings()
    safety_limits = RestoreSafetyLimits(
        max_entries=settings.restore_max_entries,
        max_total_uncompressed_bytes=settings.restore_max_total_uncompressed_bytes,
        max_single_file_bytes=settings.restore_max_single_file_bytes,
        max_compression_ratio=settings.restore_max_compression_ratio,
    )
    require_signature = bool(
        settings.restore_require_signature or args.require_signature
    )
    repo = StorageRepo(
        db_path=Path(args.db_path),
        artifacts_manager=ArtifactsManager(Path(args.data_dir)),
    )
    result = restore_run_bundle(
        repo=repo,
        zip_path=Path(args.zip_path),
        data_dir=Path(args.data_dir),
        overwrite_existing=bool(args.overwrite_existing),
        rollback_on_metadata_failure=not bool(args.no_rollback_on_metadata_failure),
        safety_limits=safety_limits,
        signing_key=settings.bundle_signing_key,
        require_signature=require_signature,
        verify_only=bool(args.verify_only),
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
