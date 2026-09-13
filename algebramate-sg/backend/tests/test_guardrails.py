import pytest
from app.guardrails.guards import bounded_retry, hint_is_safe, validate_topic, verify_generated_question


def test_input_and_hint_guards() -> None:
    assert validate_topic("Factorisation") == "Factorisation"
    with pytest.raises(ValueError): validate_topic("Unsupported")
    assert hint_is_safe("Look at the common factor first.", "6(x+2)")
    assert not hint_is_safe("The final answer is 6(x+2)", "6(x+2)")


def test_generated_question_validation_and_bounded_retry() -> None:
    invalid = {"topic": "Factorisation", "difficulty": 9, "question": "bad", "answer": "x", "solution": "bad", "skill_id": "factorisation.common_factor"}
    valid = {"topic": "Factorisation", "difficulty": 3, "question": "Factorise x^2+5x+6", "answer": "(x+2)(x+3)", "solution": "Find the factor pair.", "skill_id": "factorisation.quadratic_trinomial"}
    assert not verify_generated_question(invalid)
    assert bounded_retry([invalid, valid]) == valid
    assert bounded_retry([invalid], max_retries=1) is None
