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


_THREE_RESULTS = [
    {"section_number": "16-520", "snippet": "...trade waste licensee[truncated]", "score": 2.86},
    {"section_number": "16-119", "snippet": "...unlawful dumping[truncated]", "score": 1.0},
    {"section_number": "16-118", "snippet": "...littering prohibited[truncated]", "score": 0.9},
]


class _SearchWithResultsApiClient(_RecordingApiClient):
    """Like _RecordingApiClient, but search/penalties/permits return a
    ranked, multi-result list, and get_section returns a distinguishable
    full-text payload per section - lets tests assert the needs_full_text
    follow-up fetches the right number of results in ranked order.
    """

    def search(self, query, **filters):
        self.calls.append(("search", (query,), filters))
        return {"results": list(_THREE_RESULTS), "count": len(_THREE_RESULTS)}

    def penalties(self, **params):
        self.calls.append(("penalties", (), params))
        return {"results": list(_THREE_RESULTS), "count": len(_THREE_RESULTS)}

    def get_section(self, section_number):
        self.calls.append(("get_section", (section_number,), {}))
        return {"section_number": section_number, "text": f"full untruncated text of {section_number}"}


def test_needs_full_text_true_chains_to_get_section_on_top_result_by_default():
    # Pins the fix for the "penalty for garbage not disposed correctly, give
    # me document snippet as well" case: a truncated /penalties snippet isn't
    # enough when the user explicitly wants the exact text, so the agent
    # should automatically look up the top result's full section text.
    # full_text_count defaults to 1, so only the single top result is fetched.
    fake_client = _SearchWithResultsApiClient()
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(
        endpoint="penalties", query_or_action="garbage disposal", needs_full_text=True, reasoning="x"
    )

    response = agent._call(decision)

    get_section_calls = [c for c in fake_client.calls if c[0] == "get_section"]
    assert get_section_calls == [("get_section", ("16-520",), {})]
    assert [r["section_number"] for r in response["full_text_of_top_results"]] == ["16-520"]


def test_needs_full_text_count_fetches_top_n_in_ranked_order():
    # The router can ask for more than 1 when a broad query could plausibly
    # match several distinct sections (littering vs. dumping vs. commercial
    # refuse) - keyword ranking alone can't tell which one the user meant.
    fake_client = _SearchWithResultsApiClient()
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(
        endpoint="penalties",
        query_or_action="garbage disposal",
        needs_full_text=True,
        full_text_count=3,
        reasoning="x",
    )

    response = agent._call(decision)

    get_section_calls = [c[1][0] for c in fake_client.calls if c[0] == "get_section"]
    assert get_section_calls == ["16-520", "16-119", "16-118"]
    assert [r["section_number"] for r in response["full_text_of_top_results"]] == [
        "16-520",
        "16-119",
        "16-118",
    ]


def test_needs_full_text_count_capped_by_available_results():
    fake_client = _SearchWithResultsApiClient()  # only 3 results available
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(
        endpoint="penalties",
        query_or_action="garbage disposal",
        needs_full_text=True,
        full_text_count=5,
        reasoning="x",
    )

    response = agent._call(decision)

    assert len(response["full_text_of_top_results"]) == 3


def test_needs_full_text_false_does_not_chain_to_get_section():
    fake_client = _SearchWithResultsApiClient()
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(
        endpoint="penalties", query_or_action="garbage disposal", needs_full_text=False, reasoning="x"
    )

    response = agent._call(decision)

    assert not any(call[0] == "get_section" for call in fake_client.calls)
    assert "full_text_of_top_results" not in response


def test_needs_full_text_true_with_no_results_does_not_error():
    fake_client = _RecordingApiClient()  # returns {"ok": True}, no "results" key
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(endpoint="search", query_or_action="nonsense", needs_full_text=True, reasoning="x")

    response = agent._call(decision)

    assert response == {"ok": True}


def test_needs_full_text_skips_a_failing_lookup_but_keeps_the_rest():
    class _OneBrokenSectionApiClient(_SearchWithResultsApiClient):
        def get_section(self, section_number):
            self.calls.append(("get_section", (section_number,), {}))
            if section_number == "16-119":
                raise RuntimeError("network error")
            return {"section_number": section_number, "text": f"full untruncated text of {section_number}"}

    fake_client = _OneBrokenSectionApiClient()
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(
        endpoint="penalties",
        query_or_action="garbage disposal",
        needs_full_text=True,
        full_text_count=3,
        reasoning="x",
    )

    response = agent._call(decision)

    assert [r["section_number"] for r in response["full_text_of_top_results"]] == ["16-520", "16-118"]


def test_needs_full_text_fails_open_when_every_lookup_errors():
    class _AllBrokenApiClient(_SearchWithResultsApiClient):
        def get_section(self, section_number):
            raise RuntimeError("network error")

    fake_client = _AllBrokenApiClient()
    agent = Agent(api_client=fake_client)
    decision = RoutingDecision(
        endpoint="penalties", query_or_action="garbage disposal", needs_full_text=True, reasoning="x"
    )

    response = agent._call(decision)

    assert "full_text_of_top_results" not in response
    assert response["results"][0]["section_number"] == "16-520"
