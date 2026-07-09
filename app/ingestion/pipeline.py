from datetime import datetime, timezone

from pymongo.database import Database

from app.db import LAWS_COLLECTION
from app.ingestion.chunker import chunk_section
from app.ingestion.fetcher import fetch_page
from app.ingestion.parser import parse_page


def ingest_url(db: Database, url: str) -> int:
    """Fetch, parse, and persist a single chapter/subchapter page. Returns chunks_ingested."""
    html = fetch_page(url)
    metadata, sections = parse_page(html)
    laws = db[LAWS_COLLECTION]

    document = {
        "type": "document",
        "title_num": metadata.title_num,
        "title_name": metadata.title_name,
        "chapter_num": metadata.chapter_num,
        "chapter_name": metadata.chapter_name,
        "subchapter_num": metadata.subchapter_num,
        "subchapter_name": metadata.subchapter_name,
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

    base_url = url if url.endswith("/") else f"{url}/"
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
                }
            )

    if chunk_docs:
        laws.insert_many(chunk_docs)

    return len(chunk_docs)
