from typing import Literal, Optional
from pydantic import BaseModel, Field

class IntentOutput(BaseModel):
    intent: Literal["outreach", "qna", "summarize"] = Field(
        description="Route the user request into one of the 3 flows."
    )