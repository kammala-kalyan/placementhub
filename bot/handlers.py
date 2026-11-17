"""Telegram update handlers.

Dependencies (API client, rate limiter, settings) are stored in
context.bot_data at startup, so handlers stay small and tests can inject fakes.
"""

import logging

from telegram import LinkPreviewOptions, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.api_client import ApiClient, ApiError
from bot.config import BotSettings
from bot.formatting import (
    HELP_TEXT,
    format_job,
    format_job_list,
    parse_filter_args,
    today_ist,
)
from bot.rate_limit import RateLimiter

logger = logging.getLogger("placementhub.bot")

MIN_MESSAGE_LENGTH = 30          # ignore "ok", "thanks" etc. in the group
NO_PREVIEW = LinkPreviewOptions(is_disabled=True)
API_DOWN_TEXT = "Sorry, the search service is unavailable right now. Please try again shortly."


async def reply(update: Update, text: str) -> None:
    await update.effective_message.reply_text(
        text, parse_mode=ParseMode.HTML, link_preview_options=NO_PREVIEW)


async def allowed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Apply the per-user rate limit to a command."""
    limiter: RateLimiter | None = context.bot_data.get("limiter")
    user = update.effective_user
    if limiter is None or user is None or await limiter.allow(user.id):
        return True
    await reply(update, "You're sending commands too quickly. Please wait a minute.")
    return False


# ---------------------------------------------------------------- commands


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await allowed(update, context):
        await reply(update, HELP_TEXT)


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update, context):
        return
    query = " ".join(context.args or []).strip()
    if not query:
        await reply(update, "Usage: /search &lt;text&gt;, e.g. /search data analyst")
        return
    api: ApiClient = context.bot_data["api"]
    try:
        data = await api.search(q=query, size=5)
    except ApiError:
        logger.exception("search failed")
        await reply(update, API_DOWN_TEXT)
        return
    await reply(update, format_job_list(f'Results for "{query}"', data, today_ist()))


async def latest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update, context):
        return
    try:
        data = await context.bot_data["api"].latest(limit=5)
    except ApiError:
        logger.exception("latest failed")
        await reply(update, API_DOWN_TEXT)
        return
    await reply(update, format_job_list("Latest openings", data, today_ist()))


async def deadlines_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update, context):
        return
    try:
        data = await context.bot_data["api"].deadlines(days=3)
    except ApiError:
        logger.exception("deadlines failed")
        await reply(update, API_DOWN_TEXT)
        return
    await reply(update, format_job_list("Closing within 3 days", data, today_ist()))


async def filter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update, context):
        return
    filters = parse_filter_args(context.args or [])
    if not filters:
        await reply(update, "Usage: /filter role=&lt;x&gt; location=&lt;y&gt; category=&lt;z&gt;\n"
                            "e.g. /filter role=devops location=bengaluru")
        return
    try:
        data = await context.bot_data["api"].search(**filters, sort="deadline", size=5)
    except ApiError:
        logger.exception("filter failed")
        await reply(update, API_DOWN_TEXT)
        return
    label = ", ".join(f"{k}={v}" for k, v in filters.items())
    await reply(update, format_job_list(f"Filter: {label}", data, today_ist()))


async def whereami_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Setup helper: shows the chat id and forum topic id to put in .env."""
    if not await allowed(update, context):
        return
    message = update.effective_message
    await reply(update, f"chat_id: <code>{message.chat_id}</code>\n"
                        f"topic_id: <code>{message.message_thread_id or '-'}</code>")


# ---------------------------------------------------------------- group messages


async def on_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ingest placement messages from source groups and repost them to forum topics."""
    message = update.effective_message
    settings: BotSettings = context.bot_data["settings"]
    if message is None or message.chat_id not in settings.source_ids():
        return
    text = message.text or message.caption
    if not text or len(text) < MIN_MESSAGE_LENGTH:
        return

    try:
        result = await context.bot_data["api"].ingest(
            text, source=f"telegram:{message.chat_id}", posted_at=message.date)
    except ApiError:
        logger.exception("ingest failed")
        return

    job = result["job"]
    logger.info("ingested", extra={"fields": {"status": result["status"],
                                              "category": job.get("category")}})
    forum_id = settings.forum_id()
    if result["status"] != "created" or forum_id is None:
        return   # duplicates are not reposted
    await context.bot.send_message(
        chat_id=forum_id,
        message_thread_id=settings.topic_for(job.get("category", "Other")),
        text=format_job(job, today_ist()),
        parse_mode=ParseMode.HTML,
        link_preview_options=NO_PREVIEW,
    )


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log any unhandled error instead of crashing the bot."""
    logger.error("unhandled bot error", exc_info=context.error)
