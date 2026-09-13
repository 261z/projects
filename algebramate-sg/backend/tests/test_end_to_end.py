import secrets
from fastapi.testclient import TestClient
from app.main import app

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
    diagnostic = client.post("/diagnostic/start", headers=headers, json={"topic": "Factorisation"}).json()
    for item in diagnostic["questions"]:
        response = client.post("/diagnostic/answer", headers=headers, json={"question_id": item["question_id"], "student_answer": item["answer"]})
    assert response.json()["complete"] is True
    started = client.post("/practice/start", headers=headers, json={"topic": "Factorisation", "skill_id": "factorisation.quadratic_trinomial", "difficulty": 3}).json()
    assert started["retrieval"] == "chroma"
    wrong = client.post("/practice/answer", headers=headers, json={"question_id": "S2-FAC-Q001", "student_answer": "(x+1)(x+6)", "selected_difficulty": 4}).json()
    assert wrong["correct"] is False and wrong["difficulty_overridden"] is True
    assert client.post("/practice/hint", headers=headers, json={"question_id": "S2-FAC-Q001", "hint_level": 1}).status_code == 200
    correct = client.post("/practice/answer", headers=headers, json={"question_id": "S2-FAC-Q001", "student_answer": "(x+2)(x+3)"}).json()
    assert correct["correct"] is True
    assert client.get("/progress", headers=headers).json()["skills"]
    client.post("/auth/logout", headers=headers)
    relogin = client.post("/auth/login", json={"username": "student1", "password": password}).json()["access_token"]
    assert client.get("/progress", headers={"Authorization": f"Bearer {relogin}"}).json()["skills"]
