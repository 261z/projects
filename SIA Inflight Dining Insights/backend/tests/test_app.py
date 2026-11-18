import io
from app.server import app
from app.analytics import analyze_batch

def test_analysis_health_and_flags():
    result = analyze_batch([{"review_id": "x", "review": "Delicious but I have a peanut allergy and the label was unclear."}])
    assert result["kpis"]["total_reviews"] == 1
    assert result["kpis"]["safety_flag_count"] == 1
    assert result["rows"][0]["sentiment"] in {"positive", "neutral"}

def test_sample_and_analyze_api():
    client = app.test_client()
    response = client.get("/api/samples/a")
    assert response.status_code == 200
    assert len(response.get_json()["reviews"]) == 1
    response = client.post("/api/analyze", json={"reviews": response.get_json()["reviews"]})
    assert response.status_code == 200
    assert response.get_json()["kpis"]["total_reviews"] == 1

def test_export_is_xlsx():
    client = app.test_client()
    response = client.post("/api/export", json={"rows": [{"review_id": "x", "review": "good", "topics": ["flavour"]}], "kpis": {"total_reviews": 1}})
    assert response.status_code == 200
    assert response.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert response.data[:2] == b"PK"
