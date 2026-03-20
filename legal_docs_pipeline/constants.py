"""Canonical enums and constants for the NormaDepo foundation slice."""

from __future__ import annotations

from enum import Enum
from pathlib import Path


class PipelineMode(str, Enum):
    FULL = "full"
    NEW = "new"
    RERUN = "rerun"


class RerunScope(str, Enum):
    FAILED = "failed"
    STALE = "stale"
    ALL = "all"
    DOC_ID = "doc-id"


class DocumentFamily(str, Enum):
    NORMATIVE_ACT = "normative_act"
    JUDICIAL_DECISION = "judicial_decision"
    CONSUMER_ADMIN = "consumer_admin"
    COMMENTARY_ARTICLE = "commentary_article"
    DISCOVERY_REFERENCE = "discovery_reference"
    CORPUS_README = "corpus_readme"
    UNKNOWN = "unknown"


class PromptProfile(str, Enum):
    ADDON_NORMATIVE = "addon_normative"
    ADDON_CASE_LAW = "addon_case_law"
    ADDON_UOKIK = "addon_uokik"
    ADDON_COMMENTARY = "addon_commentary"
    ADDON_DISCOVERY = "addon_discovery"
    SKIP_NON_TARGET = "skip_non_target"


class AuthorityLevel(str, Enum):
    PRIMARY = "primary"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    REFERENCE_ONLY = "reference_only"


class RelevanceLevel(str, Enum):
    CORE = "core"
    SUPPORTING = "supporting"
    PERIPHERAL = "peripheral"
    DISCOVERY_ONLY = "discovery_only"


class UsuallySupports(str, Enum):
    TENANT = "tenant"
    LANDLORD = "landlord"
    BOTH = "both"
    DEPENDS = "depends"


class UseForTaskCode(str, Enum):
    CLAIM = "claim"
    DEFENCE = "defence"
    APPEAL = "appeal"
    LEGAL_POSITION = "legal_position"
    CLIENT_ADVICE = "client_advice"
    INTERNAL_ANALYSIS = "internal_analysis"


class TopicCode(str, Enum):
    DEPOSIT_LEGAL_BASIS = "deposit_legal_basis"
    DEPOSIT_AMOUNT_LIMIT = "deposit_amount_limit"
    DEPOSIT_RETURN_TERM = "deposit_return_term"
    ALLOWED_DEDUCTIONS = "allowed_deductions"
    WEAR_AND_TEAR = "wear_and_tear"
    PROPERTY_DAMAGE = "property_damage"
    RENT_ARREARS = "rent_arrears"
    UTILITIES_ARREARS = "utilities_arrears"
    SETOFF_POTRACENIE = "setoff_potracenie"
    INDEXATION_VALORIZATION = "indexation_valorization"
    OCCASIONAL_LEASE = "occasional_lease"
    UNFAIR_TERMS = "unfair_terms"
    CONSUMER_PROTECTION = "consumer_protection"
    BURDEN_OF_PROOF = "burden_of_proof"
    CLAIM_PROCEDURE = "claim_procedure"
    APPEAL_STRATEGY = "appeal_strategy"
    COSTS_AND_FEES = "costs_and_fees"
    MEDIATION = "mediation"
    ENFORCEMENT = "enforcement"
    DISCOVERY_NAVIGATION = "discovery_navigation"


PIPELINE_SCHEMA_VERSION = "1.0.0"
PIPELINE_IMPLEMENTATION_VERSION = "1.0.0"
DEDUPE_VERSION = "1.0.0"
ROUTER_VERSION = "1.0.0"
DEFAULT_CONFIG_PATH = Path("config/pipeline.yaml")
DEFAULT_INPUT_GLOB = "**/*.md"
DEFAULT_PROMPT_PACK_ID = "kaucja-prompt-pack"
DEFAULT_PROMPT_PACK_VERSION = "2026-03-16"
BASE_PROMPT_FILENAME = "base_system.txt"
TRANSLATION_PROMPT_FILENAME = "translate_to_ru.txt"
OUTPUT_SCHEMA_INSTRUCTION = (
    "Return only valid JSON that strictly matches the provided JSON Schema. "
    "Do not add markdown or commentary outside the JSON object."
)

PROMPT_PROFILE_TO_FILENAME: dict[PromptProfile, str] = {
    PromptProfile.ADDON_NORMATIVE: "addon_normative.txt",
    PromptProfile.ADDON_CASE_LAW: "addon_case_law.txt",
    PromptProfile.ADDON_UOKIK: "addon_uokik.txt",
    PromptProfile.ADDON_COMMENTARY: "addon_commentary.txt",
    PromptProfile.ADDON_DISCOVERY: "addon_discovery.txt",
}

ANNOTATABLE_PROMPT_PROFILES = frozenset(PROMPT_PROFILE_TO_FILENAME)
