"""Why-Q&A endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.llm.ask import answer_question
from app.llm.client import get_client

router = APIRouter(prefix="/api", tags=["ask"])


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AskResponse(BaseModel):
    headline: str = Field(description="one-line, plain-language answer")
    detail: str = Field(description="grounded explanation with inline citations")
    answer: str = Field(description="deprecated: headline + detail; kept for older consumers")
    citations: list[str]
    refused: bool
    degraded: bool
    confidence_cap: str | None


@router.post("/ask", response_model=AskResponse)
def ask(body: AskRequest) -> AskResponse:
    return AskResponse(**answer_question(body.question, get_client()))
