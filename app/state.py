from typing import Annotated, TypedDict, List, Any, Optional, Dict
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    intent: Optional[str]
    entities: Dict[str, Any]
    result: Optional[str]
    errors: List[str]
    user_role: Optional[str]   # "student" or "admin"
    user_id: Optional[str]     # EMPLID — only set when user_role == "student"