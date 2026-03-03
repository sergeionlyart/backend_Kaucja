import os
import json
from unittest.mock import patch, MagicMock
from tempfile import TemporaryDirectory
from legal_ingest.config import (
    HttpConfig,
    PipelineConfig,
    RunConfig,
    MongoConfig,
    ParsersConfig,
    SourceConfig,
)
from legal_ingest.pipeline import run_pipeline


@patch("legal_ingest.pipeline.save_run")
@patch("legal_ingest.pipeline.save_document_pipeline_results")
@patch("legal_ingest.pipeline.fetch_source")
@patch("legal_ingest.pipeline.uuid.uuid4")
def test_pipeline_artifacts_creation(
    mock_uuid, mock_fetch, mock_save_doc, mock_save_run
):
    mock_uuid.return_value = MagicMock(hex="test_run_123")

    # Mocking fetch to return a simple HTML page
    mock_resp = MagicMock()
    mock_resp.raw_bytes = (
        b"<html><head><title>TestDoc</title></head><body>Hello World</body></html>"
    )
    mock_resp.headers = {"content-type": "text/html"}
    mock_resp.status_code = 200
    mock_resp.final_url = "http://test.com"
    mock_fetch.return_value = (mock_resp, [])

    with TemporaryDirectory() as tmpdir:
        config = PipelineConfig(
            run=RunConfig(artifact_dir=tmpdir, run_id="auto"),
            mongo=MongoConfig(uri="stub", db="stub"),
            parsers=ParsersConfig(),
            sources=[
                SourceConfig(
                    source_id="test_mock",
                    url="http://test.com",
                    fetch_strategy="direct",
                    doc_type_hint="STATUTE",
                    jurisdiction="PL",
                    language="pl",
                )
            ],
        )

        run_pipeline(config)

        # Verify docs output
        doc_dir_base = os.path.join(tmpdir, "docs")
        docs_list = os.listdir(doc_dir_base)
        assert len(docs_list) == 1
        doc_uid = docs_list[0]

        norm_dir_base = os.path.join(doc_dir_base, doc_uid, "normalized")
        source_hashes = os.listdir(norm_dir_base)
        assert len(source_hashes) == 1
        source_hash = source_hashes[0]

        # Exact artifact path
        norm_dir = os.path.join(norm_dir_base, source_hash)

        assert os.path.exists(os.path.join(norm_dir, "pages.jsonl"))
        assert os.path.exists(os.path.join(norm_dir, "nodes.jsonl"))
        assert os.path.exists(os.path.join(norm_dir, "citations.jsonl"))

        document_json_path = os.path.join(norm_dir, "document.json")
        assert os.path.exists(document_json_path)

        # Verify content
        with open(document_json_path, "r", encoding="utf-8") as f:
            doc_data = json.load(f)

        assert doc_data["doc_uid"] == doc_uid
        assert doc_data["current_source_hash"] == source_hash
        assert doc_data["title"] == "TestDoc"
        assert (
            doc_data["access_status"] == "RESTRICTED"
        )  # Due to low char count in mock html
        assert doc_data["content_stats"]["parse_method"] == "HTML"
        assert doc_data["content_stats"]["ocr_used"] is False
        assert doc_data["page_count"] == 1


@patch("legal_ingest.pipeline.save_run")
@patch("legal_ingest.pipeline.save_document_pipeline_results")
@patch("legal_ingest.pipeline.fetch_source")
@patch("legal_ingest.pipeline.uuid.uuid4")
def test_pipeline_commercial_html_with_cookie_low_chars_still_restricted(
    mock_uuid, mock_fetch, mock_save_doc, mock_save_run
):
    mock_uuid.return_value = MagicMock(hex="test_run_cookie_restricted")

    mock_resp = MagicMock()
    mock_resp.raw_bytes = (
        b"<html><head><title>LEX</title></head><body>short text</body></html>"
    )
    mock_resp.headers = {"content-type": "text/html"}
    mock_resp.status_code = 200
    mock_resp.final_url = "https://sip.lex.pl/fake"
    mock_fetch.return_value = (mock_resp, [])

    with TemporaryDirectory() as tmpdir:
        config = PipelineConfig(
            run=RunConfig(
                artifact_dir=tmpdir,
                run_id="auto",
                http=HttpConfig(lex_session_cookie="session-cookie"),
            ),
            mongo=MongoConfig(uri="stub", db="stub"),
            parsers=ParsersConfig(),
            sources=[
                SourceConfig(
                    source_id="lex_commercial",
                    url="https://sip.lex.pl/fake",
                    fetch_strategy="direct",
                    doc_type_hint="STATUTE_REF",
                    jurisdiction="PL",
                    language="pl",
                    license_tag="COMMERCIAL",
                )
            ],
        )

        run_pipeline(config)

        doc_dir_base = os.path.join(tmpdir, "docs")
        docs_list = os.listdir(doc_dir_base)
        assert len(docs_list) == 1
        doc_uid = docs_list[0]
        norm_dir_base = os.path.join(doc_dir_base, doc_uid, "normalized")
        source_hash = os.listdir(norm_dir_base)[0]
        document_json_path = os.path.join(norm_dir_base, source_hash, "document.json")

        with open(document_json_path, "r", encoding="utf-8") as f:
            doc_data = json.load(f)

        assert doc_data["access_status"] == "RESTRICTED"


@patch("legal_ingest.pipeline.save_run")
@patch("legal_ingest.pipeline.save_document_pipeline_results")
@patch("legal_ingest.pipeline.fetch_source")
@patch("legal_ingest.pipeline.uuid.uuid4")
def test_pipeline_commercial_html_paywall_marker_restricted_even_with_cookie(
    mock_uuid, mock_fetch, mock_save_doc, mock_save_run
):
    mock_uuid.return_value = MagicMock(hex="test_run_cookie_paywall")
    paywall_text = ("zaloguj aby kontynuować " * 80).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.raw_bytes = b"<html><body>" + paywall_text + b"</body></html>"
    mock_resp.headers = {"content-type": "text/html"}
    mock_resp.status_code = 200
    mock_resp.final_url = "https://sip.lex.pl/fake"
    mock_fetch.return_value = (mock_resp, [])

    with TemporaryDirectory() as tmpdir:
        config = PipelineConfig(
            run=RunConfig(
                artifact_dir=tmpdir,
                run_id="auto",
                http=HttpConfig(lex_session_cookie="session-cookie"),
            ),
            mongo=MongoConfig(uri="stub", db="stub"),
            parsers=ParsersConfig(),
            sources=[
                SourceConfig(
                    source_id="lex_commercial_paywall",
                    url="https://sip.lex.pl/fake",
                    fetch_strategy="direct",
                    doc_type_hint="STATUTE_REF",
                    jurisdiction="PL",
                    language="pl",
                    license_tag="COMMERCIAL",
                )
            ],
        )

        run_pipeline(config)

        doc_uid = os.listdir(os.path.join(tmpdir, "docs"))[0]
        norm_dir_base = os.path.join(tmpdir, "docs", doc_uid, "normalized")
        source_hash = os.listdir(norm_dir_base)[0]
        document_json_path = os.path.join(norm_dir_base, source_hash, "document.json")

        with open(document_json_path, "r", encoding="utf-8") as f:
            doc_data = json.load(f)

        assert doc_data["access_status"] == "RESTRICTED"
