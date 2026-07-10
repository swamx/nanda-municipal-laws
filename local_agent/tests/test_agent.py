"""Unit tests for Agent._call's endpoint dispatch, with a fake ApiClient
(no real HTTP/app involved) - complements test_agent_integration.py, which
covers the same dispatch through the real API.
"""

from local_agent.agent import Agent
from local_agent.models import RoutingDecision


class _RecordingApiClient:
    def __init__(self):
        self.calls: list[tuple[str, tuple, dict]] = []

    def is_action_allowed(self, action, context=None):
        self.calls.append(("is_action_allowed", (action,), {"context": context}))
        return {"ok": True}

    def search(self, query, **filters):
        self.calls.append(("search", (query,), filters))
        return {"ok": True}

    def get_section(self, section_number):
        self.calls.append(("get_section", (section_number,), {}))
        return {"ok": True}

    def get_related(self, section_number):
        self.calls.append(("get_related", (section_number,), {}))
        return {"ok": True}

    def penalties(self, **params):
        self.calls.append(("penalties", (), params))
        return {"ok": True}

    def permits(self, **params):
        self.calls.append(("permits", (), params))
        return {"ok": True}


def test_call_passes_context_through_to_is_action_allowed():
    # Pins the fix for the "Queens" keyword-collision bug: the borough must
    # reach the API via `context`, not get folded into the searched text.
    fake_client = _RecordingApiClient()
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(
        endpoint="is_action_allowed",
        query_or_action="keep backyard chickens",
        context={"borough": "Queens"},
        reasoning="x",
    )

    agent._call(decision)

    assert fake_client.calls == [
        ("is_action_allowed", ("keep backyard chickens",), {"context": {"borough": "Queens"}})
    ]


def test_call_dispatches_search_with_document_type_filter():
    fake_client = _RecordingApiClient()
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(
        endpoint="search",
        query_or_action="rooster keeping poultry",
        document_type="NYC Health Code",
        reasoning="x",
    )

    agent._call(decision)

    assert fake_client.calls == [("search", ("rooster keeping poultry",), {"document_type": "NYC Health Code"})]


def test_call_dispatches_sections_and_sections_related():
    fake_client = _RecordingApiClient()
    agent = Agent(api_client=fake_client)

    agent._call(RoutingDecision(endpoint="sections", query_or_action="161.19", reasoning="x"))
    agent._call(RoutingDecision(endpoint="sections_related", query_or_action="161.19", reasoning="x"))

    assert fake_client.calls == [
        ("get_section", ("161.19",), {}),
        ("get_related", ("161.19",), {}),
    ]


def test_call_dispatches_penalties_and_permits_with_query_param():
    fake_client = _RecordingApiClient()
    agent = Agent(api_client=fake_client)

    agent._call(RoutingDecision(endpoint="penalties", query_or_action="noise", reasoning="x"))
    agent._call(RoutingDecision(endpoint="permits", query_or_action="keep certain animals", reasoning="x"))

    assert fake_client.calls == [
        ("penalties", (), {"query": "noise"}),
        ("permits", (), {"query": "keep certain animals"}),
    ]


class _SearchWithResultsApiClient(_RecordingApiClient):
    """Like _RecordingApiClient, but search/penalties/permits return a
    results list with a top section_number, and get_section returns a
    distinguishable full-text payload - lets tests assert the
    needs_full_text follow-up actually happened.
    """

    def search(self, query, **filters):
        self.calls.append(("search", (query,), filters))
        return {"results": [{"section_number": "16-119", "snippet": "...ro[truncated]"}], "count": 1}

    def penalties(self, **params):
        self.calls.append(("penalties", (), params))
        return {"results": [{"section_number": "16-119", "snippet": "...ro[truncated]"}], "count": 1}

    def get_section(self, section_number):
        self.calls.append(("get_section", (section_number,), {}))
        return {"section_number": section_number, "text": "full untruncated statutory text"}


def test_needs_full_text_true_chains_to_get_section_on_top_result():
    # Pins the fix for the "penalty for garbage not disposed correctly, give
    # me document snippet as well" case: a truncated /penalties snippet isn't
    # enough when the user explicitly wants the exact text, so the agent
    # should automatically look up the top result's full section text.
    fake_client = _SearchWithResultsApiClient()
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(
        endpoint="penalties", query_or_action="garbage disposal", needs_full_text=True, reasoning="x"
    )

    response = agent._call(decision)

    assert ("get_section", ("16-119",), {}) in fake_client.calls
    assert response["full_text_of_top_result"]["text"] == "full untruncated statutory text"


def test_needs_full_text_false_does_not_chain_to_get_section():
    fake_client = _SearchWithResultsApiClient()
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(
        endpoint="penalties", query_or_action="garbage disposal", needs_full_text=False, reasoning="x"
    )

    response = agent._call(decision)

    assert not any(call[0] == "get_section" for call in fake_client.calls)
    assert "full_text_of_top_result" not in response


def test_needs_full_text_true_with_no_results_does_not_error():
    fake_client = _RecordingApiClient()  # returns {"ok": True}, no "results" key
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(endpoint="search", query_or_action="nonsense", needs_full_text=True, reasoning="x")

    response = agent._call(decision)

    assert response == {"ok": True}


def test_needs_full_text_fails_open_when_get_section_errors():
    class _BrokenGetSectionApiClient(_SearchWithResultsApiClient):
        def get_section(self, section_number):
            raise RuntimeError("network error")

    fake_client = _BrokenGetSectionApiClient()
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(
        endpoint="penalties", query_or_action="garbage disposal", needs_full_text=True, reasoning="x"
    )

    response = agent._call(decision)

    assert "full_text_of_top_result" not in response
    assert response["results"][0]["section_number"] == "16-119"
