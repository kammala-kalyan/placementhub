"""Rule-based parser: regular expressions + simple rules, no AI and no API keys.

Each field has its own small function so it can be tested and explained alone.
General approach for every field:
  1. Look for an explicit label first ("Location: Pune").
  2. Fall back to common sentence patterns ("X is hiring ...").
  3. Otherwise return None: better empty than wrong.
"""

import re
import unicodedata
from datetime import date
from urllib.parse import urlparse

from parser.models import ParsedJob
from parser.simple import detect_category, find_apply_link
from parser.skills import extract_skills

URL_RE = re.compile(r"https?://\S+")

# ---------------------------------------------------------------- helpers


# Invisible emoji helpers: variation selectors (U+FE0E/U+FE0F) and zero-width joiner.
_EMOJI_JOINERS = {"︎", "️", "‍"}


def clean_line(line: str) -> str:
    """Drop emojis/symbols and markdown asterisks, collapse spaces."""
    kept = "".join(
        ch for ch in line
        if ch not in _EMOJI_JOINERS and unicodedata.category(ch) not in ("So", "Sk", "Cf", "Cs")
    )
    return re.sub(r"\s+", " ", kept.replace("*", "")).strip()


def clean_lines(text: str) -> list[str]:
    """Non-empty, cleaned lines with URLs removed."""
    lines = (clean_line(URL_RE.sub("", raw)) for raw in text.splitlines())
    return [line for line in lines if line]


def label_value(lines: list[str], labels: tuple[str, ...]) -> str | None:
    """Value of the first line that starts with one of the labels, e.g. 'Role: SDE'."""
    pattern = re.compile(rf"^(?:{'|'.join(labels)})\s*:\s*(.+)$", re.I)
    for line in lines:
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return None


def strip_brackets(value: str) -> str:
    """'SDE Intern (6 months)' -> 'SDE Intern'."""
    return re.sub(r"\s*\(.*?\)", "", value).strip(" .,;:-–|")


# Title lines look like "Company – Role" or "Company | Role | Full Time".
TITLE_SPLIT = re.compile(r"\s+(?:–|—|-|\|)\s+")
# "Kaveri Systems is hiring ...", "Lotus Cloudworks hiring – ...".
HIRING_RE = re.compile(
    r"^(?P<company>[\w&.' ]+?)\s+(?:is\s+)?(?:hiring|looking for|conducting)\b(?P<rest>.*)$", re.I)
# "... Hackathon by Monsoon Mobility", "Pre-Placement Talk by Kaveri Systems".
BY_RE = re.compile(r"\bby\s+([A-Z][\w&.]*(?:\s+[A-Z][\w&.]*)*)")
CAMPUS_DRIVE_RE = re.compile(r"^(.+?)\s+(?:on-)?campus drive\b", re.I)


def title_parts(lines: list[str]) -> list[str] | None:
    """Split the first title-like line (within the first 3) on dashes/pipes."""
    for line in lines[:3]:
        parts = TITLE_SPLIT.split(line)
        if len(parts) >= 2 and ":" not in parts[0]:
            return parts
    return None


def singular(words: str) -> str:
    """'Business Analysts' -> 'Business Analyst' (only the last word)."""
    if words.endswith("s") and not words.endswith("ss"):
        return words[:-1]
    return words


# ---------------------------------------------------------------- company


def extract_company(text: str, lines: list[str], apply_link: str | None) -> str | None:
    labelled = label_value(lines, ("company", "organisation", "organization"))
    if labelled:
        return strip_brackets(labelled)
    if lines:
        by = BY_RE.search(lines[0])
        if by:
            return by.group(1)
    for line in lines:
        hiring = HIRING_RE.match(line)
        if hiring:
            return hiring.group("company").strip()
    if lines:
        drive = CAMPUS_DRIVE_RE.match(lines[0])
        if drive:
            return drive.group(1).strip()
    parts = title_parts(lines)
    if parts:
        return strip_brackets(parts[0])
    return company_from_link(text, apply_link)


def company_from_link(text: str, link: str | None) -> str | None:
    """Last resort: 'https://konark-payments.example/...' -> find 'Konark Payments' in text."""
    if not link:
        return None
    host_parts = (urlparse(link).hostname or "").split(".")
    if len(host_parts) < 2:
        return None
    letters = [ch for ch in host_parts[-2] if ch.isalnum()]
    if not letters:
        return None
    # Allow spaces/hyphens between letters so "healthtech" matches "Health Tech".
    pattern = r"[\s-]*".join(re.escape(ch) for ch in letters)
    match = re.search(pattern, URL_RE.sub("", text), re.I)
    return match.group(0) if match else host_parts[-2].replace("-", " ").title()


# ---------------------------------------------------------------- role


def extract_role(lines: list[str], category: str) -> str | None:
    if category in ("Hackathon", "Other"):
        return None   # contests and notices have no job role
    labelled = label_value(lines, ("role", "position", "designation", "job role"))
    if labelled:
        return strip_brackets(labelled)
    for line in lines:
        hiring = HIRING_RE.match(line)
        if hiring:
            rest = hiring.group("rest").strip(" –-|:")
            words = re.match(r"(?:[A-Z][\w/&+-]*\s?)+", rest)
            if words:
                return singular(words.group(0).strip())
    parts = title_parts(lines)
    if parts:
        role = strip_brackets(parts[1])
        return role or None
    return None


# ---------------------------------------------------------------- location

CITIES = {
    "bengaluru": "Bengaluru", "bangalore": "Bengaluru", "hyderabad": "Hyderabad",
    "chennai": "Chennai", "pune": "Pune", "mumbai": "Mumbai", "gurugram": "Gurugram",
    "gurgaon": "Gurugram", "noida": "Noida", "kochi": "Kochi", "ahmedabad": "Ahmedabad",
    "mysuru": "Mysuru", "mysore": "Mysuru", "ballari": "Ballari", "delhi": "Delhi",
    "kolkata": "Kolkata", "remote": "Remote",
}
CITY_RE = re.compile(r"\b(" + "|".join(CITIES) + r")\b", re.I)
REMOTE_RE = re.compile(r"work from home|\bwfh\b|\bremote\b|mode\s*:\s*online", re.I)


def extract_location(lines: list[str]) -> str | None:
    labelled = label_value(lines, ("location", "job location", "posting", "venue",
                                   "place of posting"))
    if labelled:
        city = CITY_RE.search(labelled)
        if city:
            return CITIES[city.group(1).lower()]
        if REMOTE_RE.search(labelled):
            return "Remote"
        return strip_brackets(labelled)
    joined = "\n".join(lines)
    if REMOTE_RE.search(joined):
        return "Remote"
    city = CITY_RE.search(joined)
    return CITIES[city.group(1).lower()] if city else None


# ---------------------------------------------------------------- money

LPA_RANGE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lacs?)\b", re.I)
LPA_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lacs?)\b", re.I)
# Indian digit grouping: "Rs 6,00,000 per annum" = 6 lakhs.
ANNUM_RE = re.compile(
    r"(?:rs\.?|inr|₹)\s*(\d[\d,]{4,})\s*(?:/-)?\s*(?:per annum|p\.?\s?a\.?|/annum|per year)",
    re.I)


def extract_ctc_lpa(lines: list[str]) -> float | None:
    """CTC in lakhs per annum. For a range like 6-8 LPA we keep the upper value."""
    joined = "\n".join(lines)
    match = LPA_RANGE_RE.search(joined)
    if match:
        return float(match.group(2))
    match = LPA_RE.search(joined)
    if match:
        return float(match.group(1))
    match = ANNUM_RE.search(joined)
    if match:
        return round(int(match.group(1).replace(",", "")) / 100_000, 2)
    return None


STIPEND_AMOUNT_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(k)?\b", re.I)


def extract_stipend(lines: list[str]) -> int | None:
    """Monthly stipend in INR: '₹40,000/month', 'INR 30k/month', '45,000 INR per month'."""
    for line in lines:
        if "stipend" in line.lower():
            match = STIPEND_AMOUNT_RE.search(line)
            if match:
                amount = float(match.group(1).replace(",", ""))
                return int(amount * 1000 if match.group(2) else amount)
    return None


# ---------------------------------------------------------------- eligibility

CGPA_AFTER_RE = re.compile(r"cgpa[^\d\n]{0,25}?(\d{1,2}(?:\.\d{1,2})?)", re.I)
CGPA_BEFORE_RE = re.compile(r"(\d{1,2}(?:\.\d{1,2})?)\s*\+?\s*cgpa", re.I)


def extract_cgpa(lines: list[str]) -> float | None:
    """'CGPA 7.0 and above', 'minimum CGPA of 6.5', '8.0+ CGPA', 'CGPA ≥ 7.5'."""
    for line in lines:
        for pattern in (CGPA_AFTER_RE, CGPA_BEFORE_RE):
            match = pattern.search(line)
            if match and 0 < float(match.group(1)) <= 10:
                return float(match.group(1))
    return None


BATCH_LINE_RE = re.compile(r"batch|passing|pass-?out|graduat", re.I)
YEAR_RE = re.compile(r"\b(20[2-3]\d)\b")


def extract_batch(lines: list[str]) -> list[int]:
    """Passing-out years, only from lines that talk about batches (avoids deadline years)."""
    years: set[int] = set()
    for line in lines:
        if BATCH_LINE_RE.search(line):
            years.update(int(y) for y in YEAR_RE.findall(line))
    return sorted(years)


ALL_BRANCHES_RE = re.compile(
    r"\ball (?:branches|streams|disciplines)\b|\bany branch\b|\bopen to all\b", re.I)
BRANCH_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("CSE", re.compile(r"\bCSE\b|\bcomputer science\b", re.I)),
    ("ISE", re.compile(r"\bISE\b|\binformation science\b", re.I)),
    ("IT", re.compile(r"\bIT\b|(?i:(?<=[/,&|]\s)it\b|(?<=[/,&|])it\b)")),  # avoid English "it"
    ("AIML", re.compile(r"\bAI\s*[&/-]?\s*ML\b", re.I)),
    ("DS", re.compile(r"\bDS\b", re.I)),
    ("ECE", re.compile(r"\bECE\b", re.I)),
    ("EEE", re.compile(r"\bEEE\b|\belectrical\b", re.I)),
    ("MECH", re.compile(r"\bmech(?:anical)?\b|\bME\b", re.I)),
    ("CIVIL", re.compile(r"\bcivil\b", re.I)),
]


def extract_branches(lines: list[str]) -> list[str]:
    joined = "\n".join(lines)
    if ALL_BRANCHES_RE.search(joined):
        return ["ALL"]
    return [name for name, pattern in BRANCH_PATTERNS if pattern.search(joined)]


# ---------------------------------------------------------------- deadline

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
DMY_NUMERIC_RE = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b")          # 20/11/2026
DMY_TEXT_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b")
MDY_TEXT_RE = re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b")
DEADLINE_WORDS_RE = re.compile(
    r"deadline|last date|apply (?:by|before)|register|registration|closes|submit|before|\bby\b",
    re.I)


def _month(word: str) -> int | None:
    word = word.lower()
    number = MONTHS.get(word[:3])
    full_names = ("january february march april may june july august september "
                  "october november december").split()
    # Accept "Nov", "Nov.", "November", "Sept" but not "months".
    if number and (len(word) <= 4 or full_names[number - 1].startswith(word)):
        return number
    return None


def _make_date(year: str, month: int | None, day: str) -> date | None:
    try:
        return date(int(year), month, int(day)) if month else None
    except ValueError:
        return None


def find_dates(line: str) -> list[date]:
    """All valid dates in a line, in the order they appear."""
    found: list[tuple[int, date]] = []
    for m in DMY_NUMERIC_RE.finditer(line):        # Indian order: day/month/year
        d = _make_date(m.group(3), int(m.group(2)), m.group(1))
        if d:
            found.append((m.start(), d))
    for m in DMY_TEXT_RE.finditer(line):
        d = _make_date(m.group(3), _month(m.group(2)), m.group(1))
        if d:
            found.append((m.start(), d))
    for m in MDY_TEXT_RE.finditer(line):
        d = _make_date(m.group(3), _month(m.group(1)), m.group(2))
        if d:
            found.append((m.start(), d))
    return [d for _, d in sorted(found, key=lambda item: item[0])]


def extract_deadline(lines: list[str]) -> date | None:
    """Prefer a date on a 'deadline / apply by / last date' line, else the first date."""
    for line in lines:
        if DEADLINE_WORDS_RE.search(line):
            dates = find_dates(line)
            if dates:
                return dates[0]
    for line in lines:
        dates = find_dates(line)
        if dates:
            return dates[0]
    return None


# ---------------------------------------------------------------- parser


class RuleBasedParser:
    """Extracts every ParsedJob field with regex + rules."""

    name = "rules"

    def parse(self, text: str) -> ParsedJob:
        lines = clean_lines(text)
        category = detect_category(text)
        apply_link = find_apply_link(text)
        return ParsedJob(
            category=category,
            company=extract_company(text, lines, apply_link),
            role=extract_role(lines, category),
            location=extract_location(lines),
            ctc_lpa=extract_ctc_lpa(lines),
            stipend_month=extract_stipend(lines),
            branches=extract_branches(lines),
            cgpa_min=extract_cgpa(lines),
            batch=extract_batch(lines),
            deadline=extract_deadline(lines),
            apply_link=apply_link,
            skills=extract_skills("\n".join(lines)),
        )
