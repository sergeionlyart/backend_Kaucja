import os
import json
from unittest.mock import patch, MagicMock
from tempfile import TemporaryDirectory
from legal_ingest.config import (
    PipelineConfig,
    RunConfig,
    MongoConfig,
    ParsersConfig,
    SourceConfig,
)
from legal_ingest.pipeline import run_pipeline


@patch("legal_ingest.pipeline.save_document_pipeline_results")
@patch("legal_ingest.pipeline.save_run")
@patch("legal_ingest.pipeline.fetch_source")
@patch("legal_ingest.pipeline.uuid.uuid4")
def test_pipeline_error_artifact(
    mock_uuid, mock_fetch, mock_save_run, mock_save_results
):
    mock_uuid.return_value = MagicMock(hex="err_run_1")

    # Mocking fetch to raise an exception
    mock_fetch.side_effect = Exception("Simulated network error")

    with TemporaryDirectory() as tmpdir:
        config = PipelineConfig(
            run=RunConfig(artifact_dir=tmpdir, run_id="auto", dry_run=False),
            mongo=MongoConfig(uri="stub", db="stub"),
            parsers=ParsersConfig(),
            sources=[
                SourceConfig(
                    source_id="test_error_source",
                    url="http://error.com",
                    fetch_strategy="direct",
                    doc_type_hint="STATUTE",
                    jurisdiction="PL",
                    language="pl",
                )
            ],
        )

        run_pipeline(config)

        doc_dir_base = os.path.join(tmpdir, "runs", "err_run_1")
        report_path = os.path.join(doc_dir_base, "run_report.json")

        with open(report_path, "r") as f:
            run_report = json.load(f)

        # Verify stats
        assert run_report["stats"]["docs_error"] == 1
        assert run_report["stats"]["docs_ok"] == 0
        assert len(run_report["errors"]) == 1
        assert run_report["errors"][0]["message"] == "Simulated network error"

        # Verify document.json artifact creation
        doc_uid = "unknown:urlsha:73b4bf0ccfb2ec60"
        err_hash = "ERROR"
        document_json_path = os.path.join(
            tmpdir, "docs", doc_uid, "normalized", err_hash, "document.json"
        )

        assert os.path.exists(document_json_path)
        with open(document_json_path, "r") as f:
            doc_data = json.load(f)

        assert doc_data["access_status"] == "ERROR"
        assert doc_data["current_source_hash"] == "ERROR"
        assert doc_data["content_stats"]["parse_method"] == "PDF_TEXT"
        assert doc_data["page_count"] == 0

        # Verify DB save was called with the err_doc_model
        assert mock_save_results.call_count == 1
        call_kwargs = mock_save_results.call_args.kwargs
        err_doc_saved = call_kwargs["document"]
        assert err_doc_saved.access_status == "ERROR"
