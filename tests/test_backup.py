"""Backup script: scroll export, gzip JSON lines, upload call (no real ES or S3)."""

import gzip
import json
from datetime import UTC, datetime

from scripts import backup_jobs


def fake_es(pages):
    """Return a fake es_request that serves the given pages of hits in order."""
    calls = []
    remaining = list(pages)

    def request(url, body=None, method="POST"):
        calls.append((method, url, body))
        if method == "DELETE":
            return {}
        hits = remaining.pop(0) if remaining else []
        return {"_scroll_id": "s1", "hits": {"hits": hits}}

    return request, calls


def hit(i):
    return {"_id": f"id{i}", "_source": {"company": f"C{i}", "raw_text": "msg"}}


def test_exports_all_pages_and_clears_scroll(monkeypatch, tmp_path):
    request, calls = fake_es([[hit(1), hit(2)], [hit(3)], []])
    monkeypatch.setattr(backup_jobs, "es_request", request)

    path = tmp_path / "jobs.jsonl.gz"
    count = backup_jobs.write_backup(backup_jobs.iter_jobs("http://es"), path)

    assert count == 3
    with gzip.open(path, "rt", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    assert [r["id"] for r in rows] == ["id1", "id2", "id3"]
    assert calls[-1][0] == "DELETE"          # scroll context released


def test_main_uploads_to_dated_key(monkeypatch, tmp_path):
    request, _ = fake_es([[hit(1)], []])
    monkeypatch.setattr(backup_jobs, "es_request", request)
    uploads = []
    monkeypatch.setattr(backup_jobs, "upload",
                        lambda path, bucket, key, region: uploads.append((bucket, key, region)))

    code = backup_jobs.main(["--es-url", "http://es", "--bucket", "my-bucket",
                             "--out-dir", str(tmp_path)])

    assert code == 0
    bucket, key, region = uploads[0]
    assert bucket == "my-bucket" and region == "ap-south-1"
    assert key.startswith("backups/") and key.endswith(".jsonl.gz")


def test_backup_key_format():
    key = backup_jobs.backup_key(datetime(2026, 11, 17, 21, 0, tzinfo=UTC))
    assert key == "backups/2026/11/17/jobs-20261117T210000Z.jsonl.gz"
