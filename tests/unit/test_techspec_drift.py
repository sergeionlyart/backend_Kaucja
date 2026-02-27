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

    # Extract the schema out of the Markdown file robustly.
    # The JSON schema inside Section 12.3 is an unfenced block starting with `{` and ending with `}`.
    schema_start_idx = techspec_mvp_content.find(
        "## **12.3 JSON Schema ответа (версия v001)**"
    )
    assert schema_start_idx != -1, "Failed to locate section 12.3 in TECH_SPEC_MVP.md"

    # Find the actual json block payload start by looking for the very first `{`
    json_start = techspec_mvp_content.find("{", schema_start_idx)
    assert json_start != -1, (
        "Failed to locate start of JSON schema block under section 12.3"
    )

    # We find the furthest terminating `}` that balances the dictionary safely.
    # For a deterministic schema this is the last `}` before the next `---` or end of file.
    next_section = techspec_mvp_content.find("---", json_start)
    if next_section == -1:
        next_section = len(techspec_mvp_content)

    extracted_schema_text = techspec_mvp_content[json_start:next_section].strip()

    # Trim any trailing markdown non-json text if trailing formatting exists.
    last_brace = extracted_schema_text.rfind("}")
    assert last_brace != -1, "Failed to find closing brace of JSON schema"
    extracted_schema_text = extracted_schema_text[: last_brace + 1]

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
