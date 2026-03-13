from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from app.state import State
from app.nodes.intent import intent_node
from app.nodes.flow_llms import outreach_agent_node, qna_agent_node
from app.nodes.summarize import summarize_node
from app.tools.sqlite_tools import (
    get_students_with_dues,
    get_student_by_id,
    get_students_due_next_30_days,
)
from app.tools.email_tools import send_email
from app.nodes.reset import reset_node



tools_node = ToolNode(tools=[get_students_with_dues, get_student_by_id, get_students_due_next_30_days, send_email])


def route_after_intent(state: State) -> str:
    intent = state.get("intent", "qna")
    if intent == "outreach":
        return "outreach_agent"
    if intent == "summarize":
        return "summarize"
    return "qna_agent"


def needs_tools(state: State) -> str:
    """
    If the last assistant message contains tool calls, go to ToolNode.
    Otherwise, we’re done.
    """
    msgs = state["messages"]
    last = msgs[-1]

    tool_calls = getattr(last, "tool_calls", None)
    if tool_calls and len(tool_calls) > 0:
        return "tools"

    return "done"


def finalize_result(state: State) -> State:
    if state.get("result"):
        return {"result": state["result"]}

    msgs = state.get("messages", [])
    if not msgs:
        return {"result": ""}

    last = msgs[-1]
    content = getattr(last, "content", "")
    return {"result": content}


def build_graph():
    builder = StateGraph(State)

    builder.add_node("intent", intent_node)

    builder.add_node("outreach_agent", outreach_agent_node)
    builder.add_node("qna_agent", qna_agent_node)
    builder.add_node("tools", tools_node)

    builder.add_node("summarize", summarize_node)
    builder.add_node("finalize", finalize_result)

    builder.add_node("reset", reset_node)

    builder.add_edge(START, "reset")
    builder.add_edge("reset", "intent")

    builder.add_conditional_edges(
        "intent",
        route_after_intent,
        {
            "outreach_agent": "outreach_agent",
            "qna_agent": "qna_agent",
            "summarize": "summarize",
        },
    )

    builder.add_conditional_edges(
        "outreach_agent",
        needs_tools,
        {"tools": "tools", "done": "finalize"},
    )

    builder.add_conditional_edges(
        "qna_agent",
        needs_tools,
        {"tools": "tools", "done": "finalize"},
    )

    def route_after_tools(state: State) -> str:
        intent = state.get("intent", "qna")
        return "outreach_agent" if intent == "outreach" else "qna_agent"

    builder.add_conditional_edges(
        "tools",
        route_after_tools,
        {"outreach_agent": "outreach_agent", "qna_agent": "qna_agent"},
    )


    builder.add_edge("summarize", "finalize")

    builder.add_edge("finalize", END)

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)