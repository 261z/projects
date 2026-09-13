# AlgebraMate SG

AlgebraMate SG is an adaptive, retrieval-grounded algebra tutor for Singapore Secondary 1–4 students. It is designed as a live local capstone demonstration rather than a generic chatbot: deterministic mathematics and progress logic are combined with Chroma retrieval, LangGraph orchestration, structured tutoring agents, and a React learning interface.

## Architecture

```text
React + TypeScript + Vite
            |
         FastAPI
            |
       LangGraph
     /     |       \
  LangChain Python   SymPy
      |       |        |
 Agent Router Chroma  SQLite
```

React communicates only with FastAPI. Agent Router credentials remain on the backend. **SQLite answers “what has this student done?”** while **Chroma answers “what educational content is relevant?”**.

## Included capabilities

The current implementation includes registration, login, logout, protected endpoints, multi-user isolation, persistent SQLite progress, five-question diagnostics, deterministic initial mastery, Chroma question retrieval with metadata filtering, SymPy expression/equation checking, LangGraph practice and generation workflows, adaptive difficulty, difficulty overrides, structured tutoring-agent outputs, guarded hints, explanation/analogy fallbacks, generated-question verification, algebra frames, algebra tiles, number lines, function graphs, and a complete student-facing React flow.

## Requirements

- Python 3.12 or compatible Python 3.11+
- Node.js 22 or compatible Node.js 18+
- npm

## Installation

Clone the repository and enter the application directory:

```bash
git clone https://github.com/261z/projects.git
cd projects/algebramate-sg
```

### Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` for local configuration. The minimum local settings are already safe for deterministic development:

```dotenv
DATABASE_URL=sqlite:///./data/algebra_tutor.db
CHROMA_PATH=./data/chroma
JWT_SECRET=replace-this-for-your-local-demo
PRIMARY_MODEL=gpt-5.6-sol
FAST_MODEL=deepseek-v4-flash
```

For live Agent Router explanations, add the server-side credentials:

```dotenv
AGENT_ROUTER_API_KEY=your-server-side-key
AGENT_ROUTER_BASE_URL=your-agent-router-base-url
```

Never put the Agent Router key in frontend files or commit `.env`.

### Frontend setup

In a second terminal:

```bash
cd frontend
npm install
```

## Build the Chroma question bank

From the backend directory with the virtual environment active:

```bash
python -m app.rag.ingest
```

The ingestion command is idempotent: it uses stable question IDs and persists Chroma locally under `backend/data/chroma/`.

## Run the application

### Start the backend

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URLs:

- API: `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/health`
- Interactive API docs: `http://127.0.0.1:8000/docs`

### Start the frontend

In another terminal:

```bash
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`.

For a production frontend check:

```bash
npm run build
```

## Recommended demonstration flow

1. Register a user such as `student1`.
2. Log in.
3. Choose **Factorisation**.
4. Complete the five-question diagnostic.
5. Review the calculated initial mastery and recommended starting difficulty.
6. Start practice; the backend retrieves an approved question from Chroma.
7. Submit an incorrect answer and observe deterministic SymPy feedback.
8. Request a hint, explanation, analogy, or algebra-frame visualisation.
9. Submit the corrected answer.
10. Observe mastery and adaptive difficulty updates.
11. Override the recommended difficulty and continue.
12. Open **My progress**.
13. Log out and log in again; progress remains available.
14. Register a second user and verify that the first user’s progress is not visible.

## API surface

Authentication:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

Learning:

- `GET /topics`
- `POST /diagnostic/start`
- `POST /diagnostic/answer`
- `POST /practice/start`
- `POST /practice/answer`
- `GET /progress`

Tutor support:

- `POST /practice/hint`
- `POST /practice/explain`
- `POST /practice/analogy`
- `POST /practice/visualise`

## Testing

Run all backend tests:

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. pytest -q
```

The acceptance suite covers authentication, password hashing, protected endpoints, multi-user isolation, persistence, SymPy checking, Chroma ingestion and filtering, diagnostic scoring, mastery clamping, adaptive rules, structured-agent validation, hint guards, generated-question verification, bounded fallback, difficulty overrides, the complete demo flow, and restart persistence.

The frontend build is checked with:

```bash
cd frontend
npm run build
```

## Design principles

AlgebraMate SG does not ask an LLM to decide mathematical equivalence, authentication, authorization, mastery scores, or deterministic difficulty rules. SymPy, SQLite, Pydantic, and explicit Python rules handle those responsibilities. LLMs are used only where language and reasoning add value: intent understanding, misconception interpretation, explanations, analogies, and future grounded question generation.

## Phase completion

The supplied specification defines Phase 0 through Phase 19, which is 20 numbered phases in total. The repository contains the implementation and verification work for all phases, with warnings from third-party libraries remaining non-blocking. The final test result for the backend acceptance suite is **16 passed**.
