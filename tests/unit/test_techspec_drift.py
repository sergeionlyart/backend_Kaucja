import json
from pathlib import Path


def test_techspec_prompt_drift() -> None:
    """Verifies that the canonical prompt is byte-for-byte identical to the TechSpec prompt."""
    techspec_path = Path("docs/TECH_SPEC_Prompt.md")
    canonical_prompt_path = Path("app/prompts/canonical_prompt.txt")

    assert techspec_path.exists(), "TECH_SPEC_Prompt.md is missing from docs"
    assert canonical_prompt_path.exists(), (
        "canonical_prompt.txt is missing from app/prompts"
    )

    techspec_content = techspec_path.read_text(encoding="utf-8")
    canonical_prompt = canonical_prompt_path.read_text(encoding="utf-8")

    # Needs to be a rigid byte-for-byte match
    assert techspec_content == canonical_prompt, (
        "Canonical prompt has drifted from TECH_SPEC_Prompt.md"
    )


def test_techspec_schema_drift() -> None:
    """Verifies that the canonical schema is exactly what is inside the TechSpec MVP document."""
    techspec_mvp_path = Path("docs/TECH_SPEC_MVP.md")
    canonical_schema_path = Path("app/schemas/canonical_schema.json")

    assert techspec_mvp_path.exists(), "TECH_SPEC_MVP.md is missing from docs"
    assert canonical_schema_path.exists(), (
        "canonical_schema.json is missing from app/schemas"
    )

    techspec_mvp_content = techspec_mvp_path.read_text(encoding="utf-8")
    canonical_schema_json = json.loads(
        canonical_schema_path.read_text(encoding="utf-8")
    )

    # Extract the schema out of the Markdown file
    # We look for the start and end of the JSON block under section 12.3
    lines = techspec_mvp_content.splitlines()
    in_schema_block = False
    schema_lines = []

    for line in lines:
        if "## **12.3 JSON Schema ответа (версия v001)**" in line:
            in_schema_block = True
            continue

        if in_schema_block:
            if line.startswith("{"):
                schema_lines.append(line)
            elif schema_lines and line.startswith("}"):
                schema_lines.append(line)
                break  # Reached the end of the schema block
            elif schema_lines:
                schema_lines.append(line)

    extracted_schema_text = "\n".join(schema_lines)
    assert extracted_schema_text, (
        "Failed to extract JSON schema snippet from TECH_SPEC_MVP.md"
    )

    # Unescape Markdown special characters \_, \[, \] and \# that might exist in the raw markdown code block
    extracted_schema_text = (
        extracted_schema_text.replace(r"\_", "_")
        .replace(r"\[", "[")
        .replace(r"\]", "]")
        .replace(r"\#", "#")
    )

    try:
        extracted_schema_json = json.loads(extracted_schema_text)
    except json.JSONDecodeError as error:
        assert False, (
            f"Failed to parse the JSON schema extracted from TECH_SPEC_MVP.md: {error}"
        )

    assert canonical_schema_json == extracted_schema_json, (
        "Canonical schema has drifted from the spec in TECH_SPEC_MVP.md section 12.3"
    )
