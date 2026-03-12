from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.ops.legal_collection import (
    FetchResponse,
    build_local_collection,
    derive_doc_uid,
    parse_source_markdown,
)


def test_parse_current_markdown_source_list() -> None:
    path = Path("docs/legal/cas_law_V_2.2 2.md")

    sources = parse_source_markdown(path.read_text(encoding="utf-8"))

    assert len(sources) == 38
    assert sources[0].source_id == "pl_eli_du_2001_733"
    assert sources[0].doc_uid == "eli_pl:DU/2001/733"
    assert sources[10].fetch_strategy == "saos_search"
    assert sources[10].source_id == "pl_saos_search_kaucja_mieszkaniowa"
    assert sources[11].doc_uid == "saos_pl:171957"
    assert sources[24].doc_uid == "eurlex_eu:eli:dir/1993/13/oj/eng"
    assert sources[30].doc_uid == "curia_eu:docid:137830"


def test_derive_doc_uid_uses_domain_rules() -> None:
    assert (
        derive_doc_uid(
            "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf"
        )
        == "isap_pl:WDU19640160093"
    )
    assert (
        derive_doc_uid("https://www.saos.org.pl/judgments/171957") == "saos_pl:171957"
    )
    assert (
        derive_doc_uid(
            "https://curia.europa.eu/juris/document/document.jsf?docid=137830&doclang=EN"
        )
        == "curia_eu:docid:137830"
    )


def test_build_local_collection_writes_downloaded_documents(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "sources.md"
    input_path.write_text(
        "\n".join(
            [
                "Poland - ELI",
                "1. https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf",
            ]
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "collection"
    body = b"%PDF-1.4 test document\n"
    expected_hash = hashlib.sha256(body).hexdigest()

    def fake_fetcher(url: str, timeout_seconds: float) -> FetchResponse:
        assert url == "https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf"
        assert timeout_seconds == 5.0
        return FetchResponse(
            url=url,
            status_code=200,
            headers={"Content-Type": "application/pdf"},
            body=body,
        )

    report = build_local_collection(
        input_path=input_path,
        output_dir=output_dir,
        timeout_seconds=5.0,
        fetcher=fake_fetcher,
    )

    assert report["source_count"] == 1
    assert report["summary"] == {"ok": 1, "error": 0, "dry_run": 0}

    doc_root = output_dir / "docs" / "eli_pl_du_2001_733"
    raw_path = doc_root / "raw" / expected_hash / "original.bin"
    meta_path = doc_root / "raw" / expected_hash / "response_meta.json"
    manifest_path = output_dir / "collection_manifest.json"

    assert raw_path.read_bytes() == body
    meta_payload = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta_payload["source_hash"] == expected_hash
    assert meta_payload["http_status"] == 200

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["summary"] == {"ok": 1, "error": 0, "dry_run": 0}
    assert manifest["downloads"][0]["source_id"] == "pl_eli_du_2001_733"
