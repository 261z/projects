type QuestionVisual = { question?: string; answer?: string; topic?: string; skill_id?: string };

type Props = { question?: QuestionVisual };

function factorisationModel(question: QuestionVisual) {
  const expression = question.question || "x² − x − 12";
  return <>
    <div className="frame-title">FACTOR PAIR MODEL · FACTORISATION</div>
    <div className="frame-subtitle">Find two numbers whose product is −12 and whose sum is −1.</div>
    <div className="factor-pair"><span>? × ? = −12</span><span>? + ? = −1</span></div>
    <div className="frame-equation">{expression} <strong>→ complete the factor pair</strong></div>
  </>;
}

export function AlgebraFrame({ question }: Props) {
  const isFactorisation = question?.skill_id?.includes("factorisation") || question?.topic === "Factorisation";
  const expression = question?.question || "(x + 2)(x + 3)";
  if (isFactorisation) return <div className="algebra-frame" aria-label={`Factor pair scaffold for ${expression}`}>{factorisationModel(question || {})}</div>;
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
