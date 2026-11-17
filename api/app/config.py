"""Application settings, read from environment variables (12-factor style).

The same Docker image runs locally and on EC2; only the environment changes.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration. Env var names are case-insensitive (ES_URL -> es_url)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    es_url: str = "http://localhost:9200"
    es_alias: str = "jobs"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 60
    parser: str = "simple"
    timezone: str = "Asia/Kolkata"   # used for "closing within N days"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Load settings once and reuse them."""
    return Settings()
