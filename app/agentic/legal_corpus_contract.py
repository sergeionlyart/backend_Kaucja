"""Type contracts for legal corpus tool adapters used by Scenario 2."""

from __future__ import annotations

from typing import Any, Literal, Protocol, TypedDict

try:
    from typing import NotRequired
except ImportError:  # pragma: no cover

    class _FallbackNotRequired:
        def __class_getitem__(self, item: Any) -> Any:
            return item

    NotRequired = _FallbackNotRequired()


class SearchRequest(TypedDict):
    query: str
    query_language: NotRequired[str]
    query_expansions: NotRequired[list[str]]
    scope: Literal["acts", "case_law", "mixed"]
    return_level: Literal["document", "fragment", "mixed"]
    as_of_date: NotRequired[str]
    include_history: NotRequired[bool]
    expand_citations: NotRequired[bool]
    top_k: NotRequired[int]
    locator: NotRequired[dict[str, Any]]
    filters: NotRequired[dict[str, Any]]


class FetchFragmentsRequest(TypedDict):
    refs: list[dict[str, Any]]
    include_neighbors: NotRequired[bool]
    neighbor_window: NotRequired[int]
    max_chars_per_fragment: NotRequired[int]


class ExpandRelatedRequest(TypedDict):
    refs: list[dict[str, Any]]
    relation_types: list[
        Literal["cites", "cited_by", "same_case", "supersedes", "related_provision"]
    ]
    top_k: NotRequired[int]


class ProvenanceRequest(TypedDict):
    ref: dict[str, Any]
    include_artifacts: NotRequired[bool]
    debug: NotRequired[bool]


class LegalCorpusTool(Protocol):
    def search(self, request: SearchRequest) -> dict[str, Any]:
        ...

    def fetch_fragments(self, request: FetchFragmentsRequest) -> dict[str, Any]:
        ...

    def expand_related(self, request: ExpandRelatedRequest) -> dict[str, Any]:
        ...

    def get_provenance(self, request: ProvenanceRequest) -> dict[str, Any]:
        ...
