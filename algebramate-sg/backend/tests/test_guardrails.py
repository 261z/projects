import pytest
from app.guardrails.guards import bounded_retry, hint_is_safe, validate_topic, verify_generated_question


def test_input_and_hint_guards() -> None:
    assert validate_topic("Factorisation") == "Factorisation"
    with pytest.raises(ValueError):
        validate_topic("Unsupported")
    assert hint_is_safe("Look at the common factor first.", "6(x+2)")
    assert not hint_is_safe("The final answer is 6(x+2)", "6(x+2)")


def test_generated_question_validation_and_bounded_retry() -> None:
    invalid = {"topic": "Factorisation", "difficulty": 9, "question": "bad", "answer": "x", "solution": "bad", "skill_id": "factorisation.common_factor"}
    valid = {"topic": "Factorisation", "subtopic": "Quadratic trinomial", "difficulty": 3, "question": "Factorise x^2+5x+6.", "answer": "(x+2)(x+3)", "solution": "Find two integers whose product is 6 and sum is 5.", "skill_id": "factorisation.quadratic_trinomial", "marks": 2, "learning_objective": "Factorise a monic quadratic."}
    wrong_answer = {**valid, "answer": "(x+1)(x+6)"}
    assert not verify_generated_question(invalid)
    assert not verify_generated_question(wrong_answer)
    assert bounded_retry([invalid, valid]) == valid
    assert bounded_retry([invalid], max_retries=1) is None
