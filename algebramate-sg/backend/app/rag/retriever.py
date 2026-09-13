from __future__ import annotations

import logging

from .chroma import get_questions_collection
from .ingest import load_questions

logger = logging.getLogger(__name__)


def retrieve_question(skill_id: str | None = None, difficulty: int | None = None, topic: str | None = None, exclude_question_ids: list[str] | None = None, usage: str = "practice") -> dict | None:
    excluded = set(exclude_question_ids or [])
    collection = get_questions_collection()
    clauses: list[dict] = [{"usage": usage}]
    if skill_id:
        clauses.append({"skill_id": skill_id})
    if difficulty is not None:
        clauses.append({"difficulty": difficulty})
    if topic:
        clauses.append({"topic": topic})
    where = clauses[0] if len(clauses) == 1 else {"$and": clauses}
    query_text = " ".join(part for part in [topic, skill_id, f"difficulty {difficulty}" if difficulty else None] if part)
    try:
        available = collection.get(where=where).get("ids", [])
        if not available:
            return None
        result = collection.query(query_texts=[query_text or "algebra practice"], where=where, n_results=len(available))
        ranked_ids = result.get("ids", [[]])[0]
        approved = {item["question_id"]: item for item in load_questions()}
        selected = next((approved[qid] for qid in ranked_ids if qid not in excluded and qid in approved), None)
        logger.info("[retrieval] source=chroma topic=%s skill=%s difficulty=%s usage=%s selected=%s", topic, skill_id, difficulty, usage, selected["question_id"] if selected else None)
        return selected
    except Exception as exc:
        logger.warning("[retrieval] Chroma lookup failed: %s", type(exc).__name__)
        return None
