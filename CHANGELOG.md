# Changelog

All notable changes, phase by phase.

## Phase 2 – Parser, dedup, tests
- `RuleBasedParser` (now the default): company, role, CTC (ranges and Indian
  lakh format), stipend (`30k/month`), location (aliases, remote), branches,
  CGPA, batch and deadline (4 date formats). 100% field accuracy on the 47
  unique labelled sample messages.
- `scripts/parser_accuracy.py`: per-field accuracy report with a `--min` gate
  (exit code 1 below the threshold) for CI and the nightly Jenkins job.
- Redis duplicate pre-check (`SET NX EX`, 30-day TTL) in front of the
  Elasticsearch create-only id check. Redis outages fall back to ES; a failed
  ES write rolls back the Redis mark so retries are not lost.
- New metric `placementhub_dedup_checks_total`.
- Tests: per-rule parser tests, accuracy gate, dedup failure paths, and
  `JobStore` with a mocked Elasticsearch client (126 tests, 96% coverage).

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
