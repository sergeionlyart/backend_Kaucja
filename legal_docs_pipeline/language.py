"""Language detection heuristics for the NormaDepo pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

_PL_SOURCE_SYSTEMS = {
    "eli_pl",
    "isap_pl",
    "lex_pl",
    "sn_pl",
    "saos_pl",
    "courts_pl",
    "uokik_pl",
}
_EN_SOURCE_SYSTEMS = {"eurlex_eu", "curia_eu"}
_PL_MARKERS = (
    "ustawa",
    "wyrok",
    "uchwała",
    "sygn. akt",
    "lokator",
    "kaucj",
    "najem",
    "dz. u.",
)
_EN_MARKERS = (
    "judgment of the court",
    "directive",
    "consumer contracts",
    "this entry is",
    "result links",
    "query url",
    "generated at",
    "markdown export",
)
_DISCOVERY_PAGE_EN_MARKERS = (
    "this entry is a search/discovery page",
    "result links",
    "query url",
)


@dataclass(frozen=True, slots=True)
class LanguageDetectionResult:
    language_code: str
    confidence: float
    strategy: str
    signals: tuple[str, ...]


class LanguageDetector(Protocol):
    def detect(
        self,
        *,
        normalized_text: str,
        doc_metadata: dict[str, object],
        relative_path: str,
        title: str | None,
    ) -> LanguageDetectionResult:
        """Return detected ISO 639-1 language code."""


class HeuristicLanguageDetector:
    def detect(
        self,
        *,
        normalized_text: str,
        doc_metadata: dict[str, object],
        relative_path: str,
        title: str | None,
    ) -> LanguageDetectionResult:
        scores = {"pl": 0, "en": 0}
        signals: list[str] = []
        source_system = str(
            doc_metadata.get("original_source_system")
            or doc_metadata.get("resolved_source_system")
            or ""
        ).strip()
        relative_path_upper = relative_path.upper()
        lowered_text = normalized_text.lower()
        if (
            relative_path_upper.endswith("README.MD")
            and "markdown export" in lowered_text
            and "generated at" in lowered_text
        ):
            return LanguageDetectionResult(
                language_code="en",
                confidence=0.9,
                strategy="heuristic",
                signals=("service_readme_export_markers",),
            )
        if source_system in _PL_SOURCE_SYSTEMS:
            scores["pl"] += 2
            signals.append(f"metadata.source_system={source_system}->pl")
        if source_system in _EN_SOURCE_SYSTEMS:
            scores["en"] += 2
            signals.append(f"metadata.source_system={source_system}->en")

        top_level_dir = relative_path.split("/", maxsplit=1)[0]
        if top_level_dir.startswith("pl_"):
            scores["pl"] += 1
            signals.append(f"folder={top_level_dir}->pl")
        if top_level_dir.startswith("eu_"):
            scores["en"] += 1
            signals.append(f"folder={top_level_dir}->en")

        signal_text = f"{title or ''}\n{normalized_text[:4000]}".lower()
        pl_hits = sum(1 for marker in _PL_MARKERS if marker in signal_text)
        en_hits = sum(1 for marker in _EN_MARKERS if marker in signal_text)
        if pl_hits:
            scores["pl"] += pl_hits
            signals.append(f"text_markers_pl={pl_hits}")
        if en_hits:
            scores["en"] += en_hits
            signals.append(f"text_markers_en={en_hits}")

        if all(marker in lowered_text for marker in _DISCOVERY_PAGE_EN_MARKERS):
            return LanguageDetectionResult(
                language_code="en",
                confidence=0.85,
                strategy="heuristic",
                signals=tuple(
                    [
                        *signals,
                        "discovery_page_en_markers",
                    ]
                ),
            )

        if scores["pl"] == 0 and scores["en"] == 0:
            return LanguageDetectionResult(
                language_code="und",
                confidence=0.0,
                strategy="heuristic",
                signals=("no_language_markers",),
            )

        if abs(scores["pl"] - scores["en"]) <= 1:
            return LanguageDetectionResult(
                language_code="und",
                confidence=0.0,
                strategy="heuristic",
                signals=tuple(signals) or ("ambiguous_language_signals",),
            )

        language_code = "pl" if scores["pl"] > scores["en"] else "en"
        winning_score = max(scores["pl"], scores["en"])
        total_score = scores["pl"] + scores["en"]
        confidence = round(winning_score / total_score, 2) if total_score else 0.0
        return LanguageDetectionResult(
            language_code=language_code,
            confidence=confidence,
            strategy="heuristic",
            signals=tuple(signals),
        )
