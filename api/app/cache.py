"""Redis-backed cache that never takes the app down.

If Redis is unreachable, every method logs a warning, bumps a metric and
returns a safe default, so callers simply behave as if the cache missed.
This is "graceful degradation".
"""

import json
import logging
from typing import Any

import redis

from app.metrics import REDIS_ERRORS

logger = logging.getLogger("placementhub.cache")


class RedisCache:
    """Small wrapper around redis-py with JSON values and failure handling."""

    def __init__(self, url: str | None = None, client: redis.Redis | None = None) -> None:
        # Short timeouts: a slow/dead Redis must not make every request slow.
        self.client = client or redis.Redis.from_url(
            url or "redis://localhost:6379/0",
            socket_timeout=0.5,
            socket_connect_timeout=0.5,
            decode_responses=True,
        )

    def _failed(self, action: str, exc: Exception) -> None:
        REDIS_ERRORS.inc()
        logger.warning("redis unavailable, continuing without it",
                       extra={"fields": {"action": action, "error": str(exc)}})

    def ping(self) -> bool:
        """True if Redis answers."""
        try:
            return bool(self.client.ping())
        except redis.RedisError as exc:
            self._failed("ping", exc)
            return False

    def get_json(self, key: str) -> Any | None:
        """Return the cached value, or None on a miss or when Redis is down."""
        try:
            raw = self.client.get(key)
        except redis.RedisError as exc:
            self._failed("get", exc)
            return None
        return json.loads(raw) if raw is not None else None

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Store a value that expires after ttl_seconds. Failures are ignored."""
        try:
            self.client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
        except redis.RedisError as exc:
            self._failed("set", exc)
