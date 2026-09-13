import secrets
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_support_endpoints_have_guarded_fallbacks(tmp_path, monkeypatch) -> None:
    from app.db import database
    path = tmp_path / "support.db"
    monkeypatch.setattr(database, "database_path", lambda: path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    client.post("/auth/register", json={"username": "supporter", "password": password})
    token = client.post("/auth/login", json={"username": "supporter", "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"question_id": "S2-FAC-Q001", "hint_level": 2}
    hint = client.post("/practice/hint", headers=headers, json=payload)
    assert hint.status_code == 200 and hint.json()["guard"] == "approved"
    visual = client.post("/practice/visualise", headers=headers, json=payload)
    assert visual.json()["spec"]["visual_type"] == "algebra_frame"
    explanation = client.post("/practice/explain", headers=headers, json=payload)
    assert explanation.status_code == 200 and explanation.json()["text"]
