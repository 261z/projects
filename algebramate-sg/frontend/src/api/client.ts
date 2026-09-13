export type Auth = { access_token: string; username: string };
export type Question = { question_id: string; topic: string; skill_id: string; difficulty: number; question: string; answer: string; solution: string };
export type PracticeResult = { correct: boolean; mastery: number; recommended_action: string; recommended_difficulty: number; selected_difficulty: number; difficulty_overridden: boolean; feedback: string };
export type DiagnosticResult = { question_id: string; correct: boolean; answered: number; complete: boolean; raw_score?: number; initial_mastery?: number; recommended_starting_difficulty?: number };
const token = () => localStorage.getItem("algebramate_token");
async function request<T>(path: string, options: RequestInit = {}): Promise<T> { const response = await fetch(path, { ...options, headers: { "Content-Type": "application/json", ...(token() ? { Authorization: `Bearer ${token()}` } : {}), ...(options.headers || {}) } }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Something went wrong"); return data as T; }
export const api = {
  register: (username: string, password: string) => request<{ id: number; username: string }>("/auth/register", { method: "POST", body: JSON.stringify({ username, password }) }),
  login: (username: string, password: string) => request<Auth>("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  topics: () => request<{ name: string }[]>("/topics"),
  diagnosticStatus: (topic: string) => request<{ topic: string; complete: boolean; answered: number; total: number; raw_score?: number; initial_mastery?: number; recommended_starting_difficulty?: number }>(`/diagnostic/status?topic=${encodeURIComponent(topic)}`),
  diagnosticStart: (topic: string) => request<{ topic: string; questions: Question[]; total: number }>("/diagnostic/start", { method: "POST", body: JSON.stringify({ topic }) }),
  diagnosticAnswer: (question_id: string, student_answer: string) => request<DiagnosticResult>("/diagnostic/answer", { method: "POST", body: JSON.stringify({ question_id, student_answer }) }),
  startPractice: (topic: string, skill_id?: string, difficulty = 2, exclude_question_ids: string[] = []) => request<{ question: Question; retrieval: string }>("/practice/start", { method: "POST", body: JSON.stringify({ topic, skill_id, difficulty, exclude_question_ids }) }),
  answer: (question_id: string, student_answer: string, selected_difficulty?: number, hints_used = 0) => request<PracticeResult>("/practice/answer", { method: "POST", body: JSON.stringify({ question_id, student_answer, selected_difficulty, hints_used }) }),
  hint: (question_id: string, hint_level: number) => request<{ hint: string }>("/practice/hint", { method: "POST", body: JSON.stringify({ question_id, hint_level }) }),
  explain: (question_id: string, analogy = false) => request<{ text: string }>(`/practice/${analogy ? "analogy" : "explain"}`, { method: "POST", body: JSON.stringify({ question_id, hint_level: 1 }) }),
  progress: () => request<{ skills: { skill_id: string; mastery_score: number; current_difficulty: number }[]; overall_mastery: number }>("/progress"),
};
