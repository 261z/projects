import secrets
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_users_are_isolated_bidirectionally(tmp_path, monkeypatch) -> None:
    from app.db import database
    path = tmp_path / "users.db"
    monkeypatch.setattr(database, "database_path", lambda: path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    for username in ["student_a", "student_b"]:
        client.post("/auth/register", json={"username": username, "password": password})
    tokens = [client.post("/auth/login", json={"username": u, "password": password}).json()["access_token"] for u in ["student_a", "student_b"]]
    headers_a = {"Authorization": f"Bearer {tokens[0]}"}
    headers_b = {"Authorization": f"Bearer {tokens[1]}"}
    client.post("/practice/answer", headers=headers_a, json={"question_id": "P-FAC-003", "student_answer": "(x+3)(x+4)"})
    assert client.get("/progress", headers=headers_b).json()["skills"] == []
    client.post("/practice/answer", headers=headers_b, json={"question_id": "P-EXP-001", "student_answer": "5x+10"})
    skills_a = client.get("/progress", headers=headers_a).json()["skills"]
    skills_b = client.get("/progress", headers=headers_b).json()["skills"]
    assert [item["skill_id"] for item in skills_a] == ["factorisation.quadratic_trinomial"]
    assert [item["skill_id"] for item in skills_b] == ["expansion.single_bracket"]
    with database.get_connection() as connection:
        counts = connection.execute("SELECT user_id, COUNT(*) AS count FROM attempts GROUP BY user_id ORDER BY user_id").fetchall()
    assert [row["count"] for row in counts] == [1, 1]


def test_persistence_survives_reinitialisation(tmp_path, monkeypatch) -> None:
    from app.db import database
    path = tmp_path / "restart.db"
    monkeypatch.setattr(database, "database_path", lambda: path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    client.post("/auth/register", json={"username": "persistent", "password": password})
    token = client.post("/auth/login", json={"username": "persistent", "password": password}).json()["access_token"]
    client.post("/practice/answer", headers={"Authorization": f"Bearer {token}"}, json={"question_id": "P-FAC-003", "student_answer": "(x+3)(x+4)"})
    database.init_db()
    new_token = client.post("/auth/login", json={"username": "persistent", "password": password}).json()["access_token"]
    assert client.get("/progress", headers={"Authorization": f"Bearer {new_token}"}).json()["skills"]
    with database.get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 1
