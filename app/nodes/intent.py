from langchain_google_genai import ChatGoogleGenerativeAI
from app.state import State
from app.schemas import IntentOutput

SYSTEM = """You are an intent classifier for a university bursar assistant.

Classify the user's request into exactly ONE of:

- outreach: The user wants to send, email, or contact past-due students.
  Examples: "send reminders to overdue students", "email students in the 91-120 day bucket",
  "contact all students with a hold", "send collection notices".

- qna: Everything else — lookups, listing students, bucket queries, reports,
  CSV exports, policy questions, balance checks, or any question about data.
  Examples: "give me students in the >150 bucket", "show all past due students",
  "what is student 001325845's balance?", "segregate students by aging bucket",
  "generate a report", "why does a student have a hold?", "export to CSV".

When in doubt, choose qna.
You MUST return a structured output object.
"""

intent_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0).with_structured_output(IntentOutput)

def intent_node(state: State) -> State:
    errors = state.get("errors", [])
    entities = state.get("entities", {})

    # Build last-N-turns context so short follow-ups ("all", "send email", "yes")
    # are classified correctly using the conversation history.
    context_msgs = []
    for m in state["messages"][-8:]:
        role = getattr(m, "type", None)
        if role == "human":
            context_msgs.append({"role": "user", "content": m.content})
        elif role == "ai":
            content = getattr(m, "content", "")
            if isinstance(content, list):
                content = " ".join(
                    p.get("text", "") for p in content if isinstance(p, dict)
                )
            text = str(content).strip()
            if text:
                context_msgs.append({"role": "assistant", "content": text[:300]})

    try:
        out: IntentOutput = intent_llm.invoke(
            [{"role": "system", "content": SYSTEM}] + context_msgs
        )
        intent = out.intent
    except Exception as e:
        intent = "qna"
        errors.append(f"intent_node failed, defaulting to qna: {repr(e)}")

    return {"intent": intent, "entities": entities, "errors": errors}