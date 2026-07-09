from pathlib import Path

import app.ingestion.fetcher as fetcher
from app.config import settings

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "t24_c02_sch04.html"


def test_ingest_rejects_batch_over_max_urls(client, monkeypatch):
    # Self-contained: pin the limit rather than depending on whatever
    # INGEST_MAX_URLS happens to be configured to in the ambient environment
    # (e.g. bumped locally for bulk publishing).
    monkeypatch.setattr(settings, "ingest_max_urls", 5)
    urls = [f"https://nycadmincode.readthedocs.io/t24/c02/sch01/?dup={i}" for i in range(6)]

    response = client.post("/api/v1/ingest", json={"urls": urls})
    assert response.status_code == 400


def test_ingest_requires_api_key_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "ingest_api_key", "test-secret")
    monkeypatch.setattr(fetcher, "fetch_page", lambda url: FIXTURE_PATH.read_text(encoding="utf-8"))
    # This test issues 3 calls to assert on auth, not rate limiting - raise
    # the ingest limit so it doesn't interfere with those assertions.
    monkeypatch.setattr(settings, "ingest_rate_limit_per_minute", 100)

    unauthenticated = client.post("/api/v1/ingest", json={"urls": ["https://example.com/"]})
    assert unauthenticated.status_code == 401

    wrong_key = client.post(
        "/api/v1/ingest",
        json={"urls": ["https://example.com/"]},
        headers={"X-Ingest-Api-Key": "wrong"},
    )
    assert wrong_key.status_code == 401

    authenticated = client.post(
        "/api/v1/ingest",
        json={"urls": ["https://example.com/"]},
        headers={"X-Ingest-Api-Key": "test-secret"},
    )
    assert authenticated.status_code == 200


def test_ingest_has_its_own_stricter_rate_limit(client, monkeypatch):
    monkeypatch.setattr(fetcher, "fetch_page", lambda url: FIXTURE_PATH.read_text(encoding="utf-8"))
    # Self-contained: pin the limit rather than depending on the ambient
    # INGEST_RATE_LIMIT_PER_MINUTE (e.g. bumped locally for bulk publishing).
    monkeypatch.setattr(settings, "ingest_rate_limit_per_minute", 1)

    first = client.post("/api/v1/ingest", json={"urls": ["https://example.com/"]})
    assert first.status_code == 200

    second = client.post("/api/v1/ingest", json={"urls": ["https://example.com/"]})
    assert second.status_code == 429


def test_ingest_rate_limit_does_not_share_bucket_with_general_endpoints(client, monkeypatch):
    monkeypatch.setattr(fetcher, "fetch_page", lambda url: FIXTURE_PATH.read_text(encoding="utf-8"))

    ingest_response = client.post("/api/v1/ingest", json={"urls": ["https://example.com/"]})
    assert ingest_response.status_code == 200

    # A single ingest call shouldn't count against the separate general-scope
    # bucket used by health/search/documents.
    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200
