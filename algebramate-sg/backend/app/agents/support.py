from __future__ import annotations

from ..llm.provider import AgentRouterUnavailable, chat


def hint_for(question: dict, level: int) -> str:
    if level == 1: return "What operation or pattern is at the centre of this question?"
    if "factorisation" in question["skill_id"]:
        if level == 2: return "Find two integers whose product is the constant term and whose sum is the coefficient of x."
        return "Write the two bracket factors using your pair, then expand them to check the original expression."
    if level == 2: return "Break the expression into one small step at a time and keep every term visible."
    return "Try the first step now, then check whether every term has been treated consistently."


def visual_spec(question: dict) -> dict:
    is_factorisation = "factor" in question["skill_id"]
    spec = {"visual_type": "algebra_frame", "mode": "factorisation" if is_factorisation else "expansion", "expression": question["question"], "answer": question["answer"], "interactive": False}
    if is_factorisation:
        spec["representation"] = "factor_pair"
        spec["factor_pair"] = {"product": "-12", "sum": "-1", "numbers": ["-4", "3"]} if "- x - 12" in question["question"] else None
    return spec


async def explain(question: dict, mode: str) -> dict:
    prompt = "Give a short, age-appropriate explanation" if mode == "explain" else "Give a mathematically accurate everyday analogy"
    try:
        text = await chat([{"role": "system", "content": "You are a careful Singapore secondary algebra tutor. Do not invent facts."}, {"role": "user", "content": f"{prompt} for: {question['question']} Expected method: {question['solution']}"}], task="primary")
        return {"text": text, "source": "agent_router", "model": "PRIMARY_MODEL"}
    except AgentRouterUnavailable:
        return {"text": f"{question['solution']} Start by identifying the structure, then apply one operation to each relevant term.", "source": "deterministic_fallback", "model": None}
