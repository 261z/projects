from fastapi import APIRouter, Depends

from ..agents.support import explain, hint_for, visual_spec
from ..api.auth import current_user
from ..rag.ingest import load_questions
from .learning_schemas import SupportRequest

router = APIRouter(prefix="/practice", tags=["support"])


def question(question_id: str) -> dict:
    return next(item for item in load_questions() if item["question_id"] == question_id)


@router.post("/hint")
def hint(payload: SupportRequest, _: dict = Depends(current_user)) -> dict:
    q = question(payload.question_id)
    return {"hint_level": payload.hint_level, "hint": hint_for(q, payload.hint_level), "guard": "approved"}


@router.post("/visualise")
def visualise(payload: SupportRequest, _: dict = Depends(current_user)) -> dict:
    return {"spec": visual_spec(question(payload.question_id)), "guard": "approved"}


@router.post("/explain")
async def explanation(payload: SupportRequest, _: dict = Depends(current_user)) -> dict:
    return await explain(question(payload.question_id), "explain")


@router.post("/analogy")
async def analogy(payload: SupportRequest, _: dict = Depends(current_user)) -> dict:
    return await explain(question(payload.question_id), "analogy")
