from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.action_evaluator import evaluate_action
from app.db import get_db
from app.models import ActionCheckRequest, ActionCheckResponse

router = APIRouter(tags=["actions"])


@router.post("/is_action_allowed", response_model=ActionCheckResponse)
def is_action_allowed(payload: ActionCheckRequest, db: Database = Depends(get_db)) -> ActionCheckResponse:
    return evaluate_action(db, action=payload.action, limit=payload.limit)
