from pydantic import BaseModel, Field


class DiagnosticStart(BaseModel):
    topic: str = Field(min_length=1, max_length=80)


class DiagnosticAnswer(BaseModel):
    question_id: str
    student_answer: str = Field(max_length=500)


class PracticeStart(BaseModel):
    topic: str = Field(min_length=1, max_length=80)
    skill_id: str | None = None
    difficulty: int = Field(default=2, ge=1, le=5)
    exclude_question_ids: list[str] = Field(default_factory=list, max_length=50)


class PracticeAnswer(BaseModel):
    question_id: str
    student_answer: str = Field(max_length=500)
    selected_difficulty: int | None = Field(default=None, ge=1, le=5)
    hints_used: int = Field(default=0, ge=0, le=3)


class SupportRequest(BaseModel):
    question_id: str
    hint_level: int = Field(default=1, ge=1, le=3)
