from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.db import get_db
from app.models import SearchRequest, SearchResponse
from app.retrieval import search_chunks

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, db: Database = Depends(get_db)) -> SearchResponse:
    results, reasoning = search_chunks(
        db,
        query=payload.query,
        limit=payload.limit,
        title_num=payload.title_num,
        chapter_num=payload.chapter_num,
        document_type=payload.document_type,
        agency=payload.agency,
        topic=payload.topic,
    )
    return SearchResponse(query=payload.query, results=results, count=len(results), reasoning=reasoning)
