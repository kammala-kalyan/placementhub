"""Prometheus metrics exposed at GET /metrics.

Counter   = a number that only goes up (requests served, errors).
Histogram = counts values into buckets (request latency), so we can
            compute averages and percentiles like p95.
"""

from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    "placementhub_http_requests_total", "HTTP requests served", ["method", "path", "status"]
)
HTTP_LATENCY = Histogram(
    "placementhub_http_request_duration_seconds", "HTTP request latency in seconds", ["path"]
)
JOBS_INGESTED = Counter(
    "placementhub_jobs_ingested_total", "Ingested messages by result", ["result"]
)
CACHE_REQUESTS = Counter(
    "placementhub_search_cache_total", "Search cache lookups (hit/miss)", ["result"]
)
REDIS_ERRORS = Counter(
    "placementhub_redis_errors_total", "Redis operations that failed while the app kept working"
)
