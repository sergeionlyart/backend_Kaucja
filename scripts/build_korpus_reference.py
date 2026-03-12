# ruff: noqa: E402

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from legal_ingest.config import MongoConfig
from legal_ingest.mongo import MongoRuntime
from legal_ingest.normalization import clean_title, is_explicit_broken_inventory_record

DEFAULT_OUTPUT_PATH = Path("KORPUS_DOKUMENTOW_KAUCJA_PL.md")
KIND_ORDER = (
    "STATUTE",
    "EU_ACT",
    "GUIDANCE",
    "COMMENTARY",
    "STATUTE_REF",
    "CASELAW",
)
STATUS_ORDER = ("canonical", "active", "optional", "alias", "excluded", "article_node")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the external KORPUS reference from legal_rag_runtime."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Markdown output path.",
    )
    parser.add_argument(
        "--mongo-uri",
        default=MongoConfig().uri,
        help="MongoDB URI. Defaults to LEGAL_INGEST_MONGO_URI or mongodb://localhost:27017.",
    )
    parser.add_argument(
        "--mongo-db",
        default=MongoConfig().db_name,
        help="MongoDB database name. Defaults to LEGAL_INGEST_MONGO_DB or legal_rag_runtime.",
    )
    return parser.parse_args()


def load_documents(runtime: MongoRuntime) -> list[dict[str, Any]]:
    projection = {
        "_id": 0,
        "doc_uid": 1,
        "status": 1,
        "document_kind": 1,
        "doc_type": 1,
        "legal_role": 1,
        "source_system": 1,
        "source_tier": 1,
        "canonical_title": 1,
        "title_short": 1,
        "summary_1line": 1,
        "source_url": 1,
        "normalized_source_url": 1,
        "external_id": 1,
        "storage_uri": 1,
        "same_case_group_id": 1,
        "duplicate_role": 1,
        "duplicate_owner_doc_uid": 1,
        "canonical_doc_uid": 1,
        "superseded_by": 1,
        "exclusion_reason": 1,
        "updated_at": 1,
    }
    documents = runtime.load_collection("documents", projection=projection)
    unique_by_doc_uid: dict[str, dict[str, Any]] = {}
    for document in documents:
        doc_uid = str(document.get("doc_uid") or "")
        if not doc_uid:
            continue
        unique_by_doc_uid[doc_uid] = document
    return sorted(
        unique_by_doc_uid.values(),
        key=lambda item: (
            kind_sort_key(item),
            source_system(item),
            status_sort_key(item),
            sort_title(item),
            str(item.get("doc_uid")),
        ),
    )


def build_markdown(documents: list[dict[str, Any]], *, mongo_uri: str, mongo_db: str) -> str:
    broken_inventory = [
        document for document in documents if is_explicit_broken_inventory_record(document)
    ]
    operational_documents = [
        document for document in documents if not is_explicit_broken_inventory_record(document)
    ]
    status_counts = Counter(status_value(document) for document in documents)
    kind_counts = Counter(document_kind(document) for document in documents)
    source_counts = Counter(source_system(document) for document in documents)

    lines = [
        "# KORPUS dokumentow Kaucja PL",
        "",
        "_Read-only external corpus reference rebuilt from the current `legal_rag_runtime` snapshot._",
        "",
        "## 1. Snapshot",
        "",
        f"- MongoDB: `{mongo_uri}`",
        f"- Database: `{mongo_db}`",
        f"- Documents in full corpus: **{len(documents)}**",
        f"- Unique `doc_uid` values: **{len({str(document['doc_uid']) for document in documents})}**",
        f"- Operational slice documents: **{len(operational_documents)}**",
        f"- Broken inventory exclusions: **{len(broken_inventory)}**",
        "- Operational slice excludes only the 6 intentionally broken inventory records; the full reference below still lists canonical, alias and excluded records for traceability.",
        "",
        "## 2. Status Distribution",
        "",
        "| status | count |",
        "| --- | ---: |",
    ]
    for status in ordered_counter_items(status_counts, STATUS_ORDER):
        lines.append(f"| `{status}` | {status_counts[status]} |")

    lines.extend(
        [
            "",
            "## 3. Kind Distribution",
            "",
            "| document_kind | count |",
            "| --- | ---: |",
        ]
    )
    for kind in ordered_counter_items(kind_counts, KIND_ORDER):
        lines.append(f"| `{kind}` | {kind_counts[kind]} |")

    lines.extend(
        [
            "",
            "## 4. Source-System Distribution",
            "",
            "| source_system | count |",
            "| --- | ---: |",
        ]
    )
    for source_name, count in sorted(source_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{source_name}` | {count} |")

    lines.extend(
        [
            "",
            "## 5. Broken Inventory Records",
            "",
            "These records remain `excluded` / `INVENTORY_ONLY`, have broken checksum and/or artifact paths, and do not enter the operational slice.",
            "",
        ]
    )
    for document in broken_inventory:
        lines.append(
            f"- `{document['doc_uid']}` — {display_title(document)} | reason: {clean_title(document.get('exclusion_reason')) or 'n/a'}"
        )

    lines.extend(
        [
            "",
            "## 6. Corpus Reference",
            "",
        ]
    )

    grouped_documents = group_documents(documents)
    for kind in ordered_group_keys(grouped_documents):
        kind_documents = grouped_documents[kind]
        kind_total = sum(len(items) for items in kind_documents.values())
        lines.append(f"### `{kind}` ({kind_total})")
        lines.append("")
        for source_name in ordered_source_keys(kind_documents):
            source_documents = kind_documents[source_name]
            lines.append(f"#### `{source_name}` ({len(source_documents)})")
            lines.append("")
            for document in source_documents:
                lines.extend(render_document_entry(document))
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def group_documents(
    documents: list[dict[str, Any]],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for document in documents:
        grouped[document_kind(document)][source_system(document)].append(document)
    return grouped


def ordered_group_keys(grouped_documents: dict[str, dict[str, list[dict[str, Any]]]]) -> list[str]:
    known = [kind for kind in KIND_ORDER if kind in grouped_documents]
    unknown = sorted(kind for kind in grouped_documents if kind not in KIND_ORDER)
    return [*known, *unknown]


def ordered_source_keys(kind_documents: dict[str, list[dict[str, Any]]]) -> list[str]:
    return sorted(kind_documents, key=lambda item: (-len(kind_documents[item]), item))


def render_document_entry(document: dict[str, Any]) -> list[str]:
    lines = [
        f"##### `{document['doc_uid']}` — {display_title(document)}",
        "",
        f"- status: `{status_value(document)}`",
        f"- document_kind: `{document_kind(document)}`",
        f"- legal_role: `{clean_title(document.get('legal_role')) or 'unknown'}`",
        f"- source_system: `{source_system(document)}`",
        f"- source_tier: `{clean_title(document.get('source_tier')) or 'unknown'}`",
        f"- title_short: {clean_title(document.get('title_short')) or '—'}",
        f"- summary_1line: {clean_title(document.get('summary_1line')) or '—'}",
        f"- external_id: {clean_title(document.get('external_id')) or '—'}",
        f"- source_url: {clean_title(document.get('source_url')) or '—'}",
        f"- normalized_source_url: {clean_title(document.get('normalized_source_url')) or '—'}",
        f"- storage_uri: {clean_title(document.get('storage_uri')) or '—'}",
    ]
    same_case_group_id = clean_title(document.get("same_case_group_id"))
    if same_case_group_id:
        lines.append(f"- same_case_group_id: `{same_case_group_id}`")
    duplicate_role = clean_title(document.get("duplicate_role"))
    if duplicate_role:
        lines.append(f"- duplicate_role: `{duplicate_role}`")
    duplicate_owner_doc_uid = clean_title(document.get("duplicate_owner_doc_uid"))
    if duplicate_owner_doc_uid:
        lines.append(f"- duplicate_owner_doc_uid: `{duplicate_owner_doc_uid}`")
    canonical_doc_uid = clean_title(document.get("canonical_doc_uid"))
    if canonical_doc_uid and canonical_doc_uid != document["doc_uid"]:
        lines.append(f"- canonical_doc_uid: `{canonical_doc_uid}`")
    superseded_by = clean_title(document.get("superseded_by"))
    if superseded_by:
        lines.append(f"- superseded_by: `{superseded_by}`")
    exclusion_reason = clean_title(document.get("exclusion_reason"))
    if exclusion_reason:
        lines.append(f"- exclusion_reason: {exclusion_reason}")
    return lines


def display_title(document: dict[str, Any]) -> str:
    return clean_title(document.get("canonical_title")) or str(document["doc_uid"])


def status_value(document: dict[str, Any]) -> str:
    return clean_title(document.get("status")) or "missing"


def document_kind(document: dict[str, Any]) -> str:
    return clean_title(document.get("document_kind") or document.get("doc_type")) or "UNKNOWN"


def source_system(document: dict[str, Any]) -> str:
    return clean_title(document.get("source_system")) or "unknown"


def sort_title(document: dict[str, Any]) -> str:
    return clean_title(document.get("canonical_title")) or str(document.get("doc_uid"))


def kind_sort_key(document: dict[str, Any]) -> tuple[int, str]:
    kind = document_kind(document)
    try:
        return (KIND_ORDER.index(kind), kind)
    except ValueError:
        return (len(KIND_ORDER), kind)


def status_sort_key(document: dict[str, Any]) -> tuple[int, str]:
    status = status_value(document)
    try:
        return (STATUS_ORDER.index(status), status)
    except ValueError:
        return (len(STATUS_ORDER), status)


def ordered_counter_items(counter: Counter[str], preferred_order: tuple[str, ...]) -> list[str]:
    known = [item for item in preferred_order if item in counter]
    unknown = sorted(item for item in counter if item not in preferred_order)
    return [*known, *unknown]


def main() -> None:
    args = parse_args()
    runtime = MongoRuntime(MongoConfig(uri=args.mongo_uri, db_name=args.mongo_db))
    with runtime:
        documents = load_documents(runtime)
    output_path = args.output.resolve()
    output_path.write_text(
        build_markdown(documents, mongo_uri=args.mongo_uri, mongo_db=args.mongo_db),
        encoding="utf-8",
    )
    print(output_path)


if __name__ == "__main__":
    main()
