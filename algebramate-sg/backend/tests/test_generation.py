from app.agents.generator import generate_verified_question
from app.graph.generation_graph import generation_graph


def test_verified_generation_and_fallback() -> None:
    question = generate_verified_question("factorisation.quadratic_trinomial", 3)
    assert question["question_id"] == "S2-FAC-Q001"
    result = generation_graph.invoke({"skill_id": "factorisation.common_factor", "difficulty": 5})
    assert result["verification_status"] == "verified"
    assert result["question"]["skill_id"] == "factorisation.common_factor"
