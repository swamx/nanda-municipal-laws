from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.db import LAWS_COLLECTION, get_db
from app.models import SearchRequest, SearchResponse, SearchResultItem
from app.search_scoring import score_chunk

router = APIRouter(tags=["search"])

SNIPPET_LENGTH = 200


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, db: Database = Depends(get_db)) -> SearchResponse:
    mongo_filter: dict = {"type": "chunk"}
    if payload.title_num:
        mongo_filter["title_num"] = payload.title_num
    if payload.chapter_num:
        mongo_filter["chapter_num"] = payload.chapter_num

    scored = []
    for doc in db[LAWS_COLLECTION].find(mongo_filter):
        score = score_chunk(doc["section_title"], doc["text"], payload.query)
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    results = [
        SearchResultItem(
            document_id=str(doc["document_id"]),
            section_number=doc["section_number"],
            section_title=doc["section_title"],
            url=doc["url"],
            score=score,
            snippet=doc["text"][:SNIPPET_LENGTH],
        )
        for score, doc in scored[: payload.limit]
    ]

    return SearchResponse(query=payload.query, results=results, count=len(results))
