from __future__ import annotations

from .chroma import get_questions_collection
from .ingest import load_questions


def retrieve_question(skill_id: str | None = None, difficulty: int | None = None, topic: str | None = None, exclude_question_ids: list[str] | None = None) -> dict | None:
    excluded = set(exclude_question_ids or [])
    collection = get_questions_collection()
    clauses: list[dict] = []
    if skill_id:
        clauses.append({"skill_id": skill_id})
    if difficulty is not None:
        clauses.append({"difficulty": difficulty})
    if topic:
        clauses.append({"topic": topic})
    where = clauses[0] if len(clauses) == 1 else ({"$and": clauses} if clauses else None)
    try:
        result = collection.get(where=where, limit=10)
        ids = result.get("ids", [])
        if ids:
            approved = load_questions()
            return next((item for item in approved if item["question_id"] in ids and item["question_id"] not in excluded), None)
    except Exception:
        return None
    return None
