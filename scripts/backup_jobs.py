"""Back up every job (including the raw message text) from Elasticsearch to S3.

Output: gzipped JSON Lines, one job per line, uploaded to
    s3://<bucket>/backups/YYYY/MM/DD/jobs-<timestamp>.jsonl.gz

Usage:
    python3 -m scripts.backup_jobs --es-url http://127.0.0.1:9200 --bucket <name>
    python3 -m scripts.backup_jobs --out-dir backups            # local file only

Runs in two places:
- nightly cron on EC2 (Amazon Linux's built-in Python 3.9, no pip installs,
  uploads with the AWS CLI using the instance's IAM role);
- the nightly Jenkins pipeline (uses boto3 if it is installed).
So this file uses only the standard library and Python 3.9-compatible syntax.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import sys
import urllib.request
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path


def es_request(url: str, body: dict | None = None, method: str = "POST") -> dict:
    """Small JSON-over-HTTP helper for the Elasticsearch REST API."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read() or b"{}")


def iter_jobs(es_url: str, index: str = "jobs", page_size: int = 500) -> Iterator[dict]:
    """Yield every document using the scroll API (works for any index size)."""
    page = es_request(f"{es_url}/{index}/_search?scroll=2m",
                      {"size": page_size, "sort": ["_doc"]})
    scroll_id = page.get("_scroll_id")
    try:
        while page["hits"]["hits"]:
            for hit in page["hits"]["hits"]:
                yield {"id": hit["_id"], **hit["_source"]}
            page = es_request(f"{es_url}/_search/scroll",
                              {"scroll": "2m", "scroll_id": scroll_id})
            scroll_id = page.get("_scroll_id", scroll_id)
    finally:
        if scroll_id:   # free the scroll context on the server
            es_request(f"{es_url}/_search/scroll", {"scroll_id": scroll_id}, method="DELETE")


def write_backup(jobs: Iterator[dict], path: Path) -> int:
    """Write jobs as gzipped JSON lines; returns how many were written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with gzip.open(path, "wt", encoding="utf-8") as out:
        for job in jobs:
            out.write(json.dumps(job, ensure_ascii=False) + "\n")
            count += 1
    return count


def upload(path: Path, bucket: str, key: str, region: str) -> None:
    """Upload with boto3 when available, otherwise with the AWS CLI."""
    try:
        import boto3
    except ImportError:
        subprocess.run(["aws", "s3", "cp", str(path), f"s3://{bucket}/{key}",
                        "--region", region, "--only-show-errors"], check=True)
        return
    boto3.client("s3", region_name=region).upload_file(str(path), bucket, key)


def backup_key(now: datetime) -> str:
    return f"backups/{now:%Y/%m/%d}/jobs-{now:%Y%m%dT%H%M%SZ}.jsonl.gz"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Back up jobs from Elasticsearch to S3")
    ap.add_argument("--es-url", default=os.environ.get("ES_URL", "http://localhost:9200"))
    ap.add_argument("--index", default="jobs")
    ap.add_argument("--bucket", default=os.environ.get("S3_BUCKET", ""),
                    help="S3 bucket; if empty, only a local file is written")
    ap.add_argument("--region", default=os.environ.get("AWS_REGION", "ap-south-1"))
    ap.add_argument("--out-dir", default="backups")
    args = ap.parse_args(argv)

    now = datetime.now(timezone.utc)  # noqa: UP017 - must also run on Python 3.9
    key = backup_key(now)
    path = Path(args.out_dir) / Path(key).name
    count = write_backup(iter_jobs(args.es_url.rstrip("/"), args.index), path)
    print(f"Exported {count} jobs to {path}")

    if args.bucket:
        upload(path, args.bucket, key, args.region)
        print(f"Uploaded to s3://{args.bucket}/{key}")
    else:
        print("No bucket given: kept the local file only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
