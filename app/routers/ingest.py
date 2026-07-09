from fastapi import APIRouter, Depends, Header, HTTPException
from pymongo.database import Database

from app.config import settings
from app.db import get_db
from app.ingestion.pipeline import ingest_url
from app.models import IngestRequest, IngestResponse, IngestResultItem

router = APIRouter(tags=["ingest"])


def _require_ingest_api_key(x_ingest_api_key: str | None = Header(default=None)) -> None:
    if settings.ingest_api_key and x_ingest_api_key != settings.ingest_api_key:
        raise HTTPException(status_code=401, detail="missing or invalid X-Ingest-Api-Key header")


@router.post("/ingest", response_model=IngestResponse, dependencies=[Depends(_require_ingest_api_key)])
def ingest(payload: IngestRequest, db: Database = Depends(get_db)) -> IngestResponse:
    if len(payload.urls) > settings.ingest_max_urls:
        raise HTTPException(
            status_code=400,
            detail=f"at most {settings.ingest_max_urls} urls allowed per request",
        )

    results = []
    for url in payload.urls:
        try:
            chunks_ingested = ingest_url(db, url)
            results.append(IngestResultItem(url=url, status="ok", chunks_ingested=chunks_ingested))
        except Exception as exc:
            results.append(IngestResultItem(url=url, status="error", error=str(exc)))
    return IngestResponse(results=results)
