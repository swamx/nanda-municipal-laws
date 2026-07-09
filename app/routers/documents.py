from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.db import LAWS_COLLECTION, get_db
from app.models import ChunkOut, DocumentOut

router = APIRouter(tags=["documents"])


def _object_id(doc_id: str) -> ObjectId:
    try:
        return ObjectId(doc_id)
    except InvalidId:
        raise HTTPException(status_code=404, detail="document not found")


@router.get("/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str, db: Database = Depends(get_db)) -> DocumentOut:
    document = db[LAWS_COLLECTION].find_one({"_id": _object_id(doc_id), "type": "document"})
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")

    return DocumentOut(
        id=str(document["_id"]),
        title_num=document["title_num"],
        title_name=document.get("title_name"),
        chapter_num=document["chapter_num"],
        chapter_name=document.get("chapter_name"),
        subchapter_num=document.get("subchapter_num"),
        subchapter_name=document.get("subchapter_name"),
        source_url=document["source_url"],
        ingested_at=document["ingested_at"],
        section_count=document["section_count"],
    )


@router.get("/documents/{doc_id}/chunks", response_model=list[ChunkOut])
def get_document_chunks(doc_id: str, db: Database = Depends(get_db)) -> list[ChunkOut]:
    document_id = _object_id(doc_id)
    if db[LAWS_COLLECTION].find_one({"_id": document_id, "type": "document"}) is None:
        raise HTTPException(status_code=404, detail="document not found")

    chunks = db[LAWS_COLLECTION].find({"document_id": document_id, "type": "chunk"}).sort("chunk_index", 1)
    return [
        ChunkOut(
            section_number=chunk["section_number"],
            section_title=chunk["section_title"],
            text=chunk["text"],
            url=chunk["url"],
            chunk_index=chunk["chunk_index"],
        )
        for chunk in chunks
    ]
