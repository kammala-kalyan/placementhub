"""Bot settings from environment variables.

Chat and topic ids are kept as plain strings and parsed here, so an empty
value in .env simply means "not configured" instead of a startup error.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def _to_int(value: str) -> int | None:
    value = value.strip()
    return int(value) if value.lstrip("-").isdigit() else None


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # SecretStr hides the token in logs and error messages ("**********").
    telegram_bot_token: SecretStr = SecretStr("")
    api_url: str = "http://localhost:8000"
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_per_minute: int = 10
    log_level: str = "INFO"

    # Placement groups to read and ingest from (comma-separated chat ids).
    source_chat_ids: str = ""
    # Forum group where structured cards are reposted, one topic per category.
    forum_chat_id: str = ""
    topic_fulltime_id: str = ""
    topic_internship_id: str = ""
    topic_hackathon_id: str = ""
    topic_other_id: str = ""

    def source_ids(self) -> set[int]:
        ids = (_to_int(part) for part in self.source_chat_ids.split(","))
        return {i for i in ids if i is not None}

    def forum_id(self) -> int | None:
        return _to_int(self.forum_chat_id)

    def topic_for(self, category: str) -> int | None:
        """Forum topic (message_thread_id) for a job category."""
        return _to_int({
            "Full-time": self.topic_fulltime_id,
            "Internship": self.topic_internship_id,
            "Hackathon": self.topic_hackathon_id,
        }.get(category, self.topic_other_id))
