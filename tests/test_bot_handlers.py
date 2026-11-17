"""Bot handlers and API client, with fake Telegram objects and a mocked HTTP transport."""

import asyncio
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from bot import handlers
from bot.api_client import ApiClient, ApiError
from bot.config import BotSettings

JOB = {"id": "h1", "category": "Internship", "company": "Lotus Cloudworks",
       "role": "DevOps Intern", "stipend_month": 28000, "location": "Bengaluru"}
LONG_TEXT = "Lotus Cloudworks – DevOps Intern\nStipend: ₹28,000 per month\nLocation: Bengaluru"


class FakeApi:
    """Records calls and returns canned answers, like the real ApiClient."""

    def __init__(self, fail: bool = False, status: str = "created") -> None:
        self.calls: list[tuple[str, dict]] = []
        self.fail = fail
        self.status = status

    async def _answer(self, name: str, **kwargs):
        self.calls.append((name, kwargs))
        if self.fail:
            raise ApiError("down")
        if name == "ingest":
            return {"id": "h1", "status": self.status, "job": JOB}
        return {"total": 1, "items": [JOB]}

    async def search(self, **kw):
        return await self._answer("search", **kw)

    async def latest(self, **kw):
        return await self._answer("latest", **kw)

    async def deadlines(self, **kw):
        return await self._answer("deadlines", **kw)

    async def ingest(self, text, **kw):
        return await self._answer("ingest", text=text, **kw)


class AllowAll:
    def __init__(self, allow: bool = True) -> None:
        self.allow_value = allow

    async def allow(self, user_id: int) -> bool:
        return self.allow_value


def make(args=None, api=None, limiter=None, chat_id=-100, text="", settings=None):
    message = MagicMock()
    message.reply_text = AsyncMock()
    message.chat_id = chat_id
    message.text = text
    message.caption = None
    message.message_thread_id = None
    message.date = datetime(2026, 11, 17, 10, 0, tzinfo=UTC)
    update = MagicMock()
    update.effective_message = message
    update.effective_user.id = 1
    context = MagicMock()
    context.args = args or []
    context.bot.send_message = AsyncMock()
    context.bot_data = {
        "api": api or FakeApi(),
        "limiter": limiter or AllowAll(),
        "settings": settings or BotSettings(_env_file=None),
    }
    return update, context


def replied_text(update) -> str:
    return update.effective_message.reply_text.call_args.args[0]


# ---------------------------------------------------------------- commands
def test_search_calls_api_and_replies_with_cards():
    api = FakeApi()
    update, context = make(args=["devops", "intern"], api=api)
    asyncio.run(handlers.search_cmd(update, context))
    assert api.calls == [("search", {"q": "devops intern", "size": 5})]
    assert "Lotus Cloudworks — DevOps Intern" in replied_text(update)


def test_search_without_text_shows_usage():
    api = FakeApi()
    update, context = make(api=api)
    asyncio.run(handlers.search_cmd(update, context))
    assert api.calls == [] and "Usage" in replied_text(update)


def test_filter_passes_parsed_filters_sorted_by_deadline():
    api = FakeApi()
    update, context = make(args=["role=devops", "location=bengaluru"], api=api)
    asyncio.run(handlers.filter_cmd(update, context))
    assert api.calls == [("search", {"role": "devops", "location": "bengaluru",
                                     "sort": "deadline", "size": 5})]


def test_latest_and_deadlines():
    api = FakeApi()
    update, context = make(api=api)
    asyncio.run(handlers.latest_cmd(update, context))
    asyncio.run(handlers.deadlines_cmd(update, context))
    assert [c[0] for c in api.calls] == ["latest", "deadlines"]
    assert api.calls[1][1] == {"days": 3}


def test_rate_limited_user_gets_told_and_api_is_not_called():
    api = FakeApi()
    update, context = make(args=["x"], api=api, limiter=AllowAll(allow=False))
    asyncio.run(handlers.search_cmd(update, context))
    assert api.calls == [] and "too quickly" in replied_text(update)


def test_api_down_gives_friendly_message():
    update, context = make(args=["x"], api=FakeApi(fail=True))
    asyncio.run(handlers.search_cmd(update, context))
    assert "unavailable" in replied_text(update)


def test_help_lists_commands():
    update, context = make()
    asyncio.run(handlers.help_cmd(update, context))
    text = replied_text(update)
    assert all(cmd in text for cmd in ("/search", "/latest", "/deadlines", "/filter"))


# ---------------------------------------------------------------- group ingestion
def forum_settings() -> BotSettings:
    return BotSettings(_env_file=None, source_chat_ids="-100", forum_chat_id="-200",
                       topic_internship_id="7")


def test_group_message_is_ingested_and_reposted_to_topic():
    api = FakeApi()
    update, context = make(api=api, text=LONG_TEXT, settings=forum_settings())
    asyncio.run(handlers.on_group_message(update, context))
    assert api.calls[0][0] == "ingest" and api.calls[0][1]["source"] == "telegram:-100"
    sent = context.bot.send_message.call_args.kwargs
    assert sent["chat_id"] == -200 and sent["message_thread_id"] == 7


def test_duplicates_are_not_reposted():
    update, context = make(api=FakeApi(status="duplicate"), text=LONG_TEXT,
                           settings=forum_settings())
    asyncio.run(handlers.on_group_message(update, context))
    context.bot.send_message.assert_not_called()


def test_messages_from_other_chats_and_short_messages_are_ignored():
    api = FakeApi()
    update, context = make(api=api, chat_id=-999, text=LONG_TEXT, settings=forum_settings())
    asyncio.run(handlers.on_group_message(update, context))
    update, context = make(api=api, text="thanks!", settings=forum_settings())
    asyncio.run(handlers.on_group_message(update, context))
    assert api.calls == []


def test_ingest_failure_does_not_crash():
    update, context = make(api=FakeApi(fail=True), text=LONG_TEXT, settings=forum_settings())
    asyncio.run(handlers.on_group_message(update, context))   # no exception
    context.bot.send_message.assert_not_called()


# ---------------------------------------------------------------- settings
def test_settings_parse_ids_and_topics():
    s = BotSettings(_env_file=None, source_chat_ids="-1, -2,abc", forum_chat_id="",
                    topic_fulltime_id="3", topic_other_id="9")
    assert s.source_ids() == {-1, -2}
    assert s.forum_id() is None
    assert s.topic_for("Full-time") == 3 and s.topic_for("Weird") == 9


def test_token_is_hidden_in_repr():
    s = BotSettings(_env_file=None, telegram_bot_token="123:SECRET")
    assert "SECRET" not in repr(s)


# ---------------------------------------------------------------- API client
def make_client(handler) -> ApiClient:
    transport = httpx.MockTransport(handler)
    return ApiClient("http://api", client=httpx.AsyncClient(base_url="http://api",
                                                            transport=transport))


def test_api_client_sends_expected_requests():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    client = make_client(handler)

    async def run():
        await client.search(q="data", role=None, size=5)
        await client.ingest("hello world message", source="telegram:-1")
        await client.aclose()

    asyncio.run(run())
    assert seen[0].url.path == "/jobs/search" and "role" not in seen[0].url.params
    assert json.loads(seen[1].content) == {"text": "hello world message",
                                           "source": "telegram:-1"}


@pytest.mark.parametrize("response", [httpx.Response(500), httpx.Response(503)])
def test_api_client_raises_api_error_on_server_errors(response):
    client = make_client(lambda request: response)
    with pytest.raises(ApiError):
        asyncio.run(client.latest())


def test_api_client_raises_api_error_when_unreachable():
    def handler(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(ApiError):
        asyncio.run(make_client(handler).deadlines())
