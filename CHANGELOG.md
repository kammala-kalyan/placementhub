# Changelog

All notable changes, phase by phase.

## Phase 10 – Documentation and cleanup
- Full README: problem, Mermaid architecture and CI/CD diagrams, features,
  "why this tool" stack table, local setup, AWS deployment, observability,
  cost safety, security notes, screenshot placeholders, known limitations,
  future improvements.
- `docs/INTERVIEW_NOTES.md`: 30-second pitch, 2-minute walkthrough, design
  trade-offs, 25 interview questions with answers.
- `docs/DEMO_SCRIPT.md`: timed 5-minute demo with recovery steps.

## Phase 9 – Resume Match
- `parser/skills.py`: fixed skill dictionary with aliases and safe word
  boundaries; jobs now store `skills` and `skills_count`.
- `POST /resume`: PDF/TXT upload (2 MB max), skills extracted only from the
  file's own text, rewording tips only for skills already listed
  (e.g. `k8s` -> "Kubernetes (k8s)"), skills kept in Redis for 7 days,
  original file stored privately in S3 `resumes/` (30-day lifecycle) when a
  bucket is configured.
- `GET /jobs/match?min_score=70`: Elasticsearch `terms_set` query with a
  per-job minimum (`ceil(skills_count x ratio)`), exact score and missing
  skills computed in the API, results cached in Redis for 10 minutes; works
  with a skills list when Redis has lost the resume.
- Additive mapping update at startup (`put_mapping`) for existing indexes.
- Web UI: Resume Match panel with skill chips, tips and match scores on cards.
- Tests: skills, scoring, PDF/TXT extraction, S3 upload failures, match API.

## Phase 8 – Jenkins nightly pipeline
- `jenkins/`: Jenkins LTS image with Python and plugins, configured entirely
  as code (JCasC: admin user, security, pipeline job); no Docker socket mounted.
- `Jenkinsfile`: nightly cron, parameters, stages for parser unit tests
  (JUnit report) + accuracy gate, zero-downtime Elasticsearch re-index, and
  S3 backup with credentials from the Jenkins credential store (or a local
  artifact when no bucket is set); timeouts, log rotation, workspace cleanup.
- `scripts/reindex.py`: new versioned index, re-parse with the current parser,
  count check, atomic alias swap, keep one previous index for rollback.
- Shared `build_document()` so ingest and re-index store identical documents.
- `docs/JENKINS.md`: setup and Jenkins vs GitHub Actions comparison.

## Phase 7 – GitHub Actions CD
- `cd.yml` runs only after CI succeeds on `main` (`workflow_run`), or manually.
- Builds and pushes api, bot and web images to GHCR tagged `latest` and the
  commit SHA (layer cache, OCI source label).
- Deploys over SSH with `scripts/deploy.sh`: checkout the exact commit, pin
  `IMAGE_TAG`, pull, `compose up -d`, wait for the health check; registry
  token passed over the SSH session, not as an argument; key removed after.
- Public health check from the runner, `production` environment, no
  concurrent deploys, graceful skip when `EC2_HOST` is not configured.
- Rollback steps in `docs/DEPLOYMENT.md`.

## Phase 6 – Terraform + AWS
- `infra/terraform`: default VPC, security group (80 public, 22 key-only),
  EC2 (Amazon Linux 2023, `t3.micro` default, IMDSv2 only, encrypted gp3,
  `cpu_credits = "standard"`), S3 backup bucket (versioning, public access
  blocked, encryption, lifecycle expiry), least-privilege IAM role and
  instance profile (S3 bucket + one SSM parameter + Session Manager),
  bot token as an SSM SecureString, $5 AWS Budget alerts, useful outputs.
- First-boot `user_data`: 2 GB swap, `vm.max_map_count` for Elasticsearch,
  Docker + Compose, clone, `.env` with the token read from SSM, start the
  stack from GHCR images (falls back to building), nightly backup cron.
- `scripts/backup_jobs.py`: scroll-export all jobs to gzipped JSON lines and
  upload to `s3://<bucket>/backups/YYYY/MM/DD/` (stdlib only, Python 3.9+).
- `docs/DEPLOYMENT.md`: AWS account setup, CLI, apply, verify, CloudWatch
  note, state explanation and `terraform destroy` reminder.
- Provider lock file for Linux, Windows and macOS.

## Phase 5 – GitHub Actions CI
- `ci.yml` on every push and pull request, no secrets required:
  ruff, pytest with coverage (fails under 85%), parser accuracy gate (95%),
  `docker compose config` check, coverage artifact.
- Matrix Docker build of api, bot and web with GitHub Actions layer cache.
- `terraform fmt -check` and `terraform validate` (init without backend).
- Least-privilege `permissions`, concurrency cancels outdated runs.
- CI/CD status badges in the README.

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
