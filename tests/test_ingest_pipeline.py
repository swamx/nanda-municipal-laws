from pathlib import Path

import app.ingestion.pipeline as pipeline

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "t24_c02_sch04.html"
FIXTURE_URL = "https://nycadmincode.readthedocs.io/t24/c02/sch04/"


def test_ingest_url_persists_document_and_chunks(fake_db, monkeypatch):
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    monkeypatch.setattr(pipeline, "fetch_page", lambda url: html)

    chunks_ingested = pipeline.ingest_url(fake_db, FIXTURE_URL)

    assert chunks_ingested >= 6

    document = fake_db.laws.find_one_and_update(
        {"source_url": FIXTURE_URL, "type": "document"}, {"$set": {}}, upsert=True, return_document=True
    )
    assert document["title_num"] == "24"
    assert document["chapter_num"] == "2"
    assert document["subchapter_num"] == "4"

    section_222 = next(
        c for c in fake_db.laws._docs if c.get("type") == "chunk" and c["section_number"] == "24-222"
    )
    assert section_222["document_id"] == document["_id"]
    assert section_222["url"] == f"{FIXTURE_URL}#section-24-222"
    assert "construction" in section_222["section_title"].lower()


def test_ingest_url_is_idempotent_on_reingestion(fake_db, monkeypatch):
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    monkeypatch.setattr(pipeline, "fetch_page", lambda url: html)

    first_count = pipeline.ingest_url(fake_db, FIXTURE_URL)
    second_count = pipeline.ingest_url(fake_db, FIXTURE_URL)

    assert first_count == second_count
    assert len([d for d in fake_db.laws._docs if d.get("type") == "document"]) == 1
