"""Zero-downtime re-index of the jobs index.

Why: when the parser improves (or the mapping changes), old jobs should get
the better fields too. Elasticsearch cannot change existing field types in
place, so we build a NEW index and switch over to it.

Steps:
  1. Find the index behind the alias "jobs" (e.g. jobs_v1).
  2. Create jobs_v2 with the current mapping.
  3. Copy every job, re-parsing its raw text with the current parser.
  4. Check both indexes hold the same number of jobs.
  5. Move the alias to jobs_v2 in ONE atomic request: searches never see an
     empty or half-built index.
  6. Keep jobs_v1 for a quick rollback; delete anything older.

Usage:  PYTHONPATH=.:api python -m scripts.reindex --es-url http://localhost:9200
"""

import argparse
import re
import sys
from typing import Any

from elasticsearch import Elasticsearch, helpers

from app.es import INDEX_MAPPINGS, INDEX_SETTINGS, build_document
from parser import get_parser
from parser.base import Parser


def next_index_name(current: str) -> str:
    """jobs_v1 -> jobs_v2 (and jobs -> jobs_v2 for an unversioned index)."""
    match = re.match(r"^(.*)_v(\d+)$", current)
    if match:
        return f"{match.group(1)}_v{int(match.group(2)) + 1}"
    return f"{current}_v2"


def rebuild(source: dict[str, Any], parser: Parser) -> dict[str, Any]:
    """Re-parse the original message; keep where/when it was posted."""
    parsed = parser.parse(source["raw_text"]).model_dump(mode="json")
    return build_document(parsed, source["raw_text"], source.get("source", "unknown"),
                          source["posted_at"])


def reindex(client: Elasticsearch, alias: str = "jobs",
            parser: Parser | None = None) -> dict[str, Any]:
    parser = parser or get_parser("rules")
    old_indices = sorted(client.indices.get_alias(name=alias).keys())
    old = old_indices[-1]
    new = next_index_name(old)

    client.indices.create(index=new, settings=INDEX_SETTINGS, mappings=INDEX_MAPPINGS)
    actions = (
        {"_index": new, "_id": hit["_id"], "_source": rebuild(hit["_source"], parser)}
        for hit in helpers.scan(client, index=alias, query={"query": {"match_all": {}}})
    )
    copied, errors = helpers.bulk(client, actions, raise_on_error=False)
    client.indices.refresh(index=new)

    old_count = client.count(index=old)["count"]
    new_count = client.count(index=new)["count"]
    if errors or new_count != old_count:
        client.indices.delete(index=new)      # leave the live index untouched
        raise RuntimeError(f"re-index aborted: copied {new_count}/{old_count}, "
                           f"{len(errors) if errors else 0} errors")

    # Atomic switch: remove + add happen together.
    client.indices.update_aliases(actions=[
        {"remove": {"index": old, "alias": alias}},
        {"add": {"index": new, "alias": alias}},
    ])

    # Keep only the previous index (for rollback); delete older generations.
    all_versions = sorted(client.indices.get(index=f"{alias}_v*").keys(),
                          key=lambda name: int(name.rsplit("_v", 1)[-1]))
    deleted = [name for name in all_versions if name not in (old, new)]
    for name in deleted:
        client.indices.delete(index=name)

    return {"old_index": old, "new_index": new, "jobs": new_count, "deleted": deleted}


def main() -> int:
    ap = argparse.ArgumentParser(description="Zero-downtime re-index of PlacementHub jobs")
    ap.add_argument("--es-url", default="http://localhost:9200")
    ap.add_argument("--alias", default="jobs")
    args = ap.parse_args()

    result = reindex(Elasticsearch(args.es_url, request_timeout=60), alias=args.alias)
    print(f"Re-indexed {result['jobs']} jobs: {result['old_index']} -> {result['new_index']} "
          f"(alias '{args.alias}' switched; deleted: {result['deleted'] or 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
