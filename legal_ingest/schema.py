from __future__ import annotations

from dataclasses import dataclass

ACTIVE_REQUIRED_FIELDS = (
    "doc_uid",
    "status",
    "document_kind",
    "legal_role",
    "jurisdiction",
    "source_tier",
    "canonical_title",
    "title_short",
    "source_url",
    "normalized_source_url",
    "external_id",
    "checksum_sha256",
    "language",
    "summary_1line",
    "issue_tags",
    "search_terms_positive",
    "search_terms_negative",
    "query_templates",
    "relevance_score",
    "last_verified_at",
    "storage_uri",
)

BASELINE_ENRICHMENT_FIELDS = (
    "title_short",
    "summary_1line",
    "issue_tags",
    "relevance_score",
    "search_terms_positive",
    "search_terms_negative",
    "query_templates",
    "last_verified_at",
)

ACT_REQUIRED_FIELDS = (
    "act_id",
    "act_short_name",
    "is_consolidated_text",
    "current_status",
    "current_text_ref",
    "article_nodes",
    "key_provisions",
)

CASELAW_REQUIRED_FIELDS = (
    "case_signature",
    "court_name",
    "court_level",
    "judgment_date",
    "artifact_type",
    "holding_1line",
    "same_case_group_id",
    "related_provisions",
    "facts_tags",
)

CASELAW_ENRICHMENT_FIELDS = (
    "case_signature",
    "judgment_date",
    "court_name",
    "court_level",
    "artifact_type",
    "holding_1line",
    "facts_tags",
    "related_provisions",
)

EXCLUDED_REQUIRED_FIELDS = (
    "exclusion_reason",
    "superseded_by",
    "is_search_page",
)

LEGACY_FIELD_HINTS = {
    "document_kind": ["doc_type"],
    "canonical_title": ["title"],
    "source_url": ["source_urls[0]"],
    "normalized_source_url": ["document_sources.final_url"],
    "external_id": ["external_ids"],
    "checksum_sha256": ["current_source_hash"],
    "last_verified_at": ["updated_at"],
    "storage_uri": ["document_sources.raw_object_path"],
    "judgment_date": ["date_decision"],
}


@dataclass(frozen=True, slots=True)
class Section7Rule:
    doc_uid: str
    issue_type: str
    reason: str
    expected_title: str | None = None
    title_equals: tuple[str, ...] = ()
    title_contains: tuple[str, ...] = ()

    def matches(self, title: str | None) -> bool:
        if self.issue_type == "excluded_candidate":
            return True

        if not title:
            return True

        lowered = title.casefold()
        if self.title_equals and lowered in {
            value.casefold() for value in self.title_equals
        }:
            return True

        for value in self.title_contains:
            if value.casefold() in lowered:
                return True

        return False


SECTION7_RULES = (
    Section7Rule(
        doc_uid="sn_pl:V_CSK_480-18",
        issue_type="bad_title",
        reason="Section 7 requires replacing placeholder title 'SN' with official signature/title.",
        title_equals=("SN",),
    ),
    Section7Rule(
        doc_uid="sn_pl:I_CNP_31-13",
        issue_type="bad_title",
        reason="Section 7 requires removing 'Untitled HTML Document'.",
        title_contains=("Untitled HTML Document",),
    ),
    Section7Rule(
        doc_uid="uokik_pl:urlsha:c506ff470f4740ad",
        issue_type="bad_title",
        reason="Section 7 requires canonical title for UOKiK RKR-37/2013.",
        expected_title="Decyzja Prezesa UOKiK RKR-37/2013 (Novis MSK)",
        title_contains=("Untitled Document",),
    ),
    Section7Rule(
        doc_uid="curia_eu:urlsha:54acc341b17f3a57",
        issue_type="bad_title",
        reason="Section 7 requires canonical CJEU title for C-488/11.",
        expected_title="C-488/11 Asbeek Brusse and Katarina de Man Garabito",
        title_equals=("RPEX",),
    ),
    Section7Rule(
        doc_uid="curia_eu:urlsha:ef65918198e5ffee",
        issue_type="bad_title",
        reason="Section 7 requires canonical CJEU title for C-243/08.",
        expected_title="C-243/08 Pannon GSM",
        title_equals=("RPEX",),
    ),
    Section7Rule(
        doc_uid="eurlex_eu:urlsha:252f802534879b95",
        issue_type="bad_title",
        reason="Section 7 requires replacing XML filename title.",
        expected_title="Commission Notice - Guidance on the interpretation and application of Directive 93/13/EEC",
        title_contains=(".xml",),
    ),
    Section7Rule(
        doc_uid="uokik_pl:urlsha:5efe92f726049194",
        issue_type="excluded_candidate",
        reason="Section 7 requires moving this UOKiK registry item out of core runtime.",
    ),
)
