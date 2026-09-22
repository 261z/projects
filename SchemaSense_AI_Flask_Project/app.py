from __future__ import annotations

import os
import threading
import uuid
from collections import defaultdict

from flask import Flask, jsonify, render_template, request, session

from src.agent import SchemaAnalysisAgent
from src.config import get_settings


def create_app(agent: SchemaAnalysisAgent | None = None) -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-development-change-me")
    app.config["JSON_SORT_KEYS"] = False

    memory: dict[str, list[dict]] = defaultdict(list)
    memory_lock = threading.Lock()
    agent_holder: dict[str, SchemaAnalysisAgent] = {}

    def session_id() -> str:
        if "session_id" not in session:
            session["session_id"] = str(uuid.uuid4())
        return session["session_id"]

    def active_agent() -> SchemaAnalysisAgent:
        if agent is not None:
            return agent
        if "agent" not in agent_holder:
            agent_holder["agent"] = SchemaAnalysisAgent(get_settings())
        return agent_holder["agent"]

    @app.get("/")
    def index():
        settings = get_settings()
        return render_template(
            "index.html",
            model_name=settings.openai_chat_model,
            namespace=settings.pinecone_namespace,
        )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/api/chat")
    def chat():
        payload = request.get_json(silent=True) or {}
        user_message = str(payload.get("message", "")).strip()
        if not user_message:
            return jsonify({"error": "Please enter a metadata question."}), 400

        identifier = session_id()
        with memory_lock:
            history = list(memory[identifier][-10:])

        try:
            result = active_agent().invoke(user_message, history)
            answer = result.get("final_answer") or "No grounded answer was produced."
            with memory_lock:
                memory[identifier].extend(
                    [
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": answer},
                    ]
                )
                memory[identifier] = memory[identifier][-12:]

            return jsonify(
                {
                    "answer": answer,
                    "diagram": result.get("diagram"),
                    "sources": result.get("sources", []),
                    "tool_trace": result.get("tool_trace", []),
                }
            )
        except Exception as exc:
            app.logger.exception("SchemaSense chat request failed")
            return (
                jsonify(
                    {
                        "error": (
                            "SchemaSense could not complete the request. Check the API keys, "
                            "Pinecone ingestion, index name, and namespace."
                        ),
                        "error_type": type(exc).__name__,
                    }
                ),
                500,
            )

    @app.post("/api/clear")
    def clear_chat():
        identifier = session_id()
        with memory_lock:
            memory.pop(identifier, None)
        return jsonify({"status": "cleared"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

