from pathlib import Path

import app.ingestion.fetcher as fetcher

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "t24_c02_sch04.html"
FIXTURE_URL = "https://nycadmincode.readthedocs.io/t24/c02/sch04/"


def _ingest_fixture(client, monkeypatch):
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    monkeypatch.setattr(fetcher, "fetch_page", lambda url: html)
    response = client.post("/api/v1/ingest", json={"urls": [FIXTURE_URL]})
    assert response.status_code == 200
    return response.json()


def test_health_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_version(client):
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert "version" in response.json()


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Municipal Legal Intelligence Service"
    assert response.json()["skill"] == "/skill.md"


def test_skill_md_served(client):
    response = client.get("/skill.md")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text.startswith("# Municipal Legal Intelligence Service")
    assert "/api/v1/ingest" not in response.text


def test_ingest_then_search_surfaces_construction_noise_section(client, monkeypatch):
    ingest_result = _ingest_fixture(client, monkeypatch)
    assert ingest_result["results"][0]["status"] == "ok"
    assert ingest_result["results"][0]["chunks_ingested"] >= 6

    # Query phrased with the section's own title terms - keyword/BM25-style
    # search ranks on term frequency, not phrase meaning, so a query using
    # "noise" alone would rank a different section (24-220, "Noise mitigation
    # plan") higher since 24-222's body never uses the word "noise" at all.
    response = client.post(
        "/api/v1/search", json={"query": "after hours weekend limits construction work"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    assert body["results"][0]["section_number"] == "24-222"
    assert body["results"][0]["url"] == f"{FIXTURE_URL}#section-24-222"


def test_ingest_then_retrieve_document_and_chunks(client, monkeypatch):
    _ingest_fixture(client, monkeypatch)

    search_response = client.post("/api/v1/search", json={"query": "construction"})
    document_id = search_response.json()["results"][0]["document_id"]

    doc_response = client.get(f"/api/v1/documents/{document_id}")
    assert doc_response.status_code == 200
    doc_body = doc_response.json()
    assert doc_body["source_url"] == FIXTURE_URL
    assert doc_body["subchapter_num"] == "4"

    chunks_response = client.get(f"/api/v1/documents/{document_id}/chunks")
    assert chunks_response.status_code == 200
    chunks = chunks_response.json()
    assert any(c["section_number"] == "24-222" for c in chunks)


def test_get_document_not_found(client):
    response = client.get("/api/v1/documents/000000000000000000000000")
    assert response.status_code == 404
