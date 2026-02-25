from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from app.storage.zip_export import ZipExportError, export_run_bundle


def _build_run_artifacts(root: Path) -> None:
    (root / "logs").mkdir(parents=True, exist_ok=True)
    (root / "documents" / "0000001" / "ocr").mkdir(parents=True, exist_ok=True)
    (root / "llm").mkdir(parents=True, exist_ok=True)

    (root / "run.json").write_text('{"status":"completed"}', encoding="utf-8")
    (root / "logs" / "run.log").write_text("line-1\n", encoding="utf-8")
    (root / "documents" / "0000001" / "ocr" / "combined.md").write_text(
        "combined",
        encoding="utf-8",
    )
    (root / "llm" / "response_raw.txt").write_text("{}", encoding="utf-8")


def test_export_run_bundle_creates_deterministic_zip(tmp_path: Path) -> None:
    root = tmp_path / "run-artifacts"
    _build_run_artifacts(root)

    zip_path = export_run_bundle(artifacts_root_path=root)

    assert zip_path.is_file()
    assert zip_path.name == "run-artifacts_bundle.zip"

    with ZipFile(zip_path, "r") as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert names == [
            "bundle_manifest.json",
            "documents/0000001/ocr/combined.md",
            "llm/response_raw.txt",
            "logs/run.log",
            "run.json",
        ]

        for info in archive.infolist():
            assert info.date_time == (1980, 1, 1, 0, 0, 0)

        manifest_payload = json.loads(
            archive.read("bundle_manifest.json").decode("utf-8")
        )
        assert manifest_payload["version"] == "v1"
        assert manifest_payload["run_id"] == "run-artifacts"
        assert isinstance(manifest_payload["session_id"], str)
        files = manifest_payload["files"]
        assert [item["relative_path"] for item in files] == [
            "documents/0000001/ocr/combined.md",
            "llm/response_raw.txt",
            "logs/run.log",
            "run.json",
        ]


def test_export_run_bundle_fails_when_root_missing(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing"

    with pytest.raises(FileNotFoundError, match="Artifacts root not found"):
        export_run_bundle(artifacts_root_path=missing_root)


def test_export_run_bundle_rejects_symlink_paths(tmp_path: Path) -> None:
    root = tmp_path / "run-artifacts"
    _build_run_artifacts(root)

    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    symlink_path = root / "documents" / "0000001" / "ocr" / "outside-link.txt"

    try:
        symlink_path.symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation is not available in this environment")

    with pytest.raises(ZipExportError, match="Refusing to export symlinked path"):
        export_run_bundle(artifacts_root_path=root)
