from langchain_google_genai import ChatGoogleGenerativeAI
from app.state import State
from app.tools.sqlite_tools import get_student_by_id
from app.tools.email_tools import send_email
from app.tools.bigquery_tools import get_student_balance_bigquery, get_students_past_due_by_bucket

OUTREACH_TOOLS = [get_students_past_due_by_bucket, send_email]
QNA_TOOLS = [get_student_by_id, get_student_balance_bigquery, get_students_past_due_by_bucket]

outreach_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0).bind_tools(OUTREACH_TOOLS)
qna_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0).bind_tools(QNA_TOOLS)

OUTREACH_SYSTEM = """You are BursarBot's outreach assistant for SJSU Bursar's Office.

You help staff manage past-due student accounts. Students are segmented into aging buckets
based on how many days their balance is past due:
  - 61-90 days   → First collection notice (CL1)
  - 91-120 days  → Second collection notice (CL2)
  - 121-150 days → Final demand notice
  - >150 days    → Escalation / collection agency territory

When the user asks to fetch, list, or segment students by due date / bucket:
1) Call get_students_past_due_by_bucket(bucket=..., limit=...).
   - Pass bucket="61-90", "91-120", "121-150", or ">150" to filter a specific bucket.
   - Pass bucket=None to get all past-due students across all buckets.
2) Present results grouped by aging_bucket. For each bucket show:
   - Count of students
   - List: student name, student_id, email, amount_due, balance, reason_codes
3) Clearly label which collection notice tier applies to each bucket.

When the user asks to send emails:
1) First fetch the relevant students using get_students_past_due_by_bucket.
2) For each student (MAX 5 unless user specifies), call send_email(to, subject, body).
   - Use the student's email and name from the fetched data.
   - Email templates per bucket will be provided later. For now use a professional reminder.
3) Summarize: how many emails sent, which bucket, which student IDs.

Rules:
- Never invent student data. Always use tools.
- Do not email students whose financial_aid_status is "Approved" (fee deferral).
- Always state which aging bucket you are working on.
- When tool results include a "report_path" field, always tell the user:
  "An Excel report has been saved to: <report_path>"
"""

QNA_SYSTEM = """You are BursarBot's QnA assistant for SJSU Bursar's Office.

Use tools for all data. Never invent student records.

Bucket / listing queries:
- If the user asks to list, show, or segment past-due students, use get_students_past_due_by_bucket(bucket=..., limit=...).
  Valid buckets: "61-90", "91-120", "121-150", ">150". Pass bucket=None for all past-due students.
- Present results grouped by aging_bucket. Show name, student_id, email, amount_due, balance, reason_codes.

Balance / finance queries:
- If the user asks about a specific student's balance, use get_student_balance_bigquery(student_id=...).
- If no student ID is provided, ask for the EMPLID first.

General:
- If a tool returns an error field, surface it clearly and suggest the likely fix.
- When tool results include a "report_path" field, always tell the user:
  "An Excel report has been saved to: <report_path>"
"""

def outreach_agent_node(state: State) -> State:
    msgs = state["messages"]
    resp = outreach_llm.invoke([{"role": "system", "content": OUTREACH_SYSTEM}] + msgs)
    return {"messages": [resp]}

def qna_agent_node(state: State) -> State:
    msgs = state["messages"]
    resp = qna_llm.invoke([{"role": "system", "content": QNA_SYSTEM}] + msgs)
    return {"messages": [resp]}