from local_agent import composer
from local_agent.models import AgentAnswer


def _fake_response(**overrides):
    base = {
        "answer": "Yes, you can keep backyard chickens (hens), but roosters are prohibited.",
        "sources": [{"section": "161.19", "url": "https://example.com/health-code-article161.pdf", "score": 12.0}],
        "reasoning": "Derived from an absence-of-restriction inference in section 161.19.",
    }
    base.update(overrides)
    return base


def test_compose_answer_validates_claude_output_into_agent_answer(monkeypatch):
    monkeypatch.setattr(composer, "ask_structured", lambda prompt, **kwargs: _fake_response())

    answer = composer.compose_answer(
        "Can I keep backyard chickens?",
        "is_action_allowed",
        {"allowed": True, "confidence": "medium", "citations": [], "reasoning": "..."},
    )

    assert isinstance(answer, AgentAnswer)
    assert answer.sources[0].section == "161.19"


def test_compose_answer_includes_the_raw_api_response_and_skill_md_in_the_prompt(monkeypatch):
    captured = {}

    def _fake_ask_structured(prompt, *, system_prompt, json_schema, model=None, timeout=90.0):
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt
        return _fake_response()

    monkeypatch.setattr(composer, "ask_structured", _fake_ask_structured)

    api_response = {"allowed": False, "confidence": "high", "citations": [{"section_number": "161.19"}]}
    composer.compose_answer("keep a rooster?", "is_action_allowed", api_response)

    assert "161.19" in captured["prompt"]
    assert "Composing your final answer" in captured["system_prompt"]
    # Verified empirically that long, unconstrained answers add real latency
    # (1000+ output tokens, 30-40s) - this instruction measurably shortens
    # them without dropping the citation/caveat content.
    assert "concise" in captured["system_prompt"].lower()
    # Instructs the composer to prefer the enriched full-text follow-up
    # (see agent.py::_maybe_attach_full_text) over a truncated snippet.
    assert "full_text_of_top_result" in captured["system_prompt"]


def test_compose_answer_passes_model_through(monkeypatch):
    captured = {}

    def _fake_ask_structured(prompt, *, system_prompt, json_schema, model=None, timeout=90.0):
        captured["model"] = model
        return _fake_response()

    monkeypatch.setattr(composer, "ask_structured", _fake_ask_structured)

    composer.compose_answer("x", "search", {}, model="haiku")

    assert captured["model"] == "haiku"
