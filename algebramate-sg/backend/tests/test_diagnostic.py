import secrets
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_five_question_diagnostic_scores_and_persists(tmp_path, monkeypatch) -> None:
    from app.db import database
    path = tmp_path / "diagnostic.db"
    monkeypatch.setattr(database, "database_path", lambda: path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    client.post("/auth/register", json={"username": "diagnostic", "password": password})
    token = client.post("/auth/login", json={"username": "diagnostic", "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    started = client.post("/diagnostic/start", headers=headers, json={"topic": "Factorisation"})
    assert started.status_code == 200
    assert started.json()["total"] == 5
    assert started.json()["difficulty_sequence"] == [1, 2, 3, 4, 5]
    results = []
    for question in started.json()["questions"]:
        results.append(client.post("/diagnostic/answer", headers=headers, json={"question_id": question["question_id"], "student_answer": question["answer"]}).json())
    assert results[-1]["complete"] is True
    assert results[-1]["raw_score"] == 5
    assert results[-1]["initial_mastery"] == 1.0
    assert results[-1]["recommended_starting_difficulty"] == 5
    with database.get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM diagnostic_answers").fetchone()[0] == 5
        assert connection.execute("SELECT COUNT(*) FROM diagnostic_results").fetchone()[0] == 1


def test_diagnostic_status_reports_completion(tmp_path, monkeypatch) -> None:
    from app.db import database
    path = tmp_path / "status.db"
    monkeypatch.setattr(database, "database_path", lambda: path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    client.post("/auth/register", json={"username": "status_user", "password": password})
    token = client.post("/auth/login", json={"username": "status_user", "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    before = client.get("/diagnostic/status", headers=headers, params={"topic": "Factorisation"}).json()
    assert before["complete"] is False and before["answered"] == 0
    questions = client.post("/diagnostic/start", headers=headers, json={"topic": "Factorisation"}).json()["questions"]
    for item in questions:
        client.post("/diagnostic/answer", headers=headers, json={"question_id": item["question_id"], "student_answer": item["answer"]})
    after = client.get("/diagnostic/status", headers=headers, params={"topic": "Factorisation"}).json()
    assert after["complete"] is True and after["answered"] == 5
