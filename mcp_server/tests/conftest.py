"""Fixtures for mcp_server's test suite.

Same pattern as local_agent/tests/conftest.py (duplicated rather than shared -
pytest conftest fixtures don't cross into a sibling test directory): wires the
*real* FastAPI app plus the main suite's in-memory fake Mongo, then points
mcp_server.server's module-level ApiClient at that in-process TestClient
instead of the network - so these tests exercise the real MCP tool functions
against real route/retrieval logic with no live network, no live Mongo, and
no live deployment.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.ingestion.pdf_fetcher as pdf_fetcher
import mcp_server.server as mcp_server_module
from app.config import settings as app_settings
from app.db import get_db
from app.main import app as fastapi_app
from local_agent.api_client import ApiClient
from tests.fake_mongo import FakeDatabase

_HEALTH_CODE_FIXTURE = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "health_code_article161.txt"
_HEALTH_CODE_URL = "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf"


@pytest.fixture(autouse=True)
def _no_ambient_ingest_api_key(monkeypatch):
    monkeypatch.setattr(app_settings, "ingest_api_key", None)


@pytest.fixture
def fake_db():
    return FakeDatabase()


@pytest.fixture
def live_app_client(fake_db):
    fastapi_app.dependency_overrides[get_db] = lambda: fake_db
    with TestClient(fastapi_app) as client:
        yield client
    fastapi_app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def seeded_client(live_app_client, monkeypatch):
    monkeypatch.setattr(
        pdf_fetcher,
        "fetch_pdf_pages",
        lambda url, **kwargs: _HEALTH_CODE_FIXTURE.read_text(encoding="utf-8").split(
            "\n\n===PAGE BREAK===\n\n"
        ),
    )
    response = live_app_client.post("/api/v1/ingest", json={"urls": [_HEALTH_CODE_URL]})
    assert response.status_code == 200
    return live_app_client


@pytest.fixture(autouse=True)
def _wire_mcp_tools_to_the_in_process_app(seeded_client, monkeypatch):
    """Points the MCP tool functions' shared ApiClient at the seeded
    in-process app instead of the real network default (settings.api_base_url)."""
    monkeypatch.setattr(mcp_server_module, "_client", ApiClient(client=seeded_client))
