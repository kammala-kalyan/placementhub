# syntax=docker/dockerfile:1
# Build context is the repo root.

# ---------- Stage 1: install dependencies ----------
FROM python:3.12-slim AS builder
WORKDIR /build
COPY bot/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: small runtime image ----------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser
WORKDIR /srv

COPY --from=builder /install /usr/local
COPY bot/*.py ./bot/

USER appuser

# The bot has no HTTP port, so it proves it is alive by touching a heartbeat
# file every 30 s. Stale for more than 90 s (or missing) = unhealthy.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import os,sys,time; sys.exit(0 if time.time() - os.path.getmtime('/tmp/bot-heartbeat') < 90 else 1)"

CMD ["python", "-m", "bot.main"]
