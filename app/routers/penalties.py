from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.db import get_db
from app.models import TopicFilterRequest, TopicFilterResponse
from app.retrieval import search_chunks

router = APIRouter(tags=["Penalties"])


@router.post(
    "/penalties",
    response_model=TopicFilterResponse,
    summary="Find sections that mention a penalty or fine",
    description=(
        "Filters to sections flagged `mentions_penalty=true` - a word-boundary keyword heuristic "
        "(penalty/fine/violation/unlawful/misdemeanor/civil penalty/...), not a legal certainty. "
        "Optional `query` ranks within the filtered set; optional `topic` scopes to one chapter/"
        "article (e.g. `NOISE CONTROL`).\n\n"
        "**When to call this**: the question is specifically about penalties/fines, not a general "
        "lookup (`/search`) or a yes/no legality check (`/is_action_allowed`). Results are ranked "
        "snippets and can be truncated - follow up with `GET /sections/{section_number}` before "
        "quoting an exact dollar amount."
    ),
)
def find_penalties(payload: TopicFilterRequest, db: Database = Depends(get_db)) -> TopicFilterResponse:
    results, reasoning = search_chunks(
        db,
        query=payload.query,
        limit=payload.limit,
        topic=payload.topic,
        mentions_penalty=True,
        search_mode=payload.search_mode,
    )
    return TopicFilterResponse(
        results=results,
        count=len(results),
        reasoning=f"filtered to chunks flagged mentions_penalty=true; {reasoning}",
    )
