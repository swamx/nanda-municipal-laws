"""Fixtures for local_agent's test suite.

Reuses the *real* FastAPI app plus the main server test suite's in-memory
fake Mongo double (tests/fake_mongo.py) so these tests exercise the actual
route/retrieval/action-evaluator logic - no live network, no live Mongo,
no live deployment - while never needing a real `claude` CLI call either
(that's monkeypatched per-test; see test_claude_cli.py for the one place
that exercises the real subprocess-calling code path, with subprocess.run
itself faked).
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.ingestion.pdf_fetcher as pdf_fetcher
from app.config import settings as app_settings
from app.db import get_db
from app.main import app as fastapi_app
from local_agent.api_client import ApiClient
from tests.fake_mongo import FakeDatabase

_HEALTH_CODE_FIXTURE = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "health_code_article161.txt"
_HEALTH_CODE_URL = "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf"


@pytest.fixture(autouse=True)
def _no_ambient_ingest_api_key(monkeypatch):
    # Same fix as tests/conftest.py's fixture of the same name - pytest conftest
    # fixtures don't cross from tests/ into this sibling local_agent/tests/
    # directory, so it has to be duplicated here rather than shared. Without
    # this, seeding fixture data via /ingest breaks whenever the developer's
    # local .env has a real INGEST_API_KEY set (e.g. after locking down the
    # production deployment).
    monkeypatch.setattr(app_settings, "ingest_api_key", None)


@pytest.fixture
def fake_db():
    return FakeDatabase()


@pytest.fixture
def live_app_client(fake_db):
    """A TestClient wired to the real, in-process FastAPI app - not a mock of
    the API, the actual app - with a fake Mongo behind it.
    """
    fastapi_app.dependency_overrides[get_db] = lambda: fake_db
    with TestClient(fastapi_app) as client:
        yield client
    fastapi_app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def seeded_client(live_app_client, monkeypatch):
    """Same as live_app_client, but with the real Health Code Article 161
    fixture ingested first - gives tests real 161.19/161.01/161.09 data to
    exercise the flagship chicken/rooster examples against, exactly like
    tests/test_sections.py does for the main server suite.
    """
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


@pytest.fixture
def api_client(seeded_client):
    return ApiClient(client=seeded_client)
