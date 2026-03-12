from __future__ import annotations

from typing import Any

# Rule-based quality overrides for the 9 required runtime caselaw authorities.
# The strings below are derived from tracked legal notes in:
# - docs/legal/case_law_V_2.1.md
# - docs/legal/case_law.md
# - docs/legal/kaucja_registry.csv

REQUIRED_RUNTIME_CASELAW_DOC_UIDS: tuple[str, ...] = (
    "sn_pl:III_CZP_58-02",
    "saos_pl:205996",
    "saos_pl:171957",
    "saos_pl:279345",
    "saos_pl:346698",
    "saos_pl:472812",
    "saos_pl:505310",
    "curia_eu:urlsha:54acc341b17f3a57",
    "curia_eu:urlsha:ef65918198e5ffee",
)

CURATED_CASELAW_OVERRIDES: dict[str, dict[str, Any]] = {
    "sn_pl:III_CZP_58-02": {
        "holding_1line": (
            "The housing-deposit return claim remains a monetary claim and old "
            "deposits may be valorised under art. 358(1) para. 3 KC."
        ),
        "facts_tags": ["old_housing_deposit", "valorisation_claim"],
        "related_provisions": [
            "art. 358(1) para. 3 KC",
            "art. 36 dawnej ustawy o najmie lokali",
        ],
    },
    "saos_pl:205996": {
        "holding_1line": (
            "The Constitutional Tribunal criticised a regime that excluded "
            "valorisation of old housing deposits."
        ),
        "facts_tags": ["old_housing_deposit", "constitutional_review"],
        "related_provisions": [
            "art. 358(1) para. 3 KC",
            "przepisy o waloryzacji starych kaucji mieszkaniowych",
        ],
    },
    "saos_pl:171957": {
        "holding_1line": (
            "Under art. 6 ust. 4 u.o.p.l., the deposit should be returned within "
            "one month after vacating, after deducting only tenancy-based claims."
        ),
        "facts_tags": ["deposit_return_deadline", "vacating_of_flat"],
        "related_provisions": [
            "art. 6 ust. 4 ustawy o ochronie praw lokatorow",
        ],
    },
    "saos_pl:279345": {
        "holding_1line": (
            "Once the deposit-return claim becomes due, delayed payment triggers "
            "interest under art. 481 KC."
        ),
        "facts_tags": ["deposit_return_interest", "claim_maturity"],
        "related_provisions": ["art. 455 KC", "art. 481 KC"],
    },
    "saos_pl:346698": {
        "holding_1line": (
            "A landlord may deduct only proven tenancy claims; a percentage "
            "wear-charge is not a valid deposit deduction."
        ),
        "facts_tags": ["wear_charge_deduction", "damage_proof", "setoff_claim"],
        "related_provisions": [
            "art. 6 ust. 4 ustawy o ochronie praw lokatorow",
            "art. 498 KC",
        ],
    },
    "saos_pl:472812": {
        "holding_1line": (
            "The case applies art. 6 u.o.p.l. while separately addressing "
            "pre-12 November 1994 deposits and transitional valorisation rules."
        ),
        "facts_tags": [
            "old_housing_deposit",
            "transitional_rules",
            "tenant_deposit",
        ],
        "related_provisions": [
            "art. 6 ustawy o ochronie praw lokatorow",
            "art. 358(1) para. 3 KC",
        ],
    },
    "saos_pl:505310": {
        "holding_1line": (
            "Deposit retention for painting requires proof that work was actually "
            "done and that concrete costs were incurred."
        ),
        "facts_tags": ["painting_costs", "handover_protocol", "proof_of_expense"],
        "related_provisions": [
            "art. 6 KC",
            "art. 6 ust. 4 ustawy o ochronie praw lokatorow",
        ],
    },
    "curia_eu:urlsha:54acc341b17f3a57": {
        "holding_1line": (
            "Directive 93/13 applies to residential tenancy, and a penalty term "
            "that creates a significant imbalance may be unfair."
        ),
        "facts_tags": [
            "residential_tenancy",
            "penalty_clause",
            "consumer_unfair_terms",
        ],
        "related_provisions": [
            "Directive 93/13/EEC art. 3",
            "Directive 93/13/EEC art. 6",
        ],
    },
    "curia_eu:urlsha:ef65918198e5ffee": {
        "holding_1line": (
            "A national court must examine a potentially unfair standard term of "
            "its own motion once the necessary facts and law are available."
        ),
        "facts_tags": ["ex_officio_review", "consumer_unfair_terms"],
        "related_provisions": [
            "Directive 93/13/EEC art. 6",
            "Directive 93/13/EEC art. 7",
        ],
    },
}

UNAVOIDABLE_UNKNOWN_JUDGMENT_DATE_REASONS: dict[str, str] = {
    "curia_eu:urlsha:54acc341b17f3a57": (
        "Current stored CURIA artifact is an RPEX shell page without an embedded "
        "judgment date."
    ),
    "curia_eu:urlsha:ef65918198e5ffee": (
        "Current stored CURIA artifact is an RPEX shell page without an embedded "
        "judgment date."
    ),
    "curia_eu:urlsha:71b42cdf7ec305a3": (
        "Current stored CURIA artifact is an RPEX shell page without an embedded "
        "judgment date."
    ),
}


def get_curated_caselaw_override(doc_uid: str | None) -> dict[str, Any]:
    if not doc_uid:
        return {}
    return dict(CURATED_CASELAW_OVERRIDES.get(doc_uid, {}))


def get_unknown_judgment_date_exemption_reason(doc_uid: str | None) -> str | None:
    if not doc_uid:
        return None
    return UNAVOIDABLE_UNKNOWN_JUDGMENT_DATE_REASONS.get(doc_uid)
