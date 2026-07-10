import logging
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.config import settings
from app.models import CorpusStats, RootInfo
from app.rate_limit import ingest_rate_limiter, rate_limiter
from app.routers import actions, documents, health, ingest, penalties, permits, search, sections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("municipal_bylaws_api")

_APP_DESCRIPTION = """
Any autonomous agent can determine whether an action is legal in New York City by invoking this
skill. **This service never generates legal text or answers** - it only returns authoritative
legal evidence and citations (deterministic keyword retrieval, not an LLM); the calling agent
performs the reasoning and composes the final response. Same query -> same citations -> same
ordering -> no randomness, ever.

**The complete corpus, not a sample**: all 32 titles / 4,781 sections of the NYC Administrative
Code, plus all 36 articles / 501 sections of the NYC Health Code - 668 source documents, 10,702
searchable chunks.

## Try it in one call

`POST /api/v1/is_action_allowed` with `{"action": "Keep backyard chickens"}` returns
`{allowed, conditions, citations, reasoning, confidence}` - a complete, citation-backed legal
determination. That's the headline capability; see the **Legal Determination** tag below.

## Agent workflow

```
User asks a question
    -> POST /api/v1/is_action_allowed   (yes/no legality check on a described action)
       or  POST /api/v1/search          (general lookup)
       or  POST /api/v1/penalties |     (penalty/permit-specific questions)
           POST /api/v1/permits
    -> GET /api/v1/sections/{id}        (full text, if you need more than the snippet)
    -> GET /api/v1/sections/{id}/related  (cross-referenced sections, if needed)
    -> Agent composes the final answer from the returned citations + reasoning
```

Full agent-facing reference (endpoints, curl, the composing-your-final-answer contract, and the
rules for never overclaiming): [`GET /skill.md`](/skill.md).
""".strip()

_TAGS_METADATA = [
    {
        "name": "Service Info",
        "description": "Start here - service metadata, corpus stats, and the agent-facing SKILL.md reference. Not rate-limited.",
    },
    {
        "name": "Legal Determination",
        "description": "The headline capability: ask whether a described action is legal, get a structured, citation-backed verdict.",
    },
    {"name": "Search", "description": "General deterministic keyword retrieval over the entire ingested corpus."},
    {"name": "Lookup", "description": "Exact retrieval by section number or document id - full, untruncated text."},
    {"name": "Cross References", "description": "Resolve a section's own citations into a one-hop citation graph."},
    {"name": "Penalties", "description": "Find sections flagged as mentioning a penalty or fine."},
    {"name": "Permits", "description": "Find sections flagged as mentioning a permit or license requirement."},
    {
        "name": "Administration",
        "description": "Operational endpoints (health, version, corpus maintenance) - not part of the agent-facing retrieval surface.",
    },
]

app = FastAPI(
    title="Municipal Law Skill for Autonomous Agents",
    version=settings.app_version,
    description=_APP_DESCRIPTION,
    openapi_tags=_TAGS_METADATA,
)

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


@app.get(
    "/",
    response_model=RootInfo,
    tags=["Service Info"],
    summary="Service info, corpus stats, and the killer example",
    description="Not rate-limited. Read this first: what the service is, why there's no LLM, real corpus coverage, and a runnable example of the headline capability.",
)
def root() -> RootInfo:
    return RootInfo(
        name="Municipal Law Skill for Autonomous Agents",
        version=settings.app_version,
        tagline=(
            "Deterministic, citation-backed NYC municipal law retrieval. No LLM calls, ever - "
            "this service only returns authoritative legal evidence and citations; the calling "
            "agent performs reasoning."
        ),
        killer_example={
            "action": "Keep backyard chickens",
            "call": "POST /api/v1/is_action_allowed",
            "try_it": 'curl -X POST /api/v1/is_action_allowed -d \'{"action": "Keep backyard chickens"}\'',
        },
        corpus=CorpusStats(),
        docs="/docs",
        health="/api/v1/health",
        skill="/skill.md",
    )


@app.get(
    "/skill.md",
    response_class=PlainTextResponse,
    tags=["Service Info"],
    summary="Agent-facing reference (plain text)",
    description="Serves the repo's root SKILL.md live, as text/plain - the same file an autonomous agent should read to learn every endpoint, how to compose a final answer from citations, and the rules for never overclaiming. Not rate-limited.",
)
def skill_md() -> str:
    return _SKILL_MD_CONTENT


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "internal server error"})
