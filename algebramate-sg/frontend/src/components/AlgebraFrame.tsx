import { getFactorisationVisual, type VisualQuestion } from "./factorisationVisual";

type Props = { question?: VisualQuestion };

function factorisationModel(question?: VisualQuestion) {
  const model = getFactorisationVisual(question);
  return <>
    <div className="frame-title">{model.title}</div>
    <div className="frame-subtitle">{model.subtitle}</div>
    <div className="factor-pair">{model.facts.map(fact => <span key={fact}>{fact}</span>)}</div>
    <div className="frame-equation">{model.expression} <strong>→ {model.instruction}</strong></div>
  </>;
}

export function AlgebraFrame({ question }: Props) {
  const isFactorisation = question?.skill_id?.includes("factorisation") || question?.topic === "Factorisation";
  const expression = question?.question || "(x + 2)(x + 3)";
  if (isFactorisation) return <div className="algebra-frame" aria-label={`Factorisation scaffold for ${expression}`}>{factorisationModel(question)}</div>;
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
