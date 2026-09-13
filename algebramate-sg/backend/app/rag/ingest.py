from __future__ import annotations

from .chroma import get_questions_collection
from .schemas import load_questions_validated


def load_questions() -> list[dict]:
    return [question.model_dump() for question in load_questions_validated()]


def ingest_questions() -> int:
    collection = get_questions_collection()
    questions = load_questions()
    approved_ids = {question["question_id"] for question in questions}
    existing_ids = set(collection.get().get("ids", []))
    stale_ids = sorted(existing_ids - approved_ids)
    if stale_ids:
        collection.delete(ids=stale_ids)
    for question in questions:
        document = " ".join([
            question["question"], question["topic"], question["subtopic"],
            question["skill_id"], question["learning_objective"],
            " ".join(question["misconceptions"]),
        ])
        metadata = {key: question[key] for key in ["school_level", "topic", "subtopic", "skill_id", "difficulty", "usage"]}
        metadata["content_type"] = "question"
        collection.upsert(ids=[question["question_id"]], documents=[document], metadatas=[metadata])
    return len(questions)


if __name__ == "__main__":
    print(f"Ingested {ingest_questions()} approved questions into ChromaDB")
