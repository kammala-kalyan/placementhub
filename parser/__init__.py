"""PlacementHub message parser package (shared by the API and the bot)."""

from parser.base import Parser
from parser.models import CATEGORIES, Category, ParsedJob
from parser.simple import SimpleParser

# Registry of available parsers. Phase 2 adds "rules"; an LLM parser
# could be registered here later without changing any caller.
_PARSERS: dict[str, type] = {"simple": SimpleParser}


def get_parser(name: str = "simple") -> Parser:
    """Create the parser selected by the PARSER setting."""
    try:
        return _PARSERS[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown parser {name!r}. Options: {sorted(_PARSERS)}") from exc


__all__ = ["CATEGORIES", "Category", "ParsedJob", "Parser", "SimpleParser", "get_parser"]
