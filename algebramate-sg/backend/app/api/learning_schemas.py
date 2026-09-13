from pydantic import BaseModel, ConfigDict, Field


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DiagnosticStart(StrictRequest):
    topic: str = Field(min_length=1, max_length=80)


class DiagnosticAnswer(StrictRequest):
    question_id: str = Field(min_length=3, max_length=120)
    student_answer: str = Field(min_length=1, max_length=500)


class PracticeStart(StrictRequest):
    topic: str = Field(min_length=1, max_length=80)
    skill_id: str | None = Field(default=None, min_length=3, max_length=120)
    difficulty: int = Field(default=2, ge=1, le=5)
    exclude_question_ids: list[str] = Field(default_factory=list, max_length=200)
    session_id: int | None = Field(default=None, ge=1)


class PracticeAnswer(StrictRequest):
    question_id: str = Field(min_length=3, max_length=120)
    student_answer: str = Field(min_length=1, max_length=500)
    selected_difficulty: int | None = Field(default=None, ge=1, le=5)
    hints_used: int = Field(default=0, ge=0, le=3)
    session_id: int | None = Field(default=None, ge=1)


class DifficultyOverride(StrictRequest):
    question_id: str = Field(min_length=3, max_length=120)
    selected_difficulty: int = Field(ge=1, le=5)


class SupportRequest(StrictRequest):
    question_id: str = Field(min_length=3, max_length=120)
    hint_level: int = Field(default=1, ge=1, le=3)
