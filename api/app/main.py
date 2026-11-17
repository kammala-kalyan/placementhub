"""PlacementHub API: ingest placement messages and search them.

Run locally:  uvicorn app.main:app --reload   (from the api/ folder)
Docs:         http://localhost:8000/docs
"""

import hashlib
import json
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app import metrics
from app.cache import RedisCache
from app.config import Settings, get_settings
from app.es import (
    JobStore,
    StoreUnavailable,
    build_deadlines_query,
    build_search_query,
    sort_clause,
)
from app.logging_config import setup_logging
from app.models import (
    HealthResponse,
    IngestRequest,
    IngestResponse,
    Job,
    JobList,
    SearchResponse,
)
from parser import Category, get_parser
from parser.text import message_hash

logger = logging.getLogger("placementhub.api")


def create_app(
    store: JobStore | None = None,
    cache: RedisCache | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    """Build the FastAPI app. Tests pass fake store/cache objects in."""
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Runs once at startup: create clients and make sure the ES index exists.
        app.state.settings = settings
        app.state.store = store or JobStore(settings.es_url, alias=settings.es_alias)
        app.state.cache = cache or RedisCache(url=settings.redis_url)
        app.state.parser = get_parser(settings.parser)
        try:
            app.state.store.ensure_index()
        except StoreUnavailable:
            logger.exception("elasticsearch not ready at startup; will retry on first request")
        logger.info("api started", extra={"fields": {"parser": settings.parser}})
        yield

    app = FastAPI(
        title="PlacementHub API",
        version="0.1.0",
        description="Collects placement messages, extracts structured fields and searches them.",
        lifespan=lifespan,
    )

    # ---------- cross-cutting: metrics + request logging ----------
    @app.middleware("http")
    async def observe_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        # Use the route template (/jobs/{job_id}), not the real URL, to keep
        # the number of metric label values small.
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")
        metrics.HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
        metrics.HTTP_LATENCY.labels(path).observe(duration)
        logger.info("request", extra={"fields": {
            "method": request.method, "path": request.url.path,
            "status": response.status_code, "duration_ms": round(duration * 1000, 1),
        }})
        return response

    @app.exception_handler(StoreUnavailable)
    async def store_unavailable(_: Request, exc: StoreUnavailable) -> JSONResponse:
        logger.error("elasticsearch unavailable", extra={"fields": {"error": str(exc)}})
        return JSONResponse(status_code=503, content={"detail": "Search store unavailable"})

    # ---------- routes ----------
    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"name": "PlacementHub API", "docs": "/docs", "health": "/health"}

    @app.post("/ingest", response_model=IngestResponse, tags=["ingest"])
    def ingest(payload: IngestRequest, request: Request, response: Response) -> IngestResponse:
        """Parse a raw message and store it. Duplicates are detected by content hash."""
        store: JobStore = request.app.state.store
        job_id = message_hash(payload.text)
        parsed = request.app.state.parser.parse(payload.text)
        posted_at = payload.posted_at or datetime.now(UTC)
        doc = {
            **parsed.model_dump(mode="json"),
            "raw_text": payload.text,
            "source": payload.source,
            "posted_at": posted_at.isoformat(),
        }

        created = store.create_job(job_id, doc)
        result: Literal["created", "duplicate"] = "created" if created else "duplicate"
        metrics.JOBS_INGESTED.labels(result).inc()
        logger.info("ingested", extra={"fields": {"id": job_id[:12], "result": result,
                                                  "category": parsed.category}})

        stored = doc if created else (store.get(job_id) or doc)
        response.status_code = 201 if created else 200
        return IngestResponse(id=job_id, status=result, job=Job(**{"id": job_id, **stored}))

    @app.get("/jobs/search", response_model=SearchResponse, tags=["jobs"])
    def search_jobs(
        request: Request,
        q: str | None = Query(None, max_length=200, description="Free text, typos allowed"),
        category: Category | None = None,
        role: str | None = Query(None, max_length=100),
        location: str | None = Query(None, max_length=100),
        deadline_from: date | None = None,
        deadline_to: date | None = None,
        sort: Literal["relevance", "deadline"] = "relevance",
        page: int = Query(1, ge=1, le=50),
        size: int = Query(20, ge=1, le=50),
    ) -> SearchResponse:
        """Full-text search with filters. Results are cached in Redis for a short time."""
        cache: RedisCache = request.app.state.cache
        params = {"q": q, "category": category, "role": role, "location": location,
                  "deadline_from": deadline_from, "deadline_to": deadline_to,
                  "sort": sort, "page": page, "size": size}
        key = "search:" + hashlib.sha256(
            json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()

        cached = cache.get_json(key)
        if cached is not None:
            metrics.CACHE_REQUESTS.labels("hit").inc()
            return SearchResponse(**cached, cached=True)
        metrics.CACHE_REQUESTS.labels("miss").inc()

        query = build_search_query(q, category, role, location, deadline_from, deadline_to)
        total, items = request.app.state.store.search(
            query, sort_clause(sort), size=size, offset=(page - 1) * size)
        result = {"total": total, "page": page, "size": size, "items": items}
        cache.set_json(key, result, settings.cache_ttl_seconds)
        return SearchResponse(**result, cached=False)

    @app.get("/jobs/latest", response_model=JobList, tags=["jobs"])
    def latest_jobs(request: Request, limit: int = Query(10, ge=1, le=50)) -> JobList:
        """Most recently posted jobs."""
        total, items = request.app.state.store.search(
            {"match_all": {}}, sort_clause("latest"), size=limit)
        return JobList(total=total, items=items)

    @app.get("/jobs/deadlines", response_model=JobList, tags=["jobs"])
    def upcoming_deadlines(request: Request, days: int = Query(3, ge=0, le=30)) -> JobList:
        """Jobs closing between today and today + `days`, soonest first."""
        total, items = request.app.state.store.search(
            build_deadlines_query(days, settings.timezone), sort_clause("deadline"), size=50)
        return JobList(total=total, items=items)

    @app.get("/jobs/{job_id}", response_model=Job, tags=["jobs"])
    def get_job(job_id: str, request: Request) -> Job:
        """One job by id."""
        job = request.app.state.store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return Job(**job)

    @app.get("/health", response_model=HealthResponse, tags=["ops"])
    def health(request: Request, response: Response) -> HealthResponse:
        """ok = all up, degraded = Redis down (app still works), down = ES down."""
        es_up = request.app.state.store.ping()
        redis_up = request.app.state.cache.ping()
        status: Literal["ok", "degraded", "down"] = (
            "ok" if es_up and redis_up else "degraded" if es_up else "down")
        if not es_up:
            response.status_code = 503
        return HealthResponse(status=status, elasticsearch="up" if es_up else "down",
                              redis="up" if redis_up else "down")

    @app.get("/metrics", tags=["ops"])
    def prometheus_metrics() -> Response:
        """Metrics in Prometheus text format."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
