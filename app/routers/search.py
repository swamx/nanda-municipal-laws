from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.db import get_db
from app.models import SearchRequest, SearchResponse
from app.retrieval import search_chunks
from app.signing import sign_response

router = APIRouter(tags=["Search"])


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search NYC Administrative Code and Health Code",
    description=(
        "Deterministic keyword retrieval over the entire ingested corpus (32 titles / 4,781 "
        "sections of the Admin Code, plus all 36 articles / 501 sections of the Health Code). "
        "No AI-generated text - returns ranked, official citations (`section_number`, `url`, "
        "verbatim `snippet`) that an autonomous agent can use to construct a grounded response.\n\n"
        "**When to call this**: general lookups that aren't a yes/no legality question (use "
        "`/is_action_allowed` for those) and aren't a penalty/permit-specific question (use "
        "`/penalties`/`/permits` for those). Pull literal key terms from the user's question, not "
        "the full sentence - this ranks by term frequency, not phrase meaning.\n\n"
        "Same query always returns the same citations in the same order - no randomness, no model "
        "sampling, nothing to re-run for a different answer."
    ),
)
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
        search_mode=payload.search_mode,
    )
    response = SearchResponse(query=payload.query, results=results, count=len(results), reasoning=reasoning)
    provenance = sign_response(response)
    return response.model_copy(update={"provenance": provenance})
