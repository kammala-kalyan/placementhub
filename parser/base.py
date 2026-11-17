"""The parser interface every implementation must follow.

Because the API only depends on this interface, we can swap the
rule-based parser for an LLM-based one later without touching the API.
"""

from typing import Protocol

from parser.models import ParsedJob


class Parser(Protocol):
    """Anything with a ``parse(text) -> ParsedJob`` method is a Parser."""

    name: str

    def parse(self, text: str) -> ParsedJob:
        """Extract structured fields from one raw placement message."""
        ...
