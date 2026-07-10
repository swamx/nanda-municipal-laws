from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.action_evaluator import evaluate_action
from app.db import get_db
from app.models import ActionCheckRequest, ActionCheckResponse
from app.signing import sign_response

router = APIRouter(tags=["Legal Determination"])


@router.post(
    "/is_action_allowed",
    response_model=ActionCheckResponse,
    summary="Determine whether a described action is legal in Nandatown (e.g., NYC)",
    description=(
        "**The headline capability of this skill.** Describe an action in plain language "
        "(e.g. \"Keep backyard chickens\", \"Operate a food truck in Central Park\") and get back "
        "a structured, citation-backed determination: `{allowed, conditions, citations, reasoning, "
        "confidence}`.\n\n"
        "**When to call this**: any yes/no legality question about a described action - \"can I...\", "
        "\"is it legal to...\", \"am I allowed to...\". This does the search + rule evaluation for you; "
        "call it first before falling back to `/search`.\n\n"
        "**Deterministic - retrieval plus rules, not an LLM.** Keyword search finds the closest-matching "
        "statute section; a fixed keyword list classifies its text as a prohibition, a permission, or "
        "neither. `allowed` is `true`/`false` only when an explicit statement was found in the corpus; "
        "`null` when nothing relevant was found - this never guesses from silence to force a boolean. "
        "The service never generates legal text: every citation and matched_text is a verbatim excerpt "
        "from the official code."
    ),
)
def is_action_allowed(payload: ActionCheckRequest, db: Database = Depends(get_db)) -> ActionCheckResponse:
    response = evaluate_action(db, action=payload.action, limit=payload.limit)
    provenance = sign_response(response)
    return response.model_copy(update={"provenance": provenance})
