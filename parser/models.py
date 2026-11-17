"""Data model for a structured job extracted from a placement message."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

# The four job categories agreed in the design (also the Telegram topic tabs).
Category = Literal["Full-time", "Internship", "Hackathon", "Other"]
CATEGORIES: tuple[str, ...] = ("Full-time", "Internship", "Hackathon", "Other")


class ParsedJob(BaseModel):
    """Structured fields pulled out of one raw placement message.

    Every field except ``category`` is optional, because real messages
    often leave things out (no CTC, no deadline, ...).
    """

    category: Category = "Other"
    company: str | None = None
    role: str | None = None
    location: str | None = None
    ctc_lpa: float | None = Field(None, description="Full-time CTC in lakhs per annum")
    stipend_month: int | None = Field(None, description="Internship stipend in INR per month")
    branches: list[str] = Field(default_factory=list, description="Eligible branches, e.g. CSE")
    cgpa_min: float | None = None
    batch: list[int] = Field(default_factory=list, description="Eligible passing-out years")
    deadline: date | None = None
    apply_link: str | None = None
    skills: list[str] = Field(default_factory=list, description="Reserved for Resume Match")
