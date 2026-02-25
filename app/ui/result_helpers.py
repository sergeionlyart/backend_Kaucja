from __future__ import annotations

from typing import Any


def build_checklist_rows(parsed_json: dict[str, Any] | None) -> list[list[str]]:
    checklist = _checklist(parsed_json)
    rows: list[list[str]] = []
    for item in checklist:
        rows.append(
            [
                str(item.get("item_id", "")),
                str(item.get("importance", "")),
                str(item.get("status", "")),
                str(item.get("confidence", "")),
            ]
        )
    return rows


def build_gap_rows(parsed_json: dict[str, Any] | None) -> list[list[str]]:
    checklist = _checklist(parsed_json)
    rows: list[list[str]] = []
    for item in checklist:
        request = item.get("request_from_user")
        ask = ""
        if isinstance(request, dict):
            ask = str(request.get("ask", "")).strip()
        if ask:
            rows.append([str(item.get("item_id", "")), ask])
    return rows


def checklist_item_ids(parsed_json: dict[str, Any] | None) -> list[str]:
    checklist = _checklist(parsed_json)
    return [str(item.get("item_id", "")) for item in checklist if item.get("item_id")]


def render_checklist_details(
    parsed_json: dict[str, Any] | None,
    item_id: str,
) -> str:
    checklist = _checklist(parsed_json)
    target = _find_item(checklist=checklist, item_id=item_id)
    if target is None:
        return "No details available for selected item."

    lines: list[str] = [
        f"item_id: {target.get('item_id', '')}",
        f"importance: {target.get('importance', '')}",
        f"status: {target.get('status', '')}",
        f"confidence: {target.get('confidence', '')}",
        "",
        "what_it_supports:",
        str(target.get("what_it_supports", "")),
        "",
        "missing_what_exactly:",
        str(target.get("missing_what_exactly", "")),
        "",
        "request_from_user:",
    ]

    request = target.get("request_from_user")
    if isinstance(request, dict):
        lines.append(f"type: {request.get('type', '')}")
        lines.append(f"ask: {request.get('ask', '')}")
        examples = request.get("examples")
        if isinstance(examples, list) and examples:
            lines.append("examples:")
            lines.extend(f"- {example}" for example in examples)
    else:
        lines.append("(empty)")

    lines.append("")
    lines.append("findings:")
    findings = target.get("findings")
    if isinstance(findings, list) and findings:
        for index, finding in enumerate(findings, start=1):
            if not isinstance(finding, dict):
                continue
            lines.append(f"{index}. doc_id: {finding.get('doc_id', '')}")
            lines.append(f"   quote: {finding.get('quote', '')}")
            lines.append(f"   why: {finding.get('why_this_quote_matters', '')}")
    else:
        lines.append("(empty)")

    return "\n".join(lines)


def _checklist(parsed_json: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(parsed_json, dict):
        return []
    checklist = parsed_json.get("checklist")
    if not isinstance(checklist, list):
        return []
    return [item for item in checklist if isinstance(item, dict)]


def _find_item(
    *, checklist: list[dict[str, Any]], item_id: str
) -> dict[str, Any] | None:
    needle = item_id.strip()
    if not needle:
        return None
    for item in checklist:
        if str(item.get("item_id", "")) == needle:
            return item
    return None
