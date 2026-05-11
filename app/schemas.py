from typing import Literal, Optional
from pydantic import BaseModel, Field

class IntentOutput(BaseModel):
    intent: Literal["outreach", "qna"] = Field(
        description="Route the user request into one of the 2 flows."
    )