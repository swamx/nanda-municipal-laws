from app.config import settings


def test_requests_within_limit_succeed(client):
    for _ in range(settings.rate_limit_per_minute):
        response = client.get("/api/v1/health")
        assert response.status_code == 200


def test_request_over_limit_is_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_minute", 3)

    for _ in range(3):
        assert client.get("/api/v1/health").status_code == 200

    response = client.get("/api/v1/health")
    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_rate_limit_is_tracked_per_client(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_minute", 1)

    first = client.get("/api/v1/health", headers={"X-Forwarded-For": "1.1.1.1"})
    second = client.get("/api/v1/health", headers={"X-Forwarded-For": "2.2.2.2"})

    assert first.status_code == 200
    assert second.status_code == 200
