import secrets
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import pwd_context

client = TestClient(app)


def test_register_login_and_me(tmp_path, monkeypatch) -> None:
    from app.db import database
    db_path = tmp_path / "auth.db"
    monkeypatch.setattr(database, "database_path", lambda: db_path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    registered = client.post("/auth/register", json={"username": "student1", "password": password})
    assert registered.status_code == 201
    assert registered.json()["username"] == "student1"
    with database.get_connection() as connection:
        row = connection.execute("SELECT password_hash FROM users WHERE username = 'student1'").fetchone()
    assert row is not None
    assert row["password_hash"] != password
    assert pwd_context.verify(password, row["password_hash"])
    duplicate = client.post("/auth/register", json={"username": "student1", "password": secrets.token_urlsafe(24)})
    assert duplicate.status_code == 409
    login = client.post("/auth/login", json={"username": "student1", "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "student1"
    assert client.get("/auth/me").status_code == 401
