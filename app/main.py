import logging
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.config import settings
from app.rate_limit import ingest_rate_limiter, rate_limiter
from app.routers import actions, documents, health, ingest, penalties, permits, search, sections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("municipal_bylaws_api")

app = FastAPI(title="Municipal Law Skill for Autonomous Agents", version=settings.app_version)

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
app.include_router(sections.router, prefix="/api/v1", dependencies=_rate_limited)
app.include_router(penalties.router, prefix="/api/v1", dependencies=_rate_limited)
app.include_router(permits.router, prefix="/api/v1", dependencies=_rate_limited)
app.include_router(actions.router, prefix="/api/v1", dependencies=_rate_limited)
# Stricter limit for /ingest (outbound fetches + Atlas writes), not the general one.
app.include_router(ingest.router, prefix="/api/v1", dependencies=[Depends(ingest_rate_limiter)])

_SKILL_MD_PATH = Path(__file__).resolve().parent.parent / "SKILL.md"
_SKILL_MD_CONTENT = _SKILL_MD_PATH.read_text(encoding="utf-8")


@app.get("/")
def root() -> dict:
    return {
        "name": "Municipal Law Skill for Autonomous Agents",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
        "skill": "/skill.md",
    }


@app.get("/skill.md", response_class=PlainTextResponse)
def skill_md() -> str:
    return _SKILL_MD_CONTENT


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "internal server error"})
