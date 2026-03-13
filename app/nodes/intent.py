from langchain_openai import ChatOpenAI
from app.state import State
from app.schemas import IntentOutput

SYSTEM = """You are an intent classifier for a university bursar assistant.

Classify the user's request into exactly ONE of:
- outreach: send reminders/notifications to students with dues
- qna: look up or answer questions about a specific student or record
- summarize: reporting/aggregation across students (counts, totals, rollups)

You MUST return a structured output object.
"""

intent_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(IntentOutput)

def intent_node(state: State) -> State:
    errors = state.get("errors", [])
    entities = state.get("entities", {})

    user_text = ""
    for m in reversed(state["messages"]):
        if getattr(m, "type", None) == "human":
            user_text = m.content
            break
        if isinstance(m, dict) and m.get("role") == "user":
            user_text = m.get("content", "")
            break

    try:
        out: IntentOutput = intent_llm.invoke([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_text},
        ])
        intent = out.intent
    except Exception as e:
        intent = "qna"
        errors.append(f"intent_node failed, defaulting to qna: {repr(e)}")

    return {"intent": intent, "entities": entities, "errors": errors}