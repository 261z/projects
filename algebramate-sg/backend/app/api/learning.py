from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..api.auth import current_user
from ..db.database import get_connection
from ..rag.ingest import load_questions
from ..rag.retriever import retrieve_question
from ..graph.practice_graph import practice_graph
from .learning_schemas import DiagnosticAnswer, DiagnosticStart, PracticeAnswer, PracticeStart

router = APIRouter(tags=["learning"])


def _question(question_id: str) -> dict:
    question = next((item for item in load_questions() if item["question_id"] == question_id), None)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.get("/topics")
def topics(_: dict = Depends(current_user)) -> list[dict[str, str]]:
    return [{"name": name} for name in sorted({q["topic"] for q in load_questions()})]


@router.get("/diagnostic/status")
def diagnostic_status(topic: str, user: dict = Depends(current_user)) -> dict:
    with get_connection() as connection:
        result = connection.execute("SELECT raw_score, initial_mastery, recommended_starting_difficulty, created_at FROM diagnostic_results WHERE user_id = ? AND topic = ? ORDER BY id DESC LIMIT 1", (user["id"], topic)).fetchone()
        answered = connection.execute("SELECT COUNT(*) AS count FROM diagnostic_answers WHERE user_id = ? AND topic = ?", (user["id"], topic)).fetchone()["count"]
    if result is None:
        return {"topic": topic, "complete": False, "answered": answered, "total": 5}
    return {"topic": topic, "complete": True, "answered": 5, "total": 5, **dict(result)}


@router.post("/diagnostic/start")
def diagnostic_start(payload: DiagnosticStart, user: dict = Depends(current_user)) -> dict:
    questions = [q for q in load_questions() if q["topic"].lower() == payload.topic.lower()]
    questions = sorted(questions, key=lambda q: q["difficulty"])
    if len(questions) < 5:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"topic": payload.topic, "questions": questions[:5], "total": 5, "difficulty_sequence": [q["difficulty"] for q in questions[:5]]}


@router.post("/diagnostic/answer")
def diagnostic_answer(payload: DiagnosticAnswer, user: dict = Depends(current_user)) -> dict:
    question = _question(payload.question_id)
    from ..tools.sympy_checker import check_answer
    result = check_answer(payload.student_answer, question["answer"], answer_type="equation" if "=" in question["answer"] else "expression")
    with get_connection() as connection:
        connection.execute("INSERT INTO diagnostic_answers (user_id, topic, question_id, student_answer, correct) VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id, topic, question_id) DO UPDATE SET student_answer=excluded.student_answer, correct=excluded.correct, created_at=CURRENT_TIMESTAMP", (user["id"], question["topic"], payload.question_id, payload.student_answer, int(result.correct)))
        rows = connection.execute("SELECT correct FROM diagnostic_answers WHERE user_id = ? AND topic = ?", (user["id"], question["topic"])).fetchall()
    answered = len(rows)
    if answered >= 5:
        raw_score = sum(int(row["correct"]) for row in rows)
        initial_mastery = round(raw_score / 5, 4)
        starting_difficulty = max(1, min(5, 1 + raw_score))
        with get_connection() as connection:
            connection.execute("INSERT INTO diagnostic_results (user_id, topic, raw_score, initial_mastery, recommended_starting_difficulty) VALUES (?, ?, ?, ?, ?)", (user["id"], question["topic"], raw_score, initial_mastery, starting_difficulty))
        return {"question_id": payload.question_id, "correct": result.correct, "method": result.method, "answered": answered, "complete": True, "raw_score": raw_score, "initial_mastery": initial_mastery, "recommended_starting_difficulty": starting_difficulty}
    return {"question_id": payload.question_id, "correct": result.correct, "method": result.method, "answered": answered, "complete": False}


@router.post("/practice/start")
def practice_start(payload: PracticeStart, user: dict = Depends(current_user)) -> dict:
    excluded = set(payload.exclude_question_ids)
    question = retrieve_question(payload.skill_id, payload.difficulty, payload.topic, payload.exclude_question_ids)
    if question is None:
        question = next((q for q in load_questions() if q["topic"].lower() == payload.topic.lower() and q["question_id"] not in excluded), None)
    if question is None:
        raise HTTPException(status_code=404, detail="No approved question available")
    return {"question": question, "retrieval": "chroma" if payload.skill_id else "approved-fallback"}


@router.post("/practice/answer")
def practice_answer(payload: PracticeAnswer, user: dict = Depends(current_user)) -> dict:
    question = _question(payload.question_id)
    with get_connection() as connection:
        row = connection.execute("SELECT mastery_score FROM student_mastery WHERE user_id = ? AND skill_id = ?", (user["id"], question["skill_id"])).fetchone()
    previous = float(row["mastery_score"]) if row else 0.5
    result = practice_graph.invoke({"user_id": user["id"], "question_id": question["question_id"], "skill_id": question["skill_id"], "difficulty": question["difficulty"], "expected_answer": question["answer"], "student_answer": payload.student_answer, "hints_used": payload.hints_used, "previous_mastery": previous})
    selected = payload.selected_difficulty or result["recommended_difficulty"]
    with get_connection() as connection:
        connection.execute("INSERT INTO attempts (user_id, question_id, skill_id, difficulty, student_answer, expected_answer, correct, hints_used, recommended_difficulty, selected_difficulty, difficulty_overridden) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user["id"], question["question_id"], question["skill_id"], question["difficulty"], payload.student_answer, question["answer"], int(result["is_correct"]), payload.hints_used, result["recommended_difficulty"], selected, int(selected != result["recommended_difficulty"])))
        connection.execute("INSERT INTO student_mastery (user_id, skill_id, mastery_score, current_difficulty) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, skill_id) DO UPDATE SET mastery_score=excluded.mastery_score, current_difficulty=excluded.current_difficulty, updated_at=CURRENT_TIMESTAMP", (user["id"], question["skill_id"], result["mastery_score"], selected))
    return {"correct": result["is_correct"], "mastery": result["mastery_score"], "recommended_action": result["recommended_action"], "recommended_difficulty": result["recommended_difficulty"], "selected_difficulty": selected, "difficulty_overridden": selected != result["recommended_difficulty"], "feedback": result["response"]}


@router.get("/progress")
def progress(user: dict = Depends(current_user)) -> dict:
    with get_connection() as connection:
        rows = connection.execute("SELECT skill_id, mastery_score, current_difficulty, updated_at FROM student_mastery WHERE user_id = ? ORDER BY skill_id", (user["id"],)).fetchall()
    return {"skills": [dict(row) for row in rows], "overall_mastery": round(sum(row["mastery_score"] for row in rows) / len(rows), 4) if rows else 0.0}
