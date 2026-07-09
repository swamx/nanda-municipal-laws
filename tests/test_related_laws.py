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


def test_related_laws_resolves_cross_references_within_corpus(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.get("/api/v1/sections/161.19/related")
    assert response.status_code == 200
    body = response.json()

    assert body["section_number"] == "161.19"
    ref = next(r for r in body["related"] if r["section_number"] == "161.01")
    assert ref["resolved"] is True
    assert ref["document_type"] == "NYC Health Code"
    assert ref["url"] is not None


def test_related_laws_marks_unresolvable_external_reference(client, monkeypatch):
    _ingest(client, monkeypatch)

    # §161.07 (Dangerous dogs) cites §3.07 "of this Code" - a real cross-reference
    # to a different Health Code article we haven't ingested, so it should be
    # reported as unresolved rather than silently dropped.
    response = client.get("/api/v1/sections/161.07/related")
    assert response.status_code == 200
    body = response.json()

    ref = next(r for r in body["related"] if r["section_number"] == "3.07")
    assert ref["resolved"] is False
    assert ref["url"] is None


def test_related_laws_not_found_for_unknown_section(client):
    response = client.get("/api/v1/sections/999.99/related")
    assert response.status_code == 404
