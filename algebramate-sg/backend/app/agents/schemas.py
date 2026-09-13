from typing import Literal
from pydantic import BaseModel, Field


class RouterOutput(BaseModel):
    intent: Literal["start_topic", "start_diagnostic", "submit_answer", "request_hint", "request_explanation", "request_visualisation", "request_analogy", "request_next_question", "review_progress"]
    confidence: float = Field(ge=0, le=1)


class MisconceptionOutput(BaseModel):
    misconception: Literal["sign_error", "distribution_error", "missing_cross_terms", "incorrect_factor_pair", "equation_balance_error", "arithmetic_error", "inverse_operation_error", "denominator_error", "incomplete_factorisation", "wrong_root_sign", "prerequisite_gap", "concept_unknown", "uncertain"]
    confidence: float = Field(ge=0, le=1)
    explanation: str = Field(min_length=1, max_length=500)


class HintOutput(BaseModel):
    hint_level: int = Field(ge=1, le=3)
    hint: str = Field(min_length=1, max_length=500)
    reveals_final_answer: bool = False


class ExplanationOutput(BaseModel):
    explanation: str = Field(min_length=1, max_length=1500)
    worked_example: str = Field(min_length=1, max_length=500)
    quick_check: str = Field(min_length=1, max_length=500)


class VisualisationOutput(BaseModel):
    visual_type: Literal["algebra_frame", "algebra_tiles", "number_line", "function_graph"]
    spec: dict
