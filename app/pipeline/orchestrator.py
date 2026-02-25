from __future__ import annotations

import mimetypes
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from app.ocr_client.types import OCROptions, OCRResult
from app.storage.artifacts import ArtifactsManager, DocumentArtifacts
from app.storage.models import OCRStatus
from app.storage.repo import StorageRepo


class OCRClientProtocol(Protocol):
    def process_document(
        self,
        *,
        input_path: Path,
        doc_id: str,
        options: OCROptions,
        output_dir: Path,
    ) -> OCRResult: ...


@dataclass(frozen=True, slots=True)
class OCRDocumentStageResult:
    doc_id: str
    ocr_status: OCRStatus
    pages_count: int | None
    combined_markdown_path: str
    ocr_artifacts_path: str
    ocr_error: str | None


@dataclass(frozen=True, slots=True)
class OcrStageResult:
    session_id: str
    run_id: str
    run_status: str
    documents: list[OCRDocumentStageResult]


class OCRPipelineOrchestrator:
    def __init__(
        self,
        *,
        repo: StorageRepo,
        artifacts_manager: ArtifactsManager,
        ocr_client: OCRClientProtocol,
    ) -> None:
        self.repo = repo
        self.artifacts_manager = artifacts_manager
        self.ocr_client = ocr_client

    def run_ocr_stage(
        self,
        *,
        input_files: Sequence[str | Path],
        session_id: str | None,
        provider: str,
        model: str,
        prompt_name: str,
        prompt_version: str,
        ocr_options: OCROptions,
    ) -> OcrStageResult:
        paths = _normalize_input_paths(input_files)
        if not paths:
            raise ValueError("At least one input file is required")

        session = self.repo.create_session(session_id=session_id or None)
        run = self.repo.create_run(
            session_id=session.session_id,
            provider=provider,
            model=model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            schema_version=prompt_version,
            status="running",
        )

        run_artifacts = self.artifacts_manager.ensure_run_structure(
            run.artifacts_root_path
        )
        documents: list[OCRDocumentStageResult] = []
        has_failures = False

        _append_run_log(
            run_artifacts.run_log_path, f"Run started with {len(paths)} files"
        )

        for index, source_path in enumerate(paths, start=1):
            doc_id = _build_doc_id(index)
            document_artifacts = self.artifacts_manager.create_document_artifacts(
                artifacts_root_path=run.artifacts_root_path,
                doc_id=doc_id,
            )

            original_path = _store_original_file(
                source_path=source_path,
                document_artifacts=document_artifacts,
            )
            original_mime, _ = mimetypes.guess_type(source_path.name)

            self.repo.create_document(
                run_id=run.run_id,
                doc_id=doc_id,
                original_filename=source_path.name,
                original_mime=original_mime,
                original_path=str(original_path.resolve()),
                ocr_status="pending",
                ocr_artifacts_path=str(document_artifacts.ocr_dir.resolve()),
            )

            try:
                ocr_result = self.ocr_client.process_document(
                    input_path=original_path,
                    doc_id=doc_id,
                    options=ocr_options,
                    output_dir=document_artifacts.ocr_dir,
                )
                self.repo.update_document_ocr(
                    run_id=run.run_id,
                    doc_id=doc_id,
                    ocr_status="ok",
                    ocr_model=ocr_result.ocr_model,
                    pages_count=ocr_result.pages_count,
                    ocr_artifacts_path=str(document_artifacts.ocr_dir.resolve()),
                    ocr_error=None,
                )
                documents.append(
                    OCRDocumentStageResult(
                        doc_id=doc_id,
                        ocr_status="ok",
                        pages_count=ocr_result.pages_count,
                        combined_markdown_path=ocr_result.combined_markdown_path,
                        ocr_artifacts_path=str(document_artifacts.ocr_dir.resolve()),
                        ocr_error=None,
                    )
                )
                _append_run_log(run_artifacts.run_log_path, f"Doc {doc_id}: OCR ok")
            except Exception as error:
                has_failures = True
                error_message = str(error)
                self.repo.update_document_ocr(
                    run_id=run.run_id,
                    doc_id=doc_id,
                    ocr_status="failed",
                    ocr_model=ocr_options.model,
                    pages_count=None,
                    ocr_artifacts_path=str(document_artifacts.ocr_dir.resolve()),
                    ocr_error=error_message,
                )
                documents.append(
                    OCRDocumentStageResult(
                        doc_id=doc_id,
                        ocr_status="failed",
                        pages_count=None,
                        combined_markdown_path=str(
                            (document_artifacts.ocr_dir / "combined.md").resolve()
                        ),
                        ocr_artifacts_path=str(document_artifacts.ocr_dir.resolve()),
                        ocr_error=error_message,
                    )
                )
                _append_run_log(
                    run_artifacts.run_log_path,
                    f"Doc {doc_id}: OCR failed ({error_message})",
                )

        final_status = "failed" if has_failures else "completed"
        self.repo.update_run_status(
            run_id=run.run_id,
            status=final_status,
            error_code="OCR_STAGE_FAILED" if has_failures else None,
            error_message="One or more documents failed OCR" if has_failures else None,
        )
        _append_run_log(
            run_artifacts.run_log_path, f"Run finished with status={final_status}"
        )

        return OcrStageResult(
            session_id=session.session_id,
            run_id=run.run_id,
            run_status=final_status,
            documents=documents,
        )


def _normalize_input_paths(input_files: Sequence[str | Path]) -> list[Path]:
    paths: list[Path] = []
    for input_file in input_files:
        path = Path(input_file)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")
        paths.append(path)
    return paths


def _build_doc_id(index: int) -> str:
    return f"{index:07d}"


def _store_original_file(
    *,
    source_path: Path,
    document_artifacts: DocumentArtifacts,
) -> Path:
    destination_path = document_artifacts.original_dir / source_path.name
    shutil.copy2(source_path, destination_path)
    return destination_path


def _append_run_log(log_path: Path, message: str) -> None:
    with log_path.open("a", encoding="utf-8") as file:
        file.write(message)
        file.write("\n")
