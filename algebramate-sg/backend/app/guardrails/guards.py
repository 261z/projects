from __future__ import annotations

from ..tools.sympy_checker import check_answer

SUPPORTED_TOPICS = {"Factorisation", "Expansion", "Linear equations", "Quadratics"}


def validate_topic(topic: str) -> str:
    if topic not in SUPPORTED_TOPICS:
        raise ValueError("Unsupported algebra topic")
    return topic


def hint_is_safe(hint: str, expected_answer: str) -> bool:
    lowered = hint.lower()
    return len(hint) <= 500 and expected_answer.lower() not in lowered and "final answer is" not in lowered


def verify_generated_question(question: dict) -> bool:
    required = {"question", "answer", "solution", "skill_id", "difficulty", "topic"}
    if not required.issubset(question) or not 1 <= int(question["difficulty"]) <= 5:
        return False
    if question["topic"] not in SUPPORTED_TOPICS:
        return False
    return bool(check_answer(question["answer"], question["answer"]).correct)


def bounded_retry(attempts: list[dict], max_retries: int = 3) -> dict | None:
    for question in attempts[:max_retries]:
        if verify_generated_question(question):
            return question
    return None
