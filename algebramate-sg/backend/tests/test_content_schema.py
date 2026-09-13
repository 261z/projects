import json

import pytest
from pydantic import ValidationError

from app.rag.schemas import ApprovedQuestion, load_questions_validated, load_skills_validated, validate_content


def test_content_bank_and_skill_hierarchy_validate() -> None:
    skill_count, question_count = validate_content()
    assert skill_count == 15
    assert question_count == 40
    skills = {skill.id: skill for skill in load_skills_validated()}
    questions = load_questions_validated()
    assert all(question.skill_id in skills for question in questions)
    for topic in ["Factorisation", "Expansion", "Linear equations", "Quadratics"]:
        diagnostic = [question for question in questions if question.topic == topic and question.usage == "diagnostic"]
        assert sorted(question.difficulty for question in diagnostic) == [1, 2, 3, 4, 5]


def test_question_schema_rejects_unknown_fields_and_invalid_difficulty() -> None:
    valid = load_questions_validated()[0].model_dump()
    with pytest.raises(ValidationError):
        ApprovedQuestion.model_validate({**valid, "difficulty": 6})
    with pytest.raises(ValidationError):
        ApprovedQuestion.model_validate({**valid, "unexpected": "blocked"})


def test_duplicate_question_ids_are_rejected(tmp_path) -> None:
    question = load_questions_validated()[0].model_dump()
    path = tmp_path / "duplicates.json"
    path.write_text(json.dumps([question, question]))
    with pytest.raises(ValueError, match="Duplicate question ID"):
        load_questions_validated(path)


def test_skills_are_seeded_into_sqlite(tmp_path, monkeypatch) -> None:
    from app.db import database
    path = tmp_path / "skills.db"
    monkeypatch.setattr(database, "database_path", lambda: path)
    database.init_db()
    with database.get_connection() as connection:
        rows = connection.execute("SELECT id, prerequisite_skill_id FROM skills").fetchall()
    assert len(rows) == 15
    assert any(row["prerequisite_skill_id"] for row in rows)
