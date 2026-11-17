"""Tests for the Elasticsearch query builders (pure functions, no ES needed)."""

from datetime import date

from app.es import build_deadlines_query, build_search_query, sort_clause


def test_empty_search_matches_everything():
    query = build_search_query()
    assert query == {"bool": {"must": [{"match_all": {}}], "filter": []}}


def test_text_search_is_fuzzy_and_boosts_company_and_role():
    match = build_search_query(q="data anlyst")["bool"]["must"][0]["multi_match"]
    assert match["fuzziness"] == "AUTO"
    assert "company^3" in match["fields"] and "role^3" in match["fields"]


def test_filters_go_into_filter_context():
    query = build_search_query(
        category="Internship", location="Bengaluru",
        deadline_from=date(2026, 11, 1), deadline_to=date(2026, 11, 30),
    )
    filters = query["bool"]["filter"]
    assert {"term": {"category": "Internship"}} in filters
    assert {"range": {"deadline": {"gte": "2026-11-01", "lte": "2026-11-30"}}} in filters


def test_deadlines_query_uses_date_math_and_timezone():
    rng = build_deadlines_query(3, "Asia/Kolkata")["range"]["deadline"]
    assert rng == {"gte": "now/d", "lte": "now+3d/d", "time_zone": "Asia/Kolkata"}


def test_sort_by_deadline_puts_missing_last():
    assert sort_clause("deadline")[0] == {"deadline": {"order": "asc", "missing": "_last"}}
    assert sort_clause("relevance")[0] == "_score"
