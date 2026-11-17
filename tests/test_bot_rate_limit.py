"""Per-user fixed-window rate limiting."""

import asyncio

import fakeredis

from bot.rate_limit import RateLimiter


class Clock:
    """A fake clock tests can move forward."""

    def __init__(self) -> None:
        self.t = 1_000_000.0

    def __call__(self) -> float:
        return self.t


def make_limiter(server=None, clock=None, limit=3):
    client = fakeredis.FakeAsyncRedis(server=server or fakeredis.FakeServer())
    return RateLimiter(client, limit=limit, window_seconds=60, now=clock or Clock())


def test_allows_up_to_limit_then_blocks():
    limiter = make_limiter(limit=3)

    async def run():
        return [await limiter.allow(42) for _ in range(5)]

    assert asyncio.run(run()) == [True, True, True, False, False]


def test_users_are_limited_separately():
    limiter = make_limiter(limit=1)

    async def run():
        return [await limiter.allow(1), await limiter.allow(2), await limiter.allow(1)]

    assert asyncio.run(run()) == [True, True, False]


def test_next_window_resets_the_count():
    clock = Clock()
    limiter = make_limiter(clock=clock, limit=1)

    async def run():
        first = [await limiter.allow(7), await limiter.allow(7)]
        clock.t += 60                       # move to the next minute
        return first + [await limiter.allow(7)]

    assert asyncio.run(run()) == [True, False, True]


def test_counter_keys_expire():
    server = fakeredis.FakeServer()
    limiter = make_limiter(server=server)

    async def run():
        await limiter.allow(9)
        keys = await limiter.client.keys("rl:9:*")
        return await limiter.client.ttl(keys[0])

    assert 0 < asyncio.run(run()) <= 60


def test_fails_open_when_redis_is_down():
    server = fakeredis.FakeServer()
    server.connected = False
    limiter = make_limiter(server=server, limit=1)

    async def run():
        return [await limiter.allow(5) for _ in range(3)]

    assert asyncio.run(run()) == [True, True, True]
