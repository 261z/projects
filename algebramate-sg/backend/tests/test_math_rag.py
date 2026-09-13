from app.rag.ingest import ingest_questions
from app.rag.retriever import retrieve_question
from app.tools.sympy_checker import check_answer


def test_sympy_expression_equivalence() -> None:
    assert check_answer("(x+2)(x+3)", "x^2 + 5x + 6").correct
    assert not check_answer("(x+2)(x+4)", "x^2 + 5x + 6").correct


def test_sympy_equation_solution() -> None:
    assert check_answer("x = 2 or x = 3", "x^2 - 5x + 6 = 0", answer_type="equation").correct


def test_chroma_ingestion_semantic_filtering_and_usage_split() -> None:
    assert ingest_questions() == 40
    practice = retrieve_question(skill_id="factorisation.quadratic_trinomial", difficulty=3, usage="practice")
    diagnostic = retrieve_question(skill_id="factorisation.quadratic_trinomial", difficulty=3, usage="diagnostic")
    assert practice is not None and practice["question_id"] == "P-FAC-003"
    assert diagnostic is not None and diagnostic["question_id"] == "D-FAC-003"
