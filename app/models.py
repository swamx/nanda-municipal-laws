from datetime import datetime

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    title_num: str | None = None
    chapter_num: str | None = None
    document_type: str | None = None
    agency: str | None = None
    topic: str | None = None


class SearchResultItem(BaseModel):
    document_id: str
    section_number: str
    section_title: str
    url: str
    score: float
    snippet: str
    document_type: str
    agency: str
    topic: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    count: int
    reasoning: str


class DocumentOut(BaseModel):
    id: str
    document_type: str
    agency: str
    topic: str
    title_num: str | None = None
    title_name: str | None = None
    chapter_num: str | None = None
    chapter_name: str | None = None
    subchapter_num: str | None = None
    subchapter_name: str | None = None
    article_num: str | None = None
    article_name: str | None = None
    source_url: str
    ingested_at: datetime
    section_count: int


class ChunkOut(BaseModel):
    section_number: str
    section_title: str
    text: str
    url: str
    chunk_index: int
    document_type: str
    agency: str
    topic: str
    keywords: list[str]
    cross_references: list[str]
    mentions_penalty: bool
    mentions_permit: bool


class HealthResponse(BaseModel):
    status: str


class IngestRequest(BaseModel):
    urls: list[str] = Field(min_length=1, max_length=20)


class IngestResultItem(BaseModel):
    url: str
    status: str
    chunks_ingested: int = 0
    error: str | None = None


class IngestResponse(BaseModel):
    results: list[IngestResultItem]


class SectionOut(BaseModel):
    section_number: str
    section_title: str
    text: str
    url: str
    document_type: str
    agency: str
    topic: str
    jurisdiction: str
    keywords: list[str]
    cross_references: list[str]
    mentions_penalty: bool
    mentions_permit: bool
    effective_date: str | None
    repealed: bool
    structural_summary: list[str]
    chunk_count: int
    reasoning: str


class RelatedSection(BaseModel):
    section_number: str
    section_title: str | None = None
    url: str | None = None
    document_type: str | None = None
    resolved: bool


class RelatedLawsResponse(BaseModel):
    section_number: str
    related: list[RelatedSection]
    reasoning: str


class TopicFilterRequest(BaseModel):
    query: str | None = None
    topic: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class TopicFilterResponse(BaseModel):
    results: list[SearchResultItem]
    count: int
    reasoning: str
