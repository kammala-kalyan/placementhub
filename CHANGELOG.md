# Changelog

All notable changes, phase by phase.

## Phase 4 – Web UI
- Plain HTML/CSS/JS UI: search box, category/role/location/sort filters,
  "closing in 3 days" toggle, job cards with red/amber deadline highlighting,
  cache badge, live health indicator, shareable search URLs, dark mode.
- XSS-safe rendering (`textContent` only, apply links limited to http/https).
- nginx (unprivileged, port 8080) serves the UI and proxies `/api/*` to the
  API; `/api/metrics` is blocked publicly; security headers and gzip.
- Compose: `web` is the only public service; API now bound to localhost;
  log rotation (10 MB x 3) on every container.

## Phase 3 – Telegram bot
- `bot` service (python-telegram-bot 21, long polling) talking only to the API.
- Commands: `/search`, `/latest`, `/deadlines` (closing within 3 days),
  `/filter role= location= category=`, `/help`, `/whereami` (setup helper).
- Reads configured placement groups, ingests messages via `POST /ingest`, and
  reposts new (non-duplicate) jobs as cards into the matching forum topic.
- Per-user Redis rate limit (fixed window, 10/min), fail-open when Redis is down.
- HTML-escaped job cards with deadline badges (today / tomorrow / within 3 days).
- Docker image with a heartbeat-file healthcheck; bot stays idle (unhealthy)
  instead of crash-looping when no token is configured.
- Bot token handled as a secret (`SecretStr`, httpx logs silenced).
- Tests with fake Telegram updates, fakeredis and a mocked HTTP transport
  (165 tests, 93% coverage).

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
