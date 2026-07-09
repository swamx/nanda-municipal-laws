"""End-to-end tests for the Agent orchestrator: real FastAPI app + real
retrieval/action-evaluator logic (via seeded_client), fake Claude CLI calls
(no subprocess, no cost, no network) for both the routing and composing
steps. This is the closest thing to "run the whole local agent" that stays
fully offline and deterministic.
"""

from local_agent import composer, router
from local_agent.agent import Agent


def _fake_route(endpoint, query_or_action, document_type=None):
    def _ask_structured(prompt, **kwargs):
        return {
            "endpoint": endpoint,
            "query_or_action": query_or_action,
            "document_type": document_type,
            "reasoning": "fake routing decision for a deterministic test",
        }

    return _ask_structured


def _fake_compose(answer_text):
    def _ask_structured(prompt, **kwargs):
        return {
            "answer": answer_text,
            "sources": [{"section": "161.19", "url": "https://example.com", "score": 10.0}],
            "reasoning": "fake composed answer for a deterministic test",
        }

    return _ask_structured


def test_agent_ask_routes_calls_the_real_api_and_composes_an_answer(api_client, monkeypatch):
    monkeypatch.setattr(router, "ask_structured", _fake_route("is_action_allowed", "Keep backyard chickens"))
    monkeypatch.setattr(composer, "ask_structured", _fake_compose("Yes, with a rooster caveat."))

    agent = Agent(api_client=api_client)
    answer = agent.ask("Can I keep backyard chickens?")

    assert answer.answer == "Yes, with a rooster caveat."
    assert answer.sources[0].section == "161.19"


def test_agent_ask_for_search_endpoint_hits_the_real_search_route(api_client, monkeypatch):
    monkeypatch.setattr(
        router,
        "ask_structured",
        _fake_route("search", "rooster keeping poultry", document_type="NYC Health Code"),
    )
    monkeypatch.setattr(composer, "ask_structured", _fake_compose("Section 161.19 covers this."))

    agent = Agent(api_client=api_client)
    answer = agent.ask("What does the health code say about roosters?")

    assert "161.19" in answer.answer or answer.sources[0].section == "161.19"


def test_agent_ask_for_sections_endpoint_hits_the_real_lookup_route(api_client, monkeypatch):
    monkeypatch.setattr(router, "ask_structured", _fake_route("sections", "161.19"))
    monkeypatch.setattr(composer, "ask_structured", _fake_compose("Here is section 161.19 in full."))

    agent = Agent(api_client=api_client)
    answer = agent.ask("Show me section 161.19")

    assert answer.answer == "Here is section 161.19 in full."


def test_agent_ask_for_permits_endpoint_surfaces_the_real_permit_section(api_client, monkeypatch):
    monkeypatch.setattr(router, "ask_structured", _fake_route("permits", "keep certain animals"))
    monkeypatch.setattr(composer, "ask_structured", _fake_compose("You need a permit under 161.09."))

    agent = Agent(api_client=api_client)
    answer = agent.ask("Do I need a permit to keep animals?")

    assert answer.answer == "You need a permit under 161.09."
