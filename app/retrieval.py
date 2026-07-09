from pymongo.database import Database

from app.db import LAWS_COLLECTION
from app.models import SearchResultItem
from app.search_scoring import score_chunk

SNIPPET_LENGTH = 200


def search_chunks(
    db: Database,
    query: str | None,
    limit: int,
    title_num: str | None = None,
    chapter_num: str | None = None,
    document_type: str | None = None,
    agency: str | None = None,
    topic: str | None = None,
    mentions_penalty: bool | None = None,
    mentions_permit: bool | None = None,
) -> tuple[list[SearchResultItem], str]:
    """Shared filtered-search + scoring + reasoning-string builder.

    Used by /search, /penalties, and /permits so the retrieval logic (build
    an equality filter, score candidates in Python, explain how) lives in one
    place rather than being duplicated per endpoint.
    """
    mongo_filter: dict = {"type": "chunk"}
    if title_num:
        mongo_filter["title_num"] = title_num
    if chapter_num:
        mongo_filter["chapter_num"] = chapter_num
    if document_type:
        mongo_filter["document_type"] = document_type
    if agency:
        mongo_filter["agency"] = agency
    if topic:
        mongo_filter["topic"] = topic
    if mentions_penalty is not None:
        mongo_filter["mentions_penalty"] = mentions_penalty
    if mentions_permit is not None:
        mongo_filter["mentions_permit"] = mentions_permit

    candidates = list(db[LAWS_COLLECTION].find(mongo_filter))

    if query:
        scored = [(score_chunk(doc["section_title"], doc["text"], query), doc) for doc in candidates]
        scored = [(score, doc) for score, doc in scored if score > 0]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = scored[:limit]
        reasoning = (
            f"matched query {query!r} against {len(candidates)} candidate chunk(s) after applying "
            "filters; ranked by term frequency, title weighted higher than body"
        )
        results = [_to_result_item(doc, score) for score, doc in top]
    else:
        top = candidates[:limit]
        reasoning = f"no query text given; returning up to {limit} chunk(s) matching filters, unscored"
        results = [_to_result_item(doc, 0.0) for doc in top]

    return results, reasoning


def _to_result_item(doc: dict, score: float) -> SearchResultItem:
    return SearchResultItem(
        document_id=str(doc["document_id"]),
        section_number=doc["section_number"],
        section_title=doc["section_title"],
        url=doc["url"],
        score=score,
        snippet=doc["text"][:SNIPPET_LENGTH],
        document_type=doc["document_type"],
        agency=doc["agency"],
        topic=doc["topic"],
    )
