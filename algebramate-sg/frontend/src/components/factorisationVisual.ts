export type VisualQuestion = {
  topic?: string;
  skill_id?: string;
  question?: string;
};

type TileTone = "positive" | "negative" | "neutral";
type TileKind = "x2" | "x" | "one";

type ParsedTerm = {
  coefficient: number;
  variable?: string;
  variablePower: number;
};

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

function normaliseExpression(value: string) {
  const expression = value
    .replace(/[−–—]/g, "-")
    .replaceAll("²", "^2")
    .replace(/^\s*(?:(?:factorise|factorize)(?:\s+fully)?|solve)\s*:?[\s]*/i, "")
    .replace(/[.?!]\s*$/, "")
    .replace(/\s*=\s*0\s*$/, "")
    .trim();

  if (expression.startsWith("(") && expression.endsWith(")")) {
    let depth = 0;
    const wrapsWholeExpression = [...expression].every((character, index) => {
      if (character === "(") depth += 1;
      if (character === ")") depth -= 1;
      return depth > 0 || index === expression.length - 1;
    });
    if (wrapsWholeExpression) return expression.slice(1, -1).trim();
  }

  return expression;
}

function expressionFrom(question?: VisualQuestion) {
  return normaliseExpression(question?.question || "Factorise the expression.");
}

function displayExpression(expression: string) {
  return expression.replace(/\^2/g, "²").replace(/-/g, "−");
}

function displayTerm(term: string) {
  return displayExpression(term.replace(/^\+/, ""));
}

function coefficient(token: string) {
  const compact = token.replace(/\s/g, "");
  if (compact === "" || compact === "+") return 1;
  if (compact === "-") return -1;
  return Number(compact);
}

function parseQuadratic(expression: string) {
  const compact = expression.replace(/\s/g, "");
  const match = compact.match(/^([+-]?\d*)([a-z])\^2([+-](?:\d+)?)\2([+-]\d+)$/i);
  if (!match) return null;

  const a = coefficient(match[1]);
  const b = coefficient(match[3]);
  const c = Number(match[4]);
  if (![a, b, c].every(Number.isFinite) || a === 0) return null;
  return { a, b, c, variable: match[2] };
}

function parseDifferenceOfSquares(expression: string) {
  const compact = expression.replace(/\s/g, "");
  const match = compact.match(/^([+]?\d*)([a-z])\^2-(?:(\d+)|([+]?\d*)([a-z])\^2)$/i);
  if (!match) return null;

  const leading = Number(match[1] || 1);
  const leftRoot = Math.sqrt(leading);
  const rightCoefficient = Number(match[3] || match[4] || 1);
  const rightRootCoefficient = Math.sqrt(rightCoefficient);
  if (!Number.isInteger(leftRoot) || !Number.isInteger(rightRootCoefficient)) return null;

  const variable = match[2];
  const rightVariable = match[5];
  const rightSquare = rightVariable
    ? `${rightCoefficient === 1 ? "" : rightCoefficient}${rightVariable}²`
    : String(rightCoefficient);
  const rightRoot = rightVariable
    ? `${rightRootCoefficient === 1 ? "" : rightRootCoefficient}${rightVariable}`
    : String(rightRootCoefficient);
  return {
    leftSquare: leading === 1 ? `${variable}²` : `${leading}${variable}²`,
    leftRoot: leftRoot === 1 ? variable : `${leftRoot}${variable}`,
    rightSquare,
    rightRoot,
  };
}

function gcd(a: number, b: number): number {
  return b === 0 ? Math.abs(a) : gcd(b, a % b);
}

function parseTerm(term: string): ParsedTerm | null {
  const compact = term.replace(/\s/g, "");
  const match = compact.match(/^([+-]?)(\d*)(?:([a-z])(?:\^(\d+))?)?$/i);
  if (!match) return null;
  const variable = match[3];
  const magnitude = Number(match[2] || 1);
  return {
    coefficient: match[1] === "-" ? -magnitude : magnitude,
    variable,
    variablePower: variable ? Number(match[4] || 1) : 0,
  };
}

function commonFactor(expression: string) {
  const compact = expression.replace(/\s/g, "");
  const terms = compact.match(/[+-]?[^+-]+/g) || [];
  const parsed = terms.map(parseTerm);
  if (terms.length < 2 || parsed.some(term => !term)) return null;

  const validTerms = parsed as ParsedTerm[];
  const coefficientGcd = validTerms.reduce((value, term) => gcd(value, term.coefficient), 0);
  const variables = new Set(validTerms.flatMap(term => term.variable ? [term.variable.toLowerCase()] : []));
  const sharedVariable = variables.size === 1 && validTerms.every(term => term.variable || term.variablePower === 0)
    ? [...variables][0]
    : undefined;
  const variablePower = sharedVariable
    ? Math.min(...validTerms.map(term => term.variable?.toLowerCase() === sharedVariable ? term.variablePower : 0))
    : 0;
  if (coefficientGcd === 1 && variablePower === 0) return null;
  const variablePart = variablePower === 0 ? "" : variablePower === 1 ? sharedVariable! : `${sharedVariable}^${variablePower}`;
  const factor = `${coefficientGcd === 1 && variablePart ? "" : coefficientGcd}${variablePart}`;
  return { terms: terms.map(displayTerm), factor: displayExpression(factor || "1") };
}

function quadraticModel(question: VisualQuestion | undefined, expression: string): FactorisationVisualModel | null {
  const parsed = parseQuadratic(expression);
  if (!parsed) return null;
  const product = parsed.a * parsed.c;
  const sum = parsed.b;
  const displayedProduct = unicodeMinus(product);
  const displayedSum = unicodeMinus(sum);
  const squareLabel = parsed.a === 1
    ? `${parsed.variable}²`
    : parsed.a === -1
      ? `−${parsed.variable}²`
      : `${unicodeMinus(parsed.a)}${parsed.variable}²`;

  return {
    title: "FACTOR PAIR MODEL · FACTORISATION",
    subtitle: `Find two numbers whose product is ${displayedProduct} and whose sum is ${displayedSum}.`,
    facts: [`? × ? = ${displayedProduct}`, `? + ? = ${displayedSum}`],
    expression: question?.question || `Factorise ${displayExpression(expression)}.`,
    instruction: parsed.a === 1 ? "complete the factor pair" : "split the middle term, then group",
    tilesTitle: "FACTOR PAIR TILES",
    tiles: [
      { label: squareLabel, kind: "x2", tone: "neutral" },
      { label: `?${parsed.variable}`, kind: "x", tone: product < 0 ? "negative" : "neutral" },
      { label: `?${parsed.variable}`, kind: "x", tone: "positive" },
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
    facts: [`${parsed.leftSquare} = ( ? )²`, `${parsed.rightSquare} = ( ? )²`],
    expression: question?.question || `Factorise ${displayExpression(expression)}.`,
    instruction: "use the difference-of-squares pattern",
    tilesTitle: "SQUARE TILES",
    tiles: [
      { label: parsed.leftSquare, kind: "x2", tone: "neutral" },
      { label: `−${parsed.rightSquare}`, kind: "one", tone: "negative" },
    ],
    guideTitle: "PERFECT SQUARES",
    guide: "Match a² − b²:\nidentify a and b from the two terms",
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
      kind: term.includes("²") ? "x2" : /[a-z]/i.test(term) ? "x" : "one",
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
    tiles: [{ label: displayExpression(expression), kind: "x2", tone: "neutral" }],
    guideTitle: "STRUCTURE CHECK",
    guide: "Look for a common factor, a factor pair, or a special identity.",
    checkTitle: "EXPANSION CHECK",
    check: "Expand your factors to confirm that they reproduce the original expression.",
  };
}
