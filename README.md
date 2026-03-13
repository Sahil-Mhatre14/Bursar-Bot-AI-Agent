### Bursar-Bot-AI-Agent

An agentic AI system to streamline tasks in a university bursar office.

---

### Features

- **Agentic workflow**: Uses LangGraph and LangChain to route between Q&A, outreach, and summarization agents.
- **SQLite-backed data**: Reads student fee/dues data from a local SQLite database.
- **Email outreach**: Sends reminder emails via SendGrid (with a safety override address for demos).
- **CLI interface**: Simple terminal chat loop in `main.py`.

---

### Prerequisites

- **Python**: 3.10 or newer
- **Virtual environment** (recommended): `venv`, `conda`, or similar
- **SendGrid account** (only required if you want email sending to work)
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

- **`OPENAI_API_KEY`**: API key for OpenAI (or equivalent provider. E.g: Gemini).
- **`LANGCHAIN_TRACING_V2`**: set to `true` to enable LangSmith tracing in order to see logs about tool calls, token usage, cost incured in a call, etc.
- **`LANGCHAIN_PROJECT`**: name of the LangSmith project.
- **`LANGSMITH_API_KEY`**: required only if you are using LangSmith.

Example:

```bash
OPENAI_API_KEY=your-openai-key-here
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

#### Email / SendGrid configuration

These are used by `app/tools/email_tools.py`:

- **`SENDGRID_API_KEY`**: Your SendGrid API key.
- **`BURSARBOT_EMAIL_FROM`**: The verified sender email in SendGrid (must be verified in your SendGrid account).
- **`BURSARBOT_EMAIL_OVERRIDE_TO`**: Safety override recipient. All emails will be sent to this address instead of arbitrary user-supplied addresses (for demo).

Example:

```bash
SENDGRID_API_KEY=your-sendgrid-api-key
BURSARBOT_EMAIL_FROM=your-verified-sender@example.com
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


