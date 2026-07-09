from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.db import get_db
from app.models import TopicFilterRequest, TopicFilterResponse
from app.retrieval import search_chunks

router = APIRouter(tags=["penalties"])


@router.post("/penalties", response_model=TopicFilterResponse)
def find_penalties(payload: TopicFilterRequest, db: Database = Depends(get_db)) -> TopicFilterResponse:
    results, reasoning = search_chunks(
        db,
        query=payload.query,
        limit=payload.limit,
        topic=payload.topic,
        mentions_penalty=True,
    )
    return TopicFilterResponse(
        results=results,
        count=len(results),
        reasoning=f"filtered to chunks flagged mentions_penalty=true; {reasoning}",
    )
