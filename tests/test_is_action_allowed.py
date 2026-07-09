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


def test_keeping_a_rooster_is_explicitly_prohibited(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post("/api/v1/is_action_allowed", json={"action": "keep a rooster in my apartment"})
    assert response.status_code == 200
    body = response.json()

    assert body["allowed"] is False
    assert body["confidence"] == "high"
    assert body["citations"][0]["section_number"] == "161.19"
    assert "rooster" in body["reasoning"].lower()


def test_keeping_backyard_chickens_is_unrestricted_with_rooster_caveat(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post("/api/v1/is_action_allowed", json={"action": "Keep backyard chickens"})
    assert response.status_code == 200
    body = response.json()

    # No explicit statement about chickens/hens specifically (the real text
    # never uses those words - see docs/DATA_SOURCE.md), so this is an
    # absence-of-restriction inference, not an affirmative permission -
    # capped at "medium" confidence, never "high".
    assert body["allowed"] is True
    assert body["confidence"] == "medium"
    assert body["citations"][0]["section_number"] == "161.19"
    assert any("rooster" in c.lower() for c in body["conditions"])
    # Never fabricate the popular "max 6 hens" myth into a condition.
    assert not any("6 hens" in c.lower() or "maximum" in c.lower() for c in body["conditions"])


def test_unrelated_action_returns_unclear_not_a_guess(client, monkeypatch):
    _ingest(client, monkeypatch)

    response = client.post(
        "/api/v1/is_action_allowed", json={"action": "juggle flaming torches while unicycling on the moon"}
    )
    assert response.status_code == 200
    body = response.json()

    assert body["allowed"] is None
    assert body["confidence"] == "low"
    assert body["citations"] == []


def test_known_limitation_coincidental_common_word_can_still_match(client, monkeypatch):
    """Documents, rather than hides, a real limitation found while building
    this feature: a query sharing even one common/generic legal word (here,
    "party" - as in "a party to an action" - coincidentally also present in
    an unrelated section) with an ingested section can still produce a
    determinate result, even though the query has nothing to do with that
    section's actual subject. Keyword search can't distinguish "party" the
    legal term from "party" the celebration without semantic understanding,
    which this deterministic, non-LLM design deliberately doesn't attempt.
    Pinned here so any future change to this behavior is a deliberate
    decision, not an accidental regression - see SKILL.md's "Rules" section
    for the equivalent caller-facing guidance (always read `reasoning`).
    """
    _ingest(client, monkeypatch)

    response = client.post(
        "/api/v1/is_action_allowed", json={"action": "purple unicorn dance party fundraiser"}
    )
    assert response.status_code == 200
    body = response.json()

    # Current, known-imperfect behavior: a coincidental single-word match
    # ("party") still produces a low-relevance determination rather than
    # "unclear." Never "high" confidence, and the citation is real (not
    # fabricated) even though it's not actually on-topic.
    assert body["confidence"] != "high"
    assert body["citations"], "expected a (topically irrelevant but real) citation, matching known behavior"
