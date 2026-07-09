import logging

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.rate_limit import ingest_rate_limiter, rate_limiter
from app.routers import documents, health, ingest, search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("municipal_bylaws_api")

app = FastAPI(title="Municipal Bylaws Knowledge API", version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

_rate_limited = [Depends(rate_limiter)]
app.include_router(health.router, prefix="/api/v1", dependencies=_rate_limited)
app.include_router(search.router, prefix="/api/v1", dependencies=_rate_limited)
app.include_router(documents.router, prefix="/api/v1", dependencies=_rate_limited)
# Stricter limit for /ingest (outbound fetches + Atlas writes), not the general one.
app.include_router(ingest.router, prefix="/api/v1", dependencies=[Depends(ingest_rate_limiter)])


@app.get("/")
def root() -> dict:
    return {
        "name": "Municipal Bylaws Knowledge API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "internal server error"})
