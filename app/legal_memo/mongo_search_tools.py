from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from agents import function_tool
from agents.tool_context import ToolContext
from pydantic import Field

from app.legal_memo.models import SearchTrace, SearchTraceEntry, StrictModel


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


class CollectionLike(Protocol):
    def find(
        self,
        query: dict[str, Any] | None = None,
        projection: dict[str, int] | None = None,
    ) -> Any: ...

    def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> Any: ...


class DatabaseLike(Protocol):
    def __getitem__(self, name: str) -> CollectionLike: ...


class SearchBudget(StrictModel):
    search_calls_left: int = Field(ge=0)
    docs_per_search_left: int = Field(ge=0)
    anchors_per_search_left: int = Field(ge=0)
    legal_refs_left: int = Field(ge=0)


class DocHit(StrictModel):
    doc_id: str
    title: str
    document_family: str
    authority_level: str
    usually_supports: str | None = None
    topic_codes: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0)


class AnchorHit(StrictModel):
    doc_id: str
    anchor_id: str
    document_title: str
    locator_label: str
    authority_level: str
    usually_supports: str | None = None
    topic_codes: list[str] = Field(default_factory=list)
    preview: str
    score: float = Field(ge=0.0)


class AnchorDetail(StrictModel):
    doc_id: str
    anchor_id: str
    document_title: str
    locator_label: str
    authority_level: str
    usually_supports: str | None = None
    topic_codes: list[str] = Field(default_factory=list)
    quote: str
    preview: str


class SearchLegalDocsResult(StrictModel):
    status: Literal["ok", "budget_exhausted", "error"]
    query_used: str
    budget_remaining: SearchBudget
    hits: list[DocHit] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SearchLegalAnchorsResult(StrictModel):
    status: Literal["ok", "budget_exhausted", "error"]
    query_used: str
    budget_remaining: SearchBudget
    hits: list[AnchorHit] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GetAnchorDetailsItem(StrictModel):
    doc_id: str
    anchor_id: str


class GetAnchorDetailsResult(StrictModel):
    status: Literal["ok", "budget_exhausted", "error"]
    budget_remaining: SearchBudget
    items: list[AnchorDetail] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


@dataclass(slots=True)
class LegalSearchContext:
    db: DatabaseLike
    master_collection_name: str
    anchor_collection_name: str
    search_calls_left: int
    max_docs_per_search: int
    max_anchors_per_search: int
    legal_refs_left: int
    search_trace: list[dict[str, Any]] = field(default_factory=list)

    @property
    def master_collection(self) -> CollectionLike:
        return self.db[self.master_collection_name]

    @property
    def anchor_collection(self) -> CollectionLike:
        return self.db[self.anchor_collection_name]

    def to_search_trace(self) -> SearchTrace:
        entries = [
            SearchTraceEntry(
                tool_name=str(item.get("tool_name") or ""),
                query=str(item.get("query") or ""),
                hit_count=int(item.get("hit_count") or 0),
            )
            for item in self.search_trace
        ]
        return SearchTrace(
            tool_calls_used=len(entries),
            queries=[entry.query for entry in entries],
            entries=entries,
        )


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


def _consume_legal_refs(ctx: LegalSearchContext, requested: int) -> int:
    if ctx.legal_refs_left <= 0:
        return 0
    allowed = min(requested, ctx.legal_refs_left)
    ctx.legal_refs_left -= allowed
    return allowed


def _expand_issue_keywords(issue_codes: list[str]) -> list[str]:
    tokens: list[str] = []
    for issue_code in issue_codes:
        tokens.extend(ISSUE_KEYWORDS.get(issue_code, [issue_code.replace("_", " ")]))
    return tokens


def _compose_query(*parts: str, issue_codes: list[str] | None = None) -> str:
    tokens: list[str] = []
    if issue_codes:
        tokens.extend(issue_codes)
        tokens.extend(_expand_issue_keywords(issue_codes))
    tokens.extend(part.strip() for part in parts if part.strip())
    return " ".join(" ".join(tokens).split())[:500]


def _get_path(row: dict[str, Any], path: str) -> Any:
    current: Any = row
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _collection_rows(
    collection: CollectionLike,
    *,
    projection: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    rows = collection.find({}, projection=projection)
    if isinstance(rows, list):
        return rows
    return list(rows)


def _register_trace(
    ctx: LegalSearchContext,
    *,
    tool_name: str,
    query: str,
    hit_count: int,
) -> None:
    ctx.search_trace.append(
        {
            "tool_name": tool_name,
            "query": query,
            "hit_count": hit_count,
        }
    )


def _authority_passes(candidate: str | None, minimum: str) -> bool:
    if candidate is None:
        return False
    return AUTHORITY_ORDER.get(candidate, 0) >= AUTHORITY_ORDER.get(minimum, 0)


def _text_match_score(query_tokens: list[str], values: list[str]) -> float:
    haystack = " ".join(value.lower() for value in values if value).strip()
    if not haystack:
        return 0.0
    matched = sum(1 for token in query_tokens if token in haystack)
    if not matched:
        return 0.0
    return min(0.6, matched * 0.08)


def _family_penalty(document_family: str) -> float:
    return -0.10 if document_family == "commentary_article" else 0.0


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


def _search_legal_docs_logic(
    *,
    ctx: LegalSearchContext,
    question: str,
    issue_codes: list[str],
    position: Literal["tenant", "landlord", "both"] = "tenant",
    max_docs: int = 5,
    authority_min: Literal[
        "primary",
        "high",
        "medium",
        "low",
        "reference_only",
    ] = "high",
) -> SearchLegalDocsResult:
    if not _consume_search_call(ctx):
        return SearchLegalDocsResult(
            status="budget_exhausted",
            query_used="",
            budget_remaining=_budget_snapshot(ctx),
            hits=[],
            warnings=["search budget exhausted"],
        )

    query_used = _compose_query(question, issue_codes=issue_codes)
    query_tokens = [token.lower() for token in query_used.split()]
    capped_max_docs = max(1, min(max_docs, ctx.max_docs_per_search))

    try:
        raw_docs = _collection_rows(
            ctx.master_collection,
            projection={
                "_id": 1,
                "source.title": 1,
                "processing.status": 1,
                "search.document_family": 1,
                "search.authority_level": 1,
                "search.usually_supports": 1,
                "search.topic_codes": 1,
                "search.tags_original": 1,
                "search.tags_ru": 1,
            },
        )
    except Exception as error:
        return SearchLegalDocsResult(
            status="error",
            query_used=query_used,
            budget_remaining=_budget_snapshot(ctx),
            hits=[],
            warnings=[f"mongo error: {error}"],
        )

    scored: list[DocHit] = []
    for row in raw_docs:
        if _get_path(row, "processing.status") != "completed":
            continue
        document_family = str(_get_path(row, "search.document_family") or "")
        if document_family not in ALLOWED_FAMILIES:
            continue
        authority_level = str(_get_path(row, "search.authority_level") or "")
        if not _authority_passes(authority_level, authority_min):
            continue

        title = str(_get_path(row, "source.title") or row.get("_id") or "")
        topic_codes = [str(item) for item in (_get_path(row, "search.topic_codes") or [])]
        tags_original = [str(item) for item in (_get_path(row, "search.tags_original") or [])]
        tags_ru = [str(item) for item in (_get_path(row, "search.tags_ru") or [])]
        usually_supports = _get_path(row, "search.usually_supports")

        score = (
            0.30
            + _text_match_score(query_tokens, [title, *topic_codes, *tags_original, *tags_ru])
            + _authority_bonus(authority_level)
            + _topic_bonus(topic_codes, issue_codes)
            + _support_bonus(str(usually_supports or ""), position)
            + _family_penalty(document_family)
        )
        scored.append(
            DocHit(
                doc_id=str(row.get("_id")),
                title=title,
                document_family=document_family,
                authority_level=authority_level,
                usually_supports=str(usually_supports) if usually_supports else None,
                topic_codes=topic_codes,
                score=round(max(score, 0.0), 4),
            )
        )

    hits = sorted(scored, key=lambda item: item.score, reverse=True)[:capped_max_docs]
    _register_trace(ctx, tool_name="search_legal_docs", query=query_used, hit_count=len(hits))
    return SearchLegalDocsResult(
        status="ok",
        query_used=query_used,
        budget_remaining=_budget_snapshot(ctx),
        hits=hits,
        warnings=[],
    )


def _search_legal_anchors_logic(
    *,
    ctx: LegalSearchContext,
    query: str,
    candidate_doc_ids: list[str],
    issue_code: str,
    max_hits: int = 8,
) -> SearchLegalAnchorsResult:
    if not _consume_search_call(ctx):
        return SearchLegalAnchorsResult(
            status="budget_exhausted",
            query_used="",
            budget_remaining=_budget_snapshot(ctx),
            hits=[],
            warnings=["search budget exhausted"],
        )

    query_used = _compose_query(query, issue_codes=[issue_code])
    query_tokens = [token.lower() for token in query_used.split()]
    capped_max_hits = max(1, min(max_hits, ctx.max_anchors_per_search))
    candidate_doc_id_set = {item for item in candidate_doc_ids if item}

    try:
        raw_rows = _collection_rows(
            ctx.anchor_collection,
            projection={
                "doc_id": 1,
                "anchor_id": 1,
                "passage_text": 1,
                "preview": 1,
                "locator.label": 1,
                "doc_meta.title": 1,
                "doc_meta.topic_codes": 1,
                "doc_meta.authority_level": 1,
                "doc_meta.usually_supports": 1,
                "doc_meta.document_family": 1,
            },
        )
    except Exception as error:
        return SearchLegalAnchorsResult(
            status="error",
            query_used=query_used,
            budget_remaining=_budget_snapshot(ctx),
            hits=[],
            warnings=[f"mongo error: {error}"],
        )

    hits: list[AnchorHit] = []
    for row in raw_rows:
        doc_id = str(row.get("doc_id") or "")
        if candidate_doc_id_set and doc_id not in candidate_doc_id_set:
            continue

        document_family = str(_get_path(row, "doc_meta.document_family") or "")
        if document_family and document_family not in ALLOWED_FAMILIES:
            continue

        topic_codes = [str(item) for item in (_get_path(row, "doc_meta.topic_codes") or [])]
        authority_level = str(_get_path(row, "doc_meta.authority_level") or "")
        preview = str(row.get("preview") or "")
        passage_text = str(row.get("passage_text") or "")
        title = str(_get_path(row, "doc_meta.title") or doc_id)
        locator_label = str(_get_path(row, "locator.label") or row.get("anchor_id") or "")
        usually_supports = _get_path(row, "doc_meta.usually_supports")

        score = (
            0.25
            + _text_match_score(query_tokens, [passage_text, preview, title, locator_label, *topic_codes])
            + _authority_bonus(authority_level)
            + _topic_bonus(topic_codes, [issue_code])
            + _family_penalty(document_family)
        )
        if score <= 0.25:
            continue
        hits.append(
            AnchorHit(
                doc_id=doc_id,
                anchor_id=str(row.get("anchor_id") or ""),
                document_title=title,
                locator_label=locator_label,
                authority_level=authority_level,
                usually_supports=str(usually_supports) if usually_supports else None,
                topic_codes=topic_codes,
                preview=preview or passage_text[:120],
                score=round(score, 4),
            )
        )

    top_hits = sorted(hits, key=lambda item: item.score, reverse=True)[:capped_max_hits]
    warnings: list[str] = []
    if not candidate_doc_id_set:
        warnings.append("anchor search ran without candidate_doc_ids shortlist")
    _register_trace(
        ctx,
        tool_name="search_legal_anchors",
        query=query_used,
        hit_count=len(top_hits),
    )
    return SearchLegalAnchorsResult(
        status="ok",
        query_used=query_used,
        budget_remaining=_budget_snapshot(ctx),
        hits=top_hits,
        warnings=warnings,
    )


def _get_anchor_details_logic(
    *,
    ctx: LegalSearchContext,
    items: list[GetAnchorDetailsItem],
) -> GetAnchorDetailsResult:
    requested = len(items)
    allowed = _consume_legal_refs(ctx, requested)
    if allowed <= 0:
        return GetAnchorDetailsResult(
            status="budget_exhausted",
            budget_remaining=_budget_snapshot(ctx),
            items=[],
            warnings=["legal reference budget exhausted"],
        )

    warnings: list[str] = []
    if allowed < requested:
        warnings.append("requested anchor details exceeded legal_refs_left budget")

    selected_items = items[:allowed]
    try:
        raw_rows = _collection_rows(
            ctx.anchor_collection,
            projection={
                "doc_id": 1,
                "anchor_id": 1,
                "passage_text": 1,
                "preview": 1,
                "locator.label": 1,
                "doc_meta.title": 1,
                "doc_meta.topic_codes": 1,
                "doc_meta.authority_level": 1,
                "doc_meta.usually_supports": 1,
            },
        )
    except Exception as error:
        return GetAnchorDetailsResult(
            status="error",
            budget_remaining=_budget_snapshot(ctx),
            items=[],
            warnings=[f"mongo error: {error}"],
        )

    lookup = {
        (str(row.get("doc_id") or ""), str(row.get("anchor_id") or "")): row
        for row in raw_rows
    }
    details: list[AnchorDetail] = []
    for item in selected_items:
        row = lookup.get((item.doc_id, item.anchor_id))
        if row is None:
            warnings.append(f"anchor not found: {item.doc_id}#{item.anchor_id}")
            continue
        details.append(
            AnchorDetail(
                doc_id=item.doc_id,
                anchor_id=item.anchor_id,
                document_title=str(_get_path(row, "doc_meta.title") or item.doc_id),
                locator_label=str(
                    _get_path(row, "locator.label") or row.get("anchor_id") or ""
                ),
                authority_level=str(_get_path(row, "doc_meta.authority_level") or ""),
                usually_supports=(
                    str(_get_path(row, "doc_meta.usually_supports"))
                    if _get_path(row, "doc_meta.usually_supports") is not None
                    else None
                ),
                topic_codes=[
                    str(value) for value in (_get_path(row, "doc_meta.topic_codes") or [])
                ],
                quote=str(row.get("passage_text") or ""),
                preview=str(row.get("preview") or row.get("passage_text") or "")[:240],
            )
        )
    _register_trace(
        ctx,
        tool_name="get_anchor_details",
        query="|".join(f"{item.doc_id}#{item.anchor_id}" for item in selected_items),
        hit_count=len(details),
    )
    return GetAnchorDetailsResult(
        status="ok",
        budget_remaining=_budget_snapshot(ctx),
        items=details,
        warnings=warnings,
    )


@function_tool
def search_legal_docs(
    tool_ctx: ToolContext[LegalSearchContext],
    question: str,
    issue_codes: list[str],
    position: Literal["tenant", "landlord", "both"] = "tenant",
    max_docs: int = 5,
    authority_min: Literal[
        "primary",
        "high",
        "medium",
        "low",
        "reference_only",
    ] = "high",
) -> dict[str, Any]:
    result = _search_legal_docs_logic(
        ctx=tool_ctx.context,
        question=question,
        issue_codes=issue_codes,
        position=position,
        max_docs=max_docs,
        authority_min=authority_min,
    )
    return result.model_dump(mode="json")


@function_tool
def search_legal_anchors(
    tool_ctx: ToolContext[LegalSearchContext],
    query: str,
    candidate_doc_ids: list[str],
    issue_code: str,
    max_hits: int = 8,
) -> dict[str, Any]:
    result = _search_legal_anchors_logic(
        ctx=tool_ctx.context,
        query=query,
        candidate_doc_ids=candidate_doc_ids,
        issue_code=issue_code,
        max_hits=max_hits,
    )
    return result.model_dump(mode="json")


@function_tool
def get_anchor_details(
    tool_ctx: ToolContext[LegalSearchContext],
    items: list[GetAnchorDetailsItem],
) -> dict[str, Any]:
    result = _get_anchor_details_logic(
        ctx=tool_ctx.context,
        items=items,
    )
    return result.model_dump(mode="json")


def build_search_tools() -> list[Any]:
    return [search_legal_docs, search_legal_anchors, get_anchor_details]
