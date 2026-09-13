type VisualQuestion = { topic?: string; skill_id?: string; question?: string; answer?: string };

function factorPair(question?: VisualQuestion) {
  const terms = [...(question?.answer || "").matchAll(/x\s*([+-])\s*(\d+)/gi)].map(match => `${match[1] === "-" ? "-" : ""}${match[2]}`);
  const numbers = terms.length >= 2 ? terms : ["-4", "3"];
  const product = numbers.reduce((value, number) => value * Number(number), 1);
  const sum = numbers.reduce((value, number) => value + Number(number), 0);
  return { numbers, product, sum };
}

export function AlgebraTiles({ question }: { question?: VisualQuestion }) {
  const factor = question?.skill_id?.includes("factorisation") || question?.topic === "Factorisation";
  const pair = factorPair(question);
  return <div className="visual-mini"><strong>{factor ? "FACTOR PAIR TILES" : "ALGEBRA TILES"}</strong><div className="tiles-row">{factor ? <><span className="tile tile-x2">x²</span><span className="tile tile-x negative">{pair.numbers[0]}x</span><span className="tile tile-x positive">{pair.numbers[1]}x</span><span className="tile tile-one negative">{pair.product}</span></> : <><span className="tile tile-x2">x²</span><span className="tile tile-x">x</span><span className="tile tile-one">1</span></>}</div></div>;
}

export function NumberLine({ question }: { question?: VisualQuestion }) {
  const factor = question?.skill_id?.includes("factorisation") || question?.topic === "Factorisation";
  const pair = factorPair(question);
  return <div className="visual-mini"><strong>{factor ? "FACTOR PAIR NUMBERS" : "NUMBER LINE"}</strong>{factor ? <div className="pair-label">{pair.numbers[0]} · {pair.numbers[1]} → product {pair.product}<br />{pair.numbers[0]} + {pair.numbers[1]} → sum {pair.sum}</div> : <div className="number-line"><span>−5</span><i style={{ left: "50%" }} /><span>0</span><span>5</span></div>}</div>;
}

export function FunctionGraph({ question }: { question?: VisualQuestion }) {
  const factor = question?.skill_id?.includes("factorisation") || question?.topic === "Factorisation";
  const pair = factorPair(question);
  return <div className="visual-mini"><strong>{factor ? "ROOTS CHECK" : "FUNCTION GRAPH"}</strong>{factor ? <div className="pair-label">Roots: x = {Math.abs(Number(pair.numbers[1]))} and x = {Math.abs(Number(pair.numbers[0]))}</div> : <svg viewBox="0 0 240 100" role="img" aria-label="Coordinate graph"><path d="M20 50H220M120 10V90M20 80 Q120 0 220 80" fill="none" stroke="currentColor" strokeWidth="2" /></svg>}</div>;
}
