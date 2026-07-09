import logging

from pymongo.database import Database
from pymongo.errors import OperationFailure

from app.config import settings
from app.db import LAWS_COLLECTION
from app.models import SearchResultItem
from app.search_scoring import score_chunk

logger = logging.getLogger("municipal_bylaws_api.retrieval")

SNIPPET_LENGTH = 200
VALID_SEARCH_MODES = ("text_index", "in_app")


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
    search_mode: str | None = None,
) -> tuple[list[SearchResultItem], str]:
    """Shared filtered-search + scoring + reasoning-string builder.

    Used by /search, /penalties, and /permits so the retrieval logic lives in
    one place rather than being duplicated per endpoint. Two interchangeable
    scoring strategies, chosen by `search_mode` (falls back to
    settings.search_mode when not given per-request):

    - "text_index" (default): native MongoDB $text/textScore search - scales
      to large corpora without pulling every candidate into Python.
    - "in_app": Python TF-style scoring (app/search_scoring.py) - no index
      dependency, but fetches every filter-matching chunk into memory, so it
      degrades as the corpus grows.

    If "text_index" is requested but the text index is unavailable (e.g. the
    Atlas role in use can't create indexes), falls back to "in_app" rather
    than failing the request.
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

    if not query:
        cursor = db[LAWS_COLLECTION].find(mongo_filter).limit(limit)
        results = [_to_result_item(doc, 0.0) for doc in cursor]
        reasoning = f"no query text given; returning up to {limit} chunk(s) matching filters, unscored"
        return results, reasoning

    mode = search_mode if search_mode in VALID_SEARCH_MODES else settings.search_mode

    if mode == "text_index":
        try:
            return _search_via_text_index(db, mongo_filter, query, limit)
        except OperationFailure as exc:
            logger.warning("text index search failed, falling back to in-app scoring: %s", exc)

    return _search_via_in_app_scoring(db, mongo_filter, query, limit)


def _search_via_text_index(
    db: Database, mongo_filter: dict, query: str, limit: int
) -> tuple[list[SearchResultItem], str]:
    filter_with_text = {**mongo_filter, "$text": {"$search": query}}
    cursor = (
        db[LAWS_COLLECTION]
        .find(filter_with_text, {"score": {"$meta": "textScore"}})
        .sort([("score", {"$meta": "textScore"})])
        .limit(limit)
    )
    docs = list(cursor)
    results = [_to_result_item(doc, doc.get("score", 0.0)) for doc in docs]
    reasoning = (
        f"matched query {query!r} via MongoDB $text/textScore search after applying filters; "
        "ranked by MongoDB's relevance score"
    )
    return results, reasoning


def _search_via_in_app_scoring(
    db: Database, mongo_filter: dict, query: str, limit: int
) -> tuple[list[SearchResultItem], str]:
    candidates = list(db[LAWS_COLLECTION].find(mongo_filter))
    scored = [(score_chunk(doc["section_title"], doc["text"], query), doc) for doc in candidates]
    scored = [(score, doc) for score, doc in scored if score > 0]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    top = scored[:limit]
    reasoning = (
        f"matched query {query!r} against {len(candidates)} candidate chunk(s) after applying "
        "filters; ranked by term frequency (in-app scoring), title weighted higher than body"
    )
    results = [_to_result_item(doc, score) for score, doc in top]
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
