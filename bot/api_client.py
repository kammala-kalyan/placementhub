"""Async client for the PlacementHub API.

The bot talks only to the API, never to Elasticsearch, so all business logic
(parsing, dedup, caching) lives in one place.
"""

from datetime import datetime
from typing import Any

import httpx


class ApiError(Exception):
    """The API could not be reached or returned an error."""


class ApiClient:
    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or httpx.AsyncClient(base_url=base_url, timeout=10)

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            resp = await self.client.request(method, path, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise ApiError(f"{method} {path} failed: {exc}") from exc

    async def ingest(self, text: str, source: str, posted_at: datetime | None = None) -> dict:
        payload: dict[str, Any] = {"text": text, "source": source}
        if posted_at:
            payload["posted_at"] = posted_at.isoformat()
        return await self._request("POST", "/ingest", json=payload)

    async def search(self, **params: Any) -> dict:
        clean = {k: v for k, v in params.items() if v not in (None, "")}
        return await self._request("GET", "/jobs/search", params=clean)

    async def latest(self, limit: int = 5) -> dict:
        return await self._request("GET", "/jobs/latest", params={"limit": limit})

    async def deadlines(self, days: int = 3) -> dict:
        return await self._request("GET", "/jobs/deadlines", params={"days": days})

    async def aclose(self) -> None:
        await self.client.aclose()
