from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.llm_client.base import LLMResult
from app.pipeline.pack_documents import DocumentMarkdown, pack_documents
from app.pipeline.validate_output import validate_output


class MockLLMClient:
    def __init__(self, parsed_json: dict[str, Any]) -> None:
        self._parsed_json = parsed_json

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_content: str,
        json_schema: dict[str, Any],
        model: str,
        params: dict[str, Any],
        run_meta: dict[str, Any],
    ) -> LLMResult:
        del system_prompt, json_schema, model, params, run_meta
        assert "<BEGIN_DOCUMENTS>" in user_content
        return LLMResult(
            raw_text=json.dumps(self._parsed_json),
            parsed_json=self._parsed_json,
            raw_response={"mock": True},
            usage_raw={},
            usage_normalized={
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2,
                "thoughts_tokens": None,
            },
            cost={"llm_cost_usd": 0.0},
            timings={"t_llm_total_ms": 1.0},
        )


def _load_schema() -> dict[str, Any]:
    path = Path("app/prompts/kaucja_gap_analysis/v001/schema.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _valid_parsed_json(schema: dict[str, Any]) -> dict[str, Any]:
    item_ids = schema["$defs"]["checklist_item"]["properties"]["item_id"]["enum"]
    checklist = []
    for idx, item_id in enumerate(item_ids):
        status = "confirmed" if idx == 0 else "missing"
        checklist.append(
            {
                "item_id": item_id,
                "importance": "critical" if idx == 0 else "recommended",
                "status": status,
                "what_it_supports": "support",
                "findings": [
                    {
                        "doc_id": "0000001",
                        "quote": "quoted",
                        "why_this_quote_matters": "reason",
                    }
                ]
                if status == "confirmed"
                else [],
                "missing_what_exactly": "missing",
                "request_from_user": {
                    "type": "upload_document",
                    "ask": "upload",
                    "examples": ["example"],
                },
                "confidence": "high",
            }
        )

    fact = {
        "value": "v",
        "status": "confirmed",
        "sources": [{"doc_id": "0000001", "quote": "q"}],
    }

    return {
        "case_facts": {
            "parties": {"tenant": fact},
            "property_address": fact,
            "lease_type": fact,
            "key_dates": {"start": fact},
            "money": {"deposit": fact},
            "notes": [],
        },
        "checklist": checklist,
        "critical_gaps_summary": [],
        "next_questions_to_user": [],
        "conflicts_and_red_flags": [],
        "ocr_quality_warnings": [],
    }


def test_pack_llm_validate_integration() -> None:
    schema = _load_schema()
    packed = pack_documents(
        [
            DocumentMarkdown(
                doc_id="0000001",
                markdown="doc1 [tbl-0.html](tbl-0.html)",
            ),
            DocumentMarkdown(
                doc_id="0000002",
                markdown="doc2 ![img-0.png](img-0.png)",
            ),
        ]
    )

    llm = MockLLMClient(parsed_json=_valid_parsed_json(schema))
    llm_result = llm.generate_json(
        system_prompt="system",
        user_content=packed,
        json_schema=schema,
        model="gpt-5.1",
        params={},
        run_meta={},
    )

    validation = validate_output(parsed_json=llm_result.parsed_json, schema=schema)

    assert '<DOC_START id="0000001">' in packed
    assert "[tbl-0.html](tbl-0.html)" in packed
    assert "![img-0.png](img-0.png)" in packed
    assert validation.valid is True
