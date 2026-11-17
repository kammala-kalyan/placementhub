"""The bot application wires every command (built offline with a dummy token)."""

import json
import logging

from telegram.ext import CommandHandler, MessageHandler

from bot.config import BotSettings
from bot.main import COMMANDS, JsonFormatter, build_application


def test_application_registers_all_commands_and_dependencies():
    settings = BotSettings(_env_file=None, telegram_bot_token="123456:TEST-TOKEN")
    app = build_application(settings)
    handlers = [h for group in app.handlers.values() for h in group]
    commands = {c for h in handlers if isinstance(h, CommandHandler) for c in h.commands}
    assert {"start", "help", "search", "latest", "deadlines", "filter", "whereami"} <= commands
    assert any(isinstance(h, MessageHandler) for h in handlers)
    assert {"api", "limiter", "settings"} <= set(app.bot_data)
    assert {c.command for c in COMMANDS} == {"search", "latest", "deadlines", "filter", "help"}


def test_json_log_lines():
    record = logging.LogRecord("bot", logging.INFO, __file__, 1, "hello", None, None)
    record.fields = {"status": "created"}
    line = json.loads(JsonFormatter().format(record))
    assert line["msg"] == "hello" and line["status"] == "created" and line["level"] == "INFO"
