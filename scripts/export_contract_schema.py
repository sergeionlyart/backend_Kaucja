#!/usr/bin/env python3
"""Export canonical JSON schema for DocumentAnalyzeResponse.

Usage:
    python scripts/export_contract_schema.py

Output:
    docs/contracts/document_analyze_response.schema.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.api.models import DocumentAnalyzeResponse  # noqa: E402


def main() -> None:
    schema = DocumentAnalyzeResponse.model_json_schema()
    out_dir = PROJECT_ROOT / "docs" / "contracts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "document_analyze_response.schema.json"
    out_path.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"✅ Schema exported to {out_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
