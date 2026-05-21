# BursarBot

An agentic AI assistant for the SJSU Bursar's Office. It routes requests between Q&A, student outreach, and summarization flows using LangGraph and Google Gemini.

This guide walks you through running the **backend API** and the **Next.js chat UI** on your machine.

---

## Project layout

The app is split across two folders (sibling directories):

| Folder | Role |
|--------|------|
| `bursar-bot/` (this repo) | Python backend — FastAPI API, LangGraph agent, tools |
| `frontend/` | Next.js 15 chat UI (lives next to this repo, not inside it) |

Expected directory structure:

```text
Bursar Bot/
├── bursar-bot/     ← clone this repo here
└── frontend/       ← Next.js app (separate folder)
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| **Python** | 3.10+ |
| **Node.js** | 18+ (20+ recommended) |
| **npm** | Comes with Node |

**API keys and credentials** (see [Environment variables](#environment-variables)):

- **Required:** `GEMINI_API_KEY` (Google Gemini — powers all LLM calls)
- **Recommended:** BigQuery service account (`GOOGLE_APPLICATION_CREDENTIALS`) for live balance / past-due data
- **Optional:** Gmail App Password for sending outreach emails; LangSmith for tracing

The repo ships with `bursarbot.db` and `bursarbot_students.csv` for local SQLite lookups. BigQuery is used when configured for finance queries.

---

## 1. Clone and open the backend

```bash
git clone https://github.com/Sahil-Mhatre14/Bursar-Bot-AI-Agent.git bursar-bot
cd bursar-bot
```

---

## 2. Backend setup

### Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
# venv\Scripts\activate    # Windows
```

### Install Python dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file in the `bursar-bot` root (same folder as `api.py`). **Do not commit this file.**

Minimum for the web UI and API to respond:

```bash
GEMINI_API_KEY=your-gemini-api-key-here
```

See [Environment variables](#environment-variables) for the full list (BigQuery, email, database, LangSmith).

### (Optional) Populate SQLite

If you need a fresh database from CSV/Excel:

```bash
python populate_sqlite.py --input bursarbot_students.csv --db bursarbot.db
```

---

## 3. Start the backend

With the virtual environment active:

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8001
```

You should see Uvicorn listening on port **8001**.

**Verify the API:**

```bash
curl http://localhost:8001/health
# {"status":"ok"}
```

Leave this terminal running.

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `POST /chat` | Send a message (`message`, `user_id`, optional `thread_id`) |
| `GET /reports/{filename}` | Download generated Excel reports |

---

## 4. Frontend setup

Open a **second terminal**. The frontend folder sits beside `bursar-bot`:

```bash
cd ../frontend
```

If you do not have the frontend yet, obtain it from your team or the project’s frontend repository and place it at `Bursar Bot/frontend/`.

### Install Node dependencies

```bash
npm install
```

### (Optional) Point the UI at a different API URL

By default the UI calls `http://localhost:8001` directly. To override, create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8001
```

---

## 5. Start the frontend

```bash
npm run dev
```

Open **[http://localhost:3000](http://localhost:3000)** in your browser.

The UI includes a **Demo Persona** switcher (Admin vs Student) with preset EMPLIDs. The backend requires `user_id` on every `/chat` request; the frontend sends the selected persona’s ID.

---

## Quick start (two terminals)

**Terminal 1 — backend:**

```bash
cd bursar-bot
source venv/bin/activate
uvicorn api:app --reload --port 8001
```

**Terminal 2 — frontend:**

```bash
cd frontend
npm run dev
```

Then visit [http://localhost:3000](http://localhost:3000) and send a message (e.g. “What is my balance?” as the Student persona).

---

## Environment variables

Create `bursar-bot/.env` in the backend root.

### Core (required for AI)

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key (used by `langchain-google-genai`) |

### LangSmith tracing (optional)

| Variable | Description |
|----------|-------------|
| `LANGCHAIN_TRACING_V2` | Set to `true` to enable tracing |
| `LANGCHAIN_PROJECT` | LangSmith project name |
| `LANGSMITH_API_KEY` | LangSmith API key |

### SQLite (local student data)

| Variable | Description |
|----------|-------------|
| `BURSARBOT_DB_PATH` | Path to SQLite DB (default: `bursarbot.db` in project root) |

### BigQuery (finance / past-due buckets)

| Variable | Description |
|----------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Absolute path to GCP service account JSON |
| `BQ_PROJECT_ID` | Default: `sjsu-it-genai-poc` |
| `BQ_DATASET_ID` | Default: `student_financials` |
| `BQ_FINANCE_TABLE_ID` | Default: `Student_FinancialRecords` |

Place your service account JSON in the project (e.g. `service-account.json`) and add that filename to `.gitignore` — it is already ignored.

### Email / SMTP (outreach only)

| Variable | Description |
|----------|-------------|
| `SENDER_EMAIL` | Gmail address used to send mail |
| `BURSARBOT_EMAIL_PASSWORD` | Gmail [App Password](https://myaccount.google.com/apppasswords) (not your login password) |
| `RECEIVER_EMAIL` | All outbound mail goes here in demo mode |

**Gmail App Password steps:** Google Account → Security → 2-Step Verification → App passwords → create one for Mail.

### Other

| Variable | Description |
|----------|-------------|
| `BURSARBOT_BACKEND_URL` | Base URL embedded in report download links (default: `http://localhost:8001`) |
| `BURSARBOT_REPORTS_DIR` | Directory for generated reports (default: `reports/`) |

**Example `.env`:**

```bash
GEMINI_API_KEY=your-gemini-api-key-here

GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
BQ_PROJECT_ID=sjsu-it-genai-poc
BQ_DATASET_ID=student_financials
BQ_FINANCE_TABLE_ID=Student_FinancialRecords

SENDER_EMAIL=your-gmail@gmail.com
BURSARBOT_EMAIL_PASSWORD=your-16-char-app-password
RECEIVER_EMAIL=your-test@example.com

LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=bursarbot
LANGSMITH_API_KEY=your-langsmith-key
```

---

## CLI mode (no frontend)

For a terminal-only session:

```bash
source venv/bin/activate
python main.py
```

You should see `BursarBot (type 'quit' to exit)`. Type `quit` or `exit` to stop.

---

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| Frontend shows “something went wrong” | Confirm backend is running on port **8001** and `curl http://localhost:8001/health` returns `ok`. |
| CORS errors in the browser | Backend allows `http://localhost:3000` and `http://localhost:3001`. Use `npm run dev` (port 3000) or add your origin in `api.py`. |
| `user_id is required` | Use the persona switcher in the UI, or pass `user_id` in `POST /chat`. |
| `ModuleNotFoundError: markdown` | Run `pip install -r requirements.txt` again (`markdown` is listed in `requirements.txt`). |
| BigQuery / balance errors | Set `GOOGLE_APPLICATION_CREDENTIALS` and confirm the service account can read the dataset. |
| Outreach emails not sending | Set Gmail variables; emails still go to `RECEIVER_EMAIL` in demo mode. |
| Long outreach requests time out | The frontend calls the API directly (not via Next proxy) to avoid short proxy timeouts. Keep `NEXT_PUBLIC_API_BASE` pointed at the backend if you customize it. |

---

## Features

- **Agentic workflow:** LangGraph routes between Q&A, outreach, and summarization agents.
- **SQLite:** Local student fee/dues data via `bursarbot.db`.
- **BigQuery:** Live financial records when GCP credentials are configured.
- **Email outreach:** SMTP reminders with a safety override recipient for demos.
- **Web UI:** Next.js chat at `localhost:3000` talking to FastAPI on `localhost:8001`.
- **CLI:** `python main.py` for quick testing without the UI.

---

## Ports reference

| Service | URL |
|---------|-----|
| Frontend (Next.js) | http://localhost:3000 |
| Backend (FastAPI) | http://localhost:8001 |
| API health | http://localhost:8001/health |
