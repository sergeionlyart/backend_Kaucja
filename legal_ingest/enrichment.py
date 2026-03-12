from __future__ import annotations

import re
from typing import Any, Mapping

from legal_ingest.curated_quality import (
    get_curated_caselaw_override,
    get_unknown_judgment_date_exemption_reason,
)
from legal_ingest.normalization import (
    ACT_KINDS,
    clean_title,
    is_explicit_broken_inventory_record,
    normalize_title,
    normalize_url,
)

CASE_SIGNATURE_PATTERN = re.compile(
    r"\b([IVXLCDM]{1,7}\s+[A-Za-z]{1,6}(?:\s+[A-Za-z]{1,6})?\s+\d{1,6}/\d{2,4})\b",
    re.IGNORECASE,
)
GENERIC_CASE_SIGNATURE_PATTERN = re.compile(
    r"\b([A-Z]{1,4}\s+\d{1,6}/\d{2,4})\b",
    re.IGNORECASE,
)
PORTAL_SIGNATURE_PATTERN = re.compile(
    r"([IVXLCDM]{1,7})_([A-Za-z]{1,6})_(\d{1,6})_(\d{4})",
    re.IGNORECASE,
)
ISO_DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
POLISH_TEXTUAL_DATE_PATTERN = re.compile(
    r"z dnia\s+(\d{1,2})\s+([a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)\s+(\d{4})\s*r\.?",
    re.IGNORECASE,
)
POLISH_LEADING_DATE_PATTERN = re.compile(
    r"(?:^|\b)(?:dnia|Dnia)\s+(\d{1,2})\s+"
    r"([a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)\s+(\d{4})\s*r\.?",
    re.IGNORECASE,
)
ENGLISH_TEXTUAL_DATE_PATTERN = re.compile(
    r"\b(\d{1,2})\s+"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"(\d{4})\b",
    re.IGNORECASE,
)
COURT_NAME_PATTERN = re.compile(
    r"(S[aą]d\s+[A-ZĄĆĘŁŃÓŚŹŻ][^,;]+|Trybuna[łl]\s+Konstytucyjny)",
    re.IGNORECASE,
)
COURT_NAME_TEXT_PATTERN = re.compile(
    r"(S[aą]d\s+(?:Najwy[zż]szy|Apelacyjny|Okr[eę]gowy|Rejonowy)[^,\n]{0,120}?)"
    r"(?=(?:\s+[IVXLC]+\s+Wydzia[łl]|\s*[–-]\s*Wydzia[łl]|\s+w składzie|\s+po rozpoznaniu|$))",
    re.IGNORECASE,
)
COURT_NAME_DATE_SUFFIX_PATTERN = re.compile(
    r"\s+z\s+\d{4}-\d{2}-\d{2}$",
    re.IGNORECASE,
)
COURT_NAME_WYDZIAL_SUFFIX_PATTERN = re.compile(
    r"\s+(?:[IVXLC]+\s+)?Wydzia[łl].*$",
    re.IGNORECASE,
)
CELEX_CASE_PATTERN = re.compile(r"^celex:6(\d{4})([A-Z]{2})(\d{4})", re.IGNORECASE)
CASE_NUMBER_PATTERN = re.compile(r"\b([CTF])[- ](\d{1,4}/\d{2})\b", re.IGNORECASE)

POLISH_MONTHS = {
    "stycznia": "01",
    "lutego": "02",
    "marca": "03",
    "kwietnia": "04",
    "maja": "05",
    "czerwca": "06",
    "lipca": "07",
    "sierpnia": "08",
    "wrzesnia": "09",
    "października": "10",
    "pazdziernika": "10",
    "listopada": "11",
    "grudnia": "12",
}

ENGLISH_MONTHS = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}

DEFAULT_NEGATIVE_TERMS = [
    "untitled html document",
    "error",
    "wyniki wyszukiwania",
]

TOPIC_RULES = (
    ("tenant_law", ("lokator", "najem", "mieszkaniow", "mieszkaniowym")),
    ("tenant_deposit", ("kaucj",)),
    ("civil_code", ("kodeks cywilny", " kc ", "art. 385", "art. 471", "art. 481")),
    (
        "civil_procedure",
        ("postepowania cywilnego", "procedur", "kpc", "egzekuc", "nakaz"),
    ),
    ("court_costs", ("kosztach sadowych", "koszt", "oplata sadowa")),
    (
        "competition_consumer",
        ("uokik", "konkurencji", "konsument", "consumer protection"),
    ),
    (
        "unfair_terms",
        ("93/13", "unfair term", "abuzyw", "pannon gsm", "asbeek brusse"),
    ),
)

PROVISION_RULES = {
    "tenant_law": ["Ustawa o ochronie praw lokatorow"],
    "tenant_deposit": ["art. 6 ustawy o ochronie praw lokatorow"],
    "civil_code": ["Kodeks cywilny"],
    "civil_procedure": ["Kodeks postepowania cywilnego"],
    "court_costs": ["Ustawa o kosztach sadowych w sprawach cywilnych"],
    "competition_consumer": ["Ustawa o ochronie konkurencji i konsumentow"],
    "unfair_terms": ["Directive 93/13/EEC"],
}


def normalize_case_signature(signature: str) -> str:
    parts = re.split(r"\s+", signature.strip())
    if len(parts) < 2:
        return signature.strip().upper()

    head = parts[0].upper()
    middle = " ".join(part.upper() for part in parts[1:-1])
    number, _, year = parts[-1].partition("/")
    normalized_number = str(int(number))
    normalized_year = year[-2:] if len(year) == 4 else year
    if middle:
        return f"{head} {middle} {normalized_number}/{normalized_year}"
    return f"{head} {normalized_number}/{normalized_year}"


def extract_case_signature(document: Mapping[str, Any]) -> str | None:
    value = document.get("case_signature")
    if isinstance(value, str) and value.strip():
        return value.strip()

    external_ids = document.get("external_ids")
    if isinstance(external_ids, dict):
        sn_signature = external_ids.get("sn_signature")
        if isinstance(sn_signature, str) and sn_signature.strip():
            return sn_signature.strip()

    external_id = document.get("external_id")
    if isinstance(external_id, str):
        if external_id.startswith(("sn:", "case:")):
            _, _, value = external_id.partition(":")
            if value.strip():
                return value.strip()
        celex_signature = _extract_case_signature_from_celex(external_id)
        if celex_signature:
            return celex_signature

    for candidate in _case_text_candidates(document):
        if not candidate:
            continue
        normalized_candidate = candidate.replace("_", " ")
        match = CASE_SIGNATURE_PATTERN.search(normalized_candidate)
        if match is not None:
            return match.group(1)
        match = GENERIC_CASE_SIGNATURE_PATTERN.search(normalized_candidate)
        if match is not None:
            return match.group(1)
        match = CASE_NUMBER_PATTERN.search(normalized_candidate)
        if match is not None:
            family, number = match.groups()
            return f"{family.upper()}-{number}"

    for source_url in document.get("source_urls", []):
        if not isinstance(source_url, str):
            continue
        match = PORTAL_SIGNATURE_PATTERN.search(source_url)
        if match is None:
            continue
        roman, symbol, number, year = match.groups()
        return f"{roman.upper()} {symbol} {int(number)}/{year[-2:]}"

    return None


def build_section5_enrichment(
    *,
    document: Mapping[str, Any],
    current_source: Mapping[str, Any] | None,
    document_kind: str,
    status: str,
    legal_role: str,
    canonical_title: str,
    source_url: str | None,
    external_id: str,
    act_id: str | None,
    act_short_name: str | None,
    canonical_doc_uid: str | None,
    duplicate_owner_doc_uid: str | None,
    same_case_group_id: str | None,
) -> dict[str, Any]:
    title_short = derive_title_short(
        document=document,
        document_kind=document_kind,
        canonical_title=canonical_title,
        act_short_name=act_short_name,
        external_id=external_id,
    )
    issue_tags = derive_issue_tags(
        document=document,
        document_kind=document_kind,
        status=status,
        legal_role=legal_role,
        canonical_title=canonical_title,
        source_url=source_url,
        external_id=external_id,
        act_id=act_id,
    )
    query_context = {
        "document": document,
        "document_kind": document_kind,
        "title_short": title_short,
        "canonical_title": canonical_title,
        "external_id": external_id,
        "source_url": source_url,
    }
    enrichment: dict[str, Any] = {
        "title_short": title_short,
        "summary_1line": derive_summary_1line(
            document=document,
            document_kind=document_kind,
            status=status,
            legal_role=legal_role,
            title_short=title_short,
            canonical_doc_uid=canonical_doc_uid,
            duplicate_owner_doc_uid=duplicate_owner_doc_uid,
        ),
        "issue_tags": issue_tags,
        "relevance_score": derive_relevance_score(
            status=status,
            legal_role=legal_role,
            issue_tags=issue_tags,
        ),
        "search_terms_positive": derive_search_terms_positive(
            title_short=title_short,
            canonical_title=canonical_title,
            external_id=external_id,
            act_short_name=act_short_name,
            case_signature=extract_case_signature(document),
        ),
        "search_terms_negative": list(DEFAULT_NEGATIVE_TERMS),
        "query_templates": derive_query_templates(query_context),
        "last_verified_at": resolve_last_verified_at(
            document=document,
            current_source=current_source,
        ),
    }

    if document_kind == "CASELAW":
        case_signature = resolve_case_signature(document, external_id=external_id)
        if same_case_group_id is None:
            same_case_group_id = build_singleton_same_case_group_id(document)
        caselaw_issue_tags = list(issue_tags)
        enrichment.update(
            {
                "case_signature": case_signature,
                "judgment_date": derive_judgment_date(document),
                "court_name": derive_court_name(
                    document=document,
                    case_signature=case_signature,
                ),
                "court_level": derive_court_level(
                    document=document,
                    case_signature=case_signature,
                    source_url=source_url,
                ),
                "artifact_type": derive_artifact_type(document),
                "holding_1line": derive_holding_1line(
                    document=document,
                    status=status,
                    legal_role=legal_role,
                    case_signature=case_signature,
                ),
                "facts_tags": derive_facts_tags(
                    document=document,
                    issue_tags=caselaw_issue_tags,
                    status=status,
                    legal_role=legal_role,
                ),
                "related_provisions": derive_related_provisions(caselaw_issue_tags),
                "same_case_group_id": same_case_group_id,
            }
        )
        curated_override = get_curated_caselaw_override(str(document.get("doc_uid")))
        if curated_override:
            enrichment.update(curated_override)

    search_fields = derive_search_record_fields(
        document=document,
        status=status,
        legal_role=legal_role,
        canonical_doc_uid=canonical_doc_uid,
        duplicate_owner_doc_uid=duplicate_owner_doc_uid,
    )
    enrichment.update(search_fields)
    return enrichment


def derive_title_short(
    *,
    document: Mapping[str, Any],
    document_kind: str,
    canonical_title: str,
    act_short_name: str | None,
    external_id: str,
) -> str:
    existing = clean_title(document.get("title_short"))
    if existing:
        return existing

    case_signature = extract_case_signature(document)
    if document_kind == "CASELAW" and case_signature:
        return normalize_case_signature(case_signature)
    if document_kind in ACT_KINDS and act_short_name:
        return act_short_name
    if document_kind == "STATUTE_REF":
        return external_id
    return shorten_title(canonical_title)


def derive_summary_1line(
    *,
    document: Mapping[str, Any],
    document_kind: str,
    status: str,
    legal_role: str,
    title_short: str,
    canonical_doc_uid: str | None,
    duplicate_owner_doc_uid: str | None,
) -> str:
    if is_explicit_broken_inventory_record(document) or legal_role == "INVENTORY_ONLY":
        return f"Excluded inventory record retained for traceability: {title_short}."
    if status == "alias":
        owner_ref = duplicate_owner_doc_uid or canonical_doc_uid or "canonical record"
        return (
            f"Alias record for {title_short}; refer to {owner_ref} for operational use."
        )
    if document_kind in ACT_KINDS:
        return f"Normative corpus record: {title_short}."
    if document_kind == "CASELAW":
        return f"Caselaw corpus record: {title_short}."
    return f"Corpus record: {title_short}."


def derive_issue_tags(
    *,
    document: Mapping[str, Any],
    document_kind: str,
    status: str,
    legal_role: str,
    canonical_title: str,
    source_url: str | None,
    external_id: str,
    act_id: str | None,
) -> list[str]:
    tags = [kind_tag(document_kind)]
    search_blob = " ".join(
        value
        for value in (
            clean_title(canonical_title),
            clean_title(document.get("title")),
            clean_title(external_id),
            clean_title(act_id),
            clean_title(source_url),
        )
        if value
    ).casefold()

    for tag, markers in TOPIC_RULES:
        if any(marker in search_blob for marker in markers):
            tags.append(tag)

    if status == "alias":
        tags.append("alias")
    if status == "excluded":
        tags.append("excluded")
    if legal_role == "INVENTORY_ONLY":
        tags.append("inventory_only")
    if legal_role == "SECONDARY_SOURCE":
        tags.append("secondary_source")
    if "tenant_law" not in tags and act_id == "eli:DU/2001/733":
        tags.append("tenant_law")
    if "civil_code" not in tags and act_id == "isap:WDU19640160093":
        tags.append("civil_code")
    if "civil_procedure" not in tags and act_id == "eli:DU/1964/296":
        tags.append("civil_procedure")
    if "court_costs" not in tags and act_id == "eli:DU/2005/1398":
        tags.append("court_costs")
    if "competition_consumer" not in tags and act_id == "eli:DU/2007/331":
        tags.append("competition_consumer")
    return unique_strings(tags) or ["general"]


def derive_relevance_score(
    *,
    status: str,
    legal_role: str,
    issue_tags: list[str],
) -> int:
    base_scores = {
        "canonical": 100,
        "active": 80,
        "optional": 70,
        "article_node": 65,
        "alias": 45,
        "excluded": 10,
    }
    score = base_scores.get(status, 50)
    if legal_role in {"DIRECT_NORM", "PROCESS_NORM"}:
        score += 10
    if "tenant_law" in issue_tags or "tenant_deposit" in issue_tags:
        score += 5
    if legal_role in {"INVENTORY_ONLY", "DUPLICATE_ALIAS"}:
        score = min(score, 20)
    return max(0, min(score, 100))


def derive_search_terms_positive(
    *,
    title_short: str,
    canonical_title: str,
    external_id: str,
    act_short_name: str | None,
    case_signature: str | None,
) -> list[str]:
    return unique_strings(
        [
            title_short,
            case_signature,
            act_short_name,
            canonical_title,
            external_id,
        ]
    )[:5]


def derive_query_templates(context: Mapping[str, Any]) -> list[str]:
    document = context["document"]
    document_kind = str(context["document_kind"])
    title_short = str(context["title_short"])
    canonical_title = str(context["canonical_title"])
    external_id = str(context["external_id"])
    source_url = context.get("source_url")

    templates = [title_short, canonical_title, external_id]
    case_signature = extract_case_signature(document)
    if document_kind == "CASELAW" and case_signature:
        normalized_signature = clean_title(case_signature) or case_signature
        if "/" in normalized_signature:
            normalized_signature = normalize_case_signature(normalized_signature)
        templates.insert(1, normalized_signature)
    if document_kind in ACT_KINDS and source_url:
        templates.append(str(source_url))
    return unique_strings(templates)[:4]


def resolve_last_verified_at(
    *,
    document: Mapping[str, Any],
    current_source: Mapping[str, Any] | None,
) -> Any:
    for key in ("last_verified_at", "updated_at", "ingested_at"):
        value = document.get(key)
        if value is not None:
            return value

    for key in ("fetched_at", "ingested_at", "created_at"):
        value = (current_source or {}).get(key)
        if value is not None:
            return value
    return document.get("updated_at")


def resolve_case_signature(
    document: Mapping[str, Any],
    *,
    external_id: str,
) -> str:
    extracted = extract_case_signature(document)
    if extracted:
        cleaned = clean_title(extracted) or external_id
        if "/" not in cleaned:
            return cleaned
        return normalize_case_signature(cleaned)
    return external_id


def derive_judgment_date(document: Mapping[str, Any]) -> str:
    for key in ("judgment_date", "date_decision", "date_published"):
        value = document.get(key)
        if isinstance(value, str) and value.strip() and value.strip() != "unknown":
            return value.strip()

    return _extract_judgment_date_signal(document) or "unknown"


def derive_court_name(
    *,
    document: Mapping[str, Any],
    case_signature: str,
) -> str:
    existing = normalize_court_name(document.get("court_name"))
    if existing and not is_unresolved_court_name(existing):
        return existing

    for candidate in _pageindex_titles(document):
        match = COURT_NAME_PATTERN.search(candidate)
        if match is not None:
            normalized = normalize_court_name(match.group(1))
            if normalized and not is_unresolved_court_name(normalized):
                return normalized

    source_text = _source_text_blob(document)
    if source_text:
        normalized_blob = source_text.casefold()
        if "sąd ochrony konkurencji i konsumentów" in normalized_blob:
            return "Sąd Okręgowy w Warszawie, Sąd Ochrony Konkurencji i Konsumentów"
        if "sad ochrony konkurencji i konsumentow" in normalized_blob:
            return "Sad Okregowy w Warszawie, Sad Ochrony Konkurencji i Konsumentow"
        match = COURT_NAME_TEXT_PATTERN.search(source_text)
        if match is not None:
            normalized = normalize_court_name(match.group(1))
            if normalized and not is_unresolved_court_name(normalized):
                return normalized

    title_blob = " ".join(_case_text_candidates(document)).casefold()
    source_system = str(document.get("source_system") or "").lower()

    if "trybunal konstytucyjny" in title_blob or " wyrok tk " in f" {title_blob} ":
        return "Trybunal Konstytucyjny"
    if source_system == "sn_pl" or " sad najwyzszy " in f" {title_blob} ":
        return "Sad Najwyzszy"
    if source_system in {"curia_eu", "eurlex_eu"}:
        return _eu_court_name(case_signature)
    if source_system == "courts_pl":
        return "Sad powszechny (portal orzeczen)"
    if source_system == "saos_pl":
        return "Sad powszechny (SAOS)"
    return "Court not identified from source"


def derive_court_level(
    *,
    document: Mapping[str, Any],
    case_signature: str,
    source_url: str | None,
) -> str:
    existing = clean_title(document.get("court_level"))
    if existing:
        return existing

    source_system = str(document.get("source_system") or "").lower()
    titles = " ".join(_case_text_candidates(document)).casefold()
    source_text = _source_text_blob(document).casefold()
    normalized_signature = case_signature.casefold()
    normalized_source_url = normalize_url(
        source_url or document.get("source_url") or ""
    )
    normalized_source_url = normalized_source_url or ""

    if source_system == "sn_pl" or " najwyzszy" in titles:
        return "supreme"
    if "trybunal konstytucyjny" in titles or " tk " in f" {titles} ":
        return "constitutional"
    if source_system in {"curia_eu", "eurlex_eu"}:
        return "eu_court"
    if (
        "ochrony konkurencji i konsumentow" in source_text
        or "ochrony konkurencji i konsumentów" in source_text
    ):
        return "regional"
    if "apelacyjny" in titles or " aca " in f" {normalized_signature} ":
        return "appellate"
    if "okregowy" in titles or ".so.gov.pl" in normalized_source_url:
        return "regional"
    if "rejonowy" in titles or ".sr.gov.pl" in normalized_source_url:
        return "district"
    if source_system in {"saos_pl", "courts_pl"}:
        return "common_court"
    return "unknown"


def derive_artifact_type(document: Mapping[str, Any]) -> str:
    existing = clean_title(document.get("artifact_type"))
    if existing:
        return existing

    text = " ".join(
        _case_text_candidates(document) + _pageindex_titles(document)
    ).casefold()
    source_url = normalize_url(document.get("source_url") or "") or ""
    if "_uz_" in source_url or "uzasadn" in text or "reasons" in text:
        return "judgment_with_reasons"
    if "uchwal" in text:
        return "resolution"
    if "postanow" in text or "order" in text:
        return "order"
    if "decyzja" in text:
        return "decision"
    return "judgment"


def derive_holding_1line(
    *,
    document: Mapping[str, Any],
    status: str,
    legal_role: str,
    case_signature: str,
) -> str:
    if is_explicit_broken_inventory_record(document) or legal_role == "INVENTORY_ONLY":
        return f"Excluded corpus record for {case_signature}; no reliable holding extracted."
    if status == "alias" or legal_role == "SECONDARY_SOURCE":
        return f"Secondary corpus record for {case_signature}; consult the canonical record for the operative holding."
    return f"Rule-based placeholder for {case_signature}; substantive holding was not semantically extracted in this iteration."


def derive_facts_tags(
    *,
    document: Mapping[str, Any],
    issue_tags: list[str],
    status: str,
    legal_role: str,
) -> list[str]:
    if is_explicit_broken_inventory_record(document) or legal_role == "INVENTORY_ONLY":
        return ["broken_artifact_inventory"]

    tags = [
        tag
        for tag in issue_tags
        if tag
        not in {"caselaw", "excluded", "alias", "inventory_only", "secondary_source"}
    ]
    if status == "alias" or legal_role == "SECONDARY_SOURCE":
        tags.append("secondary_source")
    if not tags:
        tags.append("facts_not_extracted")
    return unique_strings(tags)


def derive_related_provisions(issue_tags: list[str]) -> list[str]:
    provisions: list[str] = []
    for tag in issue_tags:
        provisions.extend(PROVISION_RULES.get(tag, []))
    if not provisions:
        return ["not_determined"]
    return unique_strings(provisions)


def is_generic_holding_placeholder(value: Any) -> bool:
    normalized = clean_title(str(value) if value is not None else None)
    if normalized is None:
        return False
    return normalized.startswith("Rule-based placeholder for ")


def is_fallback_facts_tags(value: Any) -> bool:
    return list(value or []) == ["facts_not_extracted"]


def is_fallback_related_provisions(value: Any) -> bool:
    return list(value or []) == ["not_determined"]


def is_unresolved_court_name(value: Any) -> bool:
    normalized = clean_title(str(value) if value is not None else None)
    if normalized is None:
        return True
    return normalized == "Court not identified from source" or bool(
        ISO_DATE_PATTERN.search(normalized)
    )


def has_avoidable_unknown_judgment_date(document: Mapping[str, Any]) -> bool:
    if clean_title(document.get("judgment_date")) != "unknown":
        return False
    if detect_search_page(document):
        return False
    if get_unknown_judgment_date_exemption_reason(str(document.get("doc_uid"))):
        return False
    return _extract_judgment_date_signal(document) is not None


def derive_search_record_fields(
    *,
    document: Mapping[str, Any],
    status: str,
    legal_role: str,
    canonical_doc_uid: str | None,
    duplicate_owner_doc_uid: str | None,
) -> dict[str, Any]:
    is_search_page = detect_search_page(document)
    search_fields: dict[str, Any] = {"is_search_page": is_search_page}
    if status in {"alias", "excluded", "archived"}:
        search_fields["superseded_by"] = resolve_superseded_by(
            document=document,
            legal_role=legal_role,
            canonical_doc_uid=canonical_doc_uid,
            duplicate_owner_doc_uid=duplicate_owner_doc_uid,
        )
    return search_fields


def detect_search_page(document: Mapping[str, Any]) -> bool:
    search_blob = " ".join(
        candidate.casefold()
        for candidate in (
            clean_title(document.get("canonical_title")),
            clean_title(document.get("title")),
            clean_title(document.get("source_url")),
        )
        if candidate
    )
    return any(
        marker in search_blob
        for marker in ("search", "wyszukiwark", "wyniki", "rejestr", "registry")
    )


def resolve_superseded_by(
    *,
    document: Mapping[str, Any],
    legal_role: str,
    canonical_doc_uid: str | None,
    duplicate_owner_doc_uid: str | None,
) -> str:
    existing = clean_title(document.get("superseded_by"))
    if existing:
        return existing
    if duplicate_owner_doc_uid:
        return duplicate_owner_doc_uid
    if canonical_doc_uid and canonical_doc_uid != document.get("doc_uid"):
        return str(canonical_doc_uid)
    if is_explicit_broken_inventory_record(document) or legal_role == "INVENTORY_ONLY":
        return "inventory_only"
    if detect_search_page(document):
        return "search_page"
    return "not_applicable"


def build_singleton_same_case_group_id(document: Mapping[str, Any]) -> str:
    doc_uid = str(document.get("doc_uid") or "")
    slug = re.sub(r"[^a-z0-9]+", "_", doc_uid.casefold()).strip("_")
    return f"same_case:singleton:{slug or 'document'}"


def kind_tag(document_kind: str) -> str:
    mapping = {
        "CASELAW": "caselaw",
        "STATUTE": "act",
        "EU_ACT": "act",
        "GUIDANCE": "guidance",
        "COMMENTARY": "commentary",
        "STATUTE_REF": "article_node",
    }
    return mapping.get(document_kind, "document")


def shorten_title(value: str, *, limit: int = 96) -> str:
    normalized = clean_title(value) or ""
    if len(normalized) <= limit:
        return normalized
    clipped = normalized[: limit - 1].rsplit(" ", 1)[0]
    return (clipped or normalized[: limit - 1]) + "..."


def unique_strings(values: list[str | None]) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = clean_title(value)
        if not normalized:
            continue
        key = normalize_title(normalized) or normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        results.append(normalized)
    return results


def normalize_court_name(value: Any) -> str | None:
    normalized = clean_title(str(value) if value is not None else None)
    if normalized is None:
        return None
    normalized = COURT_NAME_DATE_SUFFIX_PATTERN.sub("", normalized)
    normalized = COURT_NAME_WYDZIAL_SUFFIX_PATTERN.sub("", normalized)
    normalized = re.sub(r"\s*,\s*", ", ", normalized)
    normalized = re.sub(r"\s+[–-]\s*$", "", normalized)
    return clean_title(normalized)


def _extract_case_signature_from_celex(external_id: str) -> str | None:
    match = CELEX_CASE_PATTERN.match(external_id.strip())
    if match is None:
        return None
    year, court_code, case_number = match.groups()
    family = {"CJ": "C", "CC": "C", "TJ": "T", "TC": "T", "FJ": "F"}.get(
        court_code.upper(),
        "C",
    )
    return f"{family}-{int(case_number)}/{year[-2:]}"


def _case_text_candidates(document: Mapping[str, Any]) -> list[str]:
    candidates = [
        clean_title(document.get("case_signature")),
        clean_title(document.get("canonical_title")),
        clean_title(document.get("title")),
        clean_title(document.get("external_id")),
    ]
    return [candidate for candidate in candidates if candidate]


def _extract_judgment_date_signal(document: Mapping[str, Any]) -> str | None:
    candidates: list[str] = []
    candidates.extend(_pageindex_titles(document))
    candidates.extend(_source_url_candidates(document))
    source_text = _source_text_blob(document)
    if source_text:
        candidates.append(source_text)
    candidates.extend(_case_text_candidates(document))

    for candidate in candidates:
        normalized = _parse_date_from_text(candidate)
        if normalized:
            return normalized
    return None


def _parse_date_from_text(value: str | None) -> str | None:
    candidate = clean_title(value)
    if candidate is None:
        return None
    if iso_match := ISO_DATE_PATTERN.search(candidate):
        return iso_match.group(1)
    for pattern in (POLISH_TEXTUAL_DATE_PATTERN, POLISH_LEADING_DATE_PATTERN):
        textual_match = pattern.search(candidate)
        if textual_match is not None:
            day, month_name, year = textual_match.groups()
            month = POLISH_MONTHS.get(month_name.casefold())
            if month:
                return f"{year}-{month}-{int(day):02d}"
    english_match = ENGLISH_TEXTUAL_DATE_PATTERN.search(candidate)
    if english_match is not None:
        day, month_name, year = english_match.groups()
        month = ENGLISH_MONTHS.get(month_name.casefold())
        if month:
            return f"{year}-{month}-{int(day):02d}"
    return None


def _source_url_candidates(document: Mapping[str, Any]) -> list[str]:
    candidates = [clean_title(document.get("source_url"))]
    for source_url in document.get("source_urls", []):
        candidates.append(clean_title(source_url))
    return [candidate for candidate in candidates if candidate]


def _source_text_blob(document: Mapping[str, Any]) -> str:
    return clean_title(document.get("_source_text_blob")) or ""


def _pageindex_titles(document: Mapping[str, Any]) -> list[str]:
    titles: list[str] = []
    for node in document.get("pageindex_tree") or []:
        _collect_pageindex_titles(node, titles)
    return titles


def _collect_pageindex_titles(node: Mapping[str, Any], titles: list[str]) -> None:
    title = clean_title(node.get("title"))
    if title:
        titles.append(title)
    for child in node.get("nodes") or []:
        if isinstance(child, Mapping):
            _collect_pageindex_titles(child, titles)


def _eu_court_name(case_signature: str) -> str:
    if case_signature.upper().startswith("T-"):
        return "General Court of the European Union"
    return "Court of Justice of the European Union"
