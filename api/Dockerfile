# syntax=docker/dockerfile:1
# Build context is the repo root (the API also needs the shared parser/ package).

# ---------- Stage 1: install dependencies ----------
FROM python:3.12-slim AS builder
WORKDIR /build
COPY api/requirements.txt .
# --prefix puts packages in /install so we can copy just them into the final image.
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: small runtime image ----------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Run as a non-root user: if the app is compromised, the attacker is not root.
RUN useradd --create-home --uid 10001 appuser
WORKDIR /srv

COPY --from=builder /install /usr/local
COPY parser/ ./parser/
COPY api/app/ ./app/

USER appuser
EXPOSE 8000

# Docker marks the container unhealthy if /health fails 3 times in a row.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
