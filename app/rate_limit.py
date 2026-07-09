import logging
import random
import time

from fastapi import Depends, HTTPException, Request
from pymongo.collection import ReturnDocument
from pymongo.database import Database

from app.config import settings
from app.db import LAWS_COLLECTION, get_db

logger = logging.getLogger("municipal_bylaws_api.rate_limit")

WINDOW_SECONDS = 60
STALE_AFTER_SECONDS = 5 * 60
CLEANUP_PROBABILITY = 0.05


def _client_id(request: Request) -> str:
    """Best-effort per-device identity: the client's IP, preferring the
    original caller from Vercel's X-Forwarded-For over the proxy hop.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(request: Request, db: Database, scope: str, limit: int) -> None:
    """Enforces `limit` requests/minute per client for the given `scope`,
    backed by MongoDB (the only state persisted across Vercel cold starts)
    rather than in-process memory. Each scope gets its own counter bucket so
    e.g. the strict /ingest limit doesn't share a counter with general
    endpoint traffic from the same client.

    Fails open on any error talking to Mongo - a rate limiter should not
    itself become the reason legitimate traffic goes down.
    """
    client_id = _client_id(request)
    window_start = int(time.time() // WINDOW_SECONDS) * WINDOW_SECONDS

    try:
        laws = db[LAWS_COLLECTION]
        result = laws.find_one_and_update(
            {"type": "ratelimit", "scope": scope, "client_id": client_id, "window_start": window_start},
            {"$inc": {"count": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        request_count = result["count"]

        if random.random() < CLEANUP_PROBABILITY:
            laws.delete_many(
                {"type": "ratelimit", "window_start": {"$lt": window_start - STALE_AFTER_SECONDS}}
            )
    except Exception:
        logger.exception("rate limiter unavailable, failing open for %s", client_id)
        return

    if request_count > limit:
        raise HTTPException(
            status_code=429,
            detail=f"rate limit exceeded: max {limit} requests per minute",
            headers={"Retry-After": str(WINDOW_SECONDS)},
        )


def rate_limiter(request: Request, db: Database = Depends(get_db)) -> None:
    """General per-client limit, applied to health/search/documents."""
    _check_rate_limit(request, db, scope="general", limit=settings.rate_limit_per_minute)


def ingest_rate_limiter(request: Request, db: Database = Depends(get_db)) -> None:
    """Stricter per-client limit for /ingest, since it triggers outbound
    fetches and Atlas writes rather than just reads.
    """
    _check_rate_limit(request, db, scope="ingest", limit=settings.ingest_rate_limit_per_minute)
