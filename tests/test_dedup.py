"""Duplicate detection: Redis pre-check, Elasticsearch fallback, failure handling."""

import fakeredis
import pytest

from app.dedup import Deduplicator
from app.es import StoreUnavailable

MESSAGE = """Zephyr Fintech | Backend Developer | Full Time
CTC: 12 LPA
Location: Pune
Deadline: 24 Nov 2026"""


@pytest.fixture
def dedup(redis_server):
    return Deduplicator(fakeredis.FakeRedis(server=redis_server), ttl_seconds=60)


def test_first_time_new_second_time_duplicate(dedup):
    assert dedup.mark_if_new("abc") is True
    assert dedup.mark_if_new("abc") is False


def test_key_has_ttl(dedup):
    dedup.mark_if_new("abc")
    assert 0 < dedup.client.ttl("dedup:abc") <= 60


def test_redis_down_returns_none_instead_of_crashing(dedup, redis_server):
    redis_server.connected = False
    assert dedup.mark_if_new("abc") is None
    dedup.forget("abc")     # must not raise either


def test_forget_allows_message_again(dedup):
    dedup.mark_if_new("abc")
    dedup.forget("abc")
    assert dedup.mark_if_new("abc") is True


# ---------- through the API ----------
def test_api_duplicate_is_caught_by_redis_before_elasticsearch(client, store):
    assert client.post("/ingest", json={"text": MESSAGE}).json()["status"] == "created"
    writes_before = store.create_calls
    again = client.post("/ingest", json={"text": MESSAGE})
    assert again.json()["status"] == "duplicate"
    assert store.create_calls == writes_before      # no second ES write


def test_api_dedup_still_works_when_redis_is_down(client, store, redis_server):
    redis_server.connected = False
    assert client.post("/ingest", json={"text": MESSAGE}).json()["status"] == "created"
    # Redis can't help, so Elasticsearch's create-only id check catches it.
    assert client.post("/ingest", json={"text": MESSAGE}).json()["status"] == "duplicate"
    assert len(store.jobs) == 1


def test_api_retry_works_after_elasticsearch_failure(client, store):
    store.fail_writes = True
    assert client.post("/ingest", json={"text": MESSAGE}).status_code == 503
    store.fail_writes = False
    # The Redis mark was rolled back, so the retry is stored, not called a duplicate.
    retry = client.post("/ingest", json={"text": MESSAGE})
    assert retry.status_code == 201 and retry.json()["status"] == "created"


def test_api_reindexes_if_redis_remembers_but_elasticsearch_lost_it(client, store):
    client.post("/ingest", json={"text": MESSAGE})
    store.jobs.clear()                                # e.g. index was rebuilt
    again = client.post("/ingest", json={"text": MESSAGE})
    assert again.json()["status"] == "created"
    assert len(store.jobs) == 1


def test_ingest_extracts_fields_with_rules_parser(client):
    job = client.post("/ingest", json={"text": MESSAGE}).json()["job"]
    assert job["company"] == "Zephyr Fintech" and job["role"] == "Backend Developer"
    assert job["ctc_lpa"] == 12.0 and job["location"] == "Pune"
    assert job["deadline"] == "2026-11-24"


def test_store_unavailable_is_a_503(client, store):
    store.fail_writes = True
    resp = client.post("/ingest", json={"text": MESSAGE})
    assert resp.status_code == 503
    assert isinstance(StoreUnavailable("x"), Exception)
