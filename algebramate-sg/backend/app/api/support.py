from fastapi import APIRouter, Depends, HTTPException

from ..agents.generator import get_generated_question
from ..agents.support import explain, hint_for, visual_spec
from ..api.auth import current_user
from ..guardrails.guards import hint_is_safe
from ..rag.ingest import load_questions
from .learning_schemas import SupportRequest

router = APIRouter(prefix="/practice", tags=["support"])


def question(question_id: str, user_id: int) -> dict:
    found = next((item for item in load_questions() if item["question_id"] == question_id), None)
    found = found or get_generated_question(question_id, user_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return found


@router.post("/hint")
def hint(payload: SupportRequest, user: dict = Depends(current_user)) -> dict:
    q = question(payload.question_id, user["id"])
    text = hint_for(q, payload.hint_level)
    if not hint_is_safe(text, q["answer"]):
        raise HTTPException(status_code=422, detail="Hint was withheld because it revealed the final answer")
    return {"hint_level": payload.hint_level, "hint": text, "guard": "approved"}


@router.post("/visualise")
def visualise(payload: SupportRequest, user: dict = Depends(current_user)) -> dict:
    return {"spec": visual_spec(question(payload.question_id, user["id"])), "guard": "approved"}


@router.post("/explain")
async def explanation(payload: SupportRequest, user: dict = Depends(current_user)) -> dict:
    return await explain(question(payload.question_id, user["id"]), "explain")


@router.post("/analogy")
async def analogy(payload: SupportRequest, user: dict = Depends(current_user)) -> dict:
    return await explain(question(payload.question_id, user["id"]), "analogy")
