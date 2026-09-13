import secrets
from fastapi.testclient import TestClient
from app.main import app
from app.rag.ingest import load_questions

client = TestClient(app)


def answer_lookup() -> dict[str, str]:
    return {item["question_id"]: item["answer"] for item in load_questions()}


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
    answers = answer_lookup()
    results = []
    for question in started.json()["questions"]:
        assert "answer" not in question and "solution" not in question
        results.append(client.post("/diagnostic/answer", headers=headers, json={"question_id": question["question_id"], "student_answer": answers[question["question_id"]]}).json())
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
    answers = answer_lookup()
    for item in questions:
        client.post("/diagnostic/answer", headers=headers, json={"question_id": item["question_id"], "student_answer": answers[item["question_id"]]})
    after = client.get("/diagnostic/status", headers=headers, params={"topic": "Factorisation"}).json()
    assert after["complete"] is True and after["answered"] == 5


def test_every_topic_has_a_separate_five_question_diagnostic(tmp_path, monkeypatch) -> None:
    from app.db import database
    path = tmp_path / "all-topics.db"
    monkeypatch.setattr(database, "database_path", lambda: path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    client.post("/auth/register", json={"username": "all_topics", "password": password})
    token = client.post("/auth/login", json={"username": "all_topics", "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    for topic in ["Factorisation", "Expansion", "Linear equations", "Quadratics"]:
        response = client.post("/diagnostic/start", headers=headers, json={"topic": topic})
        assert response.status_code == 200
        assert response.json()["difficulty_sequence"] == [1, 2, 3, 4, 5]
        assert all(item.get("usage") == "diagnostic" for item in response.json()["questions"])
