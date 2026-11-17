"""JobStore tests with a mocked Elasticsearch client (no real cluster needed)."""

from unittest.mock import MagicMock

import pytest
from elasticsearch import ConflictError, NotFoundError
from elasticsearch import ConnectionError as ESConnectionError

from app.es import INDEX_MAPPINGS, JobStore, StoreUnavailable


def api_error(cls):
    """Build an elasticsearch ApiError subclass without a real HTTP response."""
    return cls("error", meta=MagicMock(status=409), body={})


@pytest.fixture
def es():
    client = MagicMock()
    client.indices.exists_alias.return_value = False
    client.indices.exists.return_value = False
    return client


def test_ensure_index_creates_index_and_alias_once(es):
    store = JobStore("http://unused", client=es)
    store.ensure_index()
    store.ensure_index()                     # second call is a no-op
    es.indices.create.assert_called_once()
    assert es.indices.create.call_args.kwargs["index"] == "jobs_v1"
    assert es.indices.create.call_args.kwargs["mappings"] == INDEX_MAPPINGS
    es.indices.put_alias.assert_called_once_with(index="jobs_v1", name="jobs")


def test_ensure_index_only_adds_new_fields_when_alias_exists(es):
    es.indices.exists_alias.return_value = True
    JobStore("http://unused", client=es).ensure_index()
    es.indices.create.assert_not_called()
    es.indices.put_mapping.assert_called_once_with(
        index="jobs", properties=INDEX_MAPPINGS["properties"])


def test_create_job_uses_create_only_and_reports_conflict_as_duplicate(es):
    store = JobStore("http://unused", client=es)
    assert store.create_job("h1", {"raw_text": "x"}) is True
    assert es.index.call_args.kwargs["op_type"] == "create"
    es.index.side_effect = api_error(ConflictError)
    assert store.create_job("h1", {"raw_text": "x"}) is False


def test_connection_errors_become_store_unavailable(es):
    store = JobStore("http://unused", client=es)
    store.ensure_index()
    es.index.side_effect = ESConnectionError("down")
    with pytest.raises(StoreUnavailable):
        store.create_job("h1", {})
    es.search.side_effect = ESConnectionError("down")
    with pytest.raises(StoreUnavailable):
        store.search({"match_all": {}}, [])


def test_get_returns_none_when_missing(es):
    store = JobStore("http://unused", client=es)
    es.get.return_value = {"_id": "h1", "_source": {"company": "X"}}
    assert store.get("h1") == {"id": "h1", "company": "X"}
    es.get.side_effect = api_error(NotFoundError)
    assert store.get("nope") is None


def test_search_maps_hits(es):
    es.search.return_value = {"hits": {"total": {"value": 2}, "hits": [
        {"_id": "a", "_source": {"company": "A"}}, {"_id": "b", "_source": {"company": "B"}}]}}
    total, items = JobStore("http://unused", client=es).search({"match_all": {}}, ["_score"])
    assert total == 2 and [i["id"] for i in items] == ["a", "b"]


def test_ping_never_raises(es):
    es.ping.side_effect = Exception("boom")
    assert JobStore("http://unused", client=es).ping() is False
