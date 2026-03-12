from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import fitz

from legal_ingest.config import utc_now_iso

ARTICLE_PATTERN = re.compile(r"^\s*Art\.\s*(\d+[A-Za-z]?)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class ParsedPage:
    page_index: int
    text: str
    char_count: int
    token_count_est: int
    alpha_ratio: float

    def to_mongo(self, *, doc_uid: str, source_hash: str) -> dict[str, Any]:
        return {
            "doc_uid": doc_uid,
            "source_hash": source_hash,
            "page_index": self.page_index,
            "text": self.text,
            "markdown": None,
            "token_count_est": self.token_count_est,
            "char_count": self.char_count,
            "extraction": {
                "method": "PDF_TEXT",
                "quality": {
                    "alpha_ratio": self.alpha_ratio,
                    "empty": self.char_count == 0,
                },
                "ocr_meta": None,
            },
            "ingested_at": utc_now_iso(),
        }


@dataclass(frozen=True, slots=True)
class ParsedNode:
    node_id: str
    parent_node_id: str | None
    depth: int
    order_index: int
    title: str
    start_index: int
    end_index: int
    anchors: dict[str, str]

    def to_mongo(self, *, doc_uid: str, source_hash: str) -> dict[str, Any]:
        return {
            "doc_uid": doc_uid,
            "source_hash": source_hash,
            "node_id": self.node_id,
            "parent_node_id": self.parent_node_id,
            "depth": self.depth,
            "order_index": self.order_index,
            "title": self.title,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "summary": None,
            "anchors": self.anchors,
            "ingested_at": utc_now_iso(),
        }


@dataclass(frozen=True, slots=True)
class ParsedPdfDocument:
    title: str
    mime: str
    source_hash: str
    pages: list[ParsedPage]
    nodes: list[ParsedNode]

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def pageindex_tree(self) -> list[dict[str, Any]]:
        children = [
            {
                "title": node.title,
                "node_id": node.node_id,
                "start_index": node.start_index,
                "end_index": node.end_index,
                "summary": None,
                "nodes": [],
            }
            for node in self.nodes
            if node.node_id != "root"
        ]
        return [
            {
                "title": "Root Document",
                "node_id": "root",
                "start_index": 0,
                "end_index": self.page_count,
                "summary": None,
                "nodes": children,
            }
        ]

    @property
    def content_stats(self) -> dict[str, Any]:
        total_chars = sum(page.char_count for page in self.pages)
        total_tokens_est = sum(page.token_count_est for page in self.pages)
        return {
            "total_chars": total_chars,
            "total_tokens_est": total_tokens_est,
            "parse_method": "PDF_TEXT",
            "ocr_used": False,
        }


def compute_sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def parse_pdf_bytes(body: bytes, *, canonical_title: str) -> ParsedPdfDocument:
    document = fitz.open(stream=body, filetype="pdf")
    try:
        pages = [_parse_page(document, index) for index in range(document.page_count)]
        nodes = build_article_nodes(pages)
        return ParsedPdfDocument(
            title=canonical_title,
            mime="application/pdf",
            source_hash=compute_sha256(body),
            pages=pages,
            nodes=nodes,
        )
    finally:
        document.close()


def _parse_page(document: fitz.Document, index: int) -> ParsedPage:
    text = document.load_page(index).get_text("text").strip()
    char_count = len(text)
    alpha_chars = sum(1 for character in text if character.isalpha())
    alpha_ratio = round(alpha_chars / char_count, 6) if char_count else 0.0
    token_count_est = max(1, char_count // 6) if char_count else 0
    return ParsedPage(
        page_index=index,
        text=text,
        char_count=char_count,
        token_count_est=token_count_est,
        alpha_ratio=alpha_ratio,
    )


def build_article_nodes(pages: list[ParsedPage]) -> list[ParsedNode]:
    article_hits: list[tuple[str, int, str]] = []
    seen_articles: set[str] = set()
    for page in pages:
        for line in page.text.splitlines():
            match = ARTICLE_PATTERN.match(line)
            if match is None:
                continue
            article_id = match.group(1).lower()
            if article_id in seen_articles:
                continue
            seen_articles.add(article_id)
            article_hits.append((article_id, page.page_index, " ".join(line.split())))

    nodes: list[ParsedNode] = [
        ParsedNode(
            node_id="root",
            parent_node_id=None,
            depth=0,
            order_index=0,
            title="Root Document",
            start_index=0,
            end_index=len(pages),
            anchors={},
        )
    ]

    for index, (article_id, page_index, title) in enumerate(article_hits, start=1):
        next_page_index = (
            article_hits[index][1] if index < len(article_hits) else len(pages)
        )
        nodes.append(
            ParsedNode(
                node_id=f"art:{article_id}",
                parent_node_id="root",
                depth=1,
                order_index=index,
                title=title,
                start_index=page_index,
                end_index=max(page_index + 1, next_page_index),
                anchors={"article": article_id},
            )
        )

    return nodes


def write_pdf_artifacts(
    *,
    artifact_root: Path,
    doc_uid: str,
    source_hash: str,
    body: bytes,
    document_source: dict[str, Any],
    pages: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
) -> dict[str, str]:
    doc_dir = artifact_root / doc_uid
    raw_dir = doc_dir / "raw" / source_hash
    normalized_dir = doc_dir / "normalized" / source_hash
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / "original.bin"
    raw_meta_path = raw_dir / "response_meta.json"
    pages_path = normalized_dir / "pages.jsonl"
    nodes_path = normalized_dir / "nodes.jsonl"

    raw_path.write_bytes(body)
    raw_meta_path.write_text(
        json.dumps(
            document_source,
            ensure_ascii=False,
            indent=2,
            default=_json_default,
        )
        + "\n",
        encoding="utf-8",
    )
    with pages_path.open("w", encoding="utf-8") as handle:
        for page in pages:
            handle.write(json.dumps(page, ensure_ascii=False))
            handle.write("\n")
    with nodes_path.open("w", encoding="utf-8") as handle:
        for node in nodes:
            handle.write(json.dumps(node, ensure_ascii=False))
            handle.write("\n")

    return {
        "raw_object_path": str(raw_path.resolve()),
        "response_meta_path": str(raw_meta_path.resolve()),
        "pages_path": str(pages_path.resolve()),
        "nodes_path": str(nodes_path.resolve()),
    }


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
