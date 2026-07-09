from datetime import datetime

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    title_num: str | None = None
    chapter_num: str | None = None


class SearchResultItem(BaseModel):
    document_id: str
    section_number: str
    section_title: str
    url: str
    score: float
    snippet: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    count: int


class DocumentOut(BaseModel):
    id: str
    title_num: str
    title_name: str | None = None
    chapter_num: str
    chapter_name: str | None = None
    subchapter_num: str | None = None
    subchapter_name: str | None = None
    source_url: str
    ingested_at: datetime
    section_count: int


class ChunkOut(BaseModel):
    section_number: str
    section_title: str
    text: str
    url: str
    chunk_index: int


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
