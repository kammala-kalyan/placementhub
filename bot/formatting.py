"""Turn API results into Telegram messages (HTML), plus /filter argument parsing.

Everything here is a pure function (input -> text), which makes it easy to test.
Telegram HTML needs <, > and & escaped, so every value from a message goes
through html.escape() to prevent broken formatting or injected markup.
"""

import re
from datetime import date, datetime, timedelta, timezone
from html import escape
from typing import Any

IST = timezone(timedelta(hours=5, minutes=30))   # India has no daylight saving
CARD_LIMIT = 5

HELP_TEXT = (
    "<b>PlacementHub bot</b>\n"
    "/search &lt;text&gt; – search openings (typos are OK)\n"
    "/latest – newest openings\n"
    "/deadlines – closing within 3 days\n"
    "/filter role=&lt;x&gt; location=&lt;y&gt; category=&lt;z&gt; – filter openings\n"
    "   e.g. /filter role=data analyst location=bengaluru\n"
    "/help – this message"
)

CATEGORY_ALIASES = {
    "fulltime": "Full-time", "full-time": "Full-time", "ft": "Full-time", "job": "Full-time",
    "intern": "Internship", "internship": "Internship",
    "hackathon": "Hackathon", "contest": "Hackathon",
    "other": "Other",
}


def today_ist() -> date:
    return datetime.now(IST).date()


def deadline_badge(deadline: date, today: date) -> str:
    """'closes today 🔴', 'in 2 days 🟠', or just the date for later deadlines."""
    days = (deadline - today).days
    if days < 0:
        return "closed"
    if days == 0:
        return "closes today 🔴"
    if days == 1:
        return "closes tomorrow 🔴"
    if days <= 3:
        return f"in {days} days 🟠"
    return f"in {days} days"


def format_job(job: dict[str, Any], today: date) -> str:
    """One job as a compact Telegram card."""
    title = escape(job.get("company") or "Unknown company")
    if job.get("role"):
        title += f" — {escape(job['role'])}"
    lines = [f"<b>{title}</b>", f"🏷 {escape(job.get('category') or 'Other')}"]

    if job.get("ctc_lpa"):
        lines.append(f"💰 ₹{job['ctc_lpa']:g} LPA")
    elif job.get("stipend_month"):
        lines.append(f"💰 ₹{job['stipend_month']:,}/month stipend")
    if job.get("location"):
        lines.append(f"📍 {escape(job['location'])}")

    eligibility = []
    if job.get("branches"):
        eligibility.append(escape(", ".join(job["branches"])))
    if job.get("cgpa_min"):
        eligibility.append(f"CGPA ≥ {job['cgpa_min']:g}")
    if job.get("batch"):
        eligibility.append(escape(", ".join(str(y) for y in job["batch"])) + " batch")
    if eligibility:
        lines.append("🎓 " + " · ".join(eligibility))

    if job.get("deadline"):
        deadline = date.fromisoformat(str(job["deadline"])[:10])
        lines.append(f"⏰ Apply by {deadline:%d %b %Y} ({deadline_badge(deadline, today)})")
    if job.get("apply_link"):
        lines.append(f'🔗 <a href="{escape(job["apply_link"], quote=True)}">Apply here</a>')
    return "\n".join(lines)


def format_job_list(title: str, data: dict[str, Any], today: date,
                    limit: int = CARD_LIMIT) -> str:
    """Header + up to `limit` cards. Telegram messages max out at 4096 chars."""
    items = data.get("items", [])[:limit]
    total = data.get("total", len(items))
    if not items:
        return f"<b>{escape(title)}</b>\nNo openings found."
    parts = [f"<b>{escape(title)}</b> ({total} found)"]
    parts += [format_job(job, today) for job in items]
    if total > len(items):
        parts.append(f"<i>Showing {len(items)} of {total}. Narrow it down with /filter.</i>")
    return "\n\n".join(parts)


_FILTER_RE = re.compile(r"(\w+)\s*=\s*(.+?)(?=\s+\w+\s*=|$)")


def parse_filter_args(args: list[str]) -> dict[str, str]:
    """'role=data analyst location=pune' -> {'role': 'data analyst', 'location': 'pune'}.

    Unknown keys are ignored; category values are normalised (intern -> Internship).
    """
    result: dict[str, str] = {}
    for key, value in _FILTER_RE.findall(" ".join(args)):
        key, value = key.lower(), value.strip()
        if key in ("role", "location"):
            result[key] = value
        elif key == "category" and value.lower() in CATEGORY_ALIASES:
            result["category"] = CATEGORY_ALIASES[value.lower()]
    return result
