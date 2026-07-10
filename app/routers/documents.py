from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.db import LAWS_COLLECTION, get_db
from app.models import ChunkOut, DocumentOut

router = APIRouter(tags=["Lookup"])


def _object_id(doc_id: str) -> ObjectId:
    try:
        return ObjectId(doc_id)
    except InvalidId:
        raise HTTPException(status_code=404, detail="document not found")


@router.get(
    "/documents/{doc_id}",
    response_model=DocumentOut,
    summary="Get metadata for one ingested source document",
    description=(
        "Metadata for one ingested source document (an Admin Code chapter/subchapter page, or a "
        "Health Code article), by the `document_id` a `/search` result returned.\n\n"
        "**When to call this**: rarely needed directly by an agent - `document_id` exists mainly to "
        "chain into `GET /documents/{id}/chunks` for every section in that document. For a single "
        "section's full text, prefer `GET /sections/{section_number}` instead. Returns `404` if the "
        "id doesn't exist."
    ),
)
def get_document(doc_id: str, db: Database = Depends(get_db)) -> DocumentOut:
    document = db[LAWS_COLLECTION].find_one({"_id": _object_id(doc_id), "type": "document"})
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")

    return DocumentOut(
        id=str(document["_id"]),
        document_type=document["document_type"],
        agency=document["agency"],
        topic=document["topic"],
        title_num=document.get("title_num"),
        title_name=document.get("title_name"),
        chapter_num=document.get("chapter_num"),
        chapter_name=document.get("chapter_name"),
        subchapter_num=document.get("subchapter_num"),
        subchapter_name=document.get("subchapter_name"),
        article_num=document.get("article_num"),
        article_name=document.get("article_name"),
        source_url=document["source_url"],
        ingested_at=document["ingested_at"],
        section_count=document["section_count"],
    )


@router.get(
    "/documents/{doc_id}/chunks",
    response_model=list[ChunkOut],
    summary="Get every section belonging to a document",
    description="All sections (chunks) belonging to a document, in order, each with full metadata. Returns `404` if the parent document doesn't exist.",
)
def get_document_chunks(doc_id: str, db: Database = Depends(get_db)) -> list[ChunkOut]:
    document_id = _object_id(doc_id)
    if db[LAWS_COLLECTION].find_one({"_id": document_id, "type": "document"}) is None:
        raise HTTPException(status_code=404, detail="document not found")

    chunks = db[LAWS_COLLECTION].find({"document_id": document_id, "type": "chunk"})
    ordered = sorted(chunks, key=lambda c: c["chunk_index"])
    return [
        ChunkOut(
            section_number=chunk["section_number"],
            section_title=chunk["section_title"],
            text=chunk["text"],
            url=chunk["url"],
            chunk_index=chunk["chunk_index"],
            document_type=chunk["document_type"],
            agency=chunk["agency"],
            topic=chunk["topic"],
            keywords=chunk["keywords"],
            cross_references=chunk["cross_references"],
            mentions_penalty=chunk["mentions_penalty"],
            mentions_permit=chunk["mentions_permit"],
        )
        for chunk in ordered
    ]
