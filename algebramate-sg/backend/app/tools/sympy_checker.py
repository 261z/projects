from __future__ import annotations

import re
from dataclasses import dataclass

import sympy as sp
from sympy.parsing.sympy_parser import implicit_multiplication_application, parse_expr, standard_transformations


@dataclass(frozen=True)
class CheckResult:
    correct: bool
    method: str
    message: str = ""


def _clean(text: str) -> str:
    return text.strip().replace("²", "^2").replace("×", "*").replace("−", "-")


def _expr(text: str) -> sp.Expr:
    transformations = standard_transformations + (implicit_multiplication_application,)
    return parse_expr(_clean(text).replace("^", "**"), transformations=transformations, local_dict={"x": sp.Symbol("x"), "y": sp.Symbol("y")})


def check_answer(student: str, expected: str, *, answer_type: str = "expression") -> CheckResult:
    try:
        student_clean, expected_clean = _clean(student), _clean(expected)
        if answer_type == "equation" or "=" in expected_clean:
            return _check_equation(student_clean, expected_clean)
        equivalent = sp.simplify(_expr(student_clean) - _expr(expected_clean)) == 0
        return CheckResult(equivalent, "sympy_equivalence", "Equivalent mathematical form." if equivalent else "The expression is not equivalent.")
    except (sp.SympifyError, ValueError, TypeError, SyntaxError):
        return CheckResult(False, "parse_error", "The answer could not be interpreted as a valid algebraic expression.")


def _check_equation(student: str, expected: str) -> CheckResult:
    try:
        if "or" in student.lower():
            values = re.findall(r"x\s*=\s*(-?\d+(?:\.\d+)?)", student.lower())
            student_set = {sp.sympify(value) for value in values}
        else:
            match = re.search(r"x\s*=\s*(-?\d+(?:\.\d+)?)", student.lower())
            if not match:
                student_set = {sp.solve(sp.Eq(_expr(student.split("=")[0]), _expr(student.split("=")[1])), sp.Symbol("x"))[0]}
            else:
                student_set = {sp.sympify(match.group(1))}
        lhs, rhs = expected.split("=", 1)
        expected_set = set(sp.solve(sp.Eq(_expr(lhs), _expr(rhs)), sp.Symbol("x")))
        correct = student_set == expected_set
        return CheckResult(correct, "sympy_equation_solution", "Correct solution set." if correct else "The solution set does not match.")
    except (sp.SympifyError, ValueError, TypeError, IndexError):
        return CheckResult(False, "equation_parse_error", "The equation answer could not be checked.")
