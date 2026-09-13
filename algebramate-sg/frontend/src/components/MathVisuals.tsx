import { getFactorisationVisual, type VisualQuestion } from "./factorisationVisual";

export function AlgebraTiles({ question }: { question?: VisualQuestion }) {
  const factor = question?.skill_id?.includes("factorisation") || question?.topic === "Factorisation";
  if (!factor) return <div className="visual-mini"><strong>ALGEBRA TILES</strong><div className="tiles-row"><span className="tile tile-x2">x²</span><span className="tile tile-x">x</span><span className="tile tile-one">1</span></div></div>;

  const model = getFactorisationVisual(question);
  return <div className="visual-mini"><strong>{model.tilesTitle}</strong><div className="tiles-row">{model.tiles.map((tile, index) => <span key={`${tile.label}-${index}`} className={`tile tile-${tile.kind} ${tile.tone}`}>{tile.label}</span>)}</div></div>;
}

export function NumberLine({ question }: { question?: VisualQuestion }) {
  const factor = question?.skill_id?.includes("factorisation") || question?.topic === "Factorisation";
  if (!factor) return <div className="visual-mini"><strong>NUMBER LINE</strong><div className="number-line"><span>−5</span><i style={{ left: "50%" }} /><span>0</span><span>5</span></div></div>;

  const model = getFactorisationVisual(question);
  return <div className="visual-mini"><strong>{model.guideTitle}</strong><div className="pair-label">{model.guide.split("\n").map((line, index) => <span key={line}>{index > 0 && <br />}{line}</span>)}</div></div>;
}

export function FunctionGraph({ question }: { question?: VisualQuestion }) {
  const factor = question?.skill_id?.includes("factorisation") || question?.topic === "Factorisation";
  if (!factor) return <div className="visual-mini"><strong>FUNCTION GRAPH</strong><svg viewBox="0 0 240 100" role="img" aria-label="Coordinate graph"><path d="M20 50H220M120 10V90M20 80 Q120 0 220 80" fill="none" stroke="currentColor" strokeWidth="2" /></svg></div>;

  const model = getFactorisationVisual(question);
  return <div className="visual-mini"><strong>{model.checkTitle}</strong><div className="pair-label">{model.check.split("\n").map((line, index) => <span key={line}>{index > 0 && <br />}{line}</span>)}</div></div>;
}
