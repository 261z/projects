from __future__ import annotations

from ..guardrails.guards import bounded_retry
from ..rag.ingest import load_questions


def generate_question_candidates(skill_id: str, difficulty: int) -> list[dict]:
    """Return deterministic demo candidates; live model generation can plug in here."""
    approved = [q for q in load_questions() if q["skill_id"] == skill_id]
    return [q for q in approved if q["difficulty"] == difficulty] + approved


def generate_verified_question(skill_id: str, difficulty: int, max_retries: int = 3) -> dict:
    candidate = bounded_retry(generate_question_candidates(skill_id, difficulty), max_retries=max_retries)
    if candidate is None:
        fallback = next((q for q in load_questions() if q["skill_id"] == skill_id), None)
        if fallback is None:
            raise ValueError("No approved fallback question exists for this skill")
        return fallback
    return candidate
