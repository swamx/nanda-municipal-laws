import pytest
from pydantic import ValidationError

from local_agent import router
from local_agent.models import RoutingDecision


def test_decide_route_validates_claude_output_into_routing_decision(monkeypatch):
    monkeypatch.setattr(
        router,
        "ask_structured",
        lambda prompt, **kwargs: {
            "endpoint": "is_action_allowed",
            "query_or_action": "Keep backyard chickens",
            "reasoning": "yes/no legality question about a described action",
        },
    )

    decision = router.decide_route("Can I keep backyard chickens?")

    assert isinstance(decision, RoutingDecision)
    assert decision.endpoint == "is_action_allowed"
    assert decision.query_or_action == "Keep backyard chickens"


def test_decide_route_includes_skill_md_in_the_system_prompt(monkeypatch):
    captured = {}

    def _fake_ask_structured(prompt, *, system_prompt, json_schema, model=None, timeout=90.0):
        captured["system_prompt"] = system_prompt
        captured["json_schema"] = json_schema
        return {"endpoint": "search", "query_or_action": "noise", "reasoning": "general lookup"}

    monkeypatch.setattr(router, "ask_structured", _fake_ask_structured)

    router.decide_route("what does the noise code say?")

    assert "Municipal Law Skill for Autonomous Agents" in captured["system_prompt"]
    assert "endpoint" in captured["json_schema"]["properties"]


def test_decide_route_passes_model_through(monkeypatch):
    captured = {}

    def _fake_ask_structured(prompt, *, system_prompt, json_schema, model=None, timeout=90.0):
        captured["model"] = model
        return {"endpoint": "search", "query_or_action": "noise", "reasoning": "x"}

    monkeypatch.setattr(router, "ask_structured", _fake_ask_structured)

    router.decide_route("what does the noise code say?", model="opus")

    assert captured["model"] == "opus"


def test_decide_route_accepts_context_separate_from_query_or_action(monkeypatch):
    # Pins the fix for a real, observed failure mode: routing "keep backyard
    # chickens in Queens" with the borough folded into query_or_action let
    # "Queens" coincidentally match an unrelated cemetery-law section
    # (§25-112) via keyword search, producing a misleading allowed:false.
    # The system prompt now instructs the borough to go in `context` instead.
    monkeypatch.setattr(
        router,
        "ask_structured",
        lambda prompt, **kwargs: {
            "endpoint": "is_action_allowed",
            "query_or_action": "keep backyard chickens",
            "context": {"borough": "Queens"},
            "reasoning": "core action only; borough kept out of the keyword search",
        },
    )

    decision = router.decide_route("Can I keep backyard chickens in Queens?")

    assert decision.query_or_action == "keep backyard chickens"
    assert "queens" not in decision.query_or_action.lower()
    assert decision.context == {"borough": "Queens"}


def test_decide_route_raises_when_claude_returns_an_invalid_endpoint(monkeypatch):
    monkeypatch.setattr(
        router,
        "ask_structured",
        lambda prompt, **kwargs: {
            "endpoint": "not_a_real_endpoint",
            "query_or_action": "x",
            "reasoning": "y",
        },
    )

    with pytest.raises(ValidationError):
        router.decide_route("anything")
