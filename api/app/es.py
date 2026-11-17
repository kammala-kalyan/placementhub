"""Elasticsearch storage: index mapping, alias and search queries.

Design notes
- We write and read through an *alias* ("jobs") that points to a real index
  ("jobs_v1"). To change the mapping later we build "jobs_v2" and move the
  alias, with zero downtime (the nightly Jenkins re-index uses this).
- The document id is the SHA-256 of the normalized message, and we index with
  op_type="create". If the id already exists ES refuses the write, so
  duplicates are blocked even when Redis is down.
"""

import logging
from datetime import date
from typing import Any

from elasticsearch import ConflictError, Elasticsearch, NotFoundError, TransportError
from elasticsearch import ConnectionError as ESConnectionError

logger = logging.getLogger("placementhub.es")

INDEX_SETTINGS: dict[str, Any] = {
    "number_of_shards": 1,
    "number_of_replicas": 0,   # single node: replicas could never be assigned
}

# "text" fields are analyzed for full-text search; ".keyword" sub-fields hold
# the exact value for filters, sorting and aggregations.
_TEXT_WITH_KEYWORD = {
    "type": "text",
    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
}

INDEX_MAPPINGS: dict[str, Any] = {
    "dynamic": "strict",       # reject unknown fields instead of guessing types
    "properties": {
        "raw_text": {"type": "text", "analyzer": "english"},
        "company": _TEXT_WITH_KEYWORD,
        "role": _TEXT_WITH_KEYWORD,
        "location": _TEXT_WITH_KEYWORD,
        "category": {"type": "keyword"},
        "ctc_lpa": {"type": "float"},
        "stipend_month": {"type": "integer"},
        "cgpa_min": {"type": "float"},
        "batch": {"type": "integer"},
        "branches": {"type": "keyword"},
        "skills": {"type": "keyword"},
        "deadline": {"type": "date"},
        "posted_at": {"type": "date"},
        "apply_link": {"type": "keyword", "index": False},
        "source": {"type": "keyword"},
    },
}

SEARCH_FIELDS = ["company^3", "role^3", "location^2", "raw_text"]   # ^n = boost


class StoreUnavailable(Exception):
    """Raised when Elasticsearch cannot be reached."""


def build_document(parsed: dict[str, Any], raw_text: str, source: str,
                   posted_at: str) -> dict[str, Any]:
    """The exact document stored in Elasticsearch. Used by /ingest and by the
    re-index script, so both always produce the same shape."""
    return {**parsed, "raw_text": raw_text, "source": source, "posted_at": posted_at}


def build_search_query(
    q: str | None = None,
    category: str | None = None,
    role: str | None = None,
    location: str | None = None,
    deadline_from: date | None = None,
    deadline_to: date | None = None,
) -> dict[str, Any]:
    """Build an ES bool query.

    - ``must``: full-text match that affects the relevance score.
    - ``filter``: yes/no conditions; not scored and cacheable by ES, so faster.
    """
    must: list[dict[str, Any]] = []
    if q:
        must.append({"multi_match": {"query": q, "fields": SEARCH_FIELDS, "fuzziness": "AUTO"}})
    else:
        must.append({"match_all": {}})

    filters: list[dict[str, Any]] = []
    if category:
        filters.append({"term": {"category": category}})
    if role:
        filters.append({"match": {"role": {"query": role, "fuzziness": "AUTO"}}})
    if location:
        filters.append({"match": {"location": {"query": location, "fuzziness": "AUTO"}}})
    if deadline_from or deadline_to:
        date_range: dict[str, str] = {}
        if deadline_from:
            date_range["gte"] = deadline_from.isoformat()
        if deadline_to:
            date_range["lte"] = deadline_to.isoformat()
        filters.append({"range": {"deadline": date_range}})

    return {"bool": {"must": must, "filter": filters}}


def build_deadlines_query(days: int, timezone: str) -> dict[str, Any]:
    """Jobs whose deadline is between today and today + ``days`` (inclusive)."""
    return {"range": {"deadline": {"gte": "now/d", "lte": f"now+{days}d/d", "time_zone": timezone}}}


def sort_clause(sort: str) -> list[Any]:
    """Translate the API's sort option into an ES sort clause."""
    if sort == "deadline":
        # Soonest deadline first; jobs without a deadline go last.
        return [{"deadline": {"order": "asc", "missing": "_last"}}, "_score"]
    if sort == "latest":
        return [{"posted_at": {"order": "desc"}}]
    return ["_score", {"posted_at": {"order": "desc"}}]


class JobStore:
    """All Elasticsearch access goes through this class."""

    def __init__(self, url: str, alias: str = "jobs", client: Elasticsearch | None = None) -> None:
        self.client = client or Elasticsearch(url, request_timeout=10)
        self.alias = alias
        self._ready = False

    def ping(self) -> bool:
        """True if the cluster answers."""
        try:
            return bool(self.client.ping())
        except Exception:  # health checks must never raise
            return False

    def ensure_index(self) -> None:
        """Create jobs_v1 with our mapping and point the alias at it (idempotent)."""
        if self._ready:
            return
        try:
            if not self.client.indices.exists_alias(name=self.alias):
                index = f"{self.alias}_v1"
                if not self.client.indices.exists(index=index):
                    self.client.indices.create(
                        index=index, settings=INDEX_SETTINGS, mappings=INDEX_MAPPINGS
                    )
                    logger.info("created index", extra={"fields": {"index": index}})
                self.client.indices.put_alias(index=index, name=self.alias)
        except (ESConnectionError, TransportError) as exc:
            raise StoreUnavailable(str(exc)) from exc
        self._ready = True

    def create_job(self, job_id: str, doc: dict[str, Any]) -> bool:
        """Index a new job. Returns False if a job with this id already exists."""
        self.ensure_index()
        try:
            self.client.index(
                index=self.alias, id=job_id, document=doc, op_type="create", refresh="wait_for"
            )
            return True
        except ConflictError:
            return False
        except (ESConnectionError, TransportError) as exc:
            raise StoreUnavailable(str(exc)) from exc

    def get(self, job_id: str) -> dict[str, Any] | None:
        """Fetch one job by id, or None."""
        self.ensure_index()
        try:
            resp = self.client.get(index=self.alias, id=job_id)
        except NotFoundError:
            return None
        except (ESConnectionError, TransportError) as exc:
            raise StoreUnavailable(str(exc)) from exc
        return {"id": resp["_id"], **resp["_source"]}

    def search(
        self, query: dict[str, Any], sort: list[Any], size: int = 20, offset: int = 0
    ) -> tuple[int, list[dict[str, Any]]]:
        """Run a query and return (total_hits, jobs)."""
        self.ensure_index()
        try:
            resp = self.client.search(
                index=self.alias, query=query, sort=sort, size=size, from_=offset,
                track_total_hits=True,
            )
        except (ESConnectionError, TransportError) as exc:
            raise StoreUnavailable(str(exc)) from exc
        hits = resp["hits"]
        return hits["total"]["value"], [{"id": h["_id"], **h["_source"]} for h in hits["hits"]]
