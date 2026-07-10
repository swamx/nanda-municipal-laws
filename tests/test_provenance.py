from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.signing import canonicalize, public_key_hex


def _verify(response_body: dict) -> None:
    provenance = response_body["provenance"]
    signable = {k: v for k, v in response_body.items() if k != "provenance"}
    public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(provenance["public_key"]))
    public_key.verify(bytes.fromhex(provenance["signature"]), canonicalize(signable))


def test_search_response_is_signed_and_verifiable(client, monkeypatch):
    import app.ingestion.pdf_fetcher as pdf_fetcher
    from pathlib import Path

    fixture = Path(__file__).parent / "fixtures" / "health_code_article161.txt"
    pages = fixture.read_text(encoding="utf-8").split("\n\n===PAGE BREAK===\n\n")
    monkeypatch.setattr(pdf_fetcher, "fetch_pdf_pages", lambda url, **kwargs: pages)
    client.post(
        "/api/v1/ingest",
        json={"urls": ["https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf"]},
    )

    response = client.post("/api/v1/search", json={"query": "rooster"})
    assert response.status_code == 200
    body = response.json()

    assert body["provenance"]["algorithm"] == "ed25519"
    assert body["provenance"]["public_key"] == public_key_hex()
    _verify(body)


def test_is_action_allowed_response_is_signed_and_verifiable(client, monkeypatch):
    import app.ingestion.pdf_fetcher as pdf_fetcher
    from pathlib import Path

    fixture = Path(__file__).parent / "fixtures" / "health_code_article161.txt"
    pages = fixture.read_text(encoding="utf-8").split("\n\n===PAGE BREAK===\n\n")
    monkeypatch.setattr(pdf_fetcher, "fetch_pdf_pages", lambda url, **kwargs: pages)
    client.post(
        "/api/v1/ingest",
        json={"urls": ["https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf"]},
    )

    response = client.post("/api/v1/is_action_allowed", json={"action": "keep a rooster"})
    assert response.status_code == 200
    body = response.json()

    _verify(body)


def test_tampering_with_a_signed_field_breaks_verification(client, monkeypatch):
    import app.ingestion.pdf_fetcher as pdf_fetcher
    from pathlib import Path

    fixture = Path(__file__).parent / "fixtures" / "health_code_article161.txt"
    pages = fixture.read_text(encoding="utf-8").split("\n\n===PAGE BREAK===\n\n")
    monkeypatch.setattr(pdf_fetcher, "fetch_pdf_pages", lambda url, **kwargs: pages)
    client.post(
        "/api/v1/ingest",
        json={"urls": ["https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf"]},
    )

    response = client.post("/api/v1/search", json={"query": "rooster"})
    body = response.json()
    body["query"] = "tampered query"

    try:
        _verify(body)
        assert False, "expected signature verification to fail on tampered payload"
    except Exception:
        pass


def test_pubkey_endpoint_matches_signing_key(client):
    response = client.get("/api/v1/pubkey")
    assert response.status_code == 200
    body = response.json()
    assert body["public_key"] == public_key_hex()
    assert body["algorithm"] == "ed25519"


def test_version_reports_null_freshness_for_empty_corpus(client):
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    body = response.json()
    assert body["corpus_last_ingested_at"] is None
    assert body["corpus_age_days"] is None


def test_version_reports_corpus_freshness_after_ingest(client, monkeypatch):
    import app.ingestion.pdf_fetcher as pdf_fetcher
    from pathlib import Path

    fixture = Path(__file__).parent / "fixtures" / "health_code_article161.txt"
    pages = fixture.read_text(encoding="utf-8").split("\n\n===PAGE BREAK===\n\n")
    monkeypatch.setattr(pdf_fetcher, "fetch_pdf_pages", lambda url, **kwargs: pages)
    client.post(
        "/api/v1/ingest",
        json={"urls": ["https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcode/health-code-article161.pdf"]},
    )

    response = client.get("/api/v1/version")
    body = response.json()
    assert body["corpus_last_ingested_at"] is not None
    assert body["corpus_age_days"] == 0
