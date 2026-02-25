from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


class ZipExportError(RuntimeError):
    """Raised when run bundle export cannot be completed safely."""


def export_run_bundle(
    *,
    artifacts_root_path: Path | str,
    output_dir: Path | str | None = None,
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

    with ZipFile(zip_path, mode="w") as archive:
        for file_path in file_paths:
            relative_path = _safe_relative_path(
                base_path=resolved_root,
                target_path=file_path,
            )
            zip_info = ZipInfo(filename=relative_path.as_posix())
            zip_info.date_time = (1980, 1, 1, 0, 0, 0)
            zip_info.compress_type = ZIP_DEFLATED
            data = file_path.read_bytes()
            archive.writestr(zip_info, data)

    return zip_path


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
