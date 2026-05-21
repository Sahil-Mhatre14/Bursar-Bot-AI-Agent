from langchain_google_genai import ChatGoogleGenerativeAI
from app.state import State
from app.tools.sqlite_tools import get_student_by_id
from app.tools.email_tools import send_email, send_outreach_email
from app.tools.bigquery_tools import get_student_balance_bigquery, get_students_past_due_by_bucket, get_student_comments, get_student_financial_aid

OUTREACH_TOOLS = [get_students_past_due_by_bucket, send_outreach_email]
QNA_TOOLS = [get_student_by_id, get_student_balance_bigquery, get_students_past_due_by_bucket, get_student_comments, get_student_financial_aid]
STUDENT_TOOLS = [get_student_balance_bigquery, get_student_comments, get_student_financial_aid]

outreach_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0).bind_tools(OUTREACH_TOOLS)
qna_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0).bind_tools(QNA_TOOLS)
student_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0).bind_tools(STUDENT_TOOLS)

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
1) If the user has already seen a student list in this conversation, use that data directly — do NOT re-fetch.
   If no list has been fetched yet, call get_students_past_due_by_bucket(bucket=..., limit=100).
2) Call ALL send_outreach_email tools IN A SINGLE RESPONSE — include every student as a separate
   tool call in the same message. Do NOT send one email, wait, then send the next. Batching all
   calls together is mandatory so they execute in parallel and the response stays fast.
   For each student, pass:
   - bucket: the aging bucket string (e.g. "61-90")
   - student_name: first_name + " " + last_name from the fetched data
   - student_id: student_id from the fetched data
   - email: email from the fetched data
   - balance: use the balance field returned by get_students_past_due_by_bucket (it is the student's total outstanding balance from the financials table)
   - address, city, state, postal: from the fetched data
   The tool automatically selects the correct official template (CL1/CL2/Final Demand).
   All buckets including ">150" are supported — Final Demand template is used for ">150".
3) Summarize: how many emails sent, which bucket (and notice type), which student IDs.

Rules:
- Never invent student data. Always use tools.
- Do not email students whose financial_aid_status is "Approved" (fee deferral).
- Always state which aging bucket you are working on.
- When tool results include a "report_path" field, render it as a markdown download link:
  [Download Excel Report](<report_path>)
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
- The tool returns one record per charge. Display EVERY record individually — never sum them into a total.
- Format each balance record as a labeled block (do NOT use bullet points or tables):

  **Balance #N**
  **Description:** <item_descr>
  **Date:** <item_effective_dt>
  **Balance:** $<balance>
  **Term:** <account_term>

  Leave a blank line between each record.
- Before listing the records, write one natural intro sentence such as:
  "Here are the X balance record(s) on file for your account:" (for students)
  or "Here are the X balance record(s) on file for student [ID]:" (for admin queries).

Financial aid:
- If the user asks about financial aid, awards, scholarships, or grants, use get_student_financial_aid(student_id=...).

Comments / notes:
- If the user asks about notes, comments, or history on a student account, use get_student_comments(student_id=...).

General:
- If a tool returns an error field, surface it clearly and suggest the likely fix.
- When tool results include a "report_path" field, render it as a markdown download link:
  [Download Excel Report](<report_path>)
"""

STUDENT_SYSTEM_TEMPLATE = """You are BursarBot, a financial assistant for SJSU Bursar's Office.

You are responding to an authenticated student. Their Student ID (EMPLID) is: {user_id}

Rules:
- You may ONLY answer questions about this student's own account.
- Always use student_id="{user_id}" when calling any tool. Never use a different student ID.
- Never discuss other students' records.
- Display EVERY balance record returned by the tool individually — never sum them into a total.
- Format each balance record as a labeled block (do NOT use bullet points or tables):

  **Balance #N**
  **Description:** <item_descr>
  **Date:** <item_effective_dt>
  **Balance:** $<balance>
  **Term:** <account_term>

  Leave a blank line between each record.
- Before listing the records, write one natural intro sentence such as:
  "Here are the X balance record(s) on file for your account:" (for students)
  or "Here are the X balance record(s) on file for student [ID]:" (for admin queries).
- If the tool returns a "report_path" field, tell the user an Excel report has been saved there.
- For questions about policy, payment options, or holds, answer based on your knowledge of SJSU Bursar policy.
"""

def outreach_agent_node(state: State) -> State:
    msgs = state["messages"]
    resp = outreach_llm.invoke([{"role": "system", "content": OUTREACH_SYSTEM}] + msgs)
    return {"messages": [resp]}

def qna_agent_node(state: State) -> State:
    msgs = state["messages"]
    system = QNA_SYSTEM
    user_id = state.get("user_id")
    if user_id:
        system = (
            f"CRITICAL: The authenticated user's EMPLID is {user_id}. "
            f"Whenever the user says 'my balance', 'my account', 'my financial aid', 'my holds', "
            f"or any first-person reference to their own account — ALWAYS call the tool immediately "
            f"with student_id='{user_id}'. NEVER ask them to provide their EMPLID.\n\n"
        ) + system
    resp = qna_llm.invoke([{"role": "system", "content": system}] + msgs)
    return {"messages": [resp]}

def student_agent_node(state: State) -> State:
    msgs = state["messages"]
    user_id = state.get("user_id", "")
    system = STUDENT_SYSTEM_TEMPLATE.format(user_id=user_id)
    resp = student_llm.invoke([{"role": "system", "content": system}] + msgs)
    return {"messages": [resp]}
