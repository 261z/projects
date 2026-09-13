from __future__ import annotations

import re

from ..tools.sympy_checker import check_answer

SUPPORTED_TOPICS = {"Factorisation", "Expansion", "Linear equations", "Quadratics"}
TOPIC_PREFIXES = {
    "Factorisation": "factorisation.",
    "Expansion": "expansion.",
    "Linear equations": "linear_equations.",
    "Quadratics": "quadratics.",
}


def validate_topic(topic: str) -> str:
    if topic not in SUPPORTED_TOPICS:
        raise ValueError("Unsupported algebra topic")
    return topic


def hint_is_safe(hint: str, expected_answer: str) -> bool:
    lowered = hint.lower()
    return len(hint) <= 500 and expected_answer.lower() not in lowered and "final answer is" not in lowered


def _question_expression(text: str, command: str) -> str | None:
    match = re.match(rf"\s*{command}\s+(.+?)[.?]?\s*$", text, flags=re.IGNORECASE)
    return match.group(1).rstrip(".") if match else None


def verify_generated_question(question: dict) -> bool:
    required = {"question", "answer", "solution", "skill_id", "difficulty", "topic", "subtopic", "marks", "learning_objective"}
    if not required.issubset(question):
        return False
    try:
        difficulty = int(question["difficulty"])
        marks = int(question["marks"])
    except (TypeError, ValueError):
        return False
    topic = question["topic"]
    if topic not in SUPPORTED_TOPICS or not 1 <= difficulty <= 5 or not 1 <= marks <= 5:
        return False
    if not str(question["skill_id"]).startswith(TOPIC_PREFIXES[topic]):
        return False
    if any(not str(question[field]).strip() for field in ["question", "answer", "solution", "subtopic", "learning_objective"]):
        return False
    prompt = str(question["question"])
    if topic == "Factorisation":
        expected = _question_expression(prompt, "Factorise")
        return bool(expected and check_answer(str(question["answer"]), expected).correct)
    if topic == "Expansion":
        expected = _question_expression(prompt, "Expand")
        return bool(expected and check_answer(str(question["answer"]), expected).correct)
    if topic in {"Linear equations", "Quadratics"}:
        expected = _question_expression(prompt, "Solve")
        return bool(expected and check_answer(str(question["answer"]), expected, answer_type="equation").correct)
    return False


def bounded_retry(attempts: list[dict], max_retries: int = 3) -> dict | None:
    for question in attempts[:max_retries]:
        if verify_generated_question(question):
            return question
    return None
