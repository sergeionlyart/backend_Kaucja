from __future__ import annotations

from legal_docs_pipeline.schemas import (
    AnalysisAnnotationOutput,
    ClassificationResult,
    CompleteAnnotationOutput,
    FallbackClassificationOutput,
    TranslationAnnotationOutput,
    export_annotation_json_schema,
    export_translation_json_schema,
    validate_analysis_business_rules,
    validate_translation_business_rules,
)


def test_classification_contract_uses_spec_field_names() -> None:
    payload = {
        "document_family": "judicial_decision",
        "document_type_code": "sn_uchwala_valorization",
        "prompt_profile": "addon_case_law",
        "annotatable": True,
        "classifier_method": "rule_based",
        "confidence": 0.95,
        "router_version": "1.0.0",
        "signals": {"folder": "pl_sn"},
        "skip_reason": None,
    }

    validated = ClassificationResult.model_validate(payload)

    assert validated.document_family.value == "judicial_decision"
    assert validated.document_type_code == "sn_uchwala_valorization"
    assert validated.annotatable is True


def test_complete_annotation_contract_validates_payload() -> None:
    payload = {
        "semantic": {
            "document_type_code": "sn_uchwala_valorization",
            "authority_level": "high",
            "relevance": "core",
            "usually_supports": "tenant",
            "topic_codes": ["deposit_return_term", "setoff_potracenie"],
            "use_for_tasks_codes": ["claim", "legal_position"],
        },
        "annotation_original": {
            "language_code": "pl",
            "document_type_label": "uchwała Sądu Najwyższego",
            "summary": "Dokument wyjaśnia zakres waloryzacji starej kaucji.",
            "practical_value": ["Daje mocny punkt wyjścia do pozwu."],
            "best_use_scenarios": ["Spór o zwrot starej kaucji mieszkaniowej."],
            "use_for_tasks_labels": ["pozew", "pozycja prawna"],
            "read_first": ["Sentencja uchwały.", "Kluczowe fragmenty uzasadnienia."],
            "limitations": ["Dotyczy głównie starych kaucji."],
            "tags": ["waloryzacja_kaucji", "sn_uchwala"],
        },
        "annotation_ru": {
            "language_code": "ru",
            "document_type_label": "постановление Верховного суда",
            "summary": "Документ объясняет подход к валоризации старой кауции.",
            "practical_value": ["Даёт сильную опору для иска."],
            "best_use_scenarios": ["Спор о возврате старой жилищной кауции."],
            "use_for_tasks_labels": ["иск", "правовая позиция"],
            "read_first": ["Резолютивная часть.", "Ключевые фрагменты мотивировки."],
            "limitations": ["В первую очередь относится к старым кауциям."],
            "tags": ["waloryzacja_kaucji", "sn_uchwala"],
        },
    }

    validated = CompleteAnnotationOutput.model_validate(payload)

    assert validated.annotation_ru.language_code == "ru"
    assert validated.semantic.relevance.value == "core"


def test_annotation_json_schema_is_strict() -> None:
    schema = export_annotation_json_schema()

    assert schema["additionalProperties"] is False
    assert schema["$defs"]["SemanticAnnotation"]["additionalProperties"] is False
    assert (
        schema["$defs"]["SemanticAnnotation"]["properties"]["document_type_code"][
            "type"
        ]
        == "string"
    )
    assert schema["$defs"]["OriginalLanguageAnnotation"]["additionalProperties"] is False
    assert schema["$defs"]["RussianLanguageAnnotation"]["additionalProperties"] is False


def test_analysis_business_validation_checks_source_language() -> None:
    payload = AnalysisAnnotationOutput.model_validate(
        {
            "semantic": {
                "document_type_code": "pl_statute",
                "authority_level": "primary",
                "relevance": "core",
                "usually_supports": "depends",
                "topic_codes": ["deposit_legal_basis"],
                "use_for_tasks_codes": ["claim"],
            },
            "annotation_original": {
                "language_code": "en",
                "document_type_label": "statute",
                "summary": "Useful for deposit claims.",
                "practical_value": ["Sets the statutory baseline."],
                "best_use_scenarios": ["Claim for deposit return."],
                "use_for_tasks_labels": ["claim"],
                "read_first": ["Article 6."],
                "limitations": ["Needs case-law context."],
                "tags": ["deposit", "statute"],
            },
        }
    )

    errors = validate_analysis_business_rules(payload, source_language="pl")

    assert errors == [
        "annotation_original.language_code must match source.language_original."
    ]


def test_translation_business_validation_checks_ru_and_semantic_consistency() -> None:
    analysis_payload = AnalysisAnnotationOutput.model_validate(
        {
            "semantic": {
                "document_type_code": "pl_statute",
                "authority_level": "primary",
                "relevance": "core",
                "usually_supports": "depends",
                "topic_codes": ["deposit_legal_basis"],
                "use_for_tasks_codes": ["claim"],
            },
            "annotation_original": {
                "language_code": "pl",
                "document_type_label": "ustawa",
                "summary": "Określa podstawę prawną kaucji.",
                "practical_value": ["Pozwala ustalić punkt wyjścia dla roszczenia."],
                "best_use_scenarios": ["Pozew o zwrot kaucji."],
                "use_for_tasks_labels": ["pozew"],
                "read_first": ["Art. 6."],
                "limitations": ["Wymaga uzupełnienia orzecznictwem."],
                "tags": ["kaucja", "ustawa"],
            },
        }
    )
    translation_payload = TranslationAnnotationOutput.model_validate(
        {
            "semantic": {
                "document_type_code": "eu_directive",
                "authority_level": "primary",
                "relevance": "core",
                "usually_supports": "depends",
                "topic_codes": ["deposit_legal_basis"],
                "use_for_tasks_codes": ["claim"],
            },
            "annotation_ru": {
                "language_code": "ru",
                "document_type_label": "закон",
                "summary": "Полезен для спора о кауции.",
                "practical_value": ["Помогает построить иск."],
                "best_use_scenarios": ["Иск о возврате кауции."],
                "use_for_tasks_labels": ["иск"],
                "read_first": ["Статья 6."],
                "limitations": ["Нужна судебная практика."],
                "tags": ["кауция", "закон"],
            },
        }
    )

    errors = validate_translation_business_rules(
        translation_payload,
        expected_semantic=analysis_payload.semantic,
    )

    assert errors == [
        "translation semantic block must match analysis semantic block."
    ]


def test_fallback_classifier_contract_accepts_canonical_fields() -> None:
    payload = {
        "document_family": "commentary_article",
        "prompt_profile": "addon_commentary",
        "confidence": 0.83,
    }

    validated = FallbackClassificationOutput.model_validate(payload)
    schema = export_translation_json_schema()

    assert validated.document_family.value == "commentary_article"
    assert validated.prompt_profile.value == "addon_commentary"
    assert schema["additionalProperties"] is False
