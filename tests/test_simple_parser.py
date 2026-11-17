"""Tests for the Phase 1 SimpleParser and text hashing, using the sample messages."""

from datetime import date

import pytest

from parser import get_parser
from parser.text import message_hash, normalize_text
from scripts.sample_messages import MESSAGES, render_message

TODAY = date(2026, 11, 17)


@pytest.mark.parametrize("index", range(len(MESSAGES)))
def test_category_matches_label(index):
    message = MESSAGES[index]
    parsed = get_parser("simple").parse(render_message(message, TODAY))
    assert parsed.category == message["expected"]["category"]


def test_apply_link_has_no_trailing_punctuation():
    parsed = get_parser("simple").parse("Apply here: https://x.example/apply.")
    assert parsed.apply_link == "https://x.example/apply"


def test_normalize_ignores_case_emoji_and_spacing():
    assert normalize_text("🔥 Hello,   WORLD!! ") == "hello world"


def test_seed_duplicates_hash_to_the_same_id():
    for message in MESSAGES:
        if "duplicate_of" in message:
            original = MESSAGES[message["duplicate_of"] - 1]
            assert message_hash(render_message(message, TODAY)) == message_hash(
                render_message(original, TODAY))


def test_seed_has_50_messages_with_47_unique():
    hashes = {message_hash(render_message(m, TODAY)) for m in MESSAGES}
    assert len(MESSAGES) == 50
    assert len(hashes) == 47


def test_unknown_parser_name_raises():
    with pytest.raises(ValueError):
        get_parser("magic")
