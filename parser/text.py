"""Text normalization and hashing used to detect duplicate messages.

Two messages that differ only in case, emojis, punctuation or spacing
produce the same hash, so a re-forwarded post is recognised as a duplicate.
"""

import hashlib
import re
import unicodedata

_NON_WORD = re.compile(r"[^\w\s]")   # punctuation, emojis, symbols
_SPACES = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Lowercase, drop punctuation/emojis and collapse whitespace."""
    text = unicodedata.normalize("NFKC", text).lower()
    text = _NON_WORD.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def message_hash(text: str) -> str:
    """SHA-256 of the normalized text. Used as the Elasticsearch document id."""
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()
