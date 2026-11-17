"""Load the sample placement messages into a running PlacementHub API.

Usage (from the repo root, with the stack running):
    python -m scripts.seed
    python -m scripts.seed --api http://<ec2-ip>

Uses only the Python standard library, so it runs anywhere without installs.
It goes through POST /ingest (the same path the Telegram bot uses), so it
also exercises parsing and duplicate detection.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, date, datetime, timedelta

from scripts.sample_messages import MESSAGES, render_message


def post_json(url: str, payload: dict) -> tuple[int, dict]:
    """POST a JSON body and return (status_code, parsed_json)."""
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, {"detail": exc.read().decode("utf-8", "replace")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--api", default="http://localhost:8000", help="API base URL")
    args = ap.parse_args()

    today = date.today()
    now = datetime.now(UTC)
    counts = {"created": 0, "duplicate": 0, "failed": 0}

    for i, message in enumerate(MESSAGES, start=1):
        payload = {
            "text": render_message(message, today),
            "source": "seed",
            # Spread posts over the last ~2 days so /jobs/latest has a clear order.
            "posted_at": (now - timedelta(hours=len(MESSAGES) - i)).isoformat(),
        }
        try:
            status, body = post_json(f"{args.api}/ingest", payload)
        except urllib.error.URLError as exc:
            print(f"Cannot reach the API at {args.api}: {exc.reason}")
            print("Is the stack running?  docker compose up -d --build")
            return 1

        if status in (200, 201):
            counts[body["status"]] += 1
            print(f"#{i:02d} {body['status']:<9} {body['job']['category']:<10} "
                  f"{(body['job'].get('company') or '-')[:30]}")
        else:
            counts["failed"] += 1
            print(f"#{i:02d} FAILED ({status}): {body.get('detail')}")

    print(f"\nDone: {counts['created']} created, {counts['duplicate']} duplicates skipped, "
          f"{counts['failed']} failed")
    return 0 if counts["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
