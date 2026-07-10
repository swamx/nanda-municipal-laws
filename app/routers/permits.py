from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.db import get_db
from app.models import TopicFilterRequest, TopicFilterResponse
from app.retrieval import search_chunks

router = APIRouter(tags=["Permits"])


@router.post(
    "/permits",
    response_model=TopicFilterResponse,
    summary="Find sections that mention a permit or license requirement",
    description=(
        "Filters to sections flagged `mentions_permit=true` - a word-boundary keyword heuristic "
        "(permit/license/authorized/authorization/...), not a legal certainty; intentionally broad, "
        "so it also flags sections that merely reference an exception, not only ones that establish "
        "an affirmative permit-application process. Optional `query` ranks within the filtered set; "
        "optional `topic` scopes to one chapter/article.\n\n"
        "**When to call this**: the question is specifically about permit/license requirements, not "
        "a general lookup (`/search`) or a yes/no legality check (`/is_action_allowed`). Results are "
        "ranked snippets and can be truncated - follow up with `GET /sections/{section_number}` "
        "before quoting exact wording."
    ),
)
def find_permits(payload: TopicFilterRequest, db: Database = Depends(get_db)) -> TopicFilterResponse:
    results, reasoning = search_chunks(
        db,
        query=payload.query,
        limit=payload.limit,
        topic=payload.topic,
        mentions_permit=True,
        search_mode=payload.search_mode,
    )
    return TopicFilterResponse(
        results=results,
        count=len(results),
        reasoning=f"filtered to chunks flagged mentions_permit=true; {reasoning}",
    )
