from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    schema_errors: list[str]
    invariant_errors: list[str]

    @property
    def errors(self) -> list[str]:
        return self.schema_errors + self.invariant_errors


def validate_output(
    *,
    parsed_json: dict[str, Any],
    schema: dict[str, Any],
) -> ValidationResult:
    schema_errors = _validate_schema(parsed_json=parsed_json, schema=schema)
    invariant_errors = _validate_invariants(parsed_json=parsed_json, schema=schema)

    return ValidationResult(
        valid=not schema_errors and not invariant_errors,
        schema_errors=schema_errors,
        invariant_errors=invariant_errors,
    )


def _validate_schema(
    *, parsed_json: dict[str, Any], schema: dict[str, Any]
) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(parsed_json), key=lambda item: item.path)

    messages: list[str] = []
    for error in errors:
        path = "/".join(str(item) for item in error.path)
        if path:
            messages.append(f"{path}: {error.message}")
        else:
            messages.append(error.message)

    return messages


def _validate_invariants(
    *, parsed_json: dict[str, Any], schema: dict[str, Any]
) -> list[str]:
    errors: list[str] = []

    checklist = parsed_json.get("checklist")
    if not isinstance(checklist, list):
        return ["checklist must be an array for invariant validation"]

    expected_item_ids = _expected_item_ids_from_schema(schema)
    actual_item_ids = [
        str(item.get("item_id")) for item in checklist if isinstance(item, dict)
    ]

    if len(actual_item_ids) != 22:
        errors.append(
            f"checklist must contain exactly 22 items, got {len(actual_item_ids)}"
        )

    duplicate_ids = _find_duplicates(actual_item_ids)
    if duplicate_ids:
        errors.append(
            f"duplicate checklist item_id values: {', '.join(sorted(duplicate_ids))}"
        )

    missing_ids = sorted(expected_item_ids.difference(actual_item_ids))
    if missing_ids:
        errors.append(f"missing checklist item_id values: {', '.join(missing_ids)}")

    unexpected_ids = sorted(set(actual_item_ids).difference(expected_item_ids))
    if unexpected_ids:
        errors.append(
            f"unexpected checklist item_id values: {', '.join(unexpected_ids)}"
        )

    for index, checklist_item in enumerate(checklist):
        if not isinstance(checklist_item, dict):
            errors.append(f"checklist[{index}] must be an object")
            continue

        status = str(checklist_item.get("status") or "")

        if status == "confirmed":
            findings = checklist_item.get("findings")
            if not isinstance(findings, list) or not findings:
                errors.append(
                    f"checklist[{index}] confirmed item must include findings"
                )
            elif not _has_finding_with_doc_and_quote(findings):
                errors.append(
                    f"checklist[{index}] confirmed item needs finding with doc_id and quote"
                )

        if status == "missing":
            request_from_user = checklist_item.get("request_from_user")
            ask = ""
            if isinstance(request_from_user, dict):
                ask = str(request_from_user.get("ask") or "").strip()
            if not ask:
                errors.append(
                    f"checklist[{index}] missing item requires request_from_user.ask"
                )

    next_questions = parsed_json.get("next_questions_to_user")
    if isinstance(next_questions, list) and len(next_questions) > 10:
        errors.append("next_questions_to_user must contain at most 10 items")

    return errors


def _expected_item_ids_from_schema(schema: dict[str, Any]) -> set[str]:
    defs = schema.get("$defs", {})
    if not isinstance(defs, dict):
        return set()

    checklist_item = defs.get("checklist_item", {})
    if not isinstance(checklist_item, dict):
        return set()

    properties = checklist_item.get("properties", {})
    if not isinstance(properties, dict):
        return set()

    item_id = properties.get("item_id", {})
    if not isinstance(item_id, dict):
        return set()

    values = item_id.get("enum")
    if not isinstance(values, list):
        return set()

    return {str(value) for value in values}


def _find_duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()

    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)

    return duplicates


def _has_finding_with_doc_and_quote(findings: list[Any]) -> bool:
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        doc_id = str(finding.get("doc_id") or "").strip()
        quote = str(finding.get("quote") or "").strip()
        if doc_id and quote:
            return True

    return False
