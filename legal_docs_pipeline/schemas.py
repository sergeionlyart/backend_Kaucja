"""Strict schema contracts for classification and annotation outputs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import (
    AuthorityLevel,
    DocumentFamily,
    PromptProfile,
    RelevanceLevel,
    TopicCode,
    UseForTaskCode,
    UsuallySupports,
)


class ClassificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_family: DocumentFamily
    document_type_code: str | None = None
    prompt_profile: PromptProfile
    annotatable: bool
    classifier_method: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    router_version: str = Field(min_length=1)
    signals: dict[str, Any] = Field(default_factory=dict)
    skip_reason: str | None = None


class SemanticAnnotation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type_code: str = Field(min_length=1)
    authority_level: AuthorityLevel
    relevance: RelevanceLevel
    usually_supports: UsuallySupports
    topic_codes: list[TopicCode] = Field(min_length=1)
    use_for_tasks_codes: list[UseForTaskCode] = Field(min_length=1)


class OriginalLanguageAnnotation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language_code: Literal["pl", "en"]
    document_type_label: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    practical_value: list[str] = Field(min_length=1)
    best_use_scenarios: list[str] = Field(min_length=1)
    use_for_tasks_labels: list[str] = Field(min_length=1)
    read_first: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    tags: list[str] = Field(min_length=1)

    @field_validator(
        "practical_value",
        "best_use_scenarios",
        "use_for_tasks_labels",
        "read_first",
        "limitations",
        "tags",
    )
    @classmethod
    def validate_non_empty_items(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("List items must be non-empty strings.")
        return normalized


class RussianLanguageAnnotation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language_code: Literal["ru"] = "ru"
    document_type_label: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    practical_value: list[str] = Field(min_length=1)
    best_use_scenarios: list[str] = Field(min_length=1)
    use_for_tasks_labels: list[str] = Field(min_length=1)
    read_first: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    tags: list[str] = Field(min_length=1)

    @field_validator(
        "practical_value",
        "best_use_scenarios",
        "use_for_tasks_labels",
        "read_first",
        "limitations",
        "tags",
    )
    @classmethod
    def validate_non_empty_items(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("List items must be non-empty strings.")
        return normalized


class AnalysisAnnotationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semantic: SemanticAnnotation
    annotation_original: OriginalLanguageAnnotation


class FallbackClassificationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_family: DocumentFamily
    prompt_profile: PromptProfile
    confidence: float = Field(ge=0.0, le=1.0)


class TranslationAnnotationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    annotation_ru: RussianLanguageAnnotation


class CompleteAnnotationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semantic: SemanticAnnotation
    annotation_original: OriginalLanguageAnnotation
    annotation_ru: RussianLanguageAnnotation


def export_annotation_json_schema() -> dict[str, Any]:
    return CompleteAnnotationOutput.model_json_schema()


def export_analysis_json_schema() -> dict[str, Any]:
    return AnalysisAnnotationOutput.model_json_schema()


def export_translation_json_schema() -> dict[str, Any]:
    return TranslationAnnotationOutput.model_json_schema()


def validate_analysis_business_rules(
    output: AnalysisAnnotationOutput,
    *,
    source_language: str,
) -> list[str]:
    errors: list[str] = []
    if output.annotation_original.language_code != source_language:
        errors.append(
            "annotation_original.language_code must match source.language_original."
        )
    if not output.annotation_original.summary.strip():
        errors.append("annotation_original.summary must be non-empty.")
    if not output.semantic.use_for_tasks_codes:
        errors.append("semantic.use_for_tasks_codes must be non-empty.")
    if not output.semantic.topic_codes:
        errors.append("semantic.topic_codes must be non-empty.")
    return errors


def validate_translation_business_rules(
    output: TranslationAnnotationOutput,
) -> list[str]:
    errors: list[str] = []
    if output.annotation_ru.language_code != "ru":
        errors.append("annotation_ru.language_code must be 'ru'.")
    if not output.annotation_ru.summary.strip():
        errors.append("annotation_ru.summary must be non-empty.")
    if not output.annotation_ru.read_first:
        errors.append("annotation_ru.read_first must be non-empty.")
    if not output.annotation_ru.limitations:
        errors.append("annotation_ru.limitations must be non-empty.")
    return errors
