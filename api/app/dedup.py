"""Duplicate detection with Redis (fast pre-check) backed by Elasticsearch (source of truth).

How it works
- Every message gets a SHA-256 hash of its normalized text (see parser/text.py).
- Redis: SET dedup:<hash> 1 NX EX <ttl>
    NX  = only set if the key does Not eXist -> atomic "first one wins",
          so two bot instances can't both store the same message.
    EX  = expire after the TTL so Redis memory does not grow forever.
- Elasticsearch: the same hash is the document id with op_type=create, so
  even if Redis is down, flushed or evicted, ES still refuses duplicates.
"""

import logging

import redis

from app.metrics import DEDUP_CHECKS, REDIS_ERRORS

logger = logging.getLogger("placementhub.dedup")

THIRTY_DAYS = 30 * 24 * 3600


class Deduplicator:
    """Remembers which message hashes have been seen recently."""

    def __init__(self, client: redis.Redis, ttl_seconds: int = THIRTY_DAYS) -> None:
        self.client = client
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def _key(message_hash: str) -> str:
        return f"dedup:{message_hash}"

    def mark_if_new(self, message_hash: str) -> bool | None:
        """True = first time seen, False = duplicate, None = Redis down (unknown)."""
        try:
            is_new = bool(self.client.set(self._key(message_hash), "1",
                                          nx=True, ex=self.ttl_seconds))
        except redis.RedisError as exc:
            REDIS_ERRORS.inc()
            DEDUP_CHECKS.labels("redis_down").inc()
            logger.warning("dedup check skipped, redis unavailable",
                           extra={"fields": {"error": str(exc)}})
            return None
        DEDUP_CHECKS.labels("new" if is_new else "duplicate").inc()
        return is_new

    def forget(self, message_hash: str) -> None:
        """Undo a mark, e.g. when saving to Elasticsearch failed, so a retry is not
        wrongly rejected as a duplicate."""
        try:
            self.client.delete(self._key(message_hash))
        except redis.RedisError as exc:
            REDIS_ERRORS.inc()
            logger.warning("could not clear dedup key", extra={"fields": {"error": str(exc)}})
