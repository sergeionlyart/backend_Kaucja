from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class Node(BaseModel):
    id: str = Field(alias="_id")
    doc_uid: str
    source_hash: str
    node_id: str
    parent_node_id: str
    depth: int
    order_index: int
    title: str
    start_index: int
    end_index: int
    summary: Optional[str] = None
    anchors: Dict[str, str] = Field(default_factory=dict)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(populate_by_name=True)


class PageExtractionQuality(BaseModel):
    alpha_ratio: float
    empty: bool


class PageExtraction(BaseModel):
    method: Literal["PDF_TEXT", "OCR3", "HTML", "SAOS_JSON"]
    quality: PageExtractionQuality
    ocr_meta: Optional[Dict[str, Any]] = None


class Page(BaseModel):
    id: str = Field(alias="_id")
    doc_uid: str
    source_hash: str
    page_index: int
    text: str
    markdown: Optional[str] = None
    token_count_est: int
    char_count: int
    extraction: PageExtraction
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(populate_by_name=True)


class ContentStats(BaseModel):
    total_chars: int
    total_tokens_est: int
    parse_method: Literal["PDF_TEXT", "OCR3", "HTML", "SAOS_JSON"]
    ocr_used: bool


class CitationTarget(BaseModel):
    jurisdiction: Optional[str] = None
    external_id: Optional[str] = None
    anchor: Optional[str] = None


class CitationEvidence(BaseModel):
    page_index: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None


class Citation(BaseModel):
    id: str = Field(alias="_id")
    doc_uid: str
    source_hash: str
    from_node_id: str
    raw_citation_text: str
    target: Optional[CitationTarget] = None
    confidence: Optional[float] = None
    evidence: Optional[CitationEvidence] = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(populate_by_name=True)


class Document(BaseModel):
    id: str = Field(alias="_id")
    doc_uid: str
    doc_type: str
    jurisdiction: str
    language: str
    source_system: str
    title: Optional[str] = None
    date_published: Optional[str] = None
    date_decision: Optional[str] = None
    version_label: Optional[str] = None
    external_ids: Dict[str, str] = Field(default_factory=dict)
    source_urls: List[str]
    license_tag: str
    access_status: Literal["OK", "RESTRICTED", "ERROR"]
    current_source_hash: str
    mime: str
    page_count: int
    content_stats: ContentStats
    pageindex_tree: List[Dict[str, Any]] = Field(default_factory=list)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(populate_by_name=True)


class HttpMeta(BaseModel):
    status_code: int
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    content_length: Optional[int] = None


class DocumentSource(BaseModel):
    id: str = Field(alias="_id")
    doc_uid: str
    source_hash: str
    source_id: str
    url: str
    final_url: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    http: HttpMeta
    raw_object_path: str
    raw_mime: str
    license_tag: str
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(populate_by_name=True)


class RunError(BaseModel):
    source_id: str
    stage: str
    error_type: str
    message: str


class RunStats(BaseModel):
    sources_total: int = 0
    docs_ok: int = 0
    docs_restricted: int = 0
    docs_error: int = 0
    pages_written: int = 0
    nodes_written: int = 0
    citations_written: int = 0


class IngestRun(BaseModel):
    id: str = Field(alias="_id")
    run_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    config_hash: str
    pipeline_version: str = "0.1.0"
    stats: RunStats = Field(default_factory=RunStats)
    errors: List[RunError] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)
