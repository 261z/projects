from __future__ import annotations

import json
import logging
from uuid import uuid4

from pydantic import ValidationError

from .schemas import GeneratedQuestionOutput
from ..db.database import get_connection
from ..guardrails.guards import verify_generated_question
from ..llm.provider import AgentRouterUnavailable, chat
from ..rag.ingest import load_questions

logger = logging.getLogger(__name__)


def _deterministic_variant(topic: str, difficulty: int, sequence: int) -> dict:
    offset = max(0, sequence - 1)
    if topic == "Factorisation":
        if difficulty <= 1:
            common, a, b = 2 + offset % 7, 2 + offset % 5, 3 + (offset * 2) % 7
            question, answer = f"Factorise {common*a}x + {common*b}.", f"{common}({a}x+{b})"
            subtopic, skill = "Common factor", "factorisation.common_factor"
            solution = "Identify the greatest common factor, take it outside the bracket, and divide each term by it."
        elif difficulty == 2:
            root = 2 + offset % 10
            question, answer = f"Factorise x^2 - {root**2}.", f"(x-{root})(x+{root})"
            subtopic, skill = "Difference of two squares", "factorisation.difference_two_squares"
            solution = "Use the identity a^2-b^2=(a-b)(a+b)."
        else:
            a = 2 + offset % 7
            b = 3 + (offset * 2) % 8
            if difficulty >= 4 and offset % 2 == 0:
                a = -a
            total, product = a + b, a * b
            middle = f"+ {total}x" if total >= 0 else f"- {abs(total)}x"
            constant = f"+ {product}" if product >= 0 else f"- {abs(product)}"
            sign_a = f"+{a}" if a >= 0 else str(a)
            sign_b = f"+{b}" if b >= 0 else str(b)
            question, answer = f"Factorise x^2 {middle} {constant}.", f"(x{sign_a})(x{sign_b})"
            subtopic, skill = "Quadratic trinomial", "factorisation.quadratic_trinomial"
            solution = "Find two integers whose product is the constant term and whose sum is the coefficient of x."
    elif topic == "Expansion":
        if difficulty <= 2:
            multiplier = 2 + offset % 8
            constant = 2 + (offset * 3) % 9
            question, answer = f"Expand {multiplier}(x + {constant}).", f"{multiplier}x + {multiplier*constant}"
            subtopic, skill = "Single bracket", "expansion.single_bracket"
            solution = "Distribute the multiplier to every term inside the bracket."
        else:
            a = 2 + offset % 8
            b = 3 + (offset * 2) % 9
            if difficulty >= 4 and offset % 2 == 0:
                a = -a
            total, product = a + b, a * b
            sign_a = f"+ {a}" if a >= 0 else f"- {abs(a)}"
            sign_b = f"+ {b}" if b >= 0 else f"- {abs(b)}"
            middle = f"+ {total}x" if total >= 0 else f"- {abs(total)}x"
            constant = f"+ {product}" if product >= 0 else f"- {abs(product)}"
            question, answer = f"Expand (x {sign_a})(x {sign_b}).", f"x^2 {middle} {constant}"
            subtopic, skill = "Double brackets", "expansion.double_bracket"
            solution = "Multiply every term in the first bracket by every term in the second, then collect like terms."
    elif topic == "Linear equations":
        solution_value = 2 + offset % 15
        coefficient = 2 + (offset * 2) % 8
        constant = 1 + (offset * 3) % 12
        rhs = coefficient * solution_value + constant
        question, answer = f"Solve {coefficient}x + {constant} = {rhs}.", f"x = {solution_value}"
        subtopic = "Two-step equations" if difficulty <= 3 else "Multi-step equations"
        skill = "linear_equations.two_step" if difficulty <= 3 else "linear_equations.multi_step"
        solution = f"Subtract {constant} from both sides, then divide both sides by {coefficient}."
    else:
        r1 = 2 + offset % 8
        r2 = 3 + (offset * 2) % 9
        total, product = r1 + r2, r1 * r2
        question, answer = f"Solve x^2 - {total}x + {product} = 0.", f"x = {r1} or x = {r2}"
        subtopic, skill = "Solving by factorisation", "quadratics.solving_factorisation"
        solution = "Factorise the quadratic, set each factor equal to zero, and solve for x."
    return {
        "question_id": f"GEN-{topic[:3].upper()}-{difficulty}-{sequence}-{uuid4().hex[:8]}",
        "usage": "practice", "school_level": "Secondary 2", "topic": topic,
        "subtopic": subtopic, "skill_id": skill, "difficulty": difficulty,
        "question": question, "answer": answer, "solution": solution, "marks": 2,
        "learning_objective": f"Practise {subtopic.lower()} at difficulty {difficulty}.",
        "misconceptions": ["concept_unknown"], "source": "deterministic_verified_fallback",
    }


def _normalise(candidate: dict, *, user_id: int, source: str) -> dict:
    parsed = GeneratedQuestionOutput.model_validate(candidate)
    return {
        "question_id": f"GEN-{user_id}-{uuid4().hex[:12]}", "usage": "practice",
        "school_level": "Secondary 2", "question": parsed.question,
        "answer": parsed.expected_answer, "topic": parsed.topic, "subtopic": parsed.subtopic,
        "skill_id": parsed.skill_id, "difficulty": parsed.difficulty, "solution": parsed.solution,
        "marks": parsed.marks, "learning_objective": parsed.learning_objective,
        "misconceptions": ["concept_unknown"], "source": source,
    }


def persist_generated_question(user_id: int, question: dict) -> dict:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO generated_questions (question_id, user_id, topic, subtopic, skill_id, difficulty, question, expected_answer, solution, marks, learning_objective, source, verification_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (question["question_id"], user_id, question["topic"], question["subtopic"], question["skill_id"], question["difficulty"], question["question"], question["answer"], question["solution"], question["marks"], question["learning_objective"], question["source"], "verified"),
        )
    return question


def get_generated_question(question_id: str, user_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM generated_questions WHERE question_id = ? AND user_id = ?", (question_id, user_id)).fetchone()
    if row is None:
        return None
    data = dict(row)
    return {"question_id": data["question_id"], "usage": "practice", "school_level": "Secondary 2", "topic": data["topic"], "subtopic": data["subtopic"], "skill_id": data["skill_id"], "difficulty": data["difficulty"], "question": data["question"], "answer": data["expected_answer"], "solution": data["solution"], "marks": data["marks"], "learning_objective": data["learning_objective"], "misconceptions": ["concept_unknown"], "source": data["source"]}


async def generate_verified_question(user_id: int, topic: str, difficulty: int, sequence: int, max_retries: int = 3) -> dict:
    grounding = [q for q in load_questions() if q["topic"] == topic and q.get("usage") == "practice"][:3]
    prompt = (
        "Generate one fresh Singapore secondary algebra practice question. Return JSON only with question, expected_answer, topic, subtopic, skill_id, difficulty, solution, marks, learning_objective. "
        f"Topic={topic}; difficulty={difficulty}. Do not copy these examples exactly: {json.dumps(grounding, ensure_ascii=False)}"
    )
    for retry in range(max_retries):
        try:
            raw = await chat([{"role": "system", "content": "You generate concise curriculum-aligned algebra questions as strict JSON."}, {"role": "user", "content": prompt}], task="question_generation", json_mode=True)
            candidate = _normalise(json.loads(raw), user_id=user_id, source="agent_router")
            if candidate["topic"] == topic and candidate["difficulty"] == difficulty and verify_generated_question(candidate):
                logger.info("[question_generation] model=PRIMARY_MODEL retry=%s status=verified", retry)
                return persist_generated_question(user_id, candidate)
        except AgentRouterUnavailable:
            logger.info("[question_generation] status=provider_unavailable")
            break
        except (ValidationError, json.JSONDecodeError, ValueError, TypeError):
            logger.info("[question_generation] retry=%s status=retry", retry)
            continue
    fallback = _deterministic_variant(topic, difficulty, sequence)
    if not verify_generated_question(fallback):
        raise ValueError("Unable to create a verified practice question")
    logger.info("[question_generation] source=deterministic_verified_fallback status=verified")
    return persist_generated_question(user_id, fallback)


def generate_question_candidates(skill_id: str, difficulty: int) -> list[dict]:
    approved = [q for q in load_questions() if q["skill_id"] == skill_id and q.get("usage") == "practice"]
    return [q for q in approved if q["difficulty"] == difficulty] + approved


def generate_verified_question_sync(skill_id: str, difficulty: int, max_retries: int = 3) -> dict:
    from ..guardrails.guards import bounded_retry
    candidate = bounded_retry(generate_question_candidates(skill_id, difficulty), max_retries=max_retries)
    if candidate is None:
        raise ValueError("No verified approved fallback question exists for this skill")
    return candidate
