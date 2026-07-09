from pathlib import Path

import app.ingestion.pdf_fetcher as pdf_fetcher

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "health_code_article161.txt"
FIXTURE_URL = "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf"


def _pages() -> list[str]:
    return FIXTURE_PATH.read_text(encoding="utf-8").split("\n\n===PAGE BREAK===\n\n")


def _ingest(client, monkeypatch):
    monkeypatch.setattr(pdf_fetcher, "fetch_pdf_pages", lambda url, **kwargs: _pages())
    response = client.post("/api/v1/ingest", json={"urls": [FIXTURE_URL]})
    assert response.status_code == 200


def test_find_permits_surfaces_permits_section(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post("/api/v1/permits", json={"query": "keep certain animals"})
    assert response.status_code == 200
    body = response.json()

    assert body["count"] > 0
    assert any(r["section_number"] == "161.09" for r in body["results"])
    assert "mentions_permit=true" in body["reasoning"]


def test_find_permits_without_query_returns_all_permit_flagged_chunks(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post("/api/v1/permits", json={})
    assert response.status_code == 200
    assert response.json()["count"] > 0


def test_find_penalties_filters_to_penalty_flagged_chunks(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post("/api/v1/penalties", json={})
    assert response.status_code == 200
    body = response.json()
    assert "mentions_penalty=true" in body["reasoning"]
