from __future__ import annotations

import argparse
import json
from pathlib import Path

from pymongo import MongoClient

from app.legal_memo.config import LegalMemoConfig
from app.legal_memo.service import StrategicMemoService, UserDocumentInput


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the legal memo agent contour on user markdown documents.",
    )
    parser.add_argument(
        "--user-message-file",
        required=True,
        help="Path to a UTF-8 text file with the user message.",
    )
    parser.add_argument(
        "--user-doc",
        action="append",
        required=True,
        help="Path to a user markdown document. Repeat for multiple documents.",
    )
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017")
    parser.add_argument("--mongo-db", default="kaucja_legal_corpus")
    parser.add_argument("--master-collection", default="documents_cas_law_v2_2_prod_v3")
    parser.add_argument("--anchor-collection", default="legal_anchor_nodes_proto_v1")
    parser.add_argument("--max-search-calls", type=int, default=6)
    parser.add_argument("--max-docs-per-search", type=int, default=5)
    parser.add_argument("--max-anchors-per-search", type=int, default=8)
    parser.add_argument("--legal-refs-left", type=int, default=10)
    parser.add_argument("--model", default="gpt-5.4")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    user_message = Path(args.user_message_file).read_text(encoding="utf-8")
    user_documents = [
        UserDocumentInput(
            doc_id=Path(path).name,
            file_name=Path(path).name,
            markdown=Path(path).read_text(encoding="utf-8"),
        )
        for path in args.user_doc
    ]
    config_kwargs = {
        "mongo_uri": args.mongo_uri,
        "mongo_db_name": args.mongo_db,
        "master_collection_name": args.master_collection,
        "anchor_collection_name": args.anchor_collection,
        "max_search_calls": args.max_search_calls,
        "max_docs_per_search": args.max_docs_per_search,
        "max_anchors_per_search": args.max_anchors_per_search,
        "legal_refs_left": args.legal_refs_left,
        "model": args.model,
    }
    if args.data_dir:
        config_kwargs["data_dir"] = Path(args.data_dir)
    config = LegalMemoConfig.from_settings(**config_kwargs)

    mongo_client = MongoClient(config.mongo_uri)
    try:
        mongo_db = mongo_client[config.mongo_db_name]
        service = StrategicMemoService(config=config, mongo_db=mongo_db)
        result = service.run(
            user_message=user_message,
            user_documents=user_documents,
            session_id=args.session_id,
            run_id=args.run_id,
        )
    finally:
        mongo_client.close()

    summary = {
        "session_id": result.session_id,
        "run_id": result.run_id,
        "artifacts_root_path": str(result.artifacts_root_path),
        "memo_markdown_path": str(result.memo_markdown_path),
        "citation_register_path": str(result.citation_register_path),
        "search_trace_path": str(result.search_trace_path),
        "qc_status": result.qc_report.status,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
