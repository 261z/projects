from app import create_app


class FakeAgent:
    def invoke(self, user_query, chat_history):
        return {
            "final_answer": f"Grounded answer for: {user_query}",
            "diagram": None,
            "sources": [{"qualified_name": "aviation.flights", "score": 0.91}],
            "tool_trace": [
                {
                    "tool": "search_metadata",
                    "status": "success",
                    "summary": "Retrieved one table.",
                }
            ],
        }


def test_homepage_and_health_endpoint():
    app = create_app(FakeAgent())
    app.config.update(TESTING=True, SECRET_KEY="test")
    client = app.test_client()
    assert client.get("/").status_code == 200
    assert client.get("/health").get_json() == {"status": "ok"}


def test_chat_and_clear_endpoints():
    app = create_app(FakeAgent())
    app.config.update(TESTING=True, SECRET_KEY="test")
    client = app.test_client()
    response = client.post("/api/chat", json={"message": "Tell me about flights"})
    assert response.status_code == 200
    assert response.get_json()["sources"][0]["qualified_name"] == "aviation.flights"
    assert client.post("/api/clear").get_json() == {"status": "cleared"}


def test_empty_chat_message_is_rejected():
    app = create_app(FakeAgent())
    app.config.update(TESTING=True, SECRET_KEY="test")
    client = app.test_client()
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 400

