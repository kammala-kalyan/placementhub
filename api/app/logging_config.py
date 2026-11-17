"""Structured JSON logging.

One JSON object per line is easy to search in CloudWatch Logs or any log tool,
unlike free-text log lines.
"""

import json
import logging
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Format each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Extra structured fields: logger.info("x", extra={"fields": {...}})
        payload.update(getattr(record, "fields", {}))
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Send all logs (ours and uvicorn's) to stdout as JSON."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers = [handler]
        uv_logger.propagate = False
    # We log every request ourselves (with timing), so silence uvicorn's access log.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # The Elasticsearch client logs every HTTP call at INFO; too noisy.
    logging.getLogger("elastic_transport").setLevel(logging.WARNING)
