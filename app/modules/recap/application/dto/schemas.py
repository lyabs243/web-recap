from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class RecapSubmitRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=300)
    language: Literal["en", "fr"] = "en"


class JobAcceptedResponse(BaseModel):
    job_id: str


class ReferenceResponse(BaseModel):
    title: str
    url: str
    snippet: str
    favicon_url: str
    source: str


class RecapResultResponse(BaseModel):
    title: str
    markdown: str
    references: list[ReferenceResponse]


class ProgressEventResponse(BaseModel):
    type: Literal["progress", "completed", "failed"]
    stage: str
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    payload: dict | None = None
