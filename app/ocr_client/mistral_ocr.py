from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Protocol

from app.ocr_client.quality import evaluate_ocr_quality
from app.ocr_client.types import OCROptions, OCRResult


class OCRProcessService(Protocol):
    def process(self, **kwargs: Any) -> Any: ...


class MistralOCRClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        process_service: OCRProcessService | None = None,
    ) -> None:
        self._api_key = api_key
        self._process_service = process_service

    def process_document(
        self,
        *,
        input_path: Path,
        doc_id: str,
        options: OCROptions,
        output_dir: Path,
    ) -> OCRResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        pages_dir = output_dir / "pages"
        tables_dir = output_dir / "tables"
        images_dir = output_dir / "images"
        page_renders_dir = output_dir / "page_renders"

        pages_dir.mkdir(parents=True, exist_ok=True)
        tables_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
        page_renders_dir.mkdir(parents=True, exist_ok=True)

        payload = self._request_ocr(input_path=input_path, options=options)

        raw_response_path = output_dir / "raw_response.json"
        raw_response_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        pages = payload.get("pages")
        if not isinstance(pages, list):
            raise ValueError("OCR response missing pages list")

        page_markdowns: list[str] = []
        table_index = 0
        image_index = 0

        for page_offset, page_payload in enumerate(pages, start=1):
            page_data = page_payload if isinstance(page_payload, dict) else {}
            markdown = str(page_data.get("markdown") or "")
            page_markdowns.append(markdown)

            page_path = pages_dir / f"{page_offset:04d}.md"
            page_path.write_text(markdown, encoding="utf-8")

            table_index = _write_tables(
                page_data=page_data,
                table_index=table_index,
                table_format=options.table_format,
                tables_dir=tables_dir,
            )
            image_index = _write_images(
                page_data=page_data,
                image_index=image_index,
                images_dir=images_dir,
            )

        combined_path = output_dir / "combined.md"
        combined_path.write_text("\n\n".join(page_markdowns), encoding="utf-8")

        quality = evaluate_ocr_quality(page_markdowns)
        quality_path = output_dir / "quality.json"
        quality_path.write_text(
            json.dumps(quality.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        ocr_model = str(payload.get("model") or options.model)

        return OCRResult(
            doc_id=doc_id,
            ocr_model=ocr_model,
            pages_count=len(page_markdowns),
            combined_markdown_path=str(combined_path.resolve()),
            raw_response_path=str(raw_response_path.resolve()),
            tables_dir=str(tables_dir.resolve()),
            images_dir=str(images_dir.resolve()),
            page_renders_dir=str(page_renders_dir.resolve()),
            quality_path=str(quality_path.resolve()),
            quality_warnings=quality.warnings,
        )

    def _request_ocr(self, *, input_path: Path, options: OCROptions) -> dict[str, Any]:
        service = self._resolve_process_service()

        request_payload: dict[str, Any] = {
            "model": options.model,
            "document": {
                "type": "document_url",
                "document_url": input_path.resolve().as_uri(),
            },
            "include_image_base64": options.include_image_base64,
        }

        if options.table_format != "none":
            request_payload["table_format"] = options.table_format
        if options.extract_header:
            request_payload["extract_header"] = True
        if options.extract_footer:
            request_payload["extract_footer"] = True

        response = service.process(**request_payload)
        return _response_to_dict(response)

    def _resolve_process_service(self) -> OCRProcessService:
        if self._process_service is not None:
            return self._process_service

        if self._api_key is None:
            raise ValueError(
                "Mistral API key is required when process_service is not provided"
            )

        try:
            from mistralai import Mistral
        except ImportError as error:
            raise RuntimeError("mistralai package is not installed") from error

        client = Mistral(api_key=self._api_key)
        self._process_service = client.ocr
        return self._process_service


def _response_to_dict(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return response

    model_dump = getattr(response, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, dict):
            return dumped

    raise ValueError("Unsupported OCR response type")


def _write_tables(
    *,
    page_data: dict[str, Any],
    table_index: int,
    table_format: str,
    tables_dir: Path,
) -> int:
    tables = page_data.get("tables")
    if not isinstance(tables, list):
        return table_index

    for table in tables:
        table_data = table if isinstance(table, dict) else {}
        if table_format == "markdown":
            extension = "md"
            content = str(table_data.get("markdown") or table_data.get("content") or "")
        else:
            extension = "html"
            content = str(table_data.get("html") or table_data.get("content") or "")

        table_path = tables_dir / f"tbl-{table_index}.{extension}"
        table_path.write_text(content, encoding="utf-8")
        table_index += 1

    return table_index


def _write_images(
    *,
    page_data: dict[str, Any],
    image_index: int,
    images_dir: Path,
) -> int:
    images = page_data.get("images")
    if not isinstance(images, list):
        return image_index

    for image in images:
        image_data = image if isinstance(image, dict) else {}
        encoded = str(image_data.get("image_base64") or "")
        if not encoded:
            continue

        payload, extension = _decode_image_payload(encoded, image_data)
        image_path = images_dir / f"img-{image_index}.{extension}"
        image_path.write_bytes(payload)
        image_index += 1

    return image_index


def _decode_image_payload(
    encoded_payload: str,
    image_data: dict[str, Any],
) -> tuple[bytes, str]:
    payload = encoded_payload
    extension = _extension_from_image_data(image_data)

    if encoded_payload.startswith("data:") and "," in encoded_payload:
        header, payload = encoded_payload.split(",", maxsplit=1)
        if "image/" in header:
            mime_segment = header.split("image/", maxsplit=1)[1]
            extension = mime_segment.split(";", maxsplit=1)[0]

    raw_bytes = base64.b64decode(payload)
    return raw_bytes, extension


def _extension_from_image_data(image_data: dict[str, Any]) -> str:
    mime_type = str(image_data.get("mime_type") or "").lower()
    format_hint = str(image_data.get("format") or "").lower()

    if mime_type.startswith("image/"):
        return mime_type.split("/", maxsplit=1)[1]
    if format_hint:
        return format_hint

    return "png"
