"""Per-user rate limiting with a Redis fixed window.

Each user gets one counter per minute: key rl:<user_id>:<minute number>.
INCR adds 1 (creating the key at 1), EXPIRE deletes it after the window,
so old counters clean themselves up. If the count goes above the limit,
the command is refused until the next minute.

Fail-open: if Redis is down we allow the command. Blocking every student
because the limiter is broken would be worse than briefly having no limit.
"""

import logging
import time
from collections.abc import Callable

import redis
import redis.asyncio as aioredis

logger = logging.getLogger("placementhub.bot.ratelimit")


class RateLimiter:
    def __init__(self, client: aioredis.Redis, limit: int = 10, window_seconds: int = 60,
                 now: Callable[[], float] = time.time) -> None:
        self.client = client
        self.limit = limit
        self.window_seconds = window_seconds
        self.now = now   # injectable clock, so tests can move time forward

    async def allow(self, user_id: int) -> bool:
        """True if this user may run another command in the current window."""
        window = int(self.now() // self.window_seconds)
        key = f"rl:{user_id}:{window}"
        try:
            # A pipeline sends both commands in one round trip.
            async with self.client.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, self.window_seconds)
                count, _ = await pipe.execute()
        except (redis.RedisError, OSError) as exc:
            logger.warning("rate limiter unavailable, allowing request",
                           extra={"fields": {"error": str(exc)}})
            return True
        return int(count) <= self.limit
