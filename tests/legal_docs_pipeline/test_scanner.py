from __future__ import annotations

import hashlib
from pathlib import PurePosixPath

from legal_docs_pipeline.scanner import DocumentScanner


def test_scanner_filters_hidden_system_temp_and_sorts_case_sensitive(
    tmp_path,
) -> None:
    (tmp_path / "b.md").write_text("b", encoding="utf-8")
    (tmp_path / "A.md").write_text("A", encoding="utf-8")
    (tmp_path / ".hidden.md").write_text("hidden", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("skip", encoding="utf-8")
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()
    (sub_dir / "C.md").write_text("C", encoding="utf-8")
    (sub_dir / "~$temp.md").write_text("temp", encoding="utf-8")
    (sub_dir / ".ignored.md").write_text("ignored", encoding="utf-8")

    scanner = DocumentScanner()
    discovered = scanner.scan(tmp_path)

    assert [item.relative_path for item in discovered] == [
        PurePosixPath("A.md"),
        PurePosixPath("b.md"),
        PurePosixPath("sub/C.md"),
    ]
    assert discovered[0].file_name == "A.md"
    assert discovered[0].sha256_hex == hashlib.sha256(b"A").hexdigest()


def test_scanner_can_start_from_relative_path(tmp_path) -> None:
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    (tmp_path / "b.md").write_text("b", encoding="utf-8")
    (tmp_path / "c.md").write_text("c", encoding="utf-8")

    scanner = DocumentScanner()
    discovered = scanner.scan(tmp_path, from_relative_path="b.md")

    assert [item.relative_path for item in discovered] == [
        PurePosixPath("b.md"),
        PurePosixPath("c.md"),
    ]
