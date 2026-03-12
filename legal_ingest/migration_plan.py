from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from legal_ingest.config import DEFAULT_MIGRATION_MAP_PATH, resolve_path
from legal_ingest.source_catalog import (
    REQUIRED_SOURCE_BY_ENTRY_ID,
    TECHSPEC_SOURCE_CATALOG,
    get_source_entry,
)

MIGRATION_STATUS_VALUES = {
    "canonical",
    "article_node",
    "alias",
    "optional",
    "excluded",
    "missing_fetch",
}


@dataclass(frozen=True, slots=True)
class MigrationEntry:
    entry_id: str
    position: int | None
    source_url: str | None
    source_id: str | None
    source_doc_uid: str | None
    status: str
    canonical_title: str
    canonical_doc_uid: str | None
    document_kind: str
    legal_role: str
    expected_external_id: str | None
    required_top_level: bool
    notes: str
    match_doc_uids: tuple[str, ...] = ()
    match_source_urls: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["match_doc_uids"] = list(self.match_doc_uids)
        payload["match_source_urls"] = list(self.match_source_urls)
        return payload


POSITION_POLICIES: dict[int, dict[str, Any]] = {
    1: {
        "status": "optional",
        "canonical_title": "Ustawa o ochronie praw lokatorow, mieszkaniowym zasobie gminy i o zmianie Kodeksu cywilnego",
        "canonical_doc_uid": None,
        "document_kind": "STATUTE",
        "legal_role": "DIRECT_NORM_ARCHIVE",
        "expected_external_id": "eli:DU/2001/733",
        "required_top_level": False,
        "notes": "Archive source only; fetch current consolidated text for runtime canonical in Iteration 2.",
    },
    2: {
        "status": "optional",
        "canonical_title": "Kodeks cywilny",
        "canonical_doc_uid": None,
        "document_kind": "STATUTE",
        "legal_role": "DIRECT_NORM_ARCHIVE",
        "expected_external_id": "isap:WDU19640160093",
        "required_top_level": False,
        "notes": "Archive PDF only; fetch current consolidated text for runtime canonical in Iteration 2.",
    },
    3: {
        "status": "alias",
        "canonical_title": "Ustawa o ochronie praw lokatorow, mieszkaniowym zasobie gminy i o zmianie Kodeksu cywilnego",
        "canonical_doc_uid": None,
        "document_kind": "STATUTE",
        "legal_role": "SECONDARY_SOURCE",
        "expected_external_id": "lex:16903658",
        "required_top_level": False,
        "notes": "LEX landing page is not a top-level runtime doc; keep only as secondary source under official act.",
    },
    4: {
        "status": "article_node",
        "canonical_title": "Art. 19a ustawy o ochronie praw lokatorow",
        "canonical_doc_uid": None,
        "document_kind": "STATUTE",
        "legal_role": "ARTICLE_NODE",
        "expected_external_id": "lex:16903658:art-19-a",
        "required_top_level": False,
        "notes": "Map into article node under the official act.",
    },
    5: {
        "status": "article_node",
        "canonical_title": "Art. 118 Kodeksu cywilnego",
        "canonical_doc_uid": None,
        "document_kind": "STATUTE",
        "legal_role": "ARTICLE_NODE",
        "expected_external_id": "lex:118",
        "required_top_level": False,
        "notes": "Map into article node under the official KC text.",
    },
    6: {
        "status": "canonical",
        "canonical_title": "Uchwala SN z dnia 26 wrzesnia 2002 r., III CZP 58/02",
        "canonical_doc_uid": "sn_pl:III_CZP_58-02",
        "document_kind": "CASELAW",
        "legal_role": "LEADING_CASE",
        "expected_external_id": "sn:III CZP 58/02",
        "required_top_level": True,
        "notes": "Core leading case for waloryzacja old housing deposits.",
    },
    7: {
        "status": "optional",
        "canonical_title": "Wyrok SN II CSK 862/14",
        "canonical_doc_uid": "sn_pl:II_CSK_862-14",
        "document_kind": "CASELAW",
        "legal_role": "SUPPORTING_CASE",
        "expected_external_id": "sn:II CSK 862/14",
        "required_top_level": False,
        "notes": "Useful on formal requirements for set-off, but not rental-specific.",
    },
    8: {
        "status": "optional",
        "canonical_title": "Wyrok SN I CSK 292/12",
        "canonical_doc_uid": "sn_pl:I_CSK_292-12",
        "document_kind": "CASELAW",
        "legal_role": "SUPPORTING_CASE",
        "expected_external_id": "sn:I CSK 292/12",
        "required_top_level": False,
        "notes": "Indirectly useful only.",
    },
    9: {
        "status": "excluded",
        "canonical_title": "Postanowienie SN V CSK 480/18",
        "canonical_doc_uid": "sn_pl:V_CSK_480-18",
        "document_kind": "CASELAW",
        "legal_role": "EXCLUDED",
        "expected_external_id": "sn:V CSK 480/18",
        "required_top_level": False,
        "notes": "Commercial dispute outside tenant-vs-landlord scope.",
    },
    10: {
        "status": "excluded",
        "canonical_title": "Postanowienie SN I CNP 31/13",
        "canonical_doc_uid": "sn_pl:I_CNP_31-13",
        "document_kind": "CASELAW",
        "legal_role": "EXCLUDED",
        "expected_external_id": "sn:I CNP 31/13",
        "required_top_level": False,
        "notes": "Commercial dispute outside tenant-vs-landlord scope.",
    },
    11: {
        "status": "excluded",
        "canonical_title": "SAOS search seed for kaucja mieszkaniowa",
        "canonical_doc_uid": None,
        "document_kind": "CASELAW",
        "legal_role": "SEARCH_PAGE",
        "expected_external_id": "saos-search:kaucja-mieszkaniowa",
        "required_top_level": False,
        "notes": "Search pages can never be canonical runtime documents.",
    },
    12: {
        "status": "canonical",
        "canonical_title": "Wyrok II Ca 886/14",
        "canonical_doc_uid": "saos_pl:171957",
        "document_kind": "CASELAW",
        "legal_role": "FACTUAL_CASE",
        "expected_external_id": "saos:171957",
        "required_top_level": True,
        "notes": "Core factual layer about whether the sum was a real deposit.",
    },
    13: {
        "status": "canonical",
        "canonical_title": "Wyrok TK K 33/99",
        "canonical_doc_uid": "saos_pl:205996",
        "document_kind": "CASELAW",
        "legal_role": "LEADING_CASE",
        "expected_external_id": "saos:205996",
        "required_top_level": True,
        "notes": "Constitutional authority on old housing deposits and waloryzacja.",
    },
    14: {
        "status": "canonical",
        "canonical_title": "Wyrok I C 743/16",
        "canonical_doc_uid": "saos_pl:279345",
        "document_kind": "CASELAW",
        "legal_role": "FACTUAL_CASE",
        "expected_external_id": "saos:279345",
        "required_top_level": True,
        "notes": "Core factual layer for permissible deductions from deposit.",
    },
    15: {
        "status": "optional",
        "canonical_title": "Wyrok II C 442/16",
        "canonical_doc_uid": "saos_pl:330695",
        "document_kind": "CASELAW",
        "legal_role": "SUPPORTING_CASE",
        "expected_external_id": "saos:330695",
        "required_top_level": False,
        "notes": "Useful for burden of proof and limitation, but not top priority.",
    },
    16: {
        "status": "canonical",
        "canonical_title": "Wyrok I C 106/17",
        "canonical_doc_uid": "saos_pl:346698",
        "document_kind": "CASELAW",
        "legal_role": "FACTUAL_CASE",
        "expected_external_id": "saos:346698",
        "required_top_level": True,
        "notes": "Core factual layer for repair and utilities deductions.",
    },
    17: {
        "status": "canonical",
        "canonical_title": "Wyrok VI C 837/21",
        "canonical_doc_uid": "saos_pl:472812",
        "document_kind": "CASELAW",
        "legal_role": "FACTUAL_CASE",
        "expected_external_id": "saos:472812",
        "required_top_level": True,
        "notes": "Core factual layer for return and waloryzacja of old municipal deposit.",
    },
    18: {
        "status": "optional",
        "canonical_title": "Wyrok dotyczacy foreign-law / German BGB deposit issue",
        "canonical_doc_uid": "saos_pl:486542",
        "document_kind": "CASELAW",
        "legal_role": "OPTIONAL_EU",
        "expected_external_id": "saos:486542",
        "required_top_level": False,
        "notes": "Foreign-law deposit case; not core runtime.",
    },
    19: {
        "status": "optional",
        "canonical_title": "Wyrok dotyczacy rozliczen najmu i limitation",
        "canonical_doc_uid": "saos_pl:487012",
        "document_kind": "CASELAW",
        "legal_role": "SUPPORTING_CASE",
        "expected_external_id": "saos:487012",
        "required_top_level": False,
        "notes": "Useful on accounting, burden of proof and limitation.",
    },
    20: {
        "status": "canonical",
        "canonical_title": "Wyrok III C 224/22",
        "canonical_doc_uid": "saos_pl:505310",
        "document_kind": "CASELAW",
        "legal_role": "FACTUAL_CASE",
        "expected_external_id": "saos:505310",
        "required_top_level": True,
        "notes": "Core factual layer on occasional lease and ordinary wear.",
    },
    21: {
        "status": "optional",
        "canonical_title": "Wyrok niebedacy klasycznym zwrotem kaucji",
        "canonical_doc_uid": "saos_pl:521555",
        "document_kind": "CASELAW",
        "legal_role": "SUPPORTING_CASE",
        "expected_external_id": "saos:521555",
        "required_top_level": False,
        "notes": "Case itself is not directly about deposit return.",
    },
    22: {
        "status": "alias",
        "canonical_title": "Wyrok I Ca 56/18",
        "canonical_doc_uid": "saos_pl:360096",
        "document_kind": "CASELAW",
        "legal_role": "PORTAL_MIRROR",
        "expected_external_id": "case:I Ca 56/18",
        "required_top_level": False,
        "notes": "Portal mirror; group under same_case_group_id with SAOS canonical case.",
    },
    23: {
        "status": "alias",
        "canonical_title": "Wyrok III Ca 1707/18",
        "canonical_doc_uid": "saos_pl:385394",
        "document_kind": "CASELAW",
        "legal_role": "PORTAL_MIRROR",
        "expected_external_id": "case:III Ca 1707/18",
        "required_top_level": False,
        "notes": "Portal mirror; group under same_case_group_id with SAOS canonical case.",
    },
    24: {
        "status": "alias",
        "canonical_title": "Wyrok V ACa 599/14",
        "canonical_doc_uid": "saos_pl:132635",
        "document_kind": "CASELAW",
        "legal_role": "PORTAL_MIRROR",
        "expected_external_id": "case:V ACa 599/14",
        "required_top_level": False,
        "notes": "Portal mirror; group under same_case_group_id with SAOS canonical case.",
    },
    25: {
        "status": "canonical",
        "canonical_title": "Council Directive 93/13/EEC of 5 April 1993 on unfair terms in consumer contracts",
        "canonical_doc_uid": "eurlex_eu:dir/1993/13/oj/eng",
        "document_kind": "EU_ACT",
        "legal_role": "EU_CONSUMER_LAYER",
        "expected_external_id": "eli:dir/1993/13/oj/eng",
        "required_top_level": True,
        "notes": "Official Directive 93/13/EEC is mandatory in runtime.",
        "match_doc_uids": (
            "eurlex_eu:dir/1993/13/oj/eng",
            "eurlex_eu:eli:dir/1993/13/oj/eng",
            "eurlex_eu:urlsha:8f4d90b5081ec765",
        ),
    },
    26: {
        "status": "alias",
        "canonical_title": "Directive 93/13/EEC legacy LexUriServ mirror",
        "canonical_doc_uid": "eurlex_eu:dir/1993/13/oj/eng",
        "document_kind": "EU_ACT",
        "legal_role": "LEGACY_MIRROR",
        "expected_external_id": "celex:31993L0013",
        "required_top_level": False,
        "notes": "Legacy mirror duplicating official Directive 93/13 source.",
    },
    27: {
        "status": "canonical",
        "canonical_title": "Commission Notice - Guidance on the interpretation and application of Directive 93/13/EEC",
        "canonical_doc_uid": "eurlex_eu:urlsha:252f802534879b95",
        "document_kind": "GUIDANCE",
        "legal_role": "EU_CONSUMER_LAYER",
        "expected_external_id": "celex:52019XC0927(01)",
        "required_top_level": True,
        "notes": "Mandatory guidance layer for Directive 93/13.",
        "match_doc_uids": ("eurlex_eu:urlsha:252f802534879b95",),
    },
    28: {
        "status": "optional",
        "canonical_title": "Regulation (EC) No 861/2007",
        "canonical_doc_uid": "eurlex_eu:eli:reg/2007/861/oj/eng",
        "document_kind": "EU_ACT",
        "legal_role": "EU_CROSS_BORDER_PROCEDURE",
        "expected_external_id": "eli:reg/2007/861/oj/eng",
        "required_top_level": False,
        "notes": "Optional cross-border procedure layer only.",
    },
    29: {
        "status": "optional",
        "canonical_title": "Regulation (EC) No 1896/2006",
        "canonical_doc_uid": "eurlex_eu:eli:reg/2006/1896/oj/eng",
        "document_kind": "EU_ACT",
        "legal_role": "EU_CROSS_BORDER_PROCEDURE",
        "expected_external_id": "eli:reg/2006/1896/oj/eng",
        "required_top_level": False,
        "notes": "Optional cross-border procedure layer only.",
    },
    30: {
        "status": "optional",
        "canonical_title": "Regulation (EC) No 805/2004",
        "canonical_doc_uid": "eurlex_eu:eli:reg/2004/805/oj/eng",
        "document_kind": "EU_ACT",
        "legal_role": "EU_CROSS_BORDER_PROCEDURE",
        "expected_external_id": "eli:reg/2004/805/oj/eng",
        "required_top_level": False,
        "notes": "Optional cross-border procedure layer only.",
    },
    31: {
        "status": "canonical",
        "canonical_title": "C-488/11 Asbeek Brusse and Katarina de Man Garabito",
        "canonical_doc_uid": "curia_eu:urlsha:54acc341b17f3a57",
        "document_kind": "CASELAW",
        "legal_role": "EU_CONSUMER_LAYER",
        "expected_external_id": "curia:137830",
        "required_top_level": True,
        "notes": "Mandatory CJEU housing-tenancy authority.",
        "match_doc_uids": ("curia_eu:urlsha:54acc341b17f3a57",),
    },
    32: {
        "status": "optional",
        "canonical_title": "C-229/19 Dexia Nederland",
        "canonical_doc_uid": "curia_eu:docid:237043",
        "document_kind": "CASELAW",
        "legal_role": "OPTIONAL_EU",
        "expected_external_id": "curia:237043",
        "required_top_level": False,
        "notes": "Secondary EU unfair-terms case.",
    },
    33: {
        "status": "canonical",
        "canonical_title": "C-243/08 Pannon GSM",
        "canonical_doc_uid": "curia_eu:urlsha:ef65918198e5ffee",
        "document_kind": "CASELAW",
        "legal_role": "EU_CONSUMER_LAYER",
        "expected_external_id": "curia:74812",
        "required_top_level": True,
        "notes": "Mandatory ex officio unfair-terms authority.",
        "match_doc_uids": ("curia_eu:urlsha:ef65918198e5ffee",),
    },
    34: {
        "status": "optional",
        "canonical_title": "Curia fact sheet on unfair terms",
        "canonical_doc_uid": "curia_eu:jcms:p1_4220451",
        "document_kind": "GUIDANCE",
        "legal_role": "GUIDANCE",
        "expected_external_id": "curia:jcms:p1_4220451",
        "required_top_level": False,
        "notes": "Guidance only, not a core authority.",
    },
    35: {
        "status": "canonical",
        "canonical_title": "Decyzja Prezesa UOKiK RKR-37/2013 (Novis MSK)",
        "canonical_doc_uid": "uokik_pl:urlsha:c506ff470f4740ad",
        "document_kind": "GUIDANCE",
        "legal_role": "EU_CONSUMER_LAYER",
        "expected_external_id": "uokik:RKR-37/2013",
        "required_top_level": True,
        "notes": "Mandatory UOKiK decision on abusive lease clauses including deposit forfeiture.",
        "match_doc_uids": ("uokik_pl:urlsha:c506ff470f4740ad",),
    },
    36: {
        "status": "canonical",
        "canonical_title": "UOKiK Niedozwolone klauzule",
        "canonical_doc_uid": "uokik_pl:urlsha:054662ca9a699d16",
        "document_kind": "GUIDANCE",
        "legal_role": "EU_CONSUMER_LAYER",
        "expected_external_id": "uokik:niedozwolone-klauzule",
        "required_top_level": True,
        "notes": "Guidance/navigation page kept in consumer layer.",
    },
    37: {
        "status": "excluded",
        "canonical_title": "AmC 86/2003",
        "canonical_doc_uid": "uokik_pl:urlsha:5efe92f726049194",
        "document_kind": "CASELAW",
        "legal_role": "EXCLUDED",
        "expected_external_id": "uokik:AmC 86/2003",
        "required_top_level": False,
        "notes": "Developer/admin relation only; move out of core runtime.",
    },
    38: {
        "status": "optional",
        "canonical_title": "Prawo.pl commentary on abusive clauses in lease contracts",
        "canonical_doc_uid": "prawo_pl:urlsha:7315b25566b744a4",
        "document_kind": "COMMENTARY",
        "legal_role": "COMMENTARY",
        "expected_external_id": "prawo:510151",
        "required_top_level": False,
        "notes": "Commentary only; should not outrank official norms or leading cases.",
    },
}

DERIVED_RUNTIME_TARGETS: tuple[MigrationEntry, ...] = (
    MigrationEntry(
        entry_id="runtime-current-lokatorzy-act",
        position=None,
        source_url=REQUIRED_SOURCE_BY_ENTRY_ID[
            "runtime-current-lokatorzy-act"
        ].source_url,
        source_id=REQUIRED_SOURCE_BY_ENTRY_ID[
            "runtime-current-lokatorzy-act"
        ].source_id,
        source_doc_uid="eli_pl:DU/2001/733",
        status="canonical",
        canonical_title=REQUIRED_SOURCE_BY_ENTRY_ID[
            "runtime-current-lokatorzy-act"
        ].canonical_title,
        canonical_doc_uid=REQUIRED_SOURCE_BY_ENTRY_ID[
            "runtime-current-lokatorzy-act"
        ].doc_uid,
        document_kind="STATUTE",
        legal_role="DIRECT_NORM",
        expected_external_id=REQUIRED_SOURCE_BY_ENTRY_ID[
            "runtime-current-lokatorzy-act"
        ].external_id,
        required_top_level=True,
        notes="TechSpec 3.1 requires current consolidated text; legacy original PDF remains only as archived source in document_sources.",
        match_doc_uids=(
            "eli_pl:DU/2001/733",
            "eli_pl:urlsha:8b1bb9b48a8ca9ec",
            "lex_pl:16903658",
        ),
        match_source_urls=(
            REQUIRED_SOURCE_BY_ENTRY_ID["runtime-current-lokatorzy-act"].source_url,
        ),
    ),
    MigrationEntry(
        entry_id="runtime-current-kc",
        position=None,
        source_url=REQUIRED_SOURCE_BY_ENTRY_ID["runtime-current-kc"].source_url,
        source_id=REQUIRED_SOURCE_BY_ENTRY_ID["runtime-current-kc"].source_id,
        source_doc_uid="isap_pl:WDU19640160093",
        status="canonical",
        canonical_title=REQUIRED_SOURCE_BY_ENTRY_ID[
            "runtime-current-kc"
        ].canonical_title,
        canonical_doc_uid=REQUIRED_SOURCE_BY_ENTRY_ID["runtime-current-kc"].doc_uid,
        document_kind="STATUTE",
        legal_role="DIRECT_NORM",
        expected_external_id=REQUIRED_SOURCE_BY_ENTRY_ID[
            "runtime-current-kc"
        ].external_id,
        required_top_level=True,
        notes="TechSpec 3.1 requires current consolidated KC text; canonical record is kept in place under the existing ISAP doc_uid.",
        match_doc_uids=("isap_pl:WDU19640160093", "isap_pl:urlsha:444655e6a3a3aef1"),
        match_source_urls=(
            REQUIRED_SOURCE_BY_ENTRY_ID["runtime-current-kc"].source_url,
        ),
    ),
)

REQUIRED_ADDITIONS: tuple[MigrationEntry, ...] = (
    MigrationEntry(
        entry_id="required-addition-kpc",
        position=None,
        source_url=REQUIRED_SOURCE_BY_ENTRY_ID["required-addition-kpc"].source_url,
        source_id=REQUIRED_SOURCE_BY_ENTRY_ID["required-addition-kpc"].source_id,
        source_doc_uid=None,
        status="canonical",
        canonical_title=REQUIRED_SOURCE_BY_ENTRY_ID[
            "required-addition-kpc"
        ].canonical_title,
        canonical_doc_uid=REQUIRED_SOURCE_BY_ENTRY_ID["required-addition-kpc"].doc_uid,
        document_kind="STATUTE",
        legal_role="PROCESS_NORM",
        expected_external_id=REQUIRED_SOURCE_BY_ENTRY_ID[
            "required-addition-kpc"
        ].external_id,
        required_top_level=True,
        notes="Mandatory section 3 addition for process questions.",
        match_source_urls=(
            REQUIRED_SOURCE_BY_ENTRY_ID["required-addition-kpc"].source_url,
        ),
    ),
    MigrationEntry(
        entry_id="required-addition-costs-act",
        position=None,
        source_url=REQUIRED_SOURCE_BY_ENTRY_ID[
            "required-addition-costs-act"
        ].source_url,
        source_id=REQUIRED_SOURCE_BY_ENTRY_ID["required-addition-costs-act"].source_id,
        source_doc_uid=None,
        status="canonical",
        canonical_title=REQUIRED_SOURCE_BY_ENTRY_ID[
            "required-addition-costs-act"
        ].canonical_title,
        canonical_doc_uid=REQUIRED_SOURCE_BY_ENTRY_ID[
            "required-addition-costs-act"
        ].doc_uid,
        document_kind="STATUTE",
        legal_role="PROCESS_NORM",
        expected_external_id=REQUIRED_SOURCE_BY_ENTRY_ID[
            "required-addition-costs-act"
        ].external_id,
        required_top_level=True,
        notes="Mandatory section 3 addition for court fees.",
        match_source_urls=(
            REQUIRED_SOURCE_BY_ENTRY_ID["required-addition-costs-act"].source_url,
        ),
    ),
    MigrationEntry(
        entry_id="required-addition-uokk",
        position=None,
        source_url=REQUIRED_SOURCE_BY_ENTRY_ID["required-addition-uokk"].source_url,
        source_id=REQUIRED_SOURCE_BY_ENTRY_ID["required-addition-uokk"].source_id,
        source_doc_uid=None,
        status="canonical",
        canonical_title=REQUIRED_SOURCE_BY_ENTRY_ID[
            "required-addition-uokk"
        ].canonical_title,
        canonical_doc_uid=REQUIRED_SOURCE_BY_ENTRY_ID["required-addition-uokk"].doc_uid,
        document_kind="STATUTE",
        legal_role="EU_CONSUMER_LAYER",
        expected_external_id=REQUIRED_SOURCE_BY_ENTRY_ID[
            "required-addition-uokk"
        ].external_id,
        required_top_level=True,
        notes="Mandatory section 3 addition when consumer layer is preserved.",
        match_source_urls=(
            REQUIRED_SOURCE_BY_ENTRY_ID["required-addition-uokk"].source_url,
        ),
    ),
)


def _build_position_entry(position: int) -> MigrationEntry:
    source = get_source_entry(position)
    policy = POSITION_POLICIES[position]
    status = policy["status"]
    if status not in MIGRATION_STATUS_VALUES:
        raise ValueError(
            f"Unsupported migration status for position {position}: {status}"
        )

    canonical_doc_uid = policy.get("canonical_doc_uid")
    match_doc_uids = tuple(policy.get("match_doc_uids", ()))
    if source.source_doc_uid not in match_doc_uids:
        match_doc_uids = (source.source_doc_uid, *match_doc_uids)

    return MigrationEntry(
        entry_id=f"position-{position}",
        position=position,
        source_url=source.source_url,
        source_id=source.source_id,
        source_doc_uid=source.source_doc_uid,
        status=status,
        canonical_title=policy["canonical_title"],
        canonical_doc_uid=canonical_doc_uid,
        document_kind=policy["document_kind"],
        legal_role=policy["legal_role"],
        expected_external_id=policy["expected_external_id"],
        required_top_level=policy["required_top_level"],
        notes=policy["notes"],
        match_doc_uids=match_doc_uids,
        match_source_urls=(source.source_url,),
    )


def build_migration_payload() -> dict[str, Any]:
    positions = [
        _build_position_entry(source.position).to_dict()
        for source in TECHSPEC_SOURCE_CATALOG
    ]
    derived_targets = [entry.to_dict() for entry in DERIVED_RUNTIME_TARGETS]
    required_additions = [entry.to_dict() for entry in REQUIRED_ADDITIONS]
    payload = {
        "schema_version": "techspec-3.1",
        "source_list_path": "legal_ingest.source_catalog.TECHSPEC_SOURCE_CATALOG",
        "positions": positions,
        "derived_runtime_targets": derived_targets,
        "required_additions": required_additions,
    }
    validate_migration_payload(payload)
    return payload


def validate_migration_payload(payload: dict[str, Any]) -> None:
    seen_entry_ids: set[str] = set()
    for group_key in ("positions", "derived_runtime_targets", "required_additions"):
        for entry in payload.get(group_key, []):
            entry_id = str(entry["entry_id"])
            if entry_id in seen_entry_ids:
                raise ValueError(f"Duplicate migration entry_id: {entry_id}")
            seen_entry_ids.add(entry_id)

            status = entry.get("status")
            if status not in MIGRATION_STATUS_VALUES:
                raise ValueError(
                    f"Unsupported migration status for {entry_id}: {status}"
                )

            if status == "canonical" and not entry.get("canonical_doc_uid"):
                raise ValueError(
                    f"canonical entry must define canonical_doc_uid: {entry_id}"
                )


def get_required_runtime_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for group_key in ("positions", "derived_runtime_targets", "required_additions"):
        entries.extend(
            entry
            for entry in payload.get(group_key, [])
            if entry.get("required_top_level")
        )
    return entries


def write_migration_map(output_path: Path | None = None) -> Path:
    target_path = resolve_path(output_path or DEFAULT_MIGRATION_MAP_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_migration_payload()
    target_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target_path


def load_migration_payload(path: Path | None = None) -> dict[str, Any]:
    target_path = resolve_path(path or DEFAULT_MIGRATION_MAP_PATH)
    if target_path.exists():
        payload = json.loads(target_path.read_text(encoding="utf-8"))
        validate_migration_payload(payload)
        return payload
    return build_migration_payload()
