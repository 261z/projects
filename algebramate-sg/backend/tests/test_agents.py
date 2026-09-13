import asyncio

from app.agents.schemas import HintOutput, MisconceptionOutput, RouterOutput
from app.agents.structured import diagnose_misconception, explain_structured, route_intent, scaffold_hint


def test_structured_agent_outputs_validate() -> None:
    assert isinstance(route_intent("please give me a hint"), RouterOutput)
    question = {"skill_id": "expansion.double_bracket", "question": "Expand (x+2)(x+3).", "solution": "Multiply every term."}
    assert isinstance(diagnose_misconception(question, "x^2+6"), MisconceptionOutput)
    assert isinstance(scaffold_hint(question, 2), HintOutput)
    explanation = asyncio.run(explain_structured(question))
    assert explanation.explanation
