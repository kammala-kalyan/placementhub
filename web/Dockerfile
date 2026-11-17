# syntax=docker/dockerfile:1
# Build context is the repo root.
#
# Single stage on purpose: the UI is plain HTML/CSS/JS with no build step,
# so a multi-stage build would have nothing to leave behind. (If we added
# a bundler later, stage 1 would run it and stage 2 would copy only dist/.)

# nginx-unprivileged runs as a non-root user (uid 101) and listens on 8080.
FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY web/nginx.conf /etc/nginx/conf.d/default.conf
COPY web/index.html web/styles.css web/app.js /usr/share/nginx/html/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
