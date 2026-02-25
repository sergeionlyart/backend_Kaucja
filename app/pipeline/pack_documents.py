from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True, slots=True)
class DocumentMarkdown:
    doc_id: str
    markdown: str


def pack_documents(documents: Sequence[DocumentMarkdown]) -> str:
    lines: list[str] = ["<BEGIN_DOCUMENTS>"]

    for document in documents:
        lines.append(f'<DOC_START id="{document.doc_id}">')
        lines.append(document.markdown)
        lines.append("<DOC_END>")

    lines.append("<END_DOCUMENTS>")
    return "\n".join(lines)


def load_and_pack_documents(
    documents: Sequence[tuple[str, Path]],
) -> str:
    payload = [
        DocumentMarkdown(
            doc_id=doc_id,
            markdown=path.read_text(encoding="utf-8"),
        )
        for doc_id, path in documents
    ]
    return pack_documents(payload)
