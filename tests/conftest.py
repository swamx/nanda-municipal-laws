import os

import pytest

os.environ.setdefault("MONGO_ATLAS_CONN_STR", "mongodb://localhost:27017")

from fastapi.testclient import TestClient  # noqa: E402

from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402
from tests.fake_mongo import FakeDatabase  # noqa: E402


@pytest.fixture
def fake_db():
    return FakeDatabase()


@pytest.fixture
def client(fake_db):
    app.dependency_overrides[get_db] = lambda: fake_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
