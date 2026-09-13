import secrets
from fastapi.testclient import TestClient
from app.main import app
from app.rag.ingest import load_questions
from app.services.mastery_service import recommend_difficulty, update_mastery

client = TestClient(app)


def auth_headers(username: str, password: str) -> dict[str, str]:
    client.post("/auth/register", json={"username": username, "password": password})
    token = client.post("/auth/login", json={"username": username, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_mastery_is_clamped_and_adaptive_rules_are_deterministic() -> None:
    assert 0.0 <= update_mastery(0.99, True, 5, 0) <= 1.0
    assert 0.0 <= update_mastery(0.01, False, 5, 0) <= 1.0
    assert recommend_difficulty(2, 3, 0, 0).difficulty == 3
    assert recommend_difficulty(3, 0, 2, 0).difficulty == 2


def test_practice_persists_progress(tmp_path, monkeypatch) -> None:
    from app.db import database
    database_path = tmp_path / "learning.db"
    monkeypatch.setattr(database, "database_path", lambda: database_path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    headers = auth_headers("learner", password)
    started = client.post("/practice/start", headers=headers, json={"topic": "Factorisation", "skill_id": "factorisation.quadratic_trinomial", "difficulty": 3})
    assert started.status_code == 200
    question = started.json()["question"]
    answer = next(item["answer"] for item in load_questions() if item["question_id"] == question["question_id"])
    answered = client.post("/practice/answer", headers=headers, json={"question_id": question["question_id"], "student_answer": answer, "session_id": started.json()["session_id"]})
    assert answered.status_code == 200 and answered.json()["correct"] is True
    assert client.get("/progress", headers=headers).json()["skills"][0]["skill_id"] == "factorisation.quadratic_trinomial"


def test_practice_can_exclude_seen_question_and_generate_more(tmp_path, monkeypatch) -> None:
    from app.db import database
    database_path = tmp_path / "next-question.db"
    monkeypatch.setattr(database, "database_path", lambda: database_path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    headers = auth_headers("next_student", password)
    approved_ids = [item["question_id"] for item in load_questions() if item["topic"] == "Factorisation" and item["usage"] == "practice"]
    first = client.post("/practice/start", headers=headers, json={"topic": "Factorisation", "difficulty": 4}).json()
    generated = client.post("/practice/start", headers=headers, json={"topic": "Factorisation", "difficulty": 4, "exclude_question_ids": approved_ids, "session_id": first["session_id"]})
    assert generated.status_code == 200
    data = generated.json()
    assert data["question"]["question_id"] not in approved_ids
    assert data["retrieval"] in {"agent_router", "deterministic_verified_fallback"}
    assert "answer" not in data["question"]
    with database.get_connection() as connection:
        assert connection.execute("SELECT verification_status FROM generated_questions WHERE question_id = ?", (data["question"]["question_id"],)).fetchone()[0] == "verified"
    summary = client.post(f"/practice/session/{first['session_id']}/end", headers=headers).json()
    assert summary["progress_saved"] is True
