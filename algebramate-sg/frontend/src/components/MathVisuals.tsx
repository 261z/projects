type VisualQuestion = { topic?: string; skill_id?: string; question?: string; answer?: string };

export function AlgebraTiles({ question }: { question?: VisualQuestion }) {
  const factor = question?.skill_id?.includes("factorisation") || question?.topic === "Factorisation";
  return <div className="visual-mini"><strong>{factor ? "FACTOR PAIR TILES" : "ALGEBRA TILES"}</strong><div className="tiles-row">{factor ? <><span className="tile tile-x2">x²</span><span className="tile tile-x negative">?x</span><span className="tile tile-x positive">?x</span><span className="tile tile-one negative">?</span></> : <><span className="tile tile-x2">x²</span><span className="tile tile-x">x</span><span className="tile tile-one">1</span></>}</div></div>;
}

export function NumberLine({ question }: { question?: VisualQuestion }) {
  const factor = question?.skill_id?.includes("factorisation") || question?.topic === "Factorisation";
  return <div className="visual-mini"><strong>{factor ? "FACTOR PAIR NUMBERS" : "NUMBER LINE"}</strong>{factor ? <div className="pair-label">Find two integers:<br />product = −12 · sum = −1</div> : <div className="number-line"><span>−5</span><i style={{ left: "50%" }} /><span>0</span><span>5</span></div>}</div>;
}

export function FunctionGraph({ question }: { question?: VisualQuestion }) {
  const factor = question?.skill_id?.includes("factorisation") || question?.topic === "Factorisation";
  return <div className="visual-mini"><strong>{factor ? "ROOTS CHECK" : "FUNCTION GRAPH"}</strong>{factor ? <div className="pair-label">After you factorise:<br />check each root in the original expression.</div> : <svg viewBox="0 0 240 100" role="img" aria-label="Coordinate graph"><path d="M20 50H220M120 10V90M20 80 Q120 0 220 80" fill="none" stroke="currentColor" strokeWidth="2" /></svg>}</div>;
}
