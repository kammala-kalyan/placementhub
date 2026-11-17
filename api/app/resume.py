"""Resume Match: read a resume, find its skills, remember them, store the file in S3.

Privacy choices
- Only the extracted skill list is kept in Redis (7-day TTL), not the text.
- The original file goes to a PRIVATE S3 bucket under resumes/, which a
  lifecycle rule deletes after 30 days. Locally (no bucket) nothing is stored.
"""

import io
import json
import logging
import uuid
from typing import Any

import redis
from pypdf import PdfReader

from app.metrics import REDIS_ERRORS

logger = logging.getLogger("placementhub.resume")

MAX_RESUME_BYTES = 2 * 1024 * 1024


class ResumeError(ValueError):
    """The uploaded file cannot be used as a resume."""


def extract_text(filename: str, content: bytes) -> str:
    """Text from a PDF or plain-text resume."""
    if not content:
        raise ResumeError("The file is empty.")
    if len(content) > MAX_RESUME_BYTES:
        raise ResumeError("The file is larger than 2 MB.")
    if content.startswith(b"%PDF"):
        try:
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:  # pypdf raises many error types for broken files
            raise ResumeError("Could not read this PDF.") from exc
    elif filename.lower().endswith(".txt"):
        text = content.decode("utf-8", errors="replace")
    else:
        raise ResumeError("Please upload a PDF or a .txt file.")
    if not text.strip():
        raise ResumeError("No text found (scanned image PDFs are not supported).")
    return text


class ResumeStore:
    """Keeps each resume's skills in Redis for a while, keyed by a random id."""

    def __init__(self, client: redis.Redis, ttl_seconds: int = 7 * 24 * 3600) -> None:
        self.client = client
        self.ttl_seconds = ttl_seconds

    def save(self, skills: list[str]) -> str:
        resume_id = uuid.uuid4().hex
        try:
            self.client.set(f"resume:{resume_id}", json.dumps(skills), ex=self.ttl_seconds)
        except redis.RedisError as exc:
            REDIS_ERRORS.inc()
            logger.warning("could not save resume skills (client keeps them instead)",
                           extra={"fields": {"error": str(exc)}})
        return resume_id

    def skills(self, resume_id: str) -> list[str] | None:
        try:
            raw = self.client.get(f"resume:{resume_id}")
        except redis.RedisError as exc:
            REDIS_ERRORS.inc()
            logger.warning("could not read resume skills", extra={"fields": {"error": str(exc)}})
            return None
        return json.loads(raw) if raw else None


class S3ResumeUploader:
    """Uploads the original resume to the private bucket (only if one is configured)."""

    def __init__(self, bucket: str, region: str, client: Any | None = None) -> None:
        self.bucket = bucket
        self.region = region
        self._client = client

    def _s3(self) -> Any:
        if self._client is None:
            import boto3  # imported lazily: not needed when no bucket is set

            # On EC2, credentials come from the instance's IAM role automatically.
            self._client = boto3.client("s3", region_name=self.region)
        return self._client

    def upload(self, resume_id: str, filename: str, content: bytes) -> bool:
        if not self.bucket:
            return False
        extension = "pdf" if content.startswith(b"%PDF") else "txt"
        try:
            self._s3().put_object(
                Bucket=self.bucket, Key=f"resumes/{resume_id}.{extension}", Body=content,
                ContentType="application/pdf" if extension == "pdf" else "text/plain",
                ServerSideEncryption="AES256",
            )
            return True
        except Exception:  # an S3 problem must not break skill matching
            logger.exception("resume upload to S3 failed")
            return False
