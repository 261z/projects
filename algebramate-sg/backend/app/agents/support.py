from __future__ import annotations

from ..llm.provider import AgentRouterUnavailable, chat


def hint_for(question: dict, level: int) -> str:
    if level == 1: return "What operation or pattern is at the centre of this question?"
    if level == 2: return question.get("solution", "Break the question into one small step at a time.")
    return "Try the first step now, then check whether both sides or every term have been treated consistently."


def visual_spec(question: dict) -> dict:
    return {"visual_type": "algebra_frame", "mode": "factorisation" if "factor" in question["skill_id"] else "expansion", "expression": question["question"], "interactive": False}


async def explain(question: dict, mode: str) -> dict:
    prompt = "Give a short, age-appropriate explanation" if mode == "explain" else "Give a mathematically accurate everyday analogy"
    try:
        text = await chat([{"role": "system", "content": "You are a careful Singapore secondary algebra tutor. Do not invent facts."}, {"role": "user", "content": f"{prompt} for: {question['question']} Expected method: {question['solution']}"}], task="primary")
        return {"text": text, "source": "agent_router", "model": "PRIMARY_MODEL"}
    except AgentRouterUnavailable:
        return {"text": f"{question['solution']} Start by identifying the structure, then apply one operation to each relevant term.", "source": "deterministic_fallback", "model": None}
