# PlacementHub

Collects unstructured campus placement messages from Telegram, extracts
structured fields, removes duplicates, and makes openings searchable through a
Telegram bot and a web UI. Built to demonstrate Docker, Elasticsearch, Redis,
Terraform on AWS, GitHub Actions and Jenkins.

> Work in progress. The full README (architecture, AWS deployment, CI/CD,
> cost safety) is written in the final phase. See [docs/DESIGN.md](docs/DESIGN.md).

## Quick start (local)

Requirements: Docker Desktop, Python 3.12+ (only for the seed script and tests).

```bash
cp .env.example .env              # Windows PowerShell: Copy-Item .env.example .env
docker compose up -d --build      # starts Elasticsearch, Redis and the API
python -m scripts.seed            # loads 50 sample messages
```

Then open:
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Search: http://localhost:8000/jobs/search?q=data%20anlyst

## Run tests (no Docker needed)

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt     # Windows: .venv\Scripts\pip
.venv/bin/ruff check .
.venv/bin/pytest --cov=app --cov=parser
```

## Project layout

```
api/        FastAPI service (Dockerfile, app/)
parser/     Shared message parser (interface + implementations)
scripts/    Sample messages and seed script
tests/      Unit and API tests (fakes, no real services)
docs/       Design and interview notes
```
