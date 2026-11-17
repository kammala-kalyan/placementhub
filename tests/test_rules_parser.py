"""Tests for the rule-based parser: one focused test per tricky format."""

from datetime import date

import pytest

from parser import get_parser
from parser.rules import (
    clean_lines,
    extract_batch,
    extract_branches,
    extract_cgpa,
    extract_ctc_lpa,
    extract_deadline,
    extract_location,
    extract_stipend,
)
from scripts.parser_accuracy import FIELDS, evaluate, values_match


def lines(text: str) -> list[str]:
    return clean_lines(text)


# ---------- money ----------
@pytest.mark.parametrize("text, expected", [
    ("CTC: 7.5 LPA", 7.5),
    ("CTC: 6-8 LPA (based on interview)", 8.0),        # range -> upper value
    ("Package: Rs 6,00,000 per annum", 6.0),            # Indian lakh grouping
    ("CTC: Rs 4.8 Lakhs p.a.", 4.8),
    ("ctc: 14 lpa", 14.0),
    ("Prize pool: ₹2,00,000", None),                    # prize money is not a CTC
])
def test_ctc(text, expected):
    assert extract_ctc_lpa(lines(text)) == expected


@pytest.mark.parametrize("text, expected", [
    ("Stipend: ₹40,000/month", 40000),
    ("Stipend: INR 30k/month", 30000),
    ("Stipend: 45,000 INR per month", 45000),
    ("Stipend: ₹15K per month", 15000),
    ("CTC: 12 LPA", None),
])
def test_stipend(text, expected):
    assert extract_stipend(lines(text)) == expected


# ---------- eligibility ----------
@pytest.mark.parametrize("text, expected", [
    ("CGPA 7.0 and above", 7.0),
    ("Open to all branches with a minimum CGPA of 6.5.", 6.5),
    ("CSE & ISE students of 2027 batch with 8.0+ CGPA", 8.0),   # must not read 2027
    ("CGPA ≥ 7.5", 7.5),
    ("Batch: 2027 | Minimum CGPA: 6.0", 6.0),
    ("No CGPA criteria mentioned here", None),
])
def test_cgpa(text, expected):
    assert extract_cgpa(lines(text)) == expected


def test_batch_ignores_deadline_years():
    text = "Batch: 2027\nDeadline: 20 Nov 2026\nOpen to 2028 and 2029 batches"
    assert extract_batch(lines(text)) == [2027, 2028, 2029]


@pytest.mark.parametrize("text, expected", [
    ("Eligibility: B.Tech CSE / ISE / AIML / DS", {"CSE", "ISE", "AIML", "DS"}),
    ("Branches: EEE, Mechanical, Civil", {"EEE", "MECH", "CIVIL"}),
    ("eligibility: cse / ise / it | 2027 batch", {"CSE", "ISE", "IT"}),
    ("Open to all branches", {"ALL"}),
    ("We will review it carefully", set()),            # English "it" is not a branch
])
def test_branches(text, expected):
    assert set(extract_branches(lines(text))) == expected


# ---------- location ----------
@pytest.mark.parametrize("text, expected", [
    ("Location: Bengaluru (on-site)", "Bengaluru"),
    ("Location: Bangalore", "Bengaluru"),                # alias -> canonical name
    ("Venue: Konark Payments office, Bengaluru", "Bengaluru"),
    ("Duration: 3 months | Work from home", "Remote"),
    ("Mode: Online", "Remote"),
])
def test_location(text, expected):
    assert extract_location(lines(text)) == expected


# ---------- deadline ----------
@pytest.mark.parametrize("text, expected", [
    ("Last date to apply: 20 Nov 2026", date(2026, 11, 20)),
    ("Apply before 05/12/2026", date(2026, 12, 5)),          # Indian day/month order
    ("Deadline: 05-12-2026", date(2026, 12, 5)),
    ("Registration closes on 3 December 2026", date(2026, 12, 3)),
    ("Apply by November 20, 2026", date(2026, 11, 20)),
    ("Duration: 6 months (Jan to Jun)", None),
    ("Deadline: 31/02/2026", None),                           # invalid date is ignored
])
def test_deadline(text, expected):
    assert extract_deadline(lines(text)) == expected


# ---------- whole messages ----------
def test_full_message():
    job = get_parser("rules").parse(
        "🔥 Konark Payments – SDE-1 🔥\nCTC: 14 LPA\nLocation: Bengaluru\n"
        "Eligibility: CSE / ISE / IT | 2027 batch | CGPA 8.0 and above\n"
        "Apply by 20 Nov 2026\nLink: https://konark-payments.example/careers/sde1")
    assert (job.category, job.company, job.role) == ("Full-time", "Konark Payments", "SDE-1")
    assert job.ctc_lpa == 14.0 and job.cgpa_min == 8.0 and job.batch == [2027]
    assert job.deadline == date(2026, 11, 20)
    assert job.apply_link == "https://konark-payments.example/careers/sde1"


def test_hiring_sentence_gives_company_and_singular_role():
    job = get_parser("rules").parse("Varuna Ledger is hiring Business Analysts 📊\nCTC: 8 LPA")
    assert job.company == "Varuna Ledger"
    assert job.role == "Business Analyst"


def test_hackathon_has_no_role_and_company_from_by():
    job = get_parser("rules").parse("Smart Campus Ideathon by Silverline Edu\nMode: Online")
    assert job.category == "Hackathon"
    assert job.company == "Silverline Edu"
    assert job.role is None


def test_empty_message_does_not_crash():
    job = get_parser("rules").parse("hello there, nothing useful in this message")
    assert job.category == "Other" and job.company is None and job.deadline is None


# ---------- accuracy gate (same check the nightly Jenkins job runs) ----------
def test_accuracy_on_labelled_samples_is_at_least_95_percent():
    report = evaluate(get_parser("rules"), date(2026, 11, 17))
    assert report["overall"] >= 0.95, report["mismatches"]
    for field in FIELDS:
        s = report["fields"][field]
        assert s["correct"] / s["total"] >= 0.90, (field, report["mismatches"])


def test_values_match_rules():
    assert values_match("Data Analyst", " data analyst ")
    assert values_match(["CSE", "IT"], ["it", "cse"])
    assert values_match(7.5, 7.50001)
    assert values_match(None, [])
    assert not values_match("Pune", None)
