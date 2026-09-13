import secrets
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_users_are_isolated(tmp_path, monkeypatch) -> None:
    from app.db import database
    path = tmp_path / "users.db"
    monkeypatch.setattr(database, "database_path", lambda: path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    for username in ["student_a", "student_b"]:
        client.post("/auth/register", json={"username": username, "password": password})
    tokens = [client.post("/auth/login", json={"username": u, "password": password}).json()["access_token"] for u in ["student_a", "student_b"]]
    client.post("/practice/answer", headers={"Authorization": f"Bearer {tokens[0]}"}, json={"question_id": "S2-FAC-Q001", "student_answer": "(x+2)(x+3)"})
    assert client.get("/progress", headers={"Authorization": f"Bearer {tokens[1]}"}).json()["skills"] == []


def test_persistence_survives_reinitialisation(tmp_path, monkeypatch) -> None:
    from app.db import database
    path = tmp_path / "restart.db"
    monkeypatch.setattr(database, "database_path", lambda: path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    client.post("/auth/register", json={"username": "persistent", "password": password})
    token = client.post("/auth/login", json={"username": "persistent", "password": password}).json()["access_token"]
    client.post("/practice/answer", headers={"Authorization": f"Bearer {token}"}, json={"question_id": "S2-FAC-Q001", "student_answer": "(x+2)(x+3)"})
    database.init_db()
    new_token = client.post("/auth/login", json={"username": "persistent", "password": password}).json()["access_token"]
    assert client.get("/progress", headers={"Authorization": f"Bearer {new_token}"}).json()["skills"]
