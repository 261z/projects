from __future__ import annotations

from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from ..agents.generator import generate_verified_question_sync


class GenerationState(TypedDict, total=False):
    skill_id: str
    difficulty: int
    retry_count: int
    question: dict
    verification_status: str


def generate_node(state: GenerationState) -> GenerationState:
    question = generate_verified_question_sync(state["skill_id"], state["difficulty"], max_retries=3)
    return {**state, "question": question, "verification_status": "verified", "retry_count": state.get("retry_count", 0)}


def build_generation_graph():
    graph = StateGraph(GenerationState)
    graph.add_node("generate_and_verify", generate_node)
    graph.add_edge(START, "generate_and_verify")
    graph.add_edge("generate_and_verify", END)
    return graph.compile()


generation_graph = build_generation_graph()
