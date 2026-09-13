from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ..services.mastery_service import recommend_difficulty, update_mastery
from ..tools.sympy_checker import check_answer


class PracticeState(TypedDict, total=False):
    user_id: int
    question_id: str
    skill_id: str
    difficulty: int
    expected_answer: str
    student_answer: str
    hints_used: int
    previous_mastery: float
    recent_correct: int
    recent_incorrect: int
    misconception: str | None
    is_correct: bool
    mastery_score: float
    recommended_action: str
    recommended_difficulty: int
    response: str


def check_node(state: PracticeState) -> PracticeState:
    result = check_answer(state["student_answer"], state["expected_answer"])
    return {**state, "is_correct": result.correct, "response": result.message}


def adapt_node(state: PracticeState) -> PracticeState:
    mastery = update_mastery(state.get("previous_mastery", 0.5), state["is_correct"], state["difficulty"], state.get("hints_used", 0))
    recommendation = recommend_difficulty(state["difficulty"], state.get("recent_correct", 0) + int(state["is_correct"]), state.get("recent_incorrect", 0) + int(not state["is_correct"]), state.get("hints_used", 0), state.get("misconception"))
    return {**state, "mastery_score": mastery, "recommended_action": recommendation.action, "recommended_difficulty": recommendation.difficulty}


def build_practice_graph():
    graph = StateGraph(PracticeState)
    graph.add_node("answer_checker", check_node)
    graph.add_node("adaptive_learning", adapt_node)
    graph.add_edge(START, "answer_checker")
    graph.add_edge("answer_checker", "adaptive_learning")
    graph.add_edge("adaptive_learning", END)
    return graph.compile()


practice_graph = build_practice_graph()
