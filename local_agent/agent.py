from .api_client import ApiClient
from .composer import compose_answer
from .models import AgentAnswer, RoutingDecision
from .router import decide_route


class Agent:
    """Ties the three steps together: route -> call the real API -> compose.
    This is the local stand-in for what SKILL.md tells any autonomous agent
    to do on its own; nothing here runs server-side or gets deployed.
    """

    def __init__(self, api_client: ApiClient | None = None, model: str | None = None):
        self.api_client = api_client or ApiClient()
        self.model = model

    def ask(self, user_prompt: str) -> AgentAnswer:
        decision = decide_route(user_prompt, model=self.model)
        api_response = self._call(decision)
        return compose_answer(user_prompt, decision.endpoint, api_response, model=self.model)

    def _call(self, decision: RoutingDecision) -> dict:
        if decision.endpoint == "is_action_allowed":
            return self.api_client.is_action_allowed(decision.query_or_action, context=decision.context)
        if decision.endpoint == "search":
            params = {"document_type": decision.document_type} if decision.document_type else {}
            response = self.api_client.search(decision.query_or_action, **params)
            return self._maybe_attach_full_text(decision, response)
        if decision.endpoint == "sections":
            return self.api_client.get_section(decision.query_or_action)
        if decision.endpoint == "sections_related":
            return self.api_client.get_related(decision.query_or_action)
        if decision.endpoint == "penalties":
            response = self.api_client.penalties(query=decision.query_or_action)
            return self._maybe_attach_full_text(decision, response)
        if decision.endpoint == "permits":
            response = self.api_client.permits(query=decision.query_or_action)
            return self._maybe_attach_full_text(decision, response)
        raise ValueError(f"unknown endpoint: {decision.endpoint}")  # pragma: no cover - Literal-exhaustive

    def _maybe_attach_full_text(self, decision: RoutingDecision, response: dict) -> dict:
        """When the router flagged `needs_full_text` (the user wants an exact
        amount/quote, not just a snippet), fetch the top `full_text_count`
        results' full, untruncated text via GET /sections/{section_number}
        and attach them so the composer can quote precisely instead of a
        possibly-truncated search/penalties/permits snippet. The router
        decides the count: a broad question (e.g. "penalty for garbage not
        disposed correctly") can plausibly match several distinct sections
        (littering vs. dumping vs. commercial refuse), and keyword ranking
        alone doesn't reliably put the one the user actually meant on top -
        fetching just the top-1 result risks quoting the wrong section's
        full text while citing the right one by name only.

        Fails open per-lookup: if a follow-up lookup errors, that one
        section is skipped rather than failing the whole turn over an
        enrichment step. If every lookup fails, the original
        (snippet-only) response is returned unchanged.
        """
        if not decision.needs_full_text:
            return response
        results = response.get("results") or []
        if not results:
            return response

        full_texts = []
        for result in results[: decision.full_text_count]:
            section_number = result.get("section_number")
            if not section_number:
                continue
            try:
                full_texts.append(self.api_client.get_section(section_number))
            except Exception:  # noqa: BLE001 - enrichment only, never fail the turn over one bad lookup
                continue

        if not full_texts:
            return response
        return {**response, "full_text_of_top_results": full_texts}
