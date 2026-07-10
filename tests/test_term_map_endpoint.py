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


def test_term_map_highlights_real_occurrences_in_161_19(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post("/api/v1/sections/161.19/term_map", json={"query": "rooster poultry"})
    assert response.status_code == 200
    body = response.json()

    assert body["section_number"] == "161.19"
    assert set(body["term_map"].keys()) == {"rooster", "poultry"}
    assert body["total_occurrences"] > 0

    rooster_occurrence = body["term_map"]["rooster"][0]
    assert "<mark>rooster</mark>" in rooster_occurrence["snippet"].lower()
    assert "start" in rooster_occurrence and "end" in rooster_occurrence


def test_term_map_drops_stopwords_from_the_query(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post("/api/v1/sections/161.19/term_map", json={"query": "the rooster and the poultry"})
    assert response.status_code == 200
    body = response.json()

    assert "the" not in body["term_map"]
    assert "and" not in body["term_map"]
    assert set(body["term_map"].keys()) == {"rooster", "poultry"}


def test_term_map_omits_terms_with_no_real_match(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post("/api/v1/sections/161.19/term_map", json={"query": "rooster zebra"})
    assert response.status_code == 200
    body = response.json()

    assert "zebra" not in body["term_map"]
    assert "rooster" in body["term_map"]


def test_term_map_respects_context_chars(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post(
        "/api/v1/sections/161.19/term_map", json={"query": "rooster", "context_chars": 20}
    )
    assert response.status_code == 200
    snippet = response.json()["term_map"]["rooster"][0]["snippet"]
    # Bounded by context_chars=20 on each side (plus <mark> tag overhead),
    # not by the full section's several-thousand-character text.
    assert len(snippet) < 80


def test_term_map_returns_404_for_unknown_section(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post("/api/v1/sections/999.99/term_map", json={"query": "rooster"})
    assert response.status_code == 404


def test_term_map_rejects_empty_query(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post("/api/v1/sections/161.19/term_map", json={"query": ""})
    assert response.status_code == 422
