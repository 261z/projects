from app.rag.ingest import ingest_questions
from app.rag.retriever import retrieve_question
from app.tools.sympy_checker import check_answer


def test_sympy_expression_equivalence() -> None:
    assert check_answer("(x+2)(x+3)", "x^2 + 5x + 6").correct
    assert not check_answer("(x+2)(x+4)", "x^2 + 5x + 6").correct


def test_sympy_equation_solution() -> None:
    assert check_answer("x = 2 or x = 3", "x^2 - 5x + 6 = 0", answer_type="equation").correct


def test_chroma_ingestion_and_filtering() -> None:
    assert ingest_questions() >= 8
    result = retrieve_question(skill_id="factorisation.quadratic_trinomial", difficulty=3)
    assert result is not None
    assert result["question_id"] == "S2-FAC-Q001"
