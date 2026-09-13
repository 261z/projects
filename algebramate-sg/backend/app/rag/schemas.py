from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Topic = Literal["Factorisation", "Expansion", "Linear equations", "Quadratics"]
SchoolLevel = Literal["Secondary 1", "Secondary 2", "Secondary 3", "Secondary 4"]


class StrictContentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Skill(StrictContentModel):
    id: str = Field(pattern=r"^[a-z_]+\.[a-z0-9_]+$")
    topic: Topic
    subtopic: str = Field(min_length=2, max_length=100)
    school_level: SchoolLevel
    prerequisite_skill_id: str | None = None


class ApprovedQuestion(StrictContentModel):
    question_id: str = Field(min_length=5, max_length=120)
    usage: Literal["diagnostic", "practice"]
    school_level: SchoolLevel
    topic: Topic
    subtopic: str = Field(min_length=2, max_length=100)
    skill_id: str = Field(pattern=r"^[a-z_]+\.[a-z0-9_]+$")
    difficulty: int = Field(ge=1, le=5)
    question: str = Field(min_length=5, max_length=500)
    answer: str = Field(min_length=1, max_length=200)
    solution: str = Field(min_length=5, max_length=1000)
    marks: int = Field(ge=1, le=5)
    learning_objective: str = Field(min_length=5, max_length=300)
    misconceptions: list[str] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def topic_matches_skill(self) -> "ApprovedQuestion":
        expected_prefix = self.topic.lower().replace(" ", "_") + "."
        if not self.skill_id.startswith(expected_prefix):
            raise ValueError("skill_id does not match topic")
        return self


def data_path(filename: str) -> Path:
    return Path(__file__).resolve().parents[2] / "data" / filename


def load_skills_validated(path: Path | None = None) -> list[Skill]:
    raw = json.loads((path or data_path("skills.json")).read_text())
    skills = [Skill.model_validate(item) for item in raw]
    ids = [skill.id for skill in skills]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate skill ID")
    known = set(ids)
    for skill in skills:
        if skill.prerequisite_skill_id and skill.prerequisite_skill_id not in known:
            raise ValueError(f"Unknown prerequisite: {skill.prerequisite_skill_id}")
    return skills


def load_questions_validated(path: Path | None = None) -> list[ApprovedQuestion]:
    raw = json.loads((path or data_path("questions.json")).read_text())
    questions = [ApprovedQuestion.model_validate(item) for item in raw]
    ids = [question.question_id for question in questions]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate question ID")
    skills = {skill.id: skill for skill in load_skills_validated()}
    for question in questions:
        skill = skills.get(question.skill_id)
        if skill is None:
            raise ValueError(f"Unknown skill_id: {question.skill_id}")
        if skill.topic != question.topic:
            raise ValueError(f"Question topic does not match skill: {question.question_id}")
    diagnostics = {(question.topic, question.difficulty) for question in questions if question.usage == "diagnostic"}
    for topic in ["Factorisation", "Expansion", "Linear equations", "Quadratics"]:
        missing = set(range(1, 6)) - {difficulty for item_topic, difficulty in diagnostics if item_topic == topic}
        if missing:
            raise ValueError(f"Diagnostic coverage missing for {topic}: {sorted(missing)}")
    return questions


def validate_content() -> tuple[int, int]:
    return len(load_skills_validated()), len(load_questions_validated())


if __name__ == "__main__":
    skill_count, question_count = validate_content()
    print(f"Validated {skill_count} skills and {question_count} approved questions")
