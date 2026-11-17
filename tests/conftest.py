"""Shared test fixtures.

Tests never need a real Elasticsearch, Redis or any secret:
- FakeJobStore keeps jobs in a dict and mimics JobStore's interface.
- fakeredis gives an in-memory Redis that behaves like the real thing.
"""

from typing import Any

import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.cache import RedisCache
from app.config import Settings
from app.main import create_app


class FakeJobStore:
    """In-memory stand-in for app.es.JobStore."""

    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}
        self.search_calls = 0
        self.up = True

    def ping(self) -> bool:
        return self.up

    def ensure_index(self) -> None:
        pass

    def create_job(self, job_id: str, doc: dict[str, Any]) -> bool:
        if job_id in self.jobs:
            return False
        self.jobs[job_id] = doc
        return True

    def get(self, job_id: str) -> dict[str, Any] | None:
        doc = self.jobs.get(job_id)
        return {"id": job_id, **doc} if doc else None

    def search(self, query: dict, sort: list, size: int = 20, offset: int = 0):
        # Ignores the query: we test query building separately.
        self.search_calls += 1
        items = [{"id": k, **v} for k, v in self.jobs.items()]
        return len(items), items[offset: offset + size]


@pytest.fixture
def store() -> FakeJobStore:
    return FakeJobStore()


@pytest.fixture
def redis_server() -> fakeredis.FakeServer:
    return fakeredis.FakeServer()


@pytest.fixture
def cache(redis_server: fakeredis.FakeServer) -> RedisCache:
    return RedisCache(client=fakeredis.FakeRedis(server=redis_server, decode_responses=True))


@pytest.fixture
def client(store: FakeJobStore, cache: RedisCache):
    app = create_app(store=store, cache=cache, settings=Settings(_env_file=None))
    with TestClient(app) as test_client:   # "with" runs the startup/lifespan code
        yield test_client
