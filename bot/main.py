"""Bot entry point:  python -m bot.main

Uses long polling: the bot repeatedly asks Telegram for new updates, so it
needs no public URL, domain or open inbound port (works the same on a laptop
and on EC2).
"""

import asyncio
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import redis.asyncio as aioredis
from telegram import BotCommand, Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters

from bot import handlers
from bot.api_client import ApiClient
from bot.config import BotSettings
from bot.rate_limit import RateLimiter

logger = logging.getLogger("placementhub.bot")
HEARTBEAT_FILE = Path("/tmp/bot-heartbeat")   # checked by the Docker HEALTHCHECK
HEARTBEAT_SECONDS = 30

COMMANDS = [
    BotCommand("search", "Search openings"),
    BotCommand("latest", "Newest openings"),
    BotCommand("deadlines", "Closing within 3 days"),
    BotCommand("filter", "Filter by role / location / category"),
    BotCommand("help", "How to use the bot"),
]


class JsonFormatter(logging.Formatter):
    """Same one-JSON-object-per-line format as the API logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {"ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
                   "level": record.levelname, "logger": record.name, "msg": record.getMessage()}
        payload.update(getattr(record, "fields", {}))
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=level.upper(), handlers=[handler], force=True)
    # httpx logs every Telegram poll at INFO, and those URLs contain the bot token.
    logging.getLogger("httpx").setLevel(logging.WARNING)


async def heartbeat() -> None:
    """Touch a file regularly; Docker marks the container unhealthy if it goes stale."""
    while True:
        HEARTBEAT_FILE.write_text(str(time.time()))
        await asyncio.sleep(HEARTBEAT_SECONDS)


def register_handlers(app: Application) -> None:
    app.add_handler(CommandHandler(["start", "help"], handlers.help_cmd))
    app.add_handler(CommandHandler("search", handlers.search_cmd))
    app.add_handler(CommandHandler("latest", handlers.latest_cmd))
    app.add_handler(CommandHandler("deadlines", handlers.deadlines_cmd))
    app.add_handler(CommandHandler("filter", handlers.filter_cmd))
    app.add_handler(CommandHandler("whereami", handlers.whereami_cmd))
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
        handlers.on_group_message))
    app.add_error_handler(handlers.on_error)


def build_application(settings: BotSettings) -> Application:
    async def post_init(app: Application) -> None:
        await app.bot.set_my_commands(COMMANDS)          # shows the "/" command menu
        app.create_task(heartbeat())
        logger.info("bot started", extra={"fields": {"sources": sorted(settings.source_ids()),
                                                     "forum": settings.forum_id()}})

    async def post_shutdown(app: Application) -> None:
        await app.bot_data["api"].aclose()

    app = (ApplicationBuilder()
           .token(settings.telegram_bot_token.get_secret_value())
           .post_init(post_init)
           .post_shutdown(post_shutdown)
           .build())
    redis_client = aioredis.Redis.from_url(settings.redis_url, socket_timeout=0.5,
                                           socket_connect_timeout=0.5)
    app.bot_data.update(
        settings=settings,
        api=ApiClient(settings.api_url),
        limiter=RateLimiter(redis_client, limit=settings.rate_limit_per_minute),
    )
    register_handlers(app)
    return app


def main() -> None:
    settings = BotSettings()
    setup_logging(settings.log_level)
    if not settings.telegram_bot_token.get_secret_value():
        # Stay up but unhealthy, so `docker compose up` still starts the rest of the stack.
        logger.error("TELEGRAM_BOT_TOKEN is not set; bot is idle. Add it to .env and restart.")
        while True:
            time.sleep(3600)
    build_application(settings).run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
