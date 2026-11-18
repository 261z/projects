# SIA Inflight Dining Insights

An independent hackathon prototype for reviewing fictional, synthetic long-haul passenger food feedback. It is not affiliated with or connected to Singapore Airlines and contains no actual SIA data.

## What it does

- Paste newline-separated reviews or upload CSV/XLSX/PDF/DOCX/TXT/JSON.
- Load synthetic demo sets: A (1 review), B (30), and C (200).
- Classify sentiment, compute a deterministic health score, identify recurring complaint keywords, and surface mixed aspects.
- Chunk larger batches for analysis (50 reviews per chunk by default).
- Produce role-specific recommendations for cabin crew, catering/food prep, and menu design.
- Flag allergy, food-safety, medical, and serious service concerns for human review.
- Filter findings and export the reviewed rows, KPIs, themes, recommendations, and safety flags to Excel.

## Stack

- Frontend: React 18 + Vite, plain CSS, Lucide icons.
- Backend: Flask, pandas, openpyxl, optional OpenAI Responses API structured output.
- Tests: pytest for backend API and analytics.

## Run locally on macOS/Linux

Open Terminal and run the following commands from the project folder.

### 1. Start the Flask backend

```bash
cd "/Users/maimunahiskhander/Repositories/projects/SIA Inflight Dining Insights/backend"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
python -m app
```

Leave this Terminal window running. The backend should be available at `http://127.0.0.1:5000`.

### 2. Start the React frontend

Open a second Terminal window:

```bash
cd "/Users/maimunahiskhander/Repositories/projects/SIA Inflight Dining Insights/frontend"
npm install
npm run dev
```

Open the URL printed by Vite, usually `http://localhost:5173`.

The frontend proxies `/api` requests to Flask automatically. If the page cannot load data, confirm that the backend Terminal is still running.

### 3. Optional OpenAI setup

The app works without an API key using its deterministic offline analyzer. To enable the server-side OpenAI Responses API path, set the key only in the backend Terminal before starting Flask:

```bash
cd "/Users/maimunahiskhander/Repositories/projects/SIA Inflight Dining Insights/backend"
source .venv/bin/activate
export OPENAI_API_KEY="paste-your-key-here"
export OPENAI_MODEL="gpt-4o-mini"
python -m app
```

Never put the key in `frontend/src`, `index.html`, or any browser-visible file. Do not commit it to GitHub.

### Windows PowerShell equivalent

```powershell
cd "C:\path\to\SIA Inflight Dining Insights\backend"
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m app
```

In a second PowerShell window:

```powershell
cd "C:\path\to\SIA Inflight Dining Insights\frontend"
npm install
npm run dev
```

## First demo

1. Open the Vite URL.
2. Click sample set **C** to load 200 fictional long-haul reviews.
3. Click **Analyse feedback**.
4. Use the sentiment and route filters to explore the review table.
5. Click **Export Excel** to download the five-sheet workbook.

Use sample A for a one-review smoke check and sample B for a faster team demo.

## If installation fails

- Confirm Python 3.10+ and Node.js 18+ are installed with `python3 --version` and `node --version`.
- Run backend installation from inside `backend` while `.venv` is activated.
- Run frontend installation from inside `frontend`.
- If port 5000 is busy, stop the other Flask process or change the port in `backend/app/__main__.py`; update the Vite proxy in `frontend/vite.config.js` to match.
- If `pytest` is not found, run `python -m pip install -r requirements.txt` again and then `python -m pytest -q`.

## Generate or refresh the synthetic samples

The checked-in data is already ready to use. To regenerate it:

```bash
cd "/Users/maimunahiskhander/Repositories/projects/SIA Inflight Dining Insights/backend"
python scripts/generate_samples.py
```

## API

- `GET /api/health`
- `GET /api/samples/{a|b|c}`
- `POST /api/analyze` with `{ "reviews": [...], "use_ai": true|false }`
- `POST /api/parse-upload` with multipart field `file` for CSV/XLSX/PDF/DOCX/TXT/JSON
- `POST /api/export` with an analysis payload; returns an `.xlsx` file.

Review input fields: `review_id`, `review`, `route`, `cabin`, `flight_date`, `language`, `meal`, `seat`, and `loyalty_tier` are supported. Only `review` is required. Plain-text, PDF, and Word uploads accept one `review_id<TAB>review` record per line/paragraph.

## Upload test fixtures

Ready-made synthetic files are in `backend/data/upload_fixtures/`:

| File | Records | Expected overall signal |
|---|---:|---|
| `upload_negative_250.csv` | 250 | Negative |
| `upload_neutral_100.pdf` | 100 | Neutral |
| `upload_positive_300.txt` | 300 | Positive |
| `upload_positive_450.docx` | 450 | Positive |

These files are fictional and exist only to test the upload flow. Use one at a time in the dashboard, then click **Analyse feedback**.

## Product notes

This is an internal-review prototype. Safety flags are triage signals only; they are never a diagnosis or an automated operational decision. Human review is required before action.

## Master prompt for company Codex

```text
Build a complete runnable hackathon prototype named “SIA Inflight Dining Insights”. It must be an independent prototype using synthetic data only and must not imply affiliation with Singapore Airlines or use actual SIA customer data.

Use a React + Vite frontend and Flask Python backend. Keep any OpenAI API key server-side in the backend environment only; never put it in frontend code. Use the OpenAI Responses API with strict JSON-schema structured outputs when OPENAI_API_KEY is configured, but provide a deterministic offline fallback so the app runs without a key. Use pandas/openpyxl for Excel export. Do not use any external AI tool other than the optional server-side OpenAI Responses API path.

Problem: an analytics team needs to paste or upload batches of long-haul passenger meal reviews, classify positive/neutral/negative feedback, calculate a health score, identify recurring complaint keywords, and export a spreadsheet. Include three realistic fictional demo sets: A=1 review, B=30 reviews, C=200 reviews. Reviews should span routes and cabins, include Singlish, multilingual phrases, sarcasm, mixed aspects, meal details, optional metadata, distinct IDs, and varied sentiment. Do not use actual airline data.

Build:
1. Batch multiline paste and CSV/XLSX/PDF/DOCX/TXT/JSON upload with validation and a visible preview. The file picker must allow all six formats. The backend must parse CSV/XLSX tabular records and PDF/DOCX/TXT line records safely by buffering uploads into seekable memory before parsing. Include ready-to-upload synthetic fixtures: `upload_negative_250.csv` (250 reviews, overall negative), `upload_neutral_100.pdf` (100 reviews, overall neutral), `upload_positive_300.txt` (300 reviews, overall positive), and `upload_positive_450.docx` (450 reviews, overall positive).
2. Chunked analysis for 200 reviews (50 per chunk), deterministic KPIs, sentiment, topics, mixed aspects, recurring keywords, route/cabin filters, and human-review safety flags for allergy, food-safety, medical, and serious service concerns. Include demo sets A=1 review, B=30 reviews, and C=200 reviews with distinct IDs and balanced positive, neutral, and negative examples.
3. Define the deterministic health score explicitly: positive reviews contribute 100%, neutral reviews contribute 50%, and negative reviews contribute 0%; round to an integer from 0 to 100. Show actual positive, neutral, and negative counts plus an explicit overall sentiment label so users do not confuse health score with sentiment classification.
4. Provide role-specific recommendations for cabin crew, catering/food prep, and menu design. Include safety flags with human-review language; never present them as diagnoses or automatic decisions.
5. Export an Excel workbook with Reviewed Feedback, KPI Summary, Recurring Themes, Recommendations, and Safety Flags sheets.
6. Build a navy/gold editorial dashboard with excellent empty/loading/error states and responsive layout. Use green for positive, red for negative, and gold/amber for neutral. Use a red-to-gold-to-green gradient for the health score meter. The sentiment donut must use red/neutral/green segments and show the overall sentiment in its center; do not show only “positive %” without context.
7. Add backend tests for every supported upload format, analytics, health-score math, sentiment display data, safety flags, samples, analyze, and export. README must include exact macOS/PowerShell setup, API, offline mode, data disclaimer, fixture expectations, and this master prompt.

Prefer clear, maintainable source files over clever abstractions. Validate all inputs, never expose secrets to the browser, and make the local fallback the default for an easy demo.
```
