"""Bot message formatting and /filter parsing (pure functions)."""

from datetime import date

import pytest

from bot.formatting import deadline_badge, format_job, format_job_list, parse_filter_args

TODAY = date(2026, 11, 17)
JOB = {
    "id": "abc", "category": "Full-time", "company": "Konark Payments", "role": "SDE-1",
    "ctc_lpa": 14.0, "location": "Bengaluru", "branches": ["CSE", "ISE"], "cgpa_min": 8.0,
    "batch": [2027], "deadline": "2026-11-19",
    "apply_link": "https://konark-payments.example/careers/sde1",
}


@pytest.mark.parametrize("days, expected", [
    (-1, "closed"), (0, "closes today 🔴"), (1, "closes tomorrow 🔴"),
    (3, "in 3 days 🟠"), (10, "in 10 days"),
])
def test_deadline_badge(days, expected):
    assert deadline_badge(date.fromordinal(TODAY.toordinal() + days), TODAY) == expected


def test_card_contains_all_fields():
    card = format_job(JOB, TODAY)
    assert "<b>Konark Payments — SDE-1</b>" in card
    assert "₹14 LPA" in card and "📍 Bengaluru" in card
    assert "CSE, ISE · CGPA ≥ 8 · 2027 batch" in card
    assert "19 Nov 2026 (in 2 days 🟠)" in card
    assert 'href="https://konark-payments.example/careers/sde1"' in card


def test_card_shows_stipend_for_internships():
    card = format_job({"category": "Internship", "company": "X", "stipend_month": 40000}, TODAY)
    assert "₹40,000/month stipend" in card


def test_card_escapes_html_from_messages():
    card = format_job({"company": "<script>alert(1)</script>", "category": "Other"}, TODAY)
    assert "<script>" not in card and "&lt;script&gt;" in card


def test_list_with_no_results():
    assert "No openings found" in format_job_list("Results", {"total": 0, "items": []}, TODAY)


def test_list_is_capped_and_says_so():
    data = {"total": 12, "items": [JOB] * 12}
    text = format_job_list("Latest", data, TODAY)
    assert text.count("Konark Payments") == 5
    assert "Showing 5 of 12" in text
    assert len(text) < 4096          # Telegram's message limit


@pytest.mark.parametrize("args, expected", [
    (["role=data", "analyst", "location=pune"], {"role": "data analyst", "location": "pune"}),
    (["category=intern"], {"category": "Internship"}),
    (["role", "=", "devops"], {"role": "devops"}),
    (["salary=100", "category=party"], {}),            # unknown key / bad category ignored
    ([], {}),
])
def test_parse_filter_args(args, expected):
    assert parse_filter_args(args) == expected
