from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from legal_ingest.pdf_ingest import write_pdf_artifacts


def test_write_pdf_artifacts_serializes_datetime_metadata(tmp_path) -> None:
    artifact_paths = write_pdf_artifacts(
        artifact_root=tmp_path,
        doc_uid="eli_pl:DU/1964/296",
        source_hash="hash-123",
        body=b"%PDF-1.4",
        document_source={
            "doc_uid": "eli_pl:DU/1964/296",
            "fetched_at": datetime(2026, 3, 7, 10, 0, 0, tzinfo=timezone.utc),
        },
        pages=[],
        nodes=[],
    )

    response_meta = json.loads(
        Path(artifact_paths["response_meta_path"]).read_text(encoding="utf-8")
    )

    assert response_meta["fetched_at"] == "2026-03-07T10:00:00+00:00"
