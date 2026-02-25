from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RunArtifacts:
    artifacts_root_path: Path
    logs_dir: Path
    run_log_path: Path


@dataclass(frozen=True, slots=True)
class DocumentArtifacts:
    doc_id: str
    document_root_path: Path
    original_dir: Path
    ocr_dir: Path
    pages_dir: Path
    tables_dir: Path
    images_dir: Path
    page_renders_dir: Path
    combined_markdown_path: Path
    raw_response_path: Path
    quality_path: Path


@dataclass(frozen=True, slots=True)
class LLMArtifacts:
    llm_dir: Path
    request_path: Path
    response_raw_path: Path
    response_parsed_path: Path
    validation_path: Path


class ArtifactsManager:
    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)

    def build_run_root(self, *, session_id: str, run_id: str) -> Path:
        return self.data_dir / "sessions" / session_id / "runs" / run_id

    def create_run_artifacts(self, *, session_id: str, run_id: str) -> RunArtifacts:
        root_path = self.build_run_root(session_id=session_id, run_id=run_id)
        return self.ensure_run_structure(root_path)

    def ensure_run_structure(self, artifacts_root_path: Path | str) -> RunArtifacts:
        root_path = Path(artifacts_root_path)
        logs_dir = root_path / "logs"

        logs_dir.mkdir(parents=True, exist_ok=True)

        run_log_path = logs_dir / "run.log"
        run_log_path.touch(exist_ok=True)

        return RunArtifacts(
            artifacts_root_path=root_path,
            logs_dir=logs_dir,
            run_log_path=run_log_path,
        )

    def create_document_artifacts(
        self,
        *,
        artifacts_root_path: Path | str,
        doc_id: str,
    ) -> DocumentArtifacts:
        root_path = Path(artifacts_root_path)
        document_root = root_path / "documents" / doc_id
        original_dir = document_root / "original"
        ocr_dir = document_root / "ocr"
        pages_dir = ocr_dir / "pages"
        tables_dir = ocr_dir / "tables"
        images_dir = ocr_dir / "images"
        page_renders_dir = ocr_dir / "page_renders"

        original_dir.mkdir(parents=True, exist_ok=True)
        pages_dir.mkdir(parents=True, exist_ok=True)
        tables_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
        page_renders_dir.mkdir(parents=True, exist_ok=True)

        return DocumentArtifacts(
            doc_id=doc_id,
            document_root_path=document_root,
            original_dir=original_dir,
            ocr_dir=ocr_dir,
            pages_dir=pages_dir,
            tables_dir=tables_dir,
            images_dir=images_dir,
            page_renders_dir=page_renders_dir,
            combined_markdown_path=ocr_dir / "combined.md",
            raw_response_path=ocr_dir / "raw_response.json",
            quality_path=ocr_dir / "quality.json",
        )

    def create_llm_artifacts(self, *, artifacts_root_path: Path | str) -> LLMArtifacts:
        root_path = Path(artifacts_root_path)
        llm_dir = root_path / "llm"
        llm_dir.mkdir(parents=True, exist_ok=True)

        return LLMArtifacts(
            llm_dir=llm_dir,
            request_path=llm_dir / "request.txt",
            response_raw_path=llm_dir / "response_raw.txt",
            response_parsed_path=llm_dir / "response_parsed.json",
            validation_path=llm_dir / "validation.json",
        )
