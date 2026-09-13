type QuestionVisual = { question?: string; answer?: string; topic?: string; skill_id?: string };

type Props = { question?: QuestionVisual };

function pairFromAnswer(answer = "(x−4)(x+3)") {
  const terms = [...answer.matchAll(/x\s*([+-])\s*(\d+)/gi)].map(match => `${match[1] === "-" ? "-" : ""}${match[2]}`);
  const numbers = terms.length >= 2 ? terms : ["-4", "3"];
  return { numbers, product: numbers.reduce((v, n) => v * Number(n), 1), sum: numbers.reduce((v, n) => v + Number(n), 0) };
}

function factorisationModel(question: QuestionVisual) {
  const expression = question.question || "x² − x − 12";
  const answer = question.answer || "(x−4)(x+3)";
  const pair = pairFromAnswer(answer);
  return <>
    <div className="frame-title">FACTOR PAIR MODEL · FACTORISATION</div>
    <div className="frame-subtitle">Find two numbers with product {pair.product} and sum {pair.sum}.</div>
    <div className="factor-pair"><span>{pair.numbers[0]} × {pair.numbers[1]} = {pair.product}</span><span>{pair.numbers[0]} + {pair.numbers[1]} = {pair.sum}</span></div>
    <div className="frame-equation">{expression} <strong>→ {answer}</strong></div>
  </>;
}

export function AlgebraFrame({ question }: Props) {
  const isFactorisation = question?.skill_id?.includes("factorisation") || question?.topic === "Factorisation";
  const expression = question?.question || "(x + 2)(x + 3)";
  if (isFactorisation) return <div className="algebra-frame" aria-label={`Factor pair model for ${expression}`}>{factorisationModel(question || {})}</div>;
  return <div className="algebra-frame" aria-label={`Area model for ${expression}`}>
    <div className="frame-title">AREA MODEL · EXPANSION</div>
    <div className="frame-grid">
      <div className="frame-axis blank" /><div className="frame-axis">x</div><div className="frame-axis">3</div>
      <div className="frame-axis">x</div><div className="frame-cell strong">x²</div><div className="frame-cell">3x</div>
      <div className="frame-axis">2</div><div className="frame-cell">2x</div><div className="frame-cell">6</div>
    </div>
    <div className="frame-equation">x² + 3x + 2x + 6 <strong>= x² + 5x + 6</strong></div>
  </div>;
}
