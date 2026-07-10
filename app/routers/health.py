from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.config import settings
from app.db import get_db, ping
from app.models import HealthResponse, VersionResponse

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
    summary="Deployed app version",
    description="Returns the running service's version string. Operational endpoint, not part of the retrieval surface an agent reasons over.",
)
def version() -> VersionResponse:
    return VersionResponse(version=settings.app_version)
