import os

import pytest

os.environ.setdefault("MONGO_ATLAS_CONN_STR", "mongodb://localhost:27017")

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402
from tests.fake_mongo import FakeDatabase  # noqa: E402


@pytest.fixture(autouse=True)
def _no_ambient_ingest_api_key(monkeypatch):
    # Self-contained: most tests call /ingest with no X-Ingest-Api-Key header
    # and expect it to be open, regardless of whatever INGEST_API_KEY happens
    # to be set to in the developer's local .env (e.g. after locking down the
    # real Vercel deployment). Tests that actually exercise the auth gate
    # (test_ingest_security.py) explicitly monkeypatch their own value, which
    # simply overrides this default within that test.
    monkeypatch.setattr(settings, "ingest_api_key", None)


@pytest.fixture
def fake_db():
    return FakeDatabase()


@pytest.fixture
def client(fake_db):
    app.dependency_overrides[get_db] = lambda: fake_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
