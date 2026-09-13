import secrets
from fastapi.testclient import TestClient
from app.main import app
from app.rag.ingest import load_questions

client = TestClient(app)


def test_complete_demo_flow(tmp_path, monkeypatch) -> None:
    from app.db import database
    path = tmp_path / "e2e.db"
    monkeypatch.setattr(database, "database_path", lambda: path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    assert client.post("/auth/register", json={"username": "student1", "password": password}).status_code == 201
    token = client.post("/auth/login", json={"username": "student1", "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    answers = {item["question_id"]: item["answer"] for item in load_questions()}
    diagnostic = client.post("/diagnostic/start", headers=headers, json={"topic": "Factorisation"}).json()
    for item in diagnostic["questions"]:
        assert "answer" not in item
        response = client.post("/diagnostic/answer", headers=headers, json={"question_id": item["question_id"], "student_answer": answers[item["question_id"]]})
    assert response.json()["complete"] is True
    started = client.post("/practice/start", headers=headers, json={"topic": "Factorisation", "skill_id": "factorisation.quadratic_trinomial", "difficulty": 3}).json()
    assert started["retrieval"] == "chroma_approved"
    assert "answer" not in started["question"] and "solution" not in started["question"]
    qid = started["question"]["question_id"]
    session_id = started["session_id"]
    wrong = client.post("/practice/answer", headers=headers, json={"question_id": qid, "student_answer": "(x+1)(x+6)", "session_id": session_id}).json()
    assert wrong["correct"] is False
    assert client.post("/practice/hint", headers=headers, json={"question_id": qid, "hint_level": 1}).status_code == 200
    correct = client.post("/practice/answer", headers=headers, json={"question_id": qid, "student_answer": answers[qid], "session_id": session_id}).json()
    assert correct["correct"] is True
    override = client.post("/practice/difficulty", headers=headers, json={"question_id": qid, "selected_difficulty": 4}).json()
    assert override["selected_difficulty"] == 4
    summary = client.post(f"/practice/session/{session_id}/end", headers=headers).json()
    assert summary["progress_saved"] is True and summary["questions_attempted"] == 2
    assert client.get("/progress", headers=headers).json()["skills"]
    client.post("/auth/logout", headers=headers)
    relogin = client.post("/auth/login", json={"username": "student1", "password": password}).json()["access_token"]
    assert client.get("/progress", headers={"Authorization": f"Bearer {relogin}"}).json()["skills"]
