from __future__ import annotations

import json
from pathlib import Path

from .chroma import get_questions_collection


def load_questions() -> list[dict]:
    path = Path(__file__).resolve().parents[2] / "data" / "questions.json"
    return json.loads(path.read_text())


def ingest_questions() -> int:
    collection = get_questions_collection()
    questions = load_questions()
    for question in questions:
        document = " ".join([
            question["question"], question["topic"], question["subtopic"],
            question["skill_id"], question["learning_objective"],
            " ".join(question["misconceptions"]),
        ])
        metadata = {key: question[key] for key in ["school_level", "topic", "subtopic", "skill_id", "difficulty"]}
        metadata["content_type"] = "question"
        collection.upsert(ids=[question["question_id"]], documents=[document], metadatas=[metadata])
    return len(questions)


if __name__ == "__main__":
    print(f"Ingested {ingest_questions()} approved questions into ChromaDB")
