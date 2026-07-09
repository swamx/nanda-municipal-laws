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


def test_get_section_returns_structural_summary_and_metadata(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.get("/api/v1/sections/161.19")
    assert response.status_code == 200
    body = response.json()

    assert body["section_number"] == "161.19"
    assert body["document_type"] == "NYC Health Code"
    assert body["agency"] == "Department of Health and Mental Hygiene (DOHMH)"
    assert body["jurisdiction"] == "New York City"
    assert body["effective_date"] is None
    assert body["repealed"] is False
    assert "161.01" in body["cross_references"]

    # Never fabricate a numeric hen limit that isn't in the real source text.
    assert "6 hens" not in body["text"].lower()
    assert "maximum" not in body["text"].lower()

    summary = body["structural_summary"]
    assert len(summary) >= 3
    assert any(s.startswith("(a)") for s in summary)
    assert any(s.startswith("(b)") for s in summary)
    assert any(s.startswith("(c)") for s in summary)


def test_get_section_not_found(client):
    response = client.get("/api/v1/sections/999.99")
    assert response.status_code == 404
