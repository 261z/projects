from app.agents.generator import generate_verified_question_sync
from app.graph.generation_graph import generation_graph


def test_verified_generation_and_approved_fallback() -> None:
    question = generate_verified_question_sync("factorisation.quadratic_trinomial", 3)
    assert question["question_id"] == "P-FAC-003"
    result = generation_graph.invoke({"skill_id": "factorisation.common_factor", "difficulty": 5})
    assert result["verification_status"] == "verified"
    assert result["question"]["skill_id"] == "factorisation.common_factor"
