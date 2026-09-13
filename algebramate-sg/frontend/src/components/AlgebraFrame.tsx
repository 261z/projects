type Props = { expression?: string };

export function AlgebraFrame({ expression = "(x + 2)(x + 3)" }: Props) {
  return <div className="algebra-frame" aria-label={`Area model for ${expression}`}>
    <div className="frame-title">AREA MODEL · EXPANSION</div>
    <div className="frame-grid">
      <div className="frame-axis blank" />
      <div className="frame-axis">x</div><div className="frame-axis">3</div>
      <div className="frame-axis">x</div><div className="frame-cell strong">x²</div><div className="frame-cell">3x</div>
      <div className="frame-axis">2</div><div className="frame-cell">2x</div><div className="frame-cell">6</div>
    </div>
    <div className="frame-equation">x² + 3x + 2x + 6 <strong>= x² + 5x + 6</strong></div>
  </div>;
}
