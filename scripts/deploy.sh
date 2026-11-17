#!/usr/bin/env bash
# Runs ON the EC2 server. The CD workflow pipes this file over SSH:
#   { export SHA=...; export GHCR_USER=...; export GHCR_TOKEN=...; cat deploy.sh; } | ssh ... bash -s
# The registry token travels inside the encrypted SSH session (stdin), not as
# a command-line argument that other users on the server could see.
set -euo pipefail

: "${SHA:?commit SHA is required}"
APP_DIR=/opt/placementhub
cd "$APP_DIR"

echo "==> Updating code to $SHA"
git fetch --quiet origin
git reset --hard "$SHA"          # compose file and scripts now match the images

echo "==> Pinning image tag (restarts and reboots keep this exact version)"
sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=$SHA/" .env

echo "==> Pulling images from GHCR"
if [ -n "${GHCR_TOKEN:-}" ]; then
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
fi
docker compose pull api bot web
docker logout ghcr.io >/dev/null 2>&1 || true

echo "==> Restarting changed containers"
docker compose up -d --remove-orphans
docker image prune -f >/dev/null

echo "==> Waiting for the API to report healthy"
for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null; then
    echo "Deploy of $SHA is healthy (attempt $attempt)"
    exit 0
  fi
  sleep 5
done

echo "API did not become healthy - showing diagnostics"
docker compose ps
docker compose logs --tail 50 api
exit 1
