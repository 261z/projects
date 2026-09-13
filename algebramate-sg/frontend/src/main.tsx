import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { AlgebraFrame } from "./components/AlgebraFrame";
import { AlgebraTiles, FunctionGraph, NumberLine } from "./components/MathVisuals";
import { api, Question, PracticeResult, SessionSummary } from "./api/client";
import "./styles.css";

type Screen = "auth" | "topics" | "diagnostic" | "practice" | "progress" | "summary";
type DiagnosticStatus = { complete: boolean; raw_score?: number; initial_mastery?: number; recommended_starting_difficulty?: number };
const TOPICS = ["Factorisation", "Expansion", "Linear equations", "Quadratics"];
const LEVELS = ["Foundation", "Easy", "Standard", "Challenging", "Advanced"];

function App() {
  const [screen, setScreen] = useState<Screen>("auth");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [topic, setTopic] = useState("Factorisation");
  const [question, setQuestion] = useState<Question | null>(null);
  const [seenQuestionIds, setSeenQuestionIds] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState<number | undefined>();
  const [sessionSummary, setSessionSummary] = useState<SessionSummary | null>(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<PracticeResult | null>(null);
  const [hints, setHints] = useState(0);
  const [hintText, setHintText] = useState("");
  const [visualVisible, setVisualVisible] = useState(false);
  const [diagnosticQuestions, setDiagnosticQuestions] = useState<Question[]>([]);
  const [diagnosticIndex, setDiagnosticIndex] = useState(0);
  const [diagnosticSummary, setDiagnosticSummary] = useState<DiagnosticStatus | null>(null);
  const [diagnosticStatuses, setDiagnosticStatuses] = useState<Record<string, DiagnosticStatus>>({});
  const [error, setError] = useState("");
  const [overall, setOverall] = useState(0);
  const [skills, setSkills] = useState<{ skill_id: string; mastery_score: number }[]>([]);

  useEffect(() => {
    if (screen !== "topics" || !localStorage.getItem("algebramate_token")) return;
    Promise.all(TOPICS.map(name => api.diagnosticStatus(name)))
      .then(statuses => setDiagnosticStatuses(Object.fromEntries(statuses.map(status => [status.topic, status]))))
      .catch(error => setError((error as Error).message));
  }, [screen]);

  const submitAuth = async () => {
    try {
      setError("");
      if (authMode === "register") await api.register(username, password);
      const auth = await api.login(username, password);
      localStorage.setItem("algebramate_token", auth.access_token);
      setScreen("topics");
    } catch (error) { setError((error as Error).message); }
  };

  const startDiagnostic = async (selectedTopic: string) => {
    try {
      const data = await api.diagnosticStart(selectedTopic);
      setTopic(selectedTopic); setDiagnosticQuestions(data.questions); setDiagnosticIndex(0);
      setAnswer(""); setDiagnosticSummary(null); setScreen("diagnostic");
    } catch (error) { setError((error as Error).message); }
  };

  const answerDiagnostic = async () => {
    const current = diagnosticQuestions[diagnosticIndex];
    if (!current) return;
    try {
      const data = await api.diagnosticAnswer(current.question_id, answer);
      setAnswer("");
      if (data.complete) setDiagnosticSummary(data);
      else setDiagnosticIndex(index => index + 1);
    } catch (error) { setError((error as Error).message); }
  };

  const startPractice = async (selectedTopic = topic, excludedIds: string[] = [], difficulty?: number, existingSessionId?: number) => {
    try {
      setError("");
      const data = await api.startPractice(selectedTopic, undefined, difficulty || diagnosticSummary?.recommended_starting_difficulty || 2, excludedIds, existingSessionId);
      setTopic(selectedTopic); setQuestion(data.question); setSessionId(data.session_id);
      setSeenQuestionIds(excludedIds.includes(data.question.question_id) ? excludedIds : [...excludedIds, data.question.question_id]);
      setResult(null); setAnswer(""); setHints(0); setHintText(""); setVisualVisible(false); setScreen("practice");
    } catch (error) { setError((error as Error).message); }
  };

  const submitAnswer = async () => {
    if (!question) return;
    try { setResult(await api.answer(question.question_id, answer, undefined, hints, sessionId)); }
    catch (error) { setError((error as Error).message); }
  };

  const chooseDifficulty = async (difficulty: number) => {
    if (!question || !result) return;
    try {
      const selected = await api.overrideDifficulty(question.question_id, difficulty);
      setResult({ ...result, ...selected });
    } catch (error) { setError((error as Error).message); }
  };

  const nextQuestion = () => startPractice(topic, seenQuestionIds, result?.selected_difficulty || result?.recommended_difficulty || question?.difficulty, sessionId);

  const requestHint = async () => {
    if (!question) return;
    const next = Math.min(3, hints + 1);
    try { const data = await api.hint(question.question_id, next); setHints(next); setHintText(data.hint); }
    catch (error) { setError((error as Error).message); }
  };

  const requestExplain = async (analogy: boolean) => {
    if (!question) return;
    try { const data = await api.explain(question.question_id, analogy); setHintText(data.text); }
    catch (error) { setError((error as Error).message); }
  };

  const showVisual = async () => {
    if (!question) return;
    try { await api.visualise(question.question_id); setVisualVisible(true); setTimeout(() => document.querySelector(".algebra-frame")?.scrollIntoView({ behavior: "smooth" }), 0); }
    catch (error) { setError((error as Error).message); }
  };

  const exitPractice = async () => {
    try {
      if (sessionId) setSessionSummary(await api.endSession(sessionId));
      else setSessionSummary(null);
      setSessionId(undefined); setScreen("summary");
    } catch (error) { setError((error as Error).message); }
  };

  const openProgress = async () => {
    try { const data = await api.progress(); setOverall(data.overall_mastery); setSkills(data.skills); setScreen("progress"); }
    catch (error) { setError((error as Error).message); }
  };

  const logout = async () => {
    try { if (sessionId) await api.endSession(sessionId); await api.logout(); } catch { /* local logout still succeeds */ }
    localStorage.removeItem("algebramate_token"); setSessionId(undefined); setScreen("auth");
  };

  if (screen === "auth") return <main className="auth-shell"><section className="auth-copy"><div className="eyebrow">ALGEBRAMATE SG</div><h1>Algebra can<br /><em>click.</em></h1><p>A calm, clever study companion for your next algebra breakthrough.</p></section><section className="auth-card"><div className="card-label">{authMode === "login" ? "WELCOME BACK" : "CREATE YOUR SPACE"}</div><h2>{authMode === "login" ? "Pick up where you left off." : "Start your algebra journey."}</h2><input placeholder="Username" value={username} onChange={event => setUsername(event.target.value)} /><input placeholder="Password (8+ characters)" type="password" value={password} onChange={event => setPassword(event.target.value)} /><button className="primary-button full" onClick={submitAuth}>{authMode === "login" ? "Log in" : "Create account"}</button><button className="link-button" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>{authMode === "login" ? "New here? Create an account" : "Already have an account? Log in"}</button>{error && <p className="error">{error}</p>}</section></main>;

  return <main className="app-shell app-shell-inner"><header className="topbar"><div className="brand">Algebra<span>Mate</span> SG</div><nav><button onClick={() => setScreen("topics")}>Learn</button><button onClick={openProgress}>My progress</button><button onClick={logout}>Log out</button></nav></header>
    {screen === "topics" && <section className="content-grid"><div><div className="eyebrow dark">YOUR NEXT STEP</div><h1 className="dark-heading">What would you like<br /><em>to practise?</em></h1><p className="intro dark-intro">Diagnostics are saved once completed. Practice continues for as long as you want.</p></div><div className="topic-list">{TOPICS.map((name, index) => { const status = diagnosticStatuses[name]; return <button className="topic-card" key={name} onClick={() => status?.complete ? startPractice(name, [], status.recommended_starting_difficulty) : startDiagnostic(name)}><span className="topic-index">0{index + 1}</span><span><strong>{name}</strong><small>{status?.complete ? `Diagnostic complete · ${status.raw_score}/5 · Practise now` : "Take diagnostic → practise"}</small></span><span>→</span></button>; })}</div></section>}
    {screen === "diagnostic" && <section className="diagnostic-view"><div className="eyebrow dark">{topic.toUpperCase()} · DIAGNOSTIC</div>{diagnosticSummary ? <><h1 className="dark-heading">Your starting point<br /><em>is clear.</em></h1><div className="diagnostic-result"><strong>{diagnosticSummary.raw_score}/5 correct</strong><span>Initial mastery: {Math.round((diagnosticSummary.initial_mastery || 0) * 100)}%</span><span>Recommended starting level: {diagnosticSummary.recommended_starting_difficulty}/5</span></div><button className="primary-button" onClick={() => startPractice(topic)}>Begin practice →</button></> : <><div className="question-meta">Question {diagnosticIndex + 1} of 5 <span>Difficulty {diagnosticQuestions[diagnosticIndex]?.difficulty}/5</span></div><h2 className="question-text">{diagnosticQuestions[diagnosticIndex]?.question}</h2><input className="answer-input" placeholder="Type your answer here…" value={answer} onChange={event => setAnswer(event.target.value)} onKeyDown={event => event.key === "Enter" && answerDiagnostic()} /><button className="primary-button" onClick={answerDiagnostic}>Submit answer</button></>}</section>}
    {screen === "practice" && <section className="practice-layout"><div className="practice-main"><div className="eyebrow dark">{topic.toUpperCase()} · PRACTICE</div><div className="question-meta">Skill: {question?.skill_id} <span>{LEVELS[(question?.difficulty || 1) - 1]} · {question?.difficulty}/5</span></div><h2 className="question-text">{question?.question}</h2><input className="answer-input" placeholder="Type your answer here…" value={answer} onChange={event => setAnswer(event.target.value)} onKeyDown={event => event.key === "Enter" && submitAnswer()} /><div className="practice-actions"><button className="primary-button" onClick={submitAnswer}>Check answer</button><button className="exit-button" onClick={exitPractice}>Exit practice</button></div>{result && <div className={`result ${result.correct ? "correct" : "incorrect"}`}><strong>{result.correct ? "Correct — nice work." : "Not quite yet."}</strong><p>{result.feedback || "Try looking at the structure again."}</p><div>Mastery now <b>{Math.round(result.mastery * 100)}%</b> · Recommended: <b>{LEVELS[result.recommended_difficulty - 1]}</b></div><div className="difficulty-picker"><span>Choose next level:</span>{[Math.max(1, result.recommended_difficulty - 1), result.recommended_difficulty, Math.min(5, result.recommended_difficulty + 1)].filter((value, index, values) => values.indexOf(value) === index).map(value => <button key={value} className={value === result.selected_difficulty ? "selected" : ""} onClick={() => chooseDifficulty(value)}>{LEVELS[value - 1]}</button>)}</div><button className="next-question" onClick={nextQuestion}>Next question →</button></div>}</div><aside className="support-panel"><div className="card-label">NEED HELP?</div><p>See the structure, not just the answer.</p><button onClick={requestHint}>Hint {hints > 0 && `(${hints}/3)`}</button><button onClick={showVisual}>Show matching visual</button><button onClick={() => requestExplain(false)}>Explain another way</button><button onClick={() => requestExplain(true)}>Give me an analogy</button>{hintText && <div className="hint"><b>{hints ? `Hint ${hints}` : "Tutor"}</b><p>{hintText}</p></div>}</aside>{visualVisible && <><AlgebraFrame question={question || undefined} /><div className="visual-strip"><AlgebraTiles question={question || undefined} /><NumberLine question={question || undefined} /><FunctionGraph question={question || undefined} /></div></>}</section>}
    {screen === "summary" && <section className="progress-view"><div className="eyebrow dark">SESSION COMPLETE</div><h1 className="dark-heading">Progress saved.<br /><em>Come back anytime.</em></h1>{sessionSummary ? <div className="diagnostic-result"><strong>{sessionSummary.questions_correct}/{sessionSummary.questions_attempted} correct</strong><span>Topic: {sessionSummary.topic}</span><span>Mastery: {Math.round(sessionSummary.mastery_start * 100)}% → {Math.round(sessionSummary.mastery_end * 100)}%</span></div> : <p>No answers were submitted in this session.</p>}<button className="primary-button" onClick={() => setScreen("topics")}>Back to topics</button></section>}
    {screen === "progress" && <section className="progress-view"><div className="eyebrow dark">MY ALGEBRA JOURNEY</div><h1 className="dark-heading">Your progress,<br /><em>made visible.</em></h1><div className="progress-number">{Math.round(overall * 100)}<small>% overall mastery</small></div><div className="progress-list">{skills.length ? skills.map(skill => <div key={skill.skill_id}><span>{skill.skill_id.replaceAll(".", " · ")}</span><b>{Math.round(skill.mastery_score * 100)}%</b><div className="progress-bar"><i style={{ width: `${skill.mastery_score * 100}%` }} /></div></div>) : <p>Complete a diagnostic and practice question to begin tracking your mastery.</p>}</div></section>}
    {error && <div className="toast error">{error}<button onClick={() => setError("")}>×</button></div>}
  </main>;
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
