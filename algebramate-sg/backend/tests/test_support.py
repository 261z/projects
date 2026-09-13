import secrets
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_support_endpoints_have_guarded_answer_free_fallbacks(tmp_path, monkeypatch) -> None:
    from app.db import database
    path = tmp_path / "support.db"
    monkeypatch.setattr(database, "database_path", lambda: path)
    database.init_db()
    password = secrets.token_urlsafe(24)
    client.post("/auth/register", json={"username": "supporter", "password": password})
    token = client.post("/auth/login", json={"username": "supporter", "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"question_id": "P-FAC-004", "hint_level": 2}
    hint = client.post("/practice/hint", headers=headers, json=payload)
    assert hint.status_code == 200 and hint.json()["guard"] == "approved"
    assert "(x-5)(x+3)" not in hint.json()["hint"].replace(" ", "")
    visual = client.post("/practice/visualise", headers=headers, json=payload)
    spec = visual.json()["spec"]
    assert spec["visual_type"] == "algebra_frame"
    assert spec["mode"] == "factorisation"
    assert spec["product_target"] == "-15"
    assert spec["sum_target"] == "-2"
    assert spec["reveal_answer"] is False
    assert "answer" not in spec and "factor_pair" not in spec
    explanation = client.post("/practice/explain", headers=headers, json=payload)
    assert explanation.status_code == 200 and explanation.json()["text"]
