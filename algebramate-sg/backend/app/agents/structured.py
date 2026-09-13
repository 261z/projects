from __future__ import annotations

import json

from .schemas import ExplanationOutput, HintOutput, MisconceptionOutput, RouterOutput
from ..llm.provider import AgentRouterUnavailable, chat


def route_intent(text: str) -> RouterOutput:
    lowered = text.lower()
    if "hint" in lowered: intent = "request_hint"
    elif "visual" in lowered or "show" in lowered: intent = "request_visualisation"
    elif "analogy" in lowered or "story" in lowered: intent = "request_analogy"
    elif "explain" in lowered: intent = "request_explanation"
    elif "progress" in lowered: intent = "review_progress"
    else: intent = "submit_answer"
    return RouterOutput(intent=intent, confidence=0.82)


def diagnose_misconception(question: dict, student_answer: str) -> MisconceptionOutput:
    if "double_bracket" in question["skill_id"] and "x" not in student_answer:
        return MisconceptionOutput(misconception="missing_cross_terms", confidence=0.76, explanation="The response appears to omit the cross terms created when both brackets are multiplied.")
    if "factorisation" in question["skill_id"] and "-" in question["answer"] and "+" not in student_answer:
        return MisconceptionOutput(misconception="sign_error", confidence=0.61, explanation="The signs in the factor pair may not match the original expression.")
    return MisconceptionOutput(misconception="uncertain", confidence=0.35, explanation="The error needs another attempt before a specific misconception can be identified.")


def scaffold_hint(question: dict, level: int) -> HintOutput:
    if level == 1: text = "What structure or operation is this question asking you to recognise?"
    elif level == 2: text = "Find the pair of numbers that matches the required product and sum, without writing the final factorisation yet."
    else: text = "Write your two bracket factors, then expand them to check every term before submitting."
    return HintOutput(hint_level=level, hint=text, reveals_final_answer=False)


async def explain_structured(question: dict, analogy: bool = False) -> ExplanationOutput:
    instruction = "Use a mathematically accurate everyday analogy" if analogy else "Explain the method clearly"
    try:
        raw = await chat([{"role":"system","content":"Return JSON with explanation, worked_example, quick_check."},{"role":"user","content":f"{instruction}: {question['question']} Method: {question['solution']}"}], task="primary", json_mode=True)
        return ExplanationOutput.model_validate(json.loads(raw))
    except (AgentRouterUnavailable, ValueError, json.JSONDecodeError):
        return ExplanationOutput(explanation=question["solution"], worked_example=question["question"], quick_check="Try the same method on a similar expression.")
