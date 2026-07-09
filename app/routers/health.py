from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.config import settings
from app.db import get_db, ping

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Database = Depends(get_db)) -> dict:
    try:
        ping(db)
        return {"status": "ok"}
    except Exception:
        return {"status": "degraded"}


@router.get("/version")
def version() -> dict:
    return {"version": settings.app_version}
