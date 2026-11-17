"""Pydantic request/response models.

FastAPI uses these to validate input, serialize output and generate the
OpenAPI docs at /docs automatically.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from parser.models import ParsedJob


class IngestRequest(BaseModel):
    """One raw placement message to store."""

    text: str = Field(min_length=10, max_length=10_000, description="Raw message text")
    source: str = Field("manual", max_length=100, description="Where it came from, e.g. telegram")
    posted_at: datetime | None = Field(None, description="When it was posted (defaults to now)")


class Job(ParsedJob):
    """A stored job: parsed fields plus the original message and metadata."""

    id: str
    raw_text: str
    source: str
    posted_at: datetime


class IngestResponse(BaseModel):
    id: str
    status: Literal["created", "duplicate"]
    job: Job


class SearchResponse(BaseModel):
    total: int
    page: int
    size: int
    cached: bool = Field(description="True if served from the Redis cache")
    items: list[Job]


class JobList(BaseModel):
    total: int
    items: list[Job]


class ResumeResponse(BaseModel):
    resume_id: str
    skills: list[str] = Field(description="Skills found in the resume (never invented)")
    suggestions: list[str] = Field(description="Rewording tips for skills already listed")
    stored_in_s3: bool


class MatchedJob(Job):
    match_score: int = Field(description="Percent of the job's skills the resume has")
    matched_skills: list[str]
    missing_skills: list[str]


class MatchResponse(BaseModel):
    total: int
    min_score: int
    resume_skills: list[str]
    cached: bool
    items: list[MatchedJob]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    elasticsearch: Literal["up", "down"]
    redis: Literal["up", "down"]
