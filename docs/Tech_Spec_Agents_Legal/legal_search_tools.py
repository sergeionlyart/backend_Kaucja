from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from agents import function_tool
from agents.tool_context import ToolContext
from pydantic import BaseModel, ConfigDict, Field
from pymongo.collection import Collection
from pymongo.database import Database


ISSUE_KEYWORDS: dict[str, list[str]] = {
    "deposit_legal_basis": ["kaucja", "deposit", "legal basis"],
    "deposit_amount_limit": ["kaucja", "deposit amount", "limit"],
    "deposit_return_term": ["zwrot kaucji", "return term", "deadline"],
    "allowed_deductions": ["potracenie", "deduction", "damage", "arrears"],
    "wear_and_tear": ["normal wear", "zuzycie", "wear and tear"],
    "property_damage": ["damage", "uszkodzenie", "repair"],
    "rent_arrears": ["rent arrears", "czynsz", "arrears"],
    "utilities_arrears": ["utilities", "media", "oplaty", "arrears"],
    "setoff_potracenie": ["potracenie", "setoff", "offset"],
    "indexation_valorization": ["valorization", "waloryzacja", "indexation"],
    "occasional_lease": ["najem okazjonalny", "occasional lease"],
    "unfair_terms": ["abusive clause", "unfair terms", "consumer"],
    "consumer_protection": ["consumer", "directive", "uokik"],
    "burden_of_proof": ["burden of proof", "proof", "evidence"],
    "claim_procedure": ["wezwanie", "claim", "pre-court demand"],
    "appeal_strategy": ["appeal", "argument", "strategy"],
    "costs_and_fees": ["costs", "fees", "court fee"],
    "mediation": ["mediation", "settlement"],
    "enforcement": ["enforcement", "execution"],
    "discovery_navigation": ["overview", "discovery", "navigation"],
}

AUTHORITY_ORDER: dict[str, int] = {
    "primary": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "reference_only": 1,
}
ALLOWED_FAMILIES: tuple[str, ...] = (
    "normative_act",
    "judicial_decision",
    "consumer_admin",
    "commentary_article",
)


class SearchBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search_calls_left: int = Field(ge=0)
    docs_per_search_left: int = Field(ge=0)
    anchors_per_search_left: int = Field(ge=0)
    legal_refs_left: int = Field(ge=0)


class DocHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    title: str
    document_family: str
    authority_level: str
    usually_supports: str | None = None
    topic_codes: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0)


class AnchorHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    anchor_id: str
    document_title: str
    locator_label: str
    authority_level: str
    usually_supports: str | None = None
    topic_codes: list[str] = Field(default_factory=list)
    preview: str
    score: float = Field(ge=0.0)


class AnchorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    anchor_id: str
    document_title: str
    locator_label: str
    authority_level: str
    usually_supports: str | None = None
    topic_codes: list[str] = Field(default_factory=list)
    quote: str
    preview: str


class SearchLegalDocsResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "budget_exhausted", "error"]
    query_used: str
    budget_remaining: SearchBudget
    hits: list[DocHit] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SearchLegalAnchorsResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "budget_exhausted", "error"]
    query_used: str
    budget_remaining: SearchBudget
    hits: list[AnchorHit] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GetAnchorDetailsItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    anchor_id: str


class GetAnchorDetailsResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    items: list[AnchorDetail] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


@dataclass(slots=True)
class LegalSearchContext:
    db: Database[dict[str, Any]]
    master_collection_name: str
    anchor_collection_name: str
    search_calls_left: int
    max_docs_per_search: int
    max_anchors_per_search: int
    legal_refs_left: int
    search_trace: list[dict[str, Any]] = field(default_factory=list)

    @property
    def master_collection(self) -> Collection[dict[str, Any]]:
        return self.db[self.master_collection_name]

    @property
    def anchor_collection(self) -> Collection[dict[str, Any]]:
        return self.db[self.anchor_collection_name]


def _budget_snapshot(ctx: LegalSearchContext) -> SearchBudget:
    return SearchBudget(
        search_calls_left=max(ctx.search_calls_left, 0),
        docs_per_search_left=max(ctx.max_docs_per_search, 0),
        anchors_per_search_left=max(ctx.max_anchors_per_search, 0),
        legal_refs_left=max(ctx.legal_refs_left, 0),
    )


def _consume_search_call(ctx: LegalSearchContext) -> bool:
    if ctx.search_calls_left <= 0:
        return False
    ctx.search_calls_left -= 1
    return True


def _expand_issue_keywords(issue_codes: list[str]) -> list[str]:
    keywords: list[str] = []
    for code in issue_codes:
        keywords.extend(ISSUE_KEYWORDS.get(code, [code.replace("_", " ")]))
    return keywords


def _compose_query(*parts: str, issue_codes: list[str] | None = None) -> str:
    tokens: list[str] = []
    if issue_codes:
        tokens.extend(issue_codes)
        tokens.extend(_expand_issue_keywords(issue_codes))
    for part in parts:
        if part.strip():
            tokens.append(part.strip())
    collapsed = " ".join(tokens)
    collapsed = " ".join(collapsed.split())
    return collapsed[:500]


def _authority_passes(candidate: str | None, minimum: str) -> bool:
    if candidate is None:
        return False
    return AUTHORITY_ORDER.get(candidate, 0) >= AUTHORITY_ORDER.get(minimum, 0)


def _family_penalty(document_family: str) -> float:
    if document_family == "commentary_article":
        return -0.10
    return 0.0


def _authority_bonus(level: str) -> float:
    if level == "primary":
        return 0.30
    if level == "high":
        return 0.20
    if level == "medium":
        return 0.10
    return 0.0


def _support_bonus(usually_supports: str | None, position: str) -> float:
    if position == "tenant" and usually_supports in {"tenant", "both"}:
        return 0.05
    if position == "landlord" and usually_supports in {"landlord", "both"}:
        return 0.05
    return 0.0


def _topic_bonus(topic_codes: list[str], issue_codes: list[str]) -> float:
    return 0.10 if any(code in set(topic_codes) for code in issue_codes) else 0.0


def _register_trace(ctx: LegalSearchContext, tool_name: str, query_used: str, hit_count: int) -> None:
    ctx.search_trace.append(
        {
            "tool": tool_name,
            "query": query_used,
            "hit_count": hit_count,
        }
    )


@function_tool
def search_legal_docs(
    tool_ctx: ToolContext[LegalSearchContext],
    question: str,
    issue_codes: list[str],
    position: Literal["tenant", "landlord", "both"] = "tenant",
    max_docs: int = 5,
    authority_min: Literal["primary", "high", "medium", "low", "reference_only"] = "high",
) -> dict[str, Any]:
    """Search doc-level legal corpus metadata and return a shortlist of relevant legal documents.

    Call this tool first for a new legal issue. Use a short, focused question and the current
    issue_codes. Prefer one call per issue cluster, not many near-duplicate calls.
    """
    ctx = tool_ctx.context
    if not _consume_search_call(ctx):
        return SearchLegalDocsResult(
            status="budget_exhausted",
            query_used="",
            budget_remaining=_budget_snapshot(ctx),
            hits=[],
            warnings=["search budget exhausted"],
        ).model_dump(mode="json")

    query_used = _compose_query(question, issue_codes=issue_codes)
    capped_max_docs = max(1, min(max_docs, ctx.max_docs_per_search))
    mongo_filter: dict[str, Any] = {
        "processing.status": "completed",
        "search.document_family": {"$in": list(ALLOWED_FAMILIES)},
    }
    if issue_codes:
        mongo_filter["search.topic_codes"] = {"$in": issue_codes}

    projection = {
        "_id": 1,
        "source.title": 1,
        "search.document_family": 1,
        "search.authority_level": 1,
        "search.usually_supports": 1,
        "search.topic_codes": 1,
        "search.tags_original": 1,
        "search.tags_ru": 1,
    }

    try:
        raw_docs = list(ctx.master_collection.find(mongo_filter, projection).limit(100))
    except Exception as error:  # pragma: no cover - operational surface
        return SearchLegalDocsResult(
            status="error",
            query_used=query_used,
            budget_remaining=_budget_snapshot(ctx),
            hits=[],
            warnings=[f"mongo error: {error}"],
        ).model_dump(mode="json")

    scored: list[DocHit] = []
    q_lower = query_used.lower()
    for item in raw_docs:
        search = item.get("search", {})
        source = item.get("source", {})
        authority_level = str(search.get("authority_level") or "")
        if not _authority_passes(authority_level, authority_min):
            continue

        title = str(source.get("title") or item.get("_id") or "")
        topic_codes_value = [str(v) for v in search.get("topic_codes", [])]
        text_score = 0.40
        if title and any(token in title.lower() for token in q_lower.split()):
            text_score += 0.25
        tags = [str(v).lower() for v in search.get("tags_original", [])] + [
            str(v).lower() for v in search.get("tags_ru", [])
        ]
        if any(token in " ".join(tags) for token in q_lower.split()):
            text_score += 0.10

        score = (
            text_score
            + _authority_bonus(authority_level)
            + _topic_bonus(topic_codes_value, issue_codes)
            + _support_bonus(str(search.get("usually_supports") or ""), position)
            + _family_penalty(str(search.get("document_family") or ""))
        )
        scored.append(
            DocHit(
                doc_id=str(item.get("_id")),
                title=title,
                document_family=str(search.get("document_family") or "unknown"),
                authority_level=authority_level or "low",
                usually_supports=(
                    str(search.get("usually_supports"))
                    if search.get("usually_supports") is not None
                    else None
                ),
                topic_codes=topic_codes_value,
                score=round(max(score, 0.0), 4),
            )
        )

    scored.sort(key=lambda doc: doc.score, reverse=True)
    hits = scored[:capped_max_docs]
    _register_trace(ctx, "search_legal_docs", query_used, len(hits))
    return SearchLegalDocsResult(
        status="ok",
        query_used=query_used,
        budget_remaining=_budget_snapshot(ctx),
        hits=hits,
        warnings=[],
    ).model_dump(mode="json")


@function_tool
def search_legal_anchors(
    tool_ctx: ToolContext[LegalSearchContext],
    query: str,
    candidate_doc_ids: list[str] | None = None,
    issue_code: str | None = None,
    max_hits: int = 8,
) -> dict[str, Any]:
    """Search anchor-level passages inside a shortlisted legal corpus or, if needed, the whole anchor collection.

    Call this after search_legal_docs. Prefer passing candidate_doc_ids from the previous shortlist.
    """
    ctx = tool_ctx.context
    if not _consume_search_call(ctx):
        return SearchLegalAnchorsResult(
            status="budget_exhausted",
            query_used="",
            budget_remaining=_budget_snapshot(ctx),
            hits=[],
            warnings=["search budget exhausted"],
        ).model_dump(mode="json")

    query_used = _compose_query(query, issue_codes=[issue_code] if issue_code else None)
    capped_max_hits = max(1, min(max_hits, ctx.max_anchors_per_search))
    mongo_filter: dict[str, Any] = {}
    if candidate_doc_ids:
        mongo_filter["doc_id"] = {"$in": list(dict.fromkeys(candidate_doc_ids))}
    if issue_code:
        mongo_filter["doc_meta.topic_codes"] = issue_code

    projection = {
        "doc_id": 1,
        "anchor_id": 1,
        "preview": 1,
        "passage_text": 1,
        "locator.label": 1,
        "doc_meta.title": 1,
        "doc_meta.authority_level": 1,
        "doc_meta.usually_supports": 1,
        "doc_meta.topic_codes": 1,
        "doc_meta.document_family": 1,
    }

    try:
        raw_anchors = list(ctx.anchor_collection.find(mongo_filter, projection).limit(200))
    except Exception as error:  # pragma: no cover - operational surface
        return SearchLegalAnchorsResult(
            status="error",
            query_used=query_used,
            budget_remaining=_budget_snapshot(ctx),
            hits=[],
            warnings=[f"mongo error: {error}"],
        ).model_dump(mode="json")

    q_lower = query_used.lower()
    hits: list[AnchorHit] = []
    for item in raw_anchors:
        preview = str(item.get("preview") or "")
        passage_text = str(item.get("passage_text") or "")
        locator = item.get("locator", {})
        doc_meta = item.get("doc_meta", {})
        authority_level = str(doc_meta.get("authority_level") or "low")
        topic_codes = [str(v) for v in doc_meta.get("topic_codes", [])]

        haystack = " ".join(
            [
                preview.lower(),
                passage_text.lower(),
                str(locator.get("label") or "").lower(),
                str(doc_meta.get("title") or "").lower(),
            ]
        )
        token_hits = sum(1 for token in q_lower.split() if token and token in haystack)
        if token_hits == 0 and q_lower:
            continue

        text_score = min(0.60, 0.15 * token_hits)
        score = (
            text_score
            + _authority_bonus(authority_level)
            + _topic_bonus(topic_codes, [issue_code] if issue_code else [])
            + _family_penalty(str(doc_meta.get("document_family") or ""))
        )
        hits.append(
            AnchorHit(
                doc_id=str(item.get("doc_id")),
                anchor_id=str(item.get("anchor_id")),
                document_title=str(doc_meta.get("title") or item.get("doc_id") or ""),
                locator_label=str(locator.get("label") or ""),
                authority_level=authority_level,
                usually_supports=(
                    str(doc_meta.get("usually_supports"))
                    if doc_meta.get("usually_supports") is not None
                    else None
                ),
                topic_codes=topic_codes,
                preview=(preview or passage_text)[:240],
                score=round(max(score, 0.0), 4),
            )
        )

    hits.sort(key=lambda item: item.score, reverse=True)

    deduped: list[AnchorHit] = []
    seen: set[tuple[str, str]] = set()
    per_doc_count: dict[str, int] = {}
    for hit in hits:
        key = (hit.doc_id, hit.anchor_id)
        if key in seen:
            continue
        if per_doc_count.get(hit.doc_id, 0) >= 3:
            continue
        deduped.append(hit)
        seen.add(key)
        per_doc_count[hit.doc_id] = per_doc_count.get(hit.doc_id, 0) + 1
        if len(deduped) >= capped_max_hits:
            break

    _register_trace(ctx, "search_legal_anchors", query_used, len(deduped))
    return SearchLegalAnchorsResult(
        status="ok",
        query_used=query_used,
        budget_remaining=_budget_snapshot(ctx),
        hits=deduped,
        warnings=[],
    ).model_dump(mode="json")


@function_tool
def get_anchor_details(
    tool_ctx: ToolContext[LegalSearchContext],
    items: list[GetAnchorDetailsItem],
) -> dict[str, Any]:
    """Fetch exact anchor passages for doc_id + anchor_id pairs that are already shortlisted."""
    ctx = tool_ctx.context
    if not items:
        return GetAnchorDetailsResult(status="ok", items=[], warnings=[]).model_dump(mode="json")

    or_filter = [
        {"doc_id": item.doc_id, "anchor_id": item.anchor_id}
        for item in items[: max(ctx.legal_refs_left, 1)]
    ]
    projection = {
        "doc_id": 1,
        "anchor_id": 1,
        "preview": 1,
        "passage_text": 1,
        "locator.label": 1,
        "doc_meta.title": 1,
        "doc_meta.authority_level": 1,
        "doc_meta.usually_supports": 1,
        "doc_meta.topic_codes": 1,
    }

    try:
        raw_items = list(ctx.anchor_collection.find({"$or": or_filter}, projection))
    except Exception as error:  # pragma: no cover - operational surface
        return GetAnchorDetailsResult(
            status="error",
            items=[],
            warnings=[f"mongo error: {error}"],
        ).model_dump(mode="json")

    details: list[AnchorDetail] = []
    for item in raw_items:
        locator = item.get("locator", {})
        doc_meta = item.get("doc_meta", {})
        passage = str(item.get("passage_text") or "")
        preview = str(item.get("preview") or passage[:240])
        details.append(
            AnchorDetail(
                doc_id=str(item.get("doc_id")),
                anchor_id=str(item.get("anchor_id")),
                document_title=str(doc_meta.get("title") or item.get("doc_id") or ""),
                locator_label=str(locator.get("label") or ""),
                authority_level=str(doc_meta.get("authority_level") or "low"),
                usually_supports=(
                    str(doc_meta.get("usually_supports"))
                    if doc_meta.get("usually_supports") is not None
                    else None
                ),
                topic_codes=[str(v) for v in doc_meta.get("topic_codes", [])],
                quote=passage[:1200],
                preview=preview[:240],
            )
        )

    ctx.legal_refs_left = max(ctx.legal_refs_left - len(details), 0)
    return GetAnchorDetailsResult(
        status="ok",
        items=details,
        warnings=[],
    ).model_dump(mode="json")
