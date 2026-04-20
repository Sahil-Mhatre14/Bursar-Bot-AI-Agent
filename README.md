### Bursar-Bot-AI-Agent

An agentic AI system to streamline tasks in a university bursar office.

---

### Features

- **Agentic workflow**: Uses LangGraph and LangChain to route between Q&A, outreach, and summarization agents.
- **SQLite-backed data**: Reads student fee/dues data from a local SQLite database.
- **Email outreach**: Sends reminder emails via native Python SMTP (with a safety override address for demos).
- **CLI interface**: Simple terminal chat loop in `main.py`.

---

### Prerequisites

- **Python**: 3.10 or newer
- **Virtual environment** (recommended): `venv`, `conda`, or similar
- **Gmail account with App Password** (only required if you want email sending to work)
- **OpenAI (or compatible) API access** for `OPENAI_API_KEY`

---

### 1. Clone the repository

```bash
git clone https://github.com/Sahil-Mhatre14/Bursar-Bot-AI-Agent.git bursar-bot
cd bursar-bot
```

---

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
# .venv\Scripts\activate   # Windows (PowerShell/CMD)
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```


You may also need any other LangChain/LangGraph integrations you’re using in your local code.

---

### 4. Set up environment variables (`.env`)

Create a `.env` file in the project root (same folder as `main.py`). **Do not commit this file to git.**

#### Core model + tracing keys

- **`GEMINI_API_KEY`**: API key for Google Gemini (required for AI functionality).
- **`LANGCHAIN_TRACING_V2`**: set to `true` to enable LangSmith tracing in order to see logs about tool calls, token usage, cost incured in a call, etc.
- **`LANGCHAIN_PROJECT`**: name of the LangSmith project.
- **`LANGSMITH_API_KEY`**: required only if you are using LangSmith.

Example:

```bash
GEMINI_API_KEY=your-gemini-api-key-here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=bursarbot
LANGSMITH_API_KEY=your-langsmith-key-here
```

#### Database configuration

- **`BURSARBOT_DB_PATH`**: Path to the SQLite database file used by the tools in `app/tools/sqlite_tools.py`.
  - Default: `bursarbot.db` in the project root if this variable is not set.

Example:

```bash
BURSARBOT_DB_PATH=/absolute/or/relative/path/to/bursarbot.db
```

Make sure your database is populated.
You can use any helper scripts in the repo (`populate_sqlite.py`), if needed.

#### BigQuery configuration (for real finance data)

For finance questions like "what is my balance?", the agent can query BigQuery.

- **`GOOGLE_APPLICATION_CREDENTIALS`**: Absolute path to your GCP service account JSON (recommended).
- **`BQ_PROJECT_ID`**: BigQuery project ID (default: `sjsu-it-genai-poc`)
- **`BQ_DATASET_ID`**: BigQuery dataset ID (default: `student_financials`)
- **`BQ_FINANCE_TABLE_ID`**: BigQuery finance table (default: `Student_FinancialRecords`)

Example:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
BQ_PROJECT_ID=sjsu-it-genai-poc
BQ_DATASET_ID=student_financials
BQ_FINANCE_TABLE_ID=Student_FinancialRecords
```

#### Email / SMTP configuration

These are used by `app/tools/email_tools.py`:

- **`BURSARBOT_EMAIL_FROM`**: Your Gmail address.
- **`BURSARBOT_EMAIL_PASSWORD`**: Your Gmail App Password (not your regular password - see setup instructions below).
- **`BURSARBOT_EMAIL_OVERRIDE_TO`**: Safety override recipient. All emails will be sent to this address instead of arbitrary user-supplied addresses (for demo).

**Setting up Gmail App Password:**
1. Go to your Google Account settings
2. Enable 2-Factor Authentication if not already enabled
3. Go to Security → App passwords
4. Generate a new app password for "Mail"
5. Use this 16-character password as `BURSARBOT_EMAIL_PASSWORD`

Example:

```bash
BURSARBOT_EMAIL_FROM=your-gmail@gmail.com
BURSARBOT_EMAIL_PASSWORD=abcd-efgh-ijkl-mnop
BURSARBOT_EMAIL_OVERRIDE_TO=your-test-recipient@example.com
```

---

### 5. Run the agentic CLI

With your virtual environment active and `.env` configured:

```bash
python main.py
```

You should see:

```text
BursarBot (type 'quit' to exit)
```

Type messages as if you are a bursar staff member or student; the system will route between Q&A, outreach, and summarization flows as configured in `app/graph.py`. Type `quit` or `exit` to end the session.

---
