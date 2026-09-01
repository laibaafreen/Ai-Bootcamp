from typing import List
from pydantic import BaseModel, Field


class DebateRequest(BaseModel):
    topic: str
    num_rounds: int = Field(default=3, ge=1, description="Number of debate rounds")


class Turn(BaseModel):
    round: int
    speaker: str
    text: str


class DebateResponse(BaseModel):
    topic: str
    turns: List[Turn]
    winner: str
    reasoning: str
