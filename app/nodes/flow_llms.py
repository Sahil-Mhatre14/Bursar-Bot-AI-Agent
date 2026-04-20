from langchain_google_genai import ChatGoogleGenerativeAI
from app.state import State

import re
from langchain_core.messages import AIMessage

from app.tools.sqlite_tools import get_students_with_dues, get_student_by_id
from app.tools.email_tools import send_email
from app.tools.bigquery_tools import get_student_balance_bigquery

OUTREACH_TOOLS = [get_students_with_dues, send_email]
QNA_TOOLS = [get_student_by_id, get_students_with_dues, get_student_balance_bigquery]

outreach_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0).bind_tools(OUTREACH_TOOLS)
qna_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0).bind_tools(QNA_TOOLS)

OUTREACH_SYSTEM = """You are BursarBot's outreach assistant.

When the user asks to send reminders:
1) Call get_students_with_dues(limit=..., term=...) to fetch recipients.
2) For each recipient (MAX 5 unless user specifies a smaller limit), call send_email(to, subject, body).
   Note: send_email will safely override the recipient to a test inbox.
3) After sending, summarize how many emails were sent and for which student IDs.

Rules:
- Do not invent student data. Use tools.
- Keep the email short and professional.
- Include: student name, term, and balance due.
"""

QNA_SYSTEM = """You are BursarBot's QnA assistant.

Use tools for data. Do not make up student records.

Finance questions:
- If the user asks about a student's balance / amount due / charges, use get_student_balance_bigquery(student_id=...).
- If the user doesn't provide a student ID (EMPLID), ask a short follow-up question requesting it.
- If a tool returns an `error` field, surface it verbatim and suggest the most likely fix (credentials, permissions, project/dataset/table).
"""

def outreach_agent_node(state: State) -> State:
    msgs = state["messages"]
    resp = outreach_llm.invoke([{"role": "system", "content": OUTREACH_SYSTEM}] + msgs)
    return {"messages": [resp]}

def qna_agent_node(state: State) -> State:
    msgs = state["messages"]

    # Finance fast-path:
    # Balance questions were getting routed to SQLite (dropping leading zeros).
    # For now we only force BigQuery for balance/amount-due style questions.
    user_text = ""
    for m in reversed(msgs):
        if getattr(m, "type", None) == "human":
            user_text = m.content or ""
            break
        if isinstance(m, dict) and m.get("role") == "user":
            user_text = m.get("content", "") or ""
            break

    # Also handle the common follow-up:
    # User: "what is my balance?" -> Assistant asks for EMPLID -> User replies with only the ID.
    prev_assistant_text = ""
    for m in reversed(msgs[:-1]):
        if getattr(m, "type", None) in {"ai", "assistant"}:
            prev_assistant_text = m.content or ""
            break
        if isinstance(m, dict) and m.get("role") == "assistant":
            prev_assistant_text = m.get("content", "") or ""
            break

    is_balance_intent = bool(
        re.search(r"\b(balance|amount\s+due|due\s+amount|charges?)\b", user_text, flags=re.I)
        or (
            re.search(r"\bemplid\b|\bstudent\s+id\b", prev_assistant_text, flags=re.I)
            and re.search(r"\b(balance|amount\s+due|due\s+amount|charges?)\b", prev_assistant_text, flags=re.I)
            and re.search(r"\b(\d{6,12})\b", user_text)
        )
    )

    if is_balance_intent:
        m = re.search(r"\b(\d{6,12})\b", user_text)
        if not m:
            return {
                "messages": [
                    AIMessage(
                        content="What is the student's ID (EMPLID)? Please include the numeric ID so I can look up the balance."
                    )
                ]
            }

        student_id = m.group(1)
        # `@tool` wraps this as a StructuredTool, so call via `.invoke`.
        out = get_student_balance_bigquery.invoke({"student_id": student_id})
        if out.get("error"):
            return {
                "messages": [
                    AIMessage(
                        content=f"BigQuery balance lookup failed for {student_id}: {out['error']}"
                    )
                ]
            }

        return {
            "messages": [
                AIMessage(
                    content=f"Current balance for {student_id} is {out.get('balance_formatted', out.get('balance_usd'))}."
                )
            ]
        }

    resp = qna_llm.invoke([{"role": "system", "content": QNA_SYSTEM}] + msgs)
    return {"messages": [resp]}