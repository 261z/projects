export type VisualQuestion = {
  topic?: string;
  skill_id?: string;
  question?: string;
  answer?: string;
};

type TileTone = "positive" | "negative" | "neutral";
type TileKind = "x2" | "x" | "one";

export type FactorisationVisualModel = {
  title: string;
  subtitle: string;
  facts: string[];
  expression: string;
  instruction: string;
  tilesTitle: string;
  tiles: { label: string; kind: TileKind; tone: TileTone }[];
  guideTitle: string;
  guide: string;
  checkTitle: string;
  check: string;
};

const unicodeMinus = (value: number) => String(value).replace("-", "−");

function expressionFrom(question?: VisualQuestion) {
  return (question?.question || "Factorise the expression.")
    .replace(/^\s*factorise\s+/i, "")
    .replace(/[.?!]\s*$/, "")
    .replaceAll("²", "^2")
    .trim();
}

function displayExpression(expression: string) {
  return expression.replace(/\^2/g, "²").replace(/-/g, "−");
}

function coefficient(token: string) {
  const compact = token.replace(/\s/g, "");
  if (compact === "" || compact === "+") return 1;
  if (compact === "-") return -1;
  return Number(compact);
}

function parseQuadratic(expression: string) {
  const compact = expression.replace(/\s/g, "");
  const match = compact.match(/^([+-]?\d*)x\^2([+-](?:\d+)?)x([+-]\d+)$/i);
  if (!match) return null;

  const a = coefficient(match[1]);
  const b = coefficient(match[2]);
  const c = Number(match[3]);
  if (![a, b, c].every(Number.isFinite)) return null;
  return { a, b, c };
}

function parseDifferenceOfSquares(expression: string) {
  const compact = expression.replace(/\s/g, "");
  const match = compact.match(/^(?:(\d+)?)x\^2-(\d+)$/i);
  if (!match) return null;

  const leading = Number(match[1] || 1);
  const constant = Number(match[2]);
  const leftRoot = Math.sqrt(leading);
  const rightRoot = Math.sqrt(constant);
  if (!Number.isInteger(leftRoot) || !Number.isInteger(rightRoot)) return null;

  return {
    leftSquare: leading === 1 ? "x²" : `${leading}x²`,
    leftRoot: leftRoot === 1 ? "x" : `${leftRoot}x`,
    rightSquare: String(constant),
    rightRoot: String(rightRoot),
  };
}

function gcd(a: number, b: number): number {
  return b === 0 ? Math.abs(a) : gcd(b, a % b);
}

function parseTerm(term: string) {
  const compact = term.replace(/\s/g, "");
  const match = compact.match(/^([+-]?)(\d*)(?:x(?:\^(\d+))?)?$/i);
  if (!match) return null;
  const hasX = /x/i.test(compact);
  const magnitude = Number(match[2] || 1);
  return {
    coefficient: match[1] === "-" ? -magnitude : magnitude,
    xPower: hasX ? Number(match[3] || 1) : 0,
  };
}

function commonFactor(expression: string) {
  const compact = expression.replace(/\s/g, "");
  const terms = compact.match(/[+-]?[^+-]+/g) || [];
  const parsed = terms.map(parseTerm);
  if (terms.length < 2 || parsed.some(term => !term)) return null;

  const validTerms = parsed.filter((term): term is NonNullable<typeof term> => Boolean(term));
  const coefficientGcd = validTerms.reduce((value, term) => gcd(value, term.coefficient), 0);
  const xPower = Math.min(...validTerms.map(term => term.xPower));
  const variable = xPower === 0 ? "" : xPower === 1 ? "x" : `x^${xPower}`;
  const factor = `${coefficientGcd === 1 && variable ? "" : coefficientGcd}${variable}`;
  return { terms: terms.map(displayExpression), factor: displayExpression(factor || "1") };
}

function quadraticModel(question: VisualQuestion | undefined, expression: string): FactorisationVisualModel | null {
  const parsed = parseQuadratic(expression);
  if (!parsed) return null;
  const product = parsed.a * parsed.c;
  const sum = parsed.b;
  const displayedProduct = unicodeMinus(product);
  const displayedSum = unicodeMinus(sum);

  return {
    title: "FACTOR PAIR MODEL · FACTORISATION",
    subtitle: `Find two numbers whose product is ${displayedProduct} and whose sum is ${displayedSum}.`,
    facts: [`? × ? = ${displayedProduct}`, `? + ? = ${displayedSum}`],
    expression: question?.question || `Factorise ${displayExpression(expression)}.`,
    instruction: parsed.a === 1 ? "complete the factor pair" : "split the middle term, then group",
    tilesTitle: "FACTOR PAIR TILES",
    tiles: [
      { label: parsed.a === 1 ? "x²" : `${parsed.a}x²`, kind: "x2", tone: "positive" },
      { label: "?x", kind: "x", tone: product < 0 ? "negative" : "neutral" },
      { label: "?x", kind: "x", tone: "positive" },
      { label: unicodeMinus(parsed.c), kind: "one", tone: parsed.c < 0 ? "negative" : "positive" },
    ],
    guideTitle: "FACTOR PAIR NUMBERS",
    guide: `Find two integers:\nproduct = ${displayedProduct} · sum = ${displayedSum}`,
    checkTitle: "ROOTS CHECK",
    check: "After you factorise:\ncheck each root in the original expression.",
  };
}

function differenceOfSquaresModel(question: VisualQuestion | undefined, expression: string): FactorisationVisualModel | null {
  const parsed = parseDifferenceOfSquares(expression);
  if (!parsed) return null;

  return {
    title: "DIFFERENCE OF TWO SQUARES · FACTORISATION",
    subtitle: "Identify the two perfect squares separated by subtraction.",
    facts: [`${parsed.leftSquare} = (${parsed.leftRoot})²`, `${parsed.rightSquare} = ${parsed.rightRoot}²`],
    expression: question?.question || `Factorise ${displayExpression(expression)}.`,
    instruction: "use a² − b² = (a − b)(a + b)",
    tilesTitle: "SQUARE TILES",
    tiles: [
      { label: parsed.leftSquare, kind: "x2", tone: "positive" },
      { label: `−${parsed.rightSquare}`, kind: "one", tone: "negative" },
    ],
    guideTitle: "PERFECT SQUARES",
    guide: `Match a² − b²:\na = ${parsed.leftRoot} · b = ${parsed.rightRoot}`,
    checkTitle: "IDENTITY CHECK",
    check: "After you factorise:\nexpand the conjugate pair to recover the original expression.",
  };
}

function commonFactorModel(question: VisualQuestion | undefined, expression: string): FactorisationVisualModel | null {
  const parsed = commonFactor(expression);
  if (!parsed) return null;

  return {
    title: "COMMON FACTOR MODEL · FACTORISATION",
    subtitle: "Find the greatest factor shared by every term.",
    facts: parsed.terms.map(term => `shared factor of ${term}`),
    expression: question?.question || `Factorise ${displayExpression(expression)}.`,
    instruction: "take out the greatest common factor",
    tilesTitle: "TERM TILES",
    tiles: parsed.terms.map((term, index) => ({
      label: term,
      kind: term.includes("²") ? "x2" : term.toLowerCase().includes("x") ? "x" : "one",
      tone: term.startsWith("−") ? "negative" : index === 0 ? "positive" : "neutral",
    })),
    guideTitle: "COMMON FACTOR CHECK",
    guide: `Largest shared factor:\n${parsed.factor} divides every term exactly`,
    checkTitle: "EXPANSION CHECK",
    check: "After you factorise:\ndistribute the common factor to recover every original term.",
  };
}

export function getFactorisationVisual(question?: VisualQuestion): FactorisationVisualModel {
  const expression = expressionFrom(question);
  const skill = question?.skill_id || "";

  if (skill.includes("difference_two_squares")) {
    const model = differenceOfSquaresModel(question, expression);
    if (model) return model;
  }

  if (skill.includes("common_factor")) {
    const model = commonFactorModel(question, expression);
    if (model) return model;
  }

  const quadratic = quadraticModel(question, expression);
  if (quadratic) return quadratic;

  const squares = differenceOfSquaresModel(question, expression);
  if (squares) return squares;

  const sharedFactor = commonFactorModel(question, expression);
  if (sharedFactor) return sharedFactor;

  return {
    title: "FACTORISATION MODEL",
    subtitle: "Use the structure of the active expression to choose a factorisation method.",
    facts: ["What is common?", "Which identity fits?"],
    expression: question?.question || "Factorise the expression.",
    instruction: "rewrite it as a product",
    tilesTitle: "FACTORISATION TILES",
    tiles: [{ label: displayExpression(expression), kind: "x2", tone: "positive" }],
    guideTitle: "STRUCTURE CHECK",
    guide: "Look for a common factor, a factor pair, or a special identity.",
    checkTitle: "EXPANSION CHECK",
    check: "Expand your factors to confirm that they reproduce the original expression.",
  };
}
