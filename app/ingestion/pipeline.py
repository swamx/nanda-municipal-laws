from datetime import datetime, timezone

from pymongo.database import Database

from app.db import LAWS_COLLECTION
from app.ingestion.chunker import chunk_section
from app.ingestion.enrich import enrich_chunk
from app.ingestion.loader import select_loader
from app.ingestion.parser import SourceMetadata


def _citation_base_url(url: str) -> str:
    if url.lower().endswith(".pdf"):
        return url
    return url if url.endswith("/") else f"{url}/"


def ingest_url(db: Database, url: str) -> int:
    """Fetch, parse, and persist a single source page/document. Returns chunks_ingested."""
    metadata, sections = select_loader(url).load(url)
    return _persist(db, url, metadata, sections)


def _persist(db: Database, url: str, metadata: SourceMetadata, sections) -> int:
    laws = db[LAWS_COLLECTION]

    document = {
        "type": "document",
        "document_type": metadata.document_type,
        "agency": metadata.agency,
        "topic": metadata.topic,
        "title_num": metadata.title_num,
        "title_name": metadata.title_name,
        "chapter_num": metadata.chapter_num,
        "chapter_name": metadata.chapter_name,
        "subchapter_num": metadata.subchapter_num,
        "subchapter_name": metadata.subchapter_name,
        "article_num": metadata.article_num,
        "article_name": metadata.article_name,
        "source_url": url,
        "ingested_at": datetime.now(timezone.utc),
        "section_count": len(sections),
    }
    result = laws.find_one_and_update(
        {"source_url": url, "type": "document"},
        {"$set": document},
        upsert=True,
        return_document=True,
    )
    document_id = result["_id"]

    laws.delete_many({"document_id": document_id, "type": "chunk"})

    base_url = _citation_base_url(url)
    now = datetime.now(timezone.utc)
    chunk_docs = []
    for section in sections:
        for persistable in chunk_section(section):
            chunk_docs.append(
                {
                    "type": "chunk",
                    "document_id": document_id,
                    "section_number": persistable.section_number,
                    "section_title": persistable.section_title,
                    "text": persistable.text,
                    "chunk_index": persistable.chunk_index,
                    "url": f"{base_url}#{persistable.anchor_id}",
                    "title_num": metadata.title_num,
                    "chapter_num": metadata.chapter_num,
                    "subchapter_num": metadata.subchapter_num,
                    "article_num": metadata.article_num,
                    "document_type": metadata.document_type,
                    "agency": metadata.agency,
                    "topic": metadata.topic,
                    "ingested_at": now,
                    **enrich_chunk(persistable.section_number, persistable.section_title, persistable.text),
                }
            )

    if chunk_docs:
        laws.insert_many(chunk_docs)

    return len(chunk_docs)
