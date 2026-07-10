from pathlib import Path

import app.ingestion.fetcher as fetcher
import app.retrieval as retrieval
from app.config import settings

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "t24_c02_sch04.html"
FIXTURE_URL = "https://nycadmincode.readthedocs.io/t24/c02/sch04/"


def _ingest(client, monkeypatch):
    monkeypatch.setattr(fetcher, "fetch_page", lambda url: FIXTURE_PATH.read_text(encoding="utf-8"))
    response = client.post("/api/v1/ingest", json={"urls": [FIXTURE_URL]})
    assert response.status_code == 200


def test_default_search_mode_is_text_index():
    assert settings.search_mode == "text_index"


def test_search_uses_text_index_mode_by_default(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post(
        "/api/v1/search", json={"query": "after hours weekend limits construction work"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["section_number"] == "24-222"
    assert "$text/textScore" in body["reasoning"]


def test_search_can_be_overridden_to_in_app_mode_per_request(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post(
        "/api/v1/search",
        json={"query": "after hours weekend limits construction work", "search_mode": "in_app"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["section_number"] == "24-222"
    assert "in-app scoring" in body["reasoning"]


def test_search_can_be_overridden_to_idf_mode_per_request(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post(
        "/api/v1/search",
        json={"query": "after hours weekend limits construction work", "search_mode": "idf"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["section_number"] == "24-222"
    assert "IDF-weighted" in body["reasoning"]


def test_search_falls_back_to_in_app_when_text_index_unavailable(client, monkeypatch):
    _ingest(client, monkeypatch)

    from pymongo.errors import OperationFailure

    def _raise_operation_failure(*args, **kwargs):
        raise OperationFailure("text index required for $text query")

    monkeypatch.setattr(retrieval, "_search_via_text_index", _raise_operation_failure)

    response = client.post(
        "/api/v1/search", json={"query": "after hours weekend limits construction work"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["section_number"] == "24-222"
    assert "in-app scoring" in body["reasoning"]
