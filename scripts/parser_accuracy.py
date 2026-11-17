"""Measure parser accuracy against the hand-labelled sample messages.

Usage:
    python -m scripts.parser_accuracy                 # rules parser, fail below 90%
    python -m scripts.parser_accuracy --parser simple --min 0
    python -m scripts.parser_accuracy --verbose       # show every mismatch

Exit code 1 if overall accuracy is below --min, so CI or Jenkins can fail the build.
"""

import argparse
import sys
from datetime import date
from typing import Any

from parser import get_parser
from parser.base import Parser
from scripts.sample_messages import MESSAGES, deadline_for, render_message

FIELDS = ["category", "company", "role", "location", "ctc_lpa", "stipend_month",
          "cgpa_min", "batch", "branches", "deadline"]


def values_match(expected: Any, actual: Any) -> bool:
    """Compare one field: case-insensitive text, approximate numbers, lists as sets."""
    if expected is None:
        return actual in (None, [], "")
    if isinstance(expected, str):
        return isinstance(actual, str) and actual.strip().lower() == expected.strip().lower()
    if isinstance(expected, list):
        return {str(x).upper() for x in expected} == {str(x).upper() for x in (actual or [])}
    if isinstance(expected, int | float):
        return actual is not None and abs(float(actual) - float(expected)) < 0.01
    return expected == actual


def evaluate(parser: Parser, today: date) -> dict[str, Any]:
    """Run the parser over every unique labelled message and score each field."""
    scores = {field: {"correct": 0, "total": 0} for field in FIELDS}
    mismatches: list[str] = []
    for number, message in enumerate(MESSAGES, start=1):
        if "duplicate_of" in message:
            continue  # same content as an earlier message; don't count twice
        expected = {**message["expected"], "deadline": deadline_for(message, today)}
        parsed = parser.parse(render_message(message, today)).model_dump()
        for field in FIELDS:
            if field not in expected:
                continue
            scores[field]["total"] += 1
            if values_match(expected[field], parsed.get(field)):
                scores[field]["correct"] += 1
            else:
                mismatches.append(f"#{number:02d} {field}: expected {expected[field]!r}, "
                                  f"got {parsed.get(field)!r}")
    correct = sum(s["correct"] for s in scores.values())
    total = sum(s["total"] for s in scores.values())
    return {"fields": scores, "overall": correct / total if total else 0.0,
            "mismatches": mismatches}


def main() -> int:
    ap = argparse.ArgumentParser(description="Parser accuracy report")
    ap.add_argument("--parser", default="rules")
    ap.add_argument("--min", type=float, default=0.90, help="minimum overall accuracy (0-1)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    report = evaluate(get_parser(args.parser), date.today())
    print(f"Parser: {args.parser}\n")
    print(f"{'field':<14}{'correct':>8}{'total':>7}{'accuracy':>10}")
    for field, s in report["fields"].items():
        pct = s["correct"] / s["total"] if s["total"] else 0
        print(f"{field:<14}{s['correct']:>8}{s['total']:>7}{pct:>10.1%}")
    print(f"\nOVERALL: {report['overall']:.1%} (minimum {args.min:.0%})")
    if args.verbose and report["mismatches"]:
        print("\nMismatches:\n  " + "\n  ".join(report["mismatches"]))
    return 0 if report["overall"] >= args.min else 1


if __name__ == "__main__":
    sys.exit(main())
