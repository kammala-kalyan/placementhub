"""A minimal parser: detects only the category and the apply link.

Phase 1 uses this so ingestion and search work end to end. Phase 2 adds
the full rule-based parser (company, role, CTC, eligibility, deadline).
"""

import re

from parser.models import ParsedJob

# Checked in order: the first category whose pattern matches wins.
# Hackathon goes first because hackathon posts may also mention "interns".
CATEGORY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Hackathon", re.compile(
        r"\b(hackathon|ideathon|coding contest|code sprint|challenge|competition)\b", re.I)),
    ("Internship", re.compile(r"\b(interns?|internships?|stipend)\b", re.I)),
    ("Full-time", re.compile(
        r"\b(full[- ]time|fte|ctc|lpa|lakhs?|per annum|trainee)\b", re.I)),
]

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")


def detect_category(text: str) -> str:
    """Return the first matching category, or "Other"."""
    for category, pattern in CATEGORY_PATTERNS:
        if pattern.search(text):
            return category
    return "Other"


def find_apply_link(text: str) -> str | None:
    """Return the first URL in the message, without trailing punctuation."""
    match = URL_PATTERN.search(text)
    return match.group(0).rstrip(".,);]") if match else None


class SimpleParser:
    """Category + apply link only."""

    name = "simple"

    def parse(self, text: str) -> ParsedJob:
        return ParsedJob(category=detect_category(text), apply_link=find_apply_link(text))
