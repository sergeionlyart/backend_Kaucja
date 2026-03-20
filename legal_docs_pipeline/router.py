"""Rule-based routing for the NormaDepo pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .constants import DocumentFamily, PromptProfile
from .schemas import ClassificationResult

_NORMATIVE_SOURCE_SYSTEMS = {"eli_pl", "isap_pl", "lex_pl", "eurlex_eu"}
_JUDICIAL_SOURCE_SYSTEMS = {"sn_pl", "saos_pl", "courts_pl", "curia_eu"}
_CONSUMER_ADMIN_SOURCE_SYSTEMS = {"uokik_pl"}
_LEGAL_SOURCE_SYSTEMS = (
    _NORMATIVE_SOURCE_SYSTEMS
    | _JUDICIAL_SOURCE_SYSTEMS
    | _CONSUMER_ADMIN_SOURCE_SYSTEMS
)
_DISCOVERY_TITLE_MARKERS = (
    "search",
    "snapshot",
    "relevant links",
    "result links",
    "factsheet",
    "discovery",
    "index page",
)
_DISCOVERY_TEXT_MARKERS = (
    "result links",
    "query url",
    "this entry is a search/discovery page",
    "generated at",
    "markdown export",
    "search snapshot",
    "relevant links",
)
_NORMATIVE_TITLE_MARKERS = (
    "ustawa",
    "rozporządzenie",
    "obwieszczenie",
    "dyrektywa",
    "directive",
    "regulation",
    "kodeks",
)
_NORMATIVE_TEXT_MARKERS = (
    "art.",
    "§",
    "dz. u.",
    "ustawa",
    "rozporządzenie",
    "dyrektywa",
    "directive",
    "regulation (eu)",
)
_JUDICIAL_TITLE_MARKERS = (
    "wyrok",
    "postanowienie",
    "uchwała",
    "judgment of the court",
    "case c-",
    "case t-",
)
_JUDICIAL_TEXT_MARKERS = (
    "wyrok",
    "postanowienie",
    "uchwała",
    "sygn. akt",
    "judgment of the court",
    "case c-",
    "case t-",
)
_CONSUMER_ADMIN_MARKERS = (
    "uokik",
    "prezes urzędu ochrony konkurencji i konsumentów",
    "prezes uokik",
    "consumer protection",
    "niedozwolone postanowienia",
)
_COMMENTARY_TITLE_MARKERS = (
    "komentarz",
    "analysis",
    "guide",
    "poradnik",
    "article",
    "blog",
)
_COMMENTARY_TEXT_MARKERS = (
    "autor:",
    "author:",
    "published",
    "opublikowano",
    "komentarz",
    "poradnik",
    "analysis",
    "guide",
)


@dataclass(frozen=True, slots=True)
class RoutingInput:
    relative_path: str
    file_name: str
    title: str | None
    metadata: dict[str, Any]
    normalized_text: str


class DocumentRouter(Protocol):
    def route(self, payload: RoutingInput) -> ClassificationResult:
        """Classify a document before prompt resolution."""


class RuleBasedDocumentRouter:
    def __init__(self, *, router_version: str) -> None:
        self._router_version = router_version

    def route(self, payload: RoutingInput) -> ClassificationResult:
        title = (payload.title or "").strip()
        lowered_path = payload.relative_path.lower()
        lowered_title = title.lower()
        lowered_text = payload.normalized_text.lower()
        source_system = str(
            payload.metadata.get("original_source_system")
            or payload.metadata.get("resolved_source_system")
            or ""
        ).strip()

        signals = _build_signal_bucket(
            relative_path=payload.relative_path,
            source_system=source_system,
        )

        if _is_corpus_readme(payload.file_name):
            signals["matched_rules"].append("file_name:corpus_readme")
            return _build_result(
                family=DocumentFamily.CORPUS_README,
                prompt_profile=PromptProfile.SKIP_NON_TARGET,
                annotatable=False,
                confidence=0.99,
                router_version=self._router_version,
                signals=signals,
                skip_reason="service_readme",
            )

        if _match_discovery(
            signals,
            lowered_path,
            lowered_title,
            lowered_text,
            source_system,
        ):
            return _build_result(
                family=DocumentFamily.DISCOVERY_REFERENCE,
                prompt_profile=PromptProfile.ADDON_DISCOVERY,
                annotatable=True,
                confidence=0.9 if source_system else 0.82,
                router_version=self._router_version,
                signals=signals,
                document_type_code="discovery_page",
            )

        if source_system in _CONSUMER_ADMIN_SOURCE_SYSTEMS or _contains_any(
            lowered_title + "\n" + lowered_text,
            _CONSUMER_ADMIN_MARKERS,
        ):
            signals["matched_rules"].append("consumer_admin")
            return _build_result(
                family=DocumentFamily.CONSUMER_ADMIN,
                prompt_profile=PromptProfile.ADDON_UOKIK,
                annotatable=True,
                confidence=0.96 if source_system else 0.85,
                router_version=self._router_version,
                signals=signals,
                document_type_code=_infer_consumer_admin_type_code(
                    lowered_title=lowered_title,
                    lowered_text=lowered_text,
                ),
            )

        if source_system in _NORMATIVE_SOURCE_SYSTEMS or _contains_any(
            lowered_title,
            _NORMATIVE_TITLE_MARKERS,
        ):
            _collect_matches(
                signals["title_markers"],
                lowered_title,
                _NORMATIVE_TITLE_MARKERS,
            )
            _collect_matches(
                signals["text_markers"],
                lowered_text,
                _NORMATIVE_TEXT_MARKERS,
            )
            signals["matched_rules"].append("normative_act")
            return _build_result(
                family=DocumentFamily.NORMATIVE_ACT,
                prompt_profile=PromptProfile.ADDON_NORMATIVE,
                annotatable=True,
                confidence=0.95 if source_system else 0.8,
                router_version=self._router_version,
                signals=signals,
                document_type_code=_infer_normative_type_code(
                    lowered_title=lowered_title,
                    lowered_text=lowered_text,
                    source_system=source_system,
                ),
            )

        if source_system in _JUDICIAL_SOURCE_SYSTEMS or _contains_any(
            lowered_title + "\n" + lowered_text,
            _JUDICIAL_TITLE_MARKERS + _JUDICIAL_TEXT_MARKERS,
        ):
            _collect_matches(
                signals["title_markers"],
                lowered_title,
                _JUDICIAL_TITLE_MARKERS,
            )
            _collect_matches(
                signals["text_markers"],
                lowered_text,
                _JUDICIAL_TEXT_MARKERS,
            )
            signals["matched_rules"].append("judicial_decision")
            return _build_result(
                family=DocumentFamily.JUDICIAL_DECISION,
                prompt_profile=PromptProfile.ADDON_CASE_LAW,
                annotatable=True,
                confidence=0.95 if source_system else 0.83,
                router_version=self._router_version,
                signals=signals,
                document_type_code=_infer_judicial_type_code(
                    lowered_title=lowered_title,
                    lowered_text=lowered_text,
                    source_system=source_system,
                ),
            )

        if _is_commentary(
            metadata=payload.metadata,
            lowered_path=lowered_path,
            lowered_title=lowered_title,
            lowered_text=lowered_text,
            signals=signals,
        ):
            signals["matched_rules"].append("commentary_article")
            return _build_result(
                family=DocumentFamily.COMMENTARY_ARTICLE,
                prompt_profile=PromptProfile.ADDON_COMMENTARY,
                annotatable=True,
                confidence=0.76,
                router_version=self._router_version,
                signals=signals,
                document_type_code="commentary_article",
            )

        signals["matched_rules"].append("unknown")
        return _build_result(
            family=DocumentFamily.UNKNOWN,
            prompt_profile=PromptProfile.SKIP_NON_TARGET,
            annotatable=False,
            confidence=0.0,
            router_version=self._router_version,
            signals=signals,
            skip_reason="rule_router_no_match",
        )


def _build_signal_bucket(
    *,
    relative_path: str,
    source_system: str,
) -> dict[str, Any]:
    top_level_dir = relative_path.split("/", maxsplit=1)[0]
    folder_signals: list[str] = []
    if top_level_dir:
        folder_signals.append(top_level_dir)
    if relative_path.lower().startswith("eu_"):
        folder_signals.append("eu_folder")
    if relative_path.lower().startswith("pl_"):
        folder_signals.append("pl_folder")

    metadata_signals: list[str] = []
    if source_system:
        metadata_signals.append(f"source_system:{source_system}")

    return {
        "folder_signals": folder_signals,
        "metadata_signals": metadata_signals,
        "title_markers": [],
        "text_markers": [],
        "matched_rules": [],
    }


def _build_result(
    *,
    family: DocumentFamily,
    prompt_profile: PromptProfile,
    annotatable: bool,
    confidence: float,
    router_version: str,
    signals: dict[str, Any],
    document_type_code: str | None = None,
    skip_reason: str | None = None,
) -> ClassificationResult:
    return ClassificationResult(
        document_family=family,
        document_type_code=document_type_code,
        prompt_profile=prompt_profile,
        annotatable=annotatable,
        classifier_method="rule_based",
        confidence=confidence,
        router_version=router_version,
        signals=signals,
        skip_reason=skip_reason,
    )


def _match_discovery(
    signals: dict[str, Any],
    lowered_path: str,
    lowered_title: str,
    lowered_text: str,
    source_system: str,
) -> bool:
    discovery_path = "discovery" in lowered_path or "reference" in lowered_path
    if discovery_path:
        signals["folder_signals"].append("discovery_path")
    content_text = _extract_content_text(lowered_text)
    _collect_matches(signals["title_markers"], lowered_title, _DISCOVERY_TITLE_MARKERS)
    _collect_matches(signals["text_markers"], content_text, _DISCOVERY_TEXT_MARKERS)
    explicit_discovery = discovery_path or bool(
        signals["title_markers"] or signals["text_markers"]
    )
    url_count = content_text.count("http://") + content_text.count("https://")
    if url_count >= 3:
        signals["text_markers"].append(f"content_url_count:{url_count}")
    if source_system in _LEGAL_SOURCE_SYSTEMS and not explicit_discovery:
        return False
    return explicit_discovery or url_count >= 3


def _extract_content_text(lowered_text: str) -> str:
    marker = "## content"
    content_index = lowered_text.find(marker)
    if content_index == -1:
        return lowered_text
    return lowered_text[content_index + len(marker) :].strip()


def _extract_leading_body_text(lowered_text: str, *, max_lines: int = 40) -> str:
    content_text = _extract_content_text(lowered_text)
    lines = [line.strip() for line in content_text.splitlines() if line.strip()]
    return "\n".join(lines[:max_lines])


def _is_commentary(
    *,
    metadata: dict[str, Any],
    lowered_path: str,
    lowered_title: str,
    lowered_text: str,
    signals: dict[str, Any],
) -> bool:
    article_focus = str(metadata.get("article_focus") or "").strip()
    if article_focus:
        signals["metadata_signals"].append("article_focus")
    if any(marker in lowered_path for marker in ("commentary", "articles", "blog")):
        signals["folder_signals"].append("commentary_path")

    _collect_matches(
        signals["title_markers"],
        lowered_title,
        _COMMENTARY_TITLE_MARKERS,
    )
    _collect_matches(
        signals["text_markers"],
        lowered_text,
        _COMMENTARY_TEXT_MARKERS,
    )
    return bool(article_focus) or bool(
        signals["title_markers"] or signals["text_markers"]
    )


def _infer_normative_type_code(
    *,
    lowered_title: str,
    lowered_text: str,
    source_system: str,
) -> str | None:
    if "directive" in lowered_title or source_system == "eurlex_eu":
        if "directive" in lowered_title or "dyrektywa" in lowered_title:
            return "eu_directive"
        if "regulation" in lowered_title or "rozporządzenie" in lowered_title:
            return "eu_regulation"
        return "eu_normative_act"
    if "rozporządzenie" in lowered_title:
        return "pl_regulation"
    if "kodeks" in lowered_title:
        return "pl_code"
    if "ustawa" in lowered_title or "dz. u." in lowered_text:
        return "pl_statute"
    if "excerpt" in lowered_title or "fragment" in lowered_title:
        return "normative_excerpt"
    return None


def _infer_judicial_type_code(
    *,
    lowered_title: str,
    lowered_text: str,
    source_system: str,
) -> str | None:
    leading_text = _extract_leading_body_text(lowered_text)
    title_and_leading = lowered_title + "\n" + leading_text
    if source_system == "curia_eu" or "judgment of the court" in title_and_leading:
        return "eu_judgment"
    primary_form = _infer_primary_polish_decision_form(lowered_title)
    if primary_form is None:
        primary_form = _infer_primary_polish_decision_form(leading_text)
    if primary_form == "uchwała":
        return "pl_resolution"
    if primary_form == "postanowienie":
        return "pl_order"
    if primary_form == "wyrok":
        return "pl_judgment"
    if "sygn. akt" in leading_text:
        return "pl_judgment"
    return None


def _infer_consumer_admin_type_code(
    *,
    lowered_title: str,
    lowered_text: str,
) -> str | None:
    if "decyzja" in lowered_title or "decyzja" in lowered_text:
        return "uokik_decision"
    if "stanowisko" in lowered_title or "guidance" in lowered_text:
        return "uokik_guidance"
    return "uokik_material"


def _is_corpus_readme(file_name: str) -> bool:
    upper_name = file_name.upper()
    return upper_name == "README.MD" or upper_name.endswith("_README.MD")


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _infer_primary_polish_decision_form(text: str) -> str | None:
    candidates: list[tuple[int, str]] = []
    for marker in ("wyrok", "postanowienie", "uchwała"):
        index = text.find(marker)
        if index != -1:
            candidates.append((index, marker))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def _collect_matches(
    target: list[str],
    text: str,
    markers: tuple[str, ...],
) -> None:
    for marker in markers:
        if marker in text and marker not in target:
            target.append(marker)
