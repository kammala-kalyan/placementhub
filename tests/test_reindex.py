"""Re-index script with a mocked Elasticsearch client."""

from unittest.mock import MagicMock

import pytest

from scripts import reindex as reindex_module
from scripts.reindex import next_index_name, rebuild

SOURCE = {
    "raw_text": "Konark Payments – SDE-1\nCTC: 14 LPA\nLocation: Bengaluru",
    "source": "seed", "posted_at": "2026-11-15T10:00:00+00:00",
    "company": None,   # an old, worse parse
}


@pytest.mark.parametrize("current, expected", [
    ("jobs_v1", "jobs_v2"), ("jobs_v9", "jobs_v10"), ("jobs", "jobs_v2"),
])
def test_next_index_name(current, expected):
    assert next_index_name(current) == expected


def test_rebuild_reparses_raw_text_and_keeps_metadata():
    doc = rebuild(SOURCE, reindex_module.get_parser("rules"))
    assert doc["company"] == "Konark Payments" and doc["ctc_lpa"] == 14.0
    assert doc["posted_at"] == SOURCE["posted_at"] and doc["source"] == "seed"


def make_client(old_count=2, new_count=2):
    client = MagicMock()
    client.indices.get_alias.return_value = {"jobs_v1": {"aliases": {"jobs": {}}}}
    client.indices.get.return_value = {"jobs_v0": {}, "jobs_v1": {}, "jobs_v2": {}}
    client.count.side_effect = lambda index: {"count": old_count if index == "jobs_v1"
                                              else new_count}
    return client


def patch_helpers(monkeypatch, errors=None):
    monkeypatch.setattr(reindex_module.helpers, "scan", lambda *a, **k: [
        {"_id": "a", "_source": SOURCE}, {"_id": "b", "_source": SOURCE}])
    bulked = []

    def fake_bulk(client, actions, raise_on_error):
        items = list(actions)
        bulked.extend(items)
        return len(items), errors or []

    monkeypatch.setattr(reindex_module.helpers, "bulk", fake_bulk)
    return bulked


def test_reindex_switches_alias_atomically_and_keeps_previous(monkeypatch):
    bulked = patch_helpers(monkeypatch)
    client = make_client()

    result = reindex_module.reindex(client)

    assert result == {"old_index": "jobs_v1", "new_index": "jobs_v2", "jobs": 2,
                      "deleted": ["jobs_v0"]}
    assert {item["_index"] for item in bulked} == {"jobs_v2"}
    client.indices.update_aliases.assert_called_once_with(actions=[
        {"remove": {"index": "jobs_v1", "alias": "jobs"}},
        {"add": {"index": "jobs_v2", "alias": "jobs"}},
    ])
    client.indices.delete.assert_called_once_with(index="jobs_v0")


def test_reindex_aborts_and_cleans_up_when_counts_differ(monkeypatch):
    patch_helpers(monkeypatch)
    client = make_client(old_count=2, new_count=1)

    with pytest.raises(RuntimeError, match="aborted"):
        reindex_module.reindex(client)

    client.indices.update_aliases.assert_not_called()       # live index untouched
    client.indices.delete.assert_called_once_with(index="jobs_v2")
