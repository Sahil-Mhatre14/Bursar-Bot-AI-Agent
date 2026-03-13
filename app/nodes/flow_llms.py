from langchain_openai import ChatOpenAI
from app.state import State

from app.tools.sqlite_tools import get_students_with_dues, get_student_by_id
from app.tools.email_tools import send_email

OUTREACH_TOOLS = [get_students_with_dues, send_email]
QNA_TOOLS = [get_student_by_id, get_students_with_dues]

outreach_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(OUTREACH_TOOLS)
qna_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(QNA_TOOLS)

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

QNA_SYSTEM = """You are BursarBot's QnA assistant for staff.
Use tools for data. Do not make up student records.
"""

def outreach_agent_node(state: State) -> State:
    msgs = state["messages"]
    resp = outreach_llm.invoke([{"role": "system", "content": OUTREACH_SYSTEM}] + msgs)
    return {"messages": [resp]}

def qna_agent_node(state: State) -> State:
    msgs = state["messages"]
    resp = qna_llm.invoke([{"role": "system", "content": QNA_SYSTEM}] + msgs)
    return {"messages": [resp]}