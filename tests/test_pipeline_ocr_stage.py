from __future__ import annotations

import base64
from pathlib import Path

from app.ocr_client.mistral_ocr import MistralOCRClient
from app.ocr_client.types import OCROptions
from app.pipeline.orchestrator import OCRPipelineOrchestrator
from app.storage.artifacts import ArtifactsManager
from app.storage.repo import StorageRepo


class FakeProcessService:
    def process(self, **kwargs: object) -> dict[str, object]:
        assert "document" in kwargs
        return {
            "model": "mistral-ocr-latest",
            "pages": [
                {
                    "markdown": "OCR text for document",
                    "tables": [{"html": "<table><tr><td>1</td></tr></table>"}],
                    "images": [
                        {
                            "image_base64": base64.b64encode(b"img").decode("ascii"),
                            "mime_type": "image/png",
                        }
                    ],
                }
            ],
        }


def test_pipeline_ocr_stage_persists_documents_and_artifacts(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    db_path = tmp_path / "kaucja.sqlite3"

    artifacts_manager = ArtifactsManager(data_dir)
    repo = StorageRepo(db_path=db_path, artifacts_manager=artifacts_manager)
    ocr_client = MistralOCRClient(process_service=FakeProcessService())

    orchestrator = OCRPipelineOrchestrator(
        repo=repo,
        artifacts_manager=artifacts_manager,
        ocr_client=ocr_client,
    )

    file_one = tmp_path / "one.pdf"
    file_two = tmp_path / "two.pdf"
    file_one.write_bytes(b"one")
    file_two.write_bytes(b"two")

    result = orchestrator.run_ocr_stage(
        input_files=[file_one, file_two],
        session_id=None,
        provider="openai",
        model="gpt-5.1",
        prompt_name="kaucja_gap_analysis",
        prompt_version="v001",
        ocr_options=OCROptions(model="mistral-ocr-latest"),
    )

    assert result.run_status == "completed"
    assert [item.doc_id for item in result.documents] == ["0000001", "0000002"]

    run = repo.get_run(result.run_id)
    assert run is not None
    assert run.status == "completed"

    records = repo.list_documents(run_id=result.run_id)
    assert len(records) == 2
    assert records[0].ocr_status == "ok"
    assert records[1].ocr_status == "ok"

    for record in records:
        artifacts_root = Path(record.ocr_artifacts_path or "")
        assert Path(record.original_path).is_file()
        assert artifacts_root.is_dir()
        assert (artifacts_root / "combined.md").is_file()
        assert (artifacts_root / "raw_response.json").is_file()

    assert Path(run.artifacts_root_path, "logs", "run.log").is_file()
