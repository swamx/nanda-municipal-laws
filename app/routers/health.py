from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.config import settings
from app.db import get_db, get_latest_ingested_at, ping
from app.models import HealthResponse, PublicKeyResponse, VersionResponse
from app.signing import public_key_hex

router = APIRouter(tags=["Administration"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Live health check",
    description="Pings MongoDB and reports reachability. Always returns HTTP 200 (status:'degraded' means the database is unreachable, not that the request failed) - operational endpoint, not part of the retrieval surface an agent reasons over.",
)
def health(db: Database = Depends(get_db)) -> HealthResponse:
    try:
        ping(db)
        return HealthResponse(status="ok")
    except Exception:
        return HealthResponse(status="degraded")


@router.get(
    "/version",
    response_model=VersionResponse,
    summary="Deployed app version and corpus freshness",
    description=(
        "Returns the running service's version string plus `corpus_last_ingested_at`/"
        "`corpus_age_days` - law text goes stale, and this is the mechanical signal for whether "
        "the ingested corpus reflects anything close to current law. Falls back to null freshness "
        "fields (not an error) if the database is unreachable."
    ),
)
def version(db: Database = Depends(get_db)) -> VersionResponse:
    try:
        last_ingested = get_latest_ingested_at(db)
    except Exception:
        last_ingested = None
    age_days = None
    if last_ingested is not None:
        # Real MongoDB returns naive UTC datetimes by default (no tz_aware client
        # option set) - assume UTC rather than erroring on a naive/aware subtraction.
        aware = last_ingested if last_ingested.tzinfo else last_ingested.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - aware).days
    return VersionResponse(
        version=settings.app_version,
        corpus_last_ingested_at=last_ingested,
        corpus_age_days=age_days,
    )


@router.get(
    "/pubkey",
    response_model=PublicKeyResponse,
    summary="Ed25519 public key for verifying signed responses",
    description=(
        "Every `/is_action_allowed` and `/search` response carries a `provenance.signature` - "
        "verify it against the public key returned here (see docs/PROVENANCE.md for the exact "
        "canonicalization recipe) to prove offline that this service, not a relay or a cached "
        "copy, produced those citations. Not rate-limited."
    ),
)
def pubkey() -> PublicKeyResponse:
    return PublicKeyResponse(public_key=public_key_hex())
