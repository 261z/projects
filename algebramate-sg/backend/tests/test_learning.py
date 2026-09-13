import secrets
from fastapi.testclient import TestClient
from app.main import app
from app.services.mastery_service import recommend_difficulty, update_mastery

client = TestClient(app)


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
    assert client.post("/auth/register", json={"username": "learner", "password": password}).status_code == 201
    token = client.post("/auth/login", json={"username": "learner", "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    started = client.post("/practice/start", headers=headers, json={"topic": "Factorisation", "skill_id": "factorisation.quadratic_trinomial", "difficulty": 3})
    assert started.status_code == 200
    answered = client.post("/practice/answer", headers=headers, json={"question_id": "S2-FAC-Q001", "student_answer": "(x+2)(x+3)"})
    assert answered.status_code == 200 and answered.json()["correct"] is True
    assert client.get("/progress", headers=headers).json()["skills"][0]["skill_id"] == "factorisation.quadratic_trinomial"
