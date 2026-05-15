from __future__ import annotations

import logging
import uuid
from typing import Optional, Dict, Any, List

logger = logging.getLogger("bursarbot.api")

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

# IMPORTANT: load .env BEFORE importing anything that instantiates LLM clients.
load_dotenv()

from app.graph import build_graph  # noqa: E402
from app.tools.bigquery_tools import get_user_role  # noqa: E402

app = FastAPI(title="BursarBot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    thread_id: Optional[str] = Field(
        default=None,
        description="Conversation thread/session id. If omitted, a new one is created.",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="EMPLID of the authenticated user, passed by the auth layer.",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional metadata (e.g., user id, channel)."
    )


class ChatResponse(BaseModel):
    thread_id: str
    intent: Optional[str] = None
    answer: str
    errors: List[str] = []


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    thread_id = req.thread_id or str(uuid.uuid4())

    if not req.user_id:
        raise HTTPException(status_code=400, detail="user_id is required.")

    user_role = get_user_role(req.user_id)

    if user_role == "student":
        logger.info(f"User '{req.user_id}' is querying for self")
    else:
        logger.info(f"Authenticated user (from 3rd party/Okta): {req.user_id}")
        logger.info(f"{user_role.capitalize()} '{req.user_id}' is querying — role: {user_role}")

    out = graph.invoke(
        {
            "messages": [HumanMessage(content=req.message)],
            "entities": {},
            "errors": [],
            "user_role": user_role,
            "user_id": req.user_id,
        },
        config={
            "configurable": {"thread_id": thread_id},
            "tags": ["api", "bursarbot"],
            "metadata": req.metadata or {"entrypoint": "api.py"},
            "run_name": "bursarbot_api_turn",
        },
    )

    return ChatResponse(
        thread_id=thread_id,
        intent=out.get("intent"),
        answer=out.get("result") or "",
        errors=out.get("errors") or [],
    )

