from __future__ import annotations

import logging
import re

from ..guardrails.guards import hint_is_safe
from ..llm.provider import AgentRouterUnavailable, chat

logger = logging.getLogger(__name__)


def hint_for(question: dict, level: int) -> str:
    if level == 1:
        return "What operation or pattern is at the centre of this question?"
    if "factorisation" in question["skill_id"]:
        if level == 2:
            return "Identify the factorisation pattern and the values that must combine to reproduce the original terms."
        return "Write a tentative factor form, then expand it to check every original term before submitting."
    if "expansion" in question["skill_id"]:
        return "Distribute systematically and keep every partial product visible before collecting like terms."
    if "linear_equations" in question["skill_id"]:
        return "Use the same inverse operation on both sides, one step at a time."
    return "Factorise first, then use the zero-product rule without skipping either factor."


def visual_spec(question: dict) -> dict:
    prompt = question["question"]
    if "factorisation" in question["skill_id"]:
        product_match = re.search(r"([+-]\s*\d+)\.?$", prompt.replace("−", "-"))
        middle_match = re.search(r"x\^?2\s*([+-]\s*(?:\d+)?)x", prompt.replace("²", "^2").replace("−", "-"))
        return {"visual_type": "algebra_frame", "mode": "factorisation", "expression": prompt, "interactive": True, "product_target": product_match.group(1).replace(" ", "") if product_match else None, "sum_target": middle_match.group(1).replace(" ", "") if middle_match else None, "reveal_answer": False}
    if "expansion" in question["skill_id"]:
        return {"visual_type": "algebra_frame", "mode": "expansion", "expression": prompt, "interactive": True, "cells": ["?", "?", "?", "?"], "reveal_answer": False}
    if "linear_equations" in question["skill_id"]:
        return {"visual_type": "number_line", "mode": "equation", "expression": prompt, "interactive": True, "reveal_answer": False}
    return {"visual_type": "function_graph", "mode": "roots", "expression": prompt, "interactive": True, "reveal_answer": False}


async def explain(question: dict, mode: str) -> dict:
    prompt = "Give a short method explanation without revealing the final answer" if mode == "explain" else "Give an age-appropriate analogy, explicit mathematical mapping, a different worked example, and a quick-check question; never reveal the answer to the active question"
    try:
        text = await chat([{"role": "system", "content": "You are a careful Singapore secondary algebra tutor. Never reveal the final answer to the active question."}, {"role": "user", "content": f"{prompt}. Active question: {question['question']}. Skill: {question['skill_id']}"}], task="explanation")
        if not hint_is_safe(text, question["answer"]):
            raise AgentRouterUnavailable("Unsafe explanation was rejected")
        return {"text": text, "source": "agent_router", "model": "PRIMARY_MODEL"}
    except AgentRouterUnavailable:
        logger.info("[explanation] source=deterministic_fallback mode=%s", mode)
        return {"text": hint_for(question, 2) + " Try a simpler example first, then return to this question.", "source": "deterministic_fallback", "model": None}
