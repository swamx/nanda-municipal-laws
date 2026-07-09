from pathlib import Path

import app.ingestion.pdf_fetcher as pdf_fetcher
import app.ingestion.pipeline as pipeline

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "health_code_article161.txt"
FIXTURE_URL = "https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf"


def _pages() -> list[str]:
    return FIXTURE_PATH.read_text(encoding="utf-8").split("\n\n===PAGE BREAK===\n\n")


def test_ingest_url_dispatches_pdf_and_persists_health_code_chunks(fake_db, monkeypatch):
    monkeypatch.setattr(pdf_fetcher, "fetch_pdf_pages", lambda url, **kwargs: _pages())

    chunks_ingested = pipeline.ingest_url(fake_db, FIXTURE_URL)

    # 16 real sections, some split into multiple sub-chunks by the existing
    # chunker.py (long Health Code sections exceed the 2000-char threshold).
    assert chunks_ingested >= 16

    document = fake_db.laws.find_one_and_update(
        {"source_url": FIXTURE_URL, "type": "document"}, {"$set": {}}, upsert=True, return_document=True
    )
    assert document["document_type"] == "NYC Health Code"
    assert document["agency"] == "Department of Health and Mental Hygiene (DOHMH)"
    assert document["article_num"] == "161"

    section_161_19 = next(
        c for c in fake_db.laws._docs if c.get("type") == "chunk" and c["section_number"] == "161.19"
    )
    assert section_161_19["document_id"] == document["_id"]
    assert section_161_19["url"].startswith(f"{FIXTURE_URL}#page=")
    assert section_161_19["document_type"] == "NYC Health Code"
    # "authorized"/"authorized by ... law" appears in §161.19's real text (an
    # exception clause), so the permit heuristic correctly flags it True -
    # this is a documented, broad heuristic, not a bug.
    assert section_161_19["mentions_permit"] is True
    assert "poultry" in section_161_19["keywords"]
