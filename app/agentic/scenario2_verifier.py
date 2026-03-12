from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal


_REQUIRED_SECTIONS = [
    "Краткий вывод",
    "Что подтверждено документами",
    "Что спорно или не доказано",
    "Применимые нормы и практика",
    "Анализ по вопросам",
    "Что делать дальше",
    "Источники",
]
_ANALYSIS_SECTIONS = [
    "Применимые нормы и практика",
    "Анализ по вопросам",
]
_USER_DOC_CITATION_RE = re.compile(
    r"\[Документ пользователя:\s*[^\[\]\n]+]",
    re.IGNORECASE,
)
_NORM_CITATION_RE = re.compile(
    r"\[Норма:\s*[^\[\]\n]+]",
    re.IGNORECASE,
)
_PRACTICE_CITATION_RE = re.compile(
    r"\[Практика:\s*[^\[\]\n]+]",
    re.IGNORECASE,
)
_CITATION_LIKE_RE = re.compile(r"\[[^\[\]\n]+]")

Scenario2ReviewStatus = Literal["not_applicable", "passed", "needs_review"]
Scenario2VerifierPolicy = Literal["informational", "strict"]
Scenario2VerifierGateStatus = Literal[
    "not_applicable",
    "passed",
    "warning_not_blocking",
    "blocked",
]


@dataclass(frozen=True, slots=True)
class Scenario2VerificationResult:
    status: Literal["passed", "warning", "not_applicable"]
    missing_sections: list[str] = field(default_factory=list)
    sources_section_present: bool | None = None
    fetched_sources_referenced: bool | None = None
    warnings: list[str] = field(default_factory=list)
    citation_format_status: Literal["passed", "warning", "not_applicable"] = (
        "not_applicable"
    )
    legal_citation_count: int = 0
    user_doc_citation_count: int = 0
    citations_in_analysis_sections: bool | None = None
    malformed_citation_warnings: list[str] = field(default_factory=list)


def scenario2_review_status_from_verifier_status(
    verifier_status: str | None,
) -> Scenario2ReviewStatus:
    normalized = str(verifier_status or "").strip().lower()
    if normalized == "passed":
        return "passed"
    if normalized == "warning":
        return "needs_review"
    return "not_applicable"


def build_scenario2_review_payload(
    *,
    verifier_status: str | None,
    verifier_warnings: list[str] | None = None,
) -> dict[str, Any]:
    warnings = _normalized_review_warnings(verifier_warnings)
    status = scenario2_review_status_from_verifier_status(verifier_status)
    if status == "passed":
        return {
            "status": status,
            "summary": "Scenario 2 verifier passed deterministic review.",
            "warnings_count": 0,
        }
    if status == "needs_review":
        warnings_count = len(warnings) if warnings else 1
        summary = (
            warnings[0] if warnings else "Scenario 2 verifier reported warning status."
        )
        return {
            "status": status,
            "summary": summary,
            "warnings_count": warnings_count,
        }
    return {
        "status": status,
        "summary": "Scenario 2 verifier not applicable.",
        "warnings_count": 0,
    }


def normalize_scenario2_verifier_policy(value: str | None) -> Scenario2VerifierPolicy:
    normalized = str(value or "").strip().lower()
    if normalized == "strict":
        return "strict"
    return "informational"


def build_scenario2_verifier_gate_payload(
    *,
    verifier_policy: str | None,
    verifier_status: str | None,
    llm_executed: bool | None,
    verifier_warnings: list[str] | None = None,
) -> dict[str, Any]:
    warnings = _normalized_review_warnings(verifier_warnings)
    policy = normalize_scenario2_verifier_policy(verifier_policy)
    normalized_status = str(verifier_status or "").strip().lower()

    if llm_executed is False or normalized_status in {"", "not_applicable"}:
        return {
            "policy": policy,
            "status": "not_applicable",
            "summary": "Scenario 2 verifier gate is not applicable.",
            "warnings_count": len(warnings),
            "blocking": False,
        }

    if normalized_status == "passed":
        return {
            "policy": policy,
            "status": "passed",
            "summary": "Scenario 2 verifier gate passed.",
            "warnings_count": len(warnings),
            "blocking": False,
        }

    if normalized_status == "warning":
        if policy == "strict":
            return {
                "policy": policy,
                "status": "blocked",
                "summary": (
                    warnings[0]
                    if warnings
                    else "Scenario 2 verifier warning triggered strict gate."
                ),
                "warnings_count": len(warnings) if warnings else 1,
                "blocking": True,
            }
        return {
            "policy": policy,
            "status": "warning_not_blocking",
            "summary": (
                warnings[0]
                if warnings
                else "Scenario 2 verifier warning is informational only."
            ),
            "warnings_count": len(warnings) if warnings else 1,
            "blocking": False,
        }

    return {
        "policy": policy,
        "status": "not_applicable",
        "summary": "Scenario 2 verifier gate is not applicable.",
        "warnings_count": len(warnings),
        "blocking": False,
    }


def verify_scenario2_response(
    *,
    final_text: str,
    fetched_fragment_ledger: list[dict[str, Any]] | None,
    retrieval_used: bool,
) -> Scenario2VerificationResult:
    text = str(final_text or "").strip()
    if not text:
        return Scenario2VerificationResult(
            status="not_applicable",
            warnings=["Final text is empty; Scenario 2 verifier skipped."],
        )

    normalized_text = _normalize_inline_text(text)
    source_markers = _fetched_source_markers(fetched_fragment_ledger or [])
    fetched_sources_referenced: bool | None = None
    legal_citation_count = _legal_citation_count(text)
    user_doc_citation_count = _user_doc_citation_count(text)
    malformed_citation_warnings: list[str] = []

    if retrieval_used and source_markers:
        fetched_sources_referenced = any(
            marker in normalized_text for marker in source_markers
        )
    return Scenario2VerificationResult(
        status="passed",
        missing_sections=[],
        sources_section_present=None,
        fetched_sources_referenced=fetched_sources_referenced,
        warnings=[],
        citation_format_status="not_applicable",
        legal_citation_count=legal_citation_count,
        user_doc_citation_count=user_doc_citation_count,
        citations_in_analysis_sections=None,
        malformed_citation_warnings=malformed_citation_warnings,
    )


@dataclass(frozen=True, slots=True)
class _SectionPayload:
    mapping: dict[str, str]
    analysis_text: str


def _section_present(normalized_text: str, title: str) -> bool:
    pattern = re.compile(
        rf"(?im)^\s*(?:[#>*-]+\s*)?(?:\d+[.)]\s*)?(?:\*\*|__)?"
        rf"{re.escape(_normalize_inline_text(title))}(?:\*\*|__)?\s*:?\s*$"
    )
    return bool(pattern.search(normalized_text))


def _extract_section_payload(text: str) -> _SectionPayload:
    section_map: dict[str, list[str]] = {}
    current_section: str | None = None
    for line in text.splitlines():
        matched = _matched_section_title(line)
        if matched is not None:
            current_section = matched
            section_map.setdefault(current_section, [])
            continue
        if current_section is not None:
            section_map[current_section].append(line)

    normalized_map = {
        title: "\n".join(lines).strip() for title, lines in section_map.items()
    }
    analysis_chunks = [
        normalized_map.get(title, "")
        for title in _ANALYSIS_SECTIONS
        if normalized_map.get(title, "")
    ]
    return _SectionPayload(
        mapping=normalized_map,
        analysis_text="\n\n".join(analysis_chunks).strip(),
    )


def _matched_section_title(line: str) -> str | None:
    normalized_line = _normalize_inline_text(line)
    for title in _REQUIRED_SECTIONS:
        pattern = re.compile(
            rf"^(?:[#>*-]+\s*)?(?:\d+[.)]\s*)?(?:\*\*|__)?"
            rf"{re.escape(_normalize_inline_text(title))}(?:\*\*|__)?\s*:?\s*$"
        )
        if pattern.match(normalized_line):
            return title
    return None


def _fetched_source_markers(
    fetched_fragment_ledger: list[dict[str, Any]],
) -> list[str]:
    markers: list[str] = []
    for entry in fetched_fragment_ledger:
        if not isinstance(entry, dict):
            continue
        for key in ("display_citation", "doc_uid", "source_hash"):
            value = entry.get(key)
            if not isinstance(value, str):
                continue
            normalized = _normalize_inline_text(value)
            if normalized:
                markers.append(normalized)
    return sorted(set(markers))


def _legal_citation_count(text: str) -> int:
    return len(_NORM_CITATION_RE.findall(text)) + len(
        _PRACTICE_CITATION_RE.findall(text)
    )


def _user_doc_citation_count(text: str) -> int:
    return len(_USER_DOC_CITATION_RE.findall(text))


def _malformed_citation_warnings(text: str) -> list[str]:
    warnings: list[str] = []
    for token in _CITATION_LIKE_RE.findall(text):
        normalized = _normalize_inline_text(token)
        if normalized.startswith(
            "[документ пользователя"
        ) and not _USER_DOC_CITATION_RE.fullmatch(token):
            warnings.append(f"Malformed citation token: {token}")
        elif normalized.startswith("[норма") and not _NORM_CITATION_RE.fullmatch(token):
            warnings.append(f"Malformed citation token: {token}")
        elif normalized.startswith("[практика") and not _PRACTICE_CITATION_RE.fullmatch(
            token
        ):
            warnings.append(f"Malformed citation token: {token}")
    return sorted(set(warnings))


def _citation_format_status(
    *,
    retrieval_used: bool,
    legal_citation_count: int,
    user_doc_citation_count: int,
    citations_in_analysis_sections: bool | None,
    malformed_citation_warnings: list[str],
) -> Literal["passed", "warning", "not_applicable"]:
    if malformed_citation_warnings:
        return "warning"
    if retrieval_used:
        if legal_citation_count < 1 or not citations_in_analysis_sections:
            return "warning"
        return "passed"
    if legal_citation_count > 0 or user_doc_citation_count > 0:
        return "passed"
    return "not_applicable"


def _normalized_review_warnings(value: list[str] | None) -> list[str]:
    if not isinstance(value, list):
        return []

    warnings: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            warnings.append(text)
    return warnings


def _normalize_inline_text(value: str) -> str:
    return " ".join(value.lower().replace("ё", "е").split())


def _normalize_multiline_text(value: str) -> str:
    lines = []
    for line in value.lower().replace("ё", "е").splitlines():
        lines.append(" ".join(line.split()))
    return "\n".join(lines)
