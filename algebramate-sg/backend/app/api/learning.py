from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..agents.generator import generate_verified_question, get_generated_question
from ..api.auth import current_user
from ..db.database import get_connection
from ..guardrails.guards import validate_topic
from ..rag.ingest import load_questions
from ..rag.retriever import retrieve_question
from ..graph.practice_graph import practice_graph
from .learning_schemas import DiagnosticAnswer, DiagnosticStart, DifficultyOverride, PracticeAnswer, PracticeStart

router = APIRouter(tags=["learning"])


def _approved_question(question_id: str) -> dict | None:
    return next((item for item in load_questions() if item["question_id"] == question_id), None)


def _question(question_id: str, user_id: int | None = None) -> dict:
    question = _approved_question(question_id)
    if question is None and user_id is not None:
        question = get_generated_question(question_id, user_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


def _public_question(question: dict) -> dict:
    hidden = {"answer", "solution", "misconceptions"}
    return {key: value for key, value in question.items() if key not in hidden}


def _session(user_id: int, topic: str, session_id: int | None) -> int:
    with get_connection() as connection:
        if session_id is not None:
            row = connection.execute("SELECT id FROM learning_sessions WHERE id = ? AND user_id = ? AND topic = ? AND ended_at IS NULL", (session_id, user_id, topic)).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Practice session is not active")
            return int(row["id"])
        mastery = connection.execute("SELECT AVG(mastery_score) AS score FROM student_mastery WHERE user_id = ? AND skill_id LIKE ?", (user_id, f"{topic.lower().replace(' ', '_')}%" )).fetchone()["score"]
        cursor = connection.execute("INSERT INTO learning_sessions (user_id, topic, mastery_start) VALUES (?, ?, ?)", (user_id, topic, float(mastery) if mastery is not None else 0.5))
        return int(cursor.lastrowid)


@router.get("/topics")
def topics(_: dict = Depends(current_user)) -> list[dict[str, str]]:
    return [{"name": name} for name in sorted({q["topic"] for q in load_questions()})]


@router.get("/diagnostic/status")
def diagnostic_status(topic: str, user: dict = Depends(current_user)) -> dict:
    try:
        validate_topic(topic)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    with get_connection() as connection:
        result = connection.execute("SELECT raw_score, initial_mastery, recommended_starting_difficulty, created_at FROM diagnostic_results WHERE user_id = ? AND topic = ? ORDER BY id DESC LIMIT 1", (user["id"], topic)).fetchone()
        answered = connection.execute("SELECT COUNT(*) AS count FROM diagnostic_answers WHERE user_id = ? AND topic = ?", (user["id"], topic)).fetchone()["count"]
    if result is None:
        return {"topic": topic, "complete": False, "answered": answered, "total": 5}
    return {"topic": topic, "complete": True, "answered": 5, "total": 5, **dict(result)}


@router.post("/diagnostic/start")
def diagnostic_start(payload: DiagnosticStart, user: dict = Depends(current_user)) -> dict:
    try:
        validate_topic(payload.topic)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    questions = [q for q in load_questions() if q["topic"] == payload.topic and q.get("usage") == "diagnostic"]
    by_difficulty = {q["difficulty"]: q for q in questions}
    if set(by_difficulty) != {1, 2, 3, 4, 5}:
        raise HTTPException(status_code=503, detail="Diagnostic content is incomplete for this topic")
    selected = [by_difficulty[difficulty] for difficulty in range(1, 6)]
    return {"topic": payload.topic, "questions": [_public_question(q) for q in selected], "total": 5, "difficulty_sequence": [1, 2, 3, 4, 5]}


@router.post("/diagnostic/answer")
def diagnostic_answer(payload: DiagnosticAnswer, user: dict = Depends(current_user)) -> dict:
    question = _question(payload.question_id, user["id"])
    if question.get("usage") != "diagnostic":
        raise HTTPException(status_code=422, detail="This question is not part of the diagnostic bank")
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
            existing = connection.execute("SELECT id FROM diagnostic_results WHERE user_id = ? AND topic = ? ORDER BY id DESC LIMIT 1", (user["id"], question["topic"])).fetchone()
            if existing:
                connection.execute("UPDATE diagnostic_results SET raw_score = ?, initial_mastery = ?, recommended_starting_difficulty = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?", (raw_score, initial_mastery, starting_difficulty, existing["id"]))
            else:
                connection.execute("INSERT INTO diagnostic_results (user_id, topic, raw_score, initial_mastery, recommended_starting_difficulty) VALUES (?, ?, ?, ?, ?)", (user["id"], question["topic"], raw_score, initial_mastery, starting_difficulty))
        return {"question_id": payload.question_id, "correct": result.correct, "method": result.method, "answered": answered, "complete": True, "raw_score": raw_score, "initial_mastery": initial_mastery, "recommended_starting_difficulty": starting_difficulty}
    return {"question_id": payload.question_id, "correct": result.correct, "method": result.method, "answered": answered, "complete": False}


@router.post("/practice/start")
async def practice_start(payload: PracticeStart, user: dict = Depends(current_user)) -> dict:
    try:
        validate_topic(payload.topic)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    session_id = _session(user["id"], payload.topic, payload.session_id)
    question = retrieve_question(payload.skill_id, payload.difficulty, payload.topic, payload.exclude_question_ids, usage="practice")
    source = "chroma_approved"
    if question is None:
        sequence = len(payload.exclude_question_ids) + 1
        question = await generate_verified_question(user["id"], payload.topic, payload.difficulty, sequence)
        source = question.get("source", "generated_verified")
    return {"question": _public_question(question), "retrieval": source, "session_id": session_id}


@router.post("/practice/answer")
def practice_answer(payload: PracticeAnswer, user: dict = Depends(current_user)) -> dict:
    question = _question(payload.question_id, user["id"])
    if question.get("usage") != "practice":
        raise HTTPException(status_code=422, detail="Diagnostic questions cannot be used as practice questions")
    with get_connection() as connection:
        row = connection.execute("SELECT mastery_score FROM student_mastery WHERE user_id = ? AND skill_id = ?", (user["id"], question["skill_id"])).fetchone()
        recent = connection.execute("SELECT correct FROM attempts WHERE user_id = ? AND skill_id = ? ORDER BY id DESC LIMIT 3", (user["id"], question["skill_id"])).fetchall()
    previous = float(row["mastery_score"]) if row else 0.5
    recent_correct = sum(int(item["correct"]) for item in recent)
    recent_incorrect = len(recent) - recent_correct
    result = practice_graph.invoke({"user_id": user["id"], "question_id": question["question_id"], "skill_id": question["skill_id"], "difficulty": question["difficulty"], "expected_answer": question["answer"], "student_answer": payload.student_answer, "hints_used": payload.hints_used, "previous_mastery": previous, "recent_correct": recent_correct, "recent_incorrect": recent_incorrect})
    selected = payload.selected_difficulty or result["recommended_difficulty"]
    with get_connection() as connection:
        connection.execute("INSERT INTO attempts (user_id, question_id, skill_id, difficulty, student_answer, expected_answer, correct, hints_used, recommended_difficulty, selected_difficulty, difficulty_overridden, session_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user["id"], question["question_id"], question["skill_id"], question["difficulty"], payload.student_answer, question["answer"], int(result["is_correct"]), payload.hints_used, result["recommended_difficulty"], selected, int(selected != result["recommended_difficulty"]), payload.session_id))
        connection.execute("INSERT INTO student_mastery (user_id, skill_id, mastery_score, current_difficulty) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, skill_id) DO UPDATE SET mastery_score=excluded.mastery_score, current_difficulty=excluded.current_difficulty, updated_at=CURRENT_TIMESTAMP", (user["id"], question["skill_id"], result["mastery_score"], selected))
        if payload.session_id is not None:
            updated = connection.execute("UPDATE learning_sessions SET questions_attempted = questions_attempted + 1, questions_correct = questions_correct + ?, mastery_end = ? WHERE id = ? AND user_id = ? AND ended_at IS NULL", (int(result["is_correct"]), result["mastery_score"], payload.session_id, user["id"])).rowcount
            if not updated:
                raise HTTPException(status_code=404, detail="Practice session is not active")
    return {"correct": result["is_correct"], "mastery": result["mastery_score"], "recommended_action": result["recommended_action"], "recommended_difficulty": result["recommended_difficulty"], "selected_difficulty": selected, "difficulty_overridden": selected != result["recommended_difficulty"], "feedback": result["response"], "session_id": payload.session_id}


@router.post("/practice/session/{session_id}/end")
def end_practice_session(session_id: int, user: dict = Depends(current_user)) -> dict:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM learning_sessions WHERE id = ? AND user_id = ?", (session_id, user["id"])).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Practice session not found")
        if row["ended_at"] is None:
            connection.execute("UPDATE learning_sessions SET ended_at = CURRENT_TIMESTAMP, mastery_end = COALESCE(mastery_end, mastery_start) WHERE id = ?", (session_id,))
        final = connection.execute("SELECT * FROM learning_sessions WHERE id = ?", (session_id,)).fetchone()
    return {"session_id": session_id, "topic": final["topic"], "questions_attempted": final["questions_attempted"], "questions_correct": final["questions_correct"], "mastery_start": final["mastery_start"], "mastery_end": final["mastery_end"], "ended_at": final["ended_at"], "progress_saved": True}


@router.post("/practice/difficulty")
def override_difficulty(payload: DifficultyOverride, user: dict = Depends(current_user)) -> dict:
    question = _question(payload.question_id, user["id"])
    with get_connection() as connection:
        attempt = connection.execute("SELECT id, recommended_difficulty FROM attempts WHERE user_id = ? AND question_id = ? ORDER BY id DESC LIMIT 1", (user["id"], payload.question_id)).fetchone()
        if attempt is None:
            raise HTTPException(status_code=404, detail="Submit an answer before changing difficulty")
        overridden = payload.selected_difficulty != attempt["recommended_difficulty"]
        connection.execute("UPDATE attempts SET selected_difficulty = ?, difficulty_overridden = ? WHERE id = ?", (payload.selected_difficulty, int(overridden), attempt["id"]))
        connection.execute("UPDATE student_mastery SET current_difficulty = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND skill_id = ?", (payload.selected_difficulty, user["id"], question["skill_id"]))
    return {"selected_difficulty": payload.selected_difficulty, "recommended_difficulty": attempt["recommended_difficulty"], "difficulty_overridden": overridden}


@router.get("/progress")
def progress(user: dict = Depends(current_user)) -> dict:
    with get_connection() as connection:
        rows = connection.execute("SELECT skill_id, mastery_score, current_difficulty, updated_at FROM student_mastery WHERE user_id = ? ORDER BY skill_id", (user["id"],)).fetchall()
    return {"skills": [dict(row) for row in rows], "overall_mastery": round(sum(row["mastery_score"] for row in rows) / len(rows), 4) if rows else 0.0}
