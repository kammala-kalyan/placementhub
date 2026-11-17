# Changelog

All notable changes, phase by phase.

## Phase 1 – Skeleton, API, Elasticsearch, Redis, seed data
- Docker Compose stack: Elasticsearch 8 (512 MB heap), Redis 7, FastAPI API.
- Multi-stage, non-root API Dockerfile with a healthcheck.
- API routes: `POST /ingest`, `GET /jobs/search`, `/jobs/latest`, `/jobs/deadlines`,
  `/jobs/{id}`, `/health`, `/metrics`.
- Elasticsearch index `jobs_v1` behind alias `jobs`, strict mapping, fuzzy search.
- Duplicate-safe ingestion: content hash as document id with `op_type=create`.
- Redis search cache (60 s TTL) with graceful degradation when Redis is down.
- Structured JSON logging and Prometheus metrics.
- `parser` package with a pluggable `Parser` interface and a `SimpleParser`
  (category + apply link).
- 50 labelled sample messages (47 unique + 3 duplicates) and `scripts/seed.py`.
- Tests with a fake store and fakeredis (no services or secrets needed).

## Phase 0 – Design
- Design interview and approved design summary (`docs/DESIGN.md`).
