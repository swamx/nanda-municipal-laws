from typing import Any

import httpx

from .config import settings


class ApiClient:
    """Thin wrapper over the Municipal Law Skill's public HTTP contract - the
    same requests any external autonomous agent would make per SKILL.md. This
    deliberately does NOT import app.* server internals: it only knows the
    documented JSON shapes, so it exercises the real, public contract rather
    than an implementation detail that could drift without this client
    noticing.

    Accepts an existing httpx.Client so tests can inject an in-process ASGI
    transport (see local_agent/tests/conftest.py) instead of hitting a real
    running server or the live Vercel deployment.
    """

    def __init__(self, base_url: str | None = None, client: httpx.Client | None = None):
        self._client = client or httpx.Client(base_url=base_url or settings.api_base_url, timeout=15.0)
        self._owns_client = client is None

    def is_action_allowed(self, action: str, context: dict[str, Any] | None = None) -> dict:
        resp = self._client.post(
            "/api/v1/is_action_allowed", json={"action": action, "context": context}
        )
        resp.raise_for_status()
        return resp.json()

    def search(self, query: str, **filters: Any) -> dict:
        resp = self._client.post("/api/v1/search", json={"query": query, **filters})
        resp.raise_for_status()
        return resp.json()

    def get_section(self, section_number: str) -> dict:
        resp = self._client.get(f"/api/v1/sections/{section_number}")
        resp.raise_for_status()
        return resp.json()

    def get_related(self, section_number: str) -> dict:
        resp = self._client.get(f"/api/v1/sections/{section_number}/related")
        resp.raise_for_status()
        return resp.json()

    def penalties(self, **params: Any) -> dict:
        resp = self._client.post("/api/v1/penalties", json=params)
        resp.raise_for_status()
        return resp.json()

    def permits(self, **params: Any) -> dict:
        resp = self._client.post("/api/v1/permits", json=params)
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
