import assert from "node:assert/strict";
import test from "node:test";
import { getFactorisationVisual, type VisualQuestion } from "./factorisationVisual";

const visual = (skill_id: string, question: string, topic = "Factorisation") =>
  getFactorisationVisual({ skill_id, question, topic });

test("updates a quadratic-trinomial scaffold from the active question", () => {
  const model = visual("factorisation.quadratic_trinomial", "Factorise x^2 + 5x + 6.");

  assert.equal(model.title, "FACTOR PAIR MODEL · FACTORISATION");
  assert.equal(model.subtitle, "Find two numbers whose product is 6 and whose sum is 5.");
  assert.deepEqual(model.facts, ["? × ? = 6", "? + ? = 5"]);
  assert.equal(model.guide, "Find two integers:\nproduct = 6 · sum = 5");
  assert.doesNotMatch(JSON.stringify(model), /−12|−1/);
});

test("preserves the mixed-sign trinomial values", () => {
  const model = visual("factorisation.quadratic_trinomial", "Factorise x^2 - x - 12.");

  assert.equal(model.subtitle, "Find two numbers whose product is −12 and whose sum is −1.");
  assert.deepEqual(model.facts, ["? × ? = −12", "? + ? = −1"]);
});

test("renders a difference-of-two-squares scaffold without a stale factor pair or answer", () => {
  const model = visual("factorisation.difference_two_squares", "Factorise x^2 - 25.");

  assert.equal(model.title, "DIFFERENCE OF TWO SQUARES · FACTORISATION");
  assert.deepEqual(model.facts, ["x² = ( ? )²", "25 = ( ? )²"]);
  assert.equal(model.guide, "Match a² − b²:\nidentify a and b from the two terms");
  assert.doesNotMatch(JSON.stringify(model), /product is −12|sum is −1/);
  assert.doesNotMatch(JSON.stringify(model), /\(x\s*[−-]\s*5\)\(x\s*\+\s*5\)/);
});

test("supports a symbolic difference of two squares without revealing its factors", () => {
  const model = visual("factorisation.difference_two_squares", "Factorise x² − 9y².");

  assert.deepEqual(model.facts, ["x² = ( ? )²", "9y² = ( ? )²"]);
  assert.deepEqual(model.tiles.map(tile => tile.label), ["x²", "−9y²"]);
  assert.doesNotMatch(JSON.stringify(model), /3y/);
});

test("renders both seeded common-factor forms", () => {
  const integerFactor = visual("factorisation.common_factor", "Factorise 6x + 12.");
  const variableFactor = visual("factorisation.common_factor", "Factorise 3x^2 + 12x.");

  assert.equal(integerFactor.guide, "Largest shared factor:\n6 divides every term exactly");
  assert.deepEqual(integerFactor.facts, ["shared factor of 6x", "shared factor of 12"]);
  assert.equal(variableFactor.guide, "Largest shared factor:\n3x divides every term exactly");
});

test("accepts Unicode powers and minus signs", () => {
  const model = visual("factorisation.quadratic_trinomial", "Factorise x² − x − 12.");
  assert.equal(model.subtitle, "Find two numbers whose product is −12 and whose sum is −1.");
});

test("accepts alternate wording and non-monic trinomials", () => {
  const model = visual("factorisation.quadratic_trinomial", "Factorize fully 2y^2 + 7y + 3.");

  assert.equal(model.subtitle, "Find two numbers whose product is 6 and whose sum is 7.");
  assert.equal(model.instruction, "split the middle term, then group");
  assert.deepEqual(model.tiles.map(tile => tile.label), ["2y²", "?y", "?y", "3"]);
});

test("accepts a colon and one pair of outer parentheses", () => {
  const model = visual("factorisation.quadratic_trinomial", "Factorise: (x² + 5x + 6).");
  assert.equal(model.subtitle, "Find two numbers whose product is 6 and whose sum is 5.");
});

test("recognises a solve-by-factorisation equation", () => {
  const model = visual("quadratics.solving_factorisation", "Solve x^2 - 5x + 6 = 0.", "Quadratics");

  assert.equal(model.title, "FACTOR PAIR MODEL · FACTORISATION");
  assert.equal(model.subtitle, "Find two numbers whose product is 6 and whose sum is −5.");
});

test("does not derive scaffolding from the answer", () => {
  const question: VisualQuestion & { answer: string } = {
    topic: "Factorisation",
    skill_id: "factorisation.quadratic_trinomial",
    question: "Factorise x^2 + 5x + 6.",
    answer: "deliberately incorrect secret answer",
  };

  const withAnswer = getFactorisationVisual(question);
  const withoutAnswer = getFactorisationVisual({
    topic: question.topic,
    skill_id: question.skill_id,
    question: question.question,
  });
  assert.deepEqual(withAnswer, withoutAnswer);
});

test("falls back safely for an unsupported expression", () => {
  const model = visual("factorisation.unknown", "Factorise this expression.");

  assert.equal(model.title, "FACTORISATION MODEL");
  assert.doesNotMatch(JSON.stringify(model), /undefined|NaN/);
});

test("does not claim a greatest common factor when only 1 is shared", () => {
  const model = visual("factorisation.common_factor", "Factorise 2x + 3.");
  assert.equal(model.title, "FACTORISATION MODEL");
});
